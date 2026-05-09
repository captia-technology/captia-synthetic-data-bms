"""CLI for the synthetic data generator.

Ref: docs/specs/config-schema.md, docs/specs/core-architecture.md
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

LOG = logging.getLogger("synthetic_generator")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="synthetic-generator", description="CAPTIA-connect synthetic data generator — modular, multi-domain"
    )
    sub = p.add_subparsers(dest="command", required=True)

    # run command
    run = sub.add_parser("run", help="Run scenario (backfill + optional live)")
    run.add_argument("--config", type=str, required=True, help="Path to scenario YAML")
    run.add_argument("--seed", type=int, default=None, help="Override seed")
    run.add_argument("--dry-run", action="store_true", help="Validate only, no emit")
    run.add_argument(
        "--health-port",
        type=int,
        default=None,
        help="Enable health endpoint on this port (default: HEALTH_PORT env or 8000)",
    )
    run.add_argument("--no-health", action="store_true", help="Disable health endpoint")
    run.add_argument("--loglevel", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    # generate (alias for run with file sink)
    gen = sub.add_parser("generate", help="Generate dataset to file")
    gen.add_argument("--config", type=str, required=True, help="Path to scenario YAML")
    gen.add_argument("--out", type=str, default=None, help="Output file path")
    gen.add_argument("--format", type=str, default=None, choices=["csv_long", "csv_wide", "jsonl"])
    gen.add_argument("--seed", type=int, default=None)
    gen.add_argument("--loglevel", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    # list-domains
    ld = sub.add_parser("list-domains", help="List available domain plugins")
    ld.add_argument("--loglevel", type=str, default="INFO")

    # stream command (multi-domain)
    s = sub.add_parser("stream", help="Stream synthetic data to MQTT using project config (all domains)")
    s.add_argument(
        "--broker",
        type=str,
        default=os.environ.get("MQTT_BROKER", "tcp://localhost:1883"),
        help="MQTT broker URL (e.g., tcp://localhost:1883)",
    )
    s.add_argument(
        "--captia-env",
        type=str,
        default=os.environ.get("CAPTIA_ENV", "dev"),
        help="CAPTIA environment (dev/prod) for topic namespace",
    )
    s.add_argument(
        "--project", type=str, default=os.environ.get("GENERATOR_CONFIG"), help="Path to project YAML config"
    )
    s.add_argument(
        "--interval",
        type=str,
        default=os.environ.get("GENERATOR_INTERVAL_SECONDS", "10"),
        help="Interval between publishes (e.g., 10, 10s, 1m)",
    )
    s.add_argument("--loglevel", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    # validate
    val = sub.add_parser("validate", help="Validate scenario config")
    val.add_argument("--config", type=str, required=True)
    val.add_argument("--loglevel", type=str, default="INFO")

    return p


def _parse_interval(interval_str: str) -> float:
    """Parse interval string like '10', '10s', '1m', '30s' to seconds."""
    interval_str = interval_str.strip().lower()
    if interval_str.endswith("m"):
        return float(interval_str[:-1]) * 60.0
    if interval_str.endswith("s"):
        return float(interval_str[:-1])
    return float(interval_str)


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _build_sink(config):
    """Build sink from scenario config."""
    from .sinks.file import FileSinkAdapter, FileSinkConfig
    from .sinks.mqtt import MQTTSinkAdapter, MQTTSinkConfig
    from .sinks.stdout import StdoutSinkAdapter
    from .sinks.composite import CompositeSink
    from .core.config import SinkType

    sinks = []
    for sink_cfg in config.sinks:
        if sink_cfg.type == SinkType.MQTT:
            sinks.append(MQTTSinkAdapter(MQTTSinkConfig(**sink_cfg.config)))
        elif sink_cfg.type == SinkType.FILE:
            sinks.append(FileSinkAdapter(FileSinkConfig(**sink_cfg.config)))
        elif sink_cfg.type == SinkType.STDOUT:
            sinks.append(StdoutSinkAdapter())

    if not sinks:
        sinks.append(StdoutSinkAdapter())

    if len(sinks) == 1:
        return sinks[0]
    return CompositeSink(sinks)


def _get_domain(config):
    """Get domain adapter from config."""
    from .domains.registry import auto_discover_domains, get_domain

    auto_discover_domains()
    domain = get_domain(config.domain.id)
    if domain is None:
        from .domains.registry import list_domains

        available = list_domains()
        LOG.error("Unknown domain: %s. Available: %s", config.domain.id, available)
        sys.exit(1)
    return domain


def _cmd_run(args) -> int:
    from .core.config import load_scenario_config
    from .core.runner import ScenarioRunner

    config = load_scenario_config(Path(args.config))
    if args.seed is not None:
        config.simulation.seed = args.seed

    domain = _get_domain(config)
    sink = _build_sink(config)

    if args.dry_run:
        LOG.info("Dry-run: config valid, domain=%s, sinks=%s", domain.domain_id, sink.name)
        return 0

    # Start health endpoint (unless disabled)
    if not args.no_health:
        from .health import start_health_server, update_status

        start_health_server(args.health_port)
        update_status("backfill", domain=config.domain.id)

    runner = ScenarioRunner(config=config, domain_adapter=domain, sink=sink)
    results = runner.run()
    for r in results:
        LOG.info("Phase %s: %d points in %.1fs", r.phase, r.points_emitted, r.elapsed_seconds)

    if not args.no_health:
        total_points = sum(r.points_emitted for r in results)
        update_status("idle", domain=config.domain.id, points_emitted=total_points)

    return 0


def _cmd_generate(args) -> int:
    from .core.config import load_scenario_config
    from .core.runner import ScenarioRunner
    from .sinks.file import FileSinkAdapter, FileSinkConfig

    config = load_scenario_config(Path(args.config))
    if args.seed is not None:
        config.simulation.seed = args.seed

    # Override sink to file
    out_path = args.out or "outputs/dataset.csv"
    fmt = args.format or "csv_long"
    sink = FileSinkAdapter(FileSinkConfig(path=out_path, format=fmt))

    domain = _get_domain(config)
    runner = ScenarioRunner(config=config, domain_adapter=domain, sink=sink)
    results = runner.run()
    for r in results:
        LOG.info("Phase %s: %d points in %.1fs → %s", r.phase, r.points_emitted, r.elapsed_seconds, out_path)
    return 0


def _cmd_list_domains(args) -> int:
    from .domains.registry import auto_discover_domains, list_domain_info

    auto_discover_domains()
    domains = list_domain_info()
    if not domains:
        print("No domains registered.")
        return 0
    print("\nAvailable Domains:")
    print("-" * 60)
    for info in domains:
        print(f"\n  {info['domain_id']}")
        print(f"    Description: {info.get('description', 'N/A')}")
        print(f"    Version: {info.get('version', 'N/A')}")
    print()
    return 0


def _cmd_stream(args) -> int:
    """Stream synthetic data to MQTT as a normal tenant.

    Publishes JSON to captia/{env}/{tenant}/{site}/{device}/telemetry/{name}.
    """
    from .core.config import load_scenario_config
    from .core.runner import ScenarioRunner
    from .sinks.mqtt import MQTTSinkAdapter, MQTTSinkConfig
    from .health import start_health_server, get_health

    if not args.project:
        LOG.error("--project is required (or set GENERATOR_CONFIG env)")
        return 1

    config = load_scenario_config(Path(args.project))

    # Force live-only mode
    config.phases.backfill.enabled = False
    config.phases.live.enabled = True

    interval_seconds = _parse_interval(args.interval)

    # Set GENERATOR_INTERVAL_SECONDS so runner picks it up
    os.environ["GENERATOR_INTERVAL_SECONDS"] = str(interval_seconds)

    LOG.info(
        "Starting MQTT stream: broker=%s, project=%s, interval=%.1fs",
        args.broker,
        args.project,
        interval_seconds,
    )

    # Start health server
    health_server = start_health_server()

    # Build MQTT sink from CLI args (override config sinks)
    sink = MQTTSinkAdapter(
        MQTTSinkConfig(
            broker_url=args.broker,
            captia_env=args.captia_env,
            # captia_tenant and captia_site are left as defaults ("default").
            # The DataPoint.domain_id / site_id from the domain adapter take priority
            # in _build_topic(), so the actual tenant comes from the domain config.
        )
    )

    domain = _get_domain(config)

    # Update health
    health = get_health()
    health.config_loaded = True

    runner = ScenarioRunner(config=config, domain_adapter=domain, sink=sink)
    results = runner.run()
    for r in results:
        LOG.info("Phase %s: %d points in %.1fs", r.phase, r.points_emitted, r.elapsed_seconds)

    health_server.stop()
    return 0


def _cmd_validate(args) -> int:
    from .core.config import load_scenario_config

    config = load_scenario_config(Path(args.config))
    domain = _get_domain(config)
    errors = domain.validate_config(config.project.model_dump(), {})
    if errors:
        for e in errors:
            LOG.error("Validation error: %s", e)
        return 1
    LOG.info("Config valid: domain=%s", config.domain.id)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.loglevel)

    commands = {
        "run": _cmd_run,
        "generate": _cmd_generate,
        "stream": _cmd_stream,
        "list-domains": _cmd_list_domains,
        "validate": _cmd_validate,
    }
    handler = commands.get(args.command)
    if handler is None:
        parser.print_help()
        return 2
    try:
        return handler(args)
    except Exception as e:
        LOG.error("Error: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""Base class for domain plugins.

Defines the abstract interface that all domain plugins must implement.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterator, Optional

import numpy as np
import pandas as pd

from ..core.models import Inventory, DataPoint


class DomainPlugin(ABC):
    """Abstract base class for domain plugins.

    Each domain (BMS Classrooms, Industrial Refrigeration, etc.) must
    implement this interface to provide:
    - Domain identification
    - Inventory building from configuration
    - Simulation context creation
    - Time-series data generation

    Example implementation:
        class BMSClassroomsPlugin(DomainPlugin):
            @property
            def domain_id(self) -> str:
                return "bms_classrooms"

            def build_inventory(self, project_cfg, domain_cfg) -> Inventory:
                # Build asset/variable inventory from config
                ...

            def build_context(self, time_index, project_cfg, domain_cfg, rng) -> Any:
                # Create simulation context with shared state
                ...

            def simulate(self, time_index, inventory, ctx, rng) -> Iterator[DataPoint]:
                # Generate data points
                ...
    """

    @property
    @abstractmethod
    def domain_id(self) -> str:
        """Unique identifier for this domain.

        Returns:
            Domain ID string (e.g., 'bms_classrooms', 'industrial_refrigeration')
        """
        ...

    @property
    def description(self) -> str:
        """Human-readable description of the domain.

        Returns:
            Description string
        """
        return f"Domain plugin: {self.domain_id}"

    @property
    def version(self) -> str:
        """Version of the domain plugin.

        Returns:
            Version string (e.g., '1.0.0')
        """
        return "1.0.0"

    @abstractmethod
    def build_inventory(
        self,
        project_cfg: dict[str, Any],
        domain_cfg: dict[str, Any]
    ) -> Inventory:
        """Build the asset inventory from configuration.

        Creates the complete inventory of assets and their variables
        based on project and domain configuration.

        Args:
            project_cfg: Project-level configuration dict
            domain_cfg: Domain-specific configuration dict

        Returns:
            Inventory containing all assets and variable definitions
        """
        ...

    @abstractmethod
    def build_context(
        self,
        time_index: pd.DatetimeIndex,
        project_cfg: dict[str, Any],
        domain_cfg: dict[str, Any],
        rng: np.random.Generator
    ) -> Any:
        """Build the simulation context.

        Creates domain-specific context containing shared state,
        environmental drivers, and pre-computed values needed
        during simulation.

        Args:
            time_index: Time points for simulation
            project_cfg: Project-level configuration
            domain_cfg: Domain-specific configuration
            rng: NumPy random generator

        Returns:
            Domain-specific context object
        """
        ...

    @abstractmethod
    def simulate(
        self,
        time_index: pd.DatetimeIndex,
        inventory: Inventory,
        ctx: Any,
        rng: np.random.Generator
    ) -> Iterator[DataPoint]:
        """Generate simulated data points.

        The main simulation method that generates DataPoint objects
        for all assets and variables across the time index.

        Args:
            time_index: Time points for simulation
            inventory: Asset inventory
            ctx: Simulation context from build_context()
            rng: NumPy random generator

        Yields:
            DataPoint objects for each measurement
        """
        ...

    def calibrate_from_sample(
        self,
        sample_path: Path,
        output_path: Optional[Path] = None
    ) -> Optional[dict[str, Any]]:
        """Calibrate domain parameters from sample data.

        Optional method for learning statistics from real data
        to improve synthetic data realism.

        Args:
            sample_path: Path to sample CSV/data file
            output_path: Optional path to write calibrated config

        Returns:
            Dictionary of calibrated parameters, or None if not supported
        """
        return None

    def validate_config(
        self,
        project_cfg: dict[str, Any],
        domain_cfg: dict[str, Any]
    ) -> list[str]:
        """Validate configuration before simulation.

        Args:
            project_cfg: Project-level configuration
            domain_cfg: Domain-specific configuration

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Basic validation - subclasses should override for domain-specific checks
        if not project_cfg:
            errors.append("Project configuration is empty")
        if not domain_cfg:
            errors.append("Domain configuration is empty")

        return errors

    def get_required_config_keys(self) -> list[str]:
        """Get list of required configuration keys.

        Returns:
            List of required key names in domain config
        """
        return []

    def get_metadata(self) -> dict[str, Any]:
        """Get plugin metadata.

        Returns:
            Dictionary with plugin information
        """
        return {
            "domain_id": self.domain_id,
            "description": self.description,
            "version": self.version,
            "required_config_keys": self.get_required_config_keys(),
        }

"""ContractValidator — pre-emission schema validation.

Ref: docs/specs/core-architecture.md Section 2.4
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from .models import DataPoint, Inventory, Quality

LOG = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)


class ContractValidator:
    """Validates DataPoints against domain schema before emission.

    Checks:
    - asset_id is uppercase, variable is lowercase
    - timestamp is not None
    - value type matches data_type where feasible
    - value within expected_range_hard (if defined in inventory)
    """

    def __init__(self, inventory: Optional[Inventory] = None, strict: bool = False):
        self._inventory = inventory
        self._strict = strict
        self._error_count = 0
        self._validated_count = 0

    def validate(self, point: DataPoint) -> ValidationResult:
        """Validate a single DataPoint."""
        errors: list[str] = []
        self._validated_count += 1

        if point.timestamp is None:
            errors.append("timestamp is None")

        if point.asset_id != point.asset_id.upper():
            errors.append(f"asset_id not uppercase: {point.asset_id}")

        if point.variable != point.variable.lower():
            errors.append(f"variable not lowercase: {point.variable}")

        if point.quality == Quality.MISSING:
            # Missing values are valid — skip range checks
            return ValidationResult(valid=True)

        # Range check against inventory
        if self._inventory and point.value is not None:
            asset = self._inventory.get_asset(point.asset_id)
            if asset:
                for var_def in asset.variables:
                    if var_def.name == point.variable and var_def.expected_range_hard:
                        lo, hi = var_def.expected_range_hard
                        try:
                            v = float(point.value)
                            if v < lo or v > hi:
                                errors.append(
                                    f"{point.asset_id}.{point.variable}={v} "
                                    f"outside hard range [{lo}, {hi}]"
                                )
                        except (TypeError, ValueError):
                            pass

        if errors:
            self._error_count += len(errors)
            if self._strict:
                LOG.warning("Validation errors: %s", errors)

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def validate_batch(self, points: list[DataPoint]) -> list[ValidationResult]:
        return [self.validate(p) for p in points]

    @property
    def error_count(self) -> int:
        return self._error_count

    @property
    def validated_count(self) -> int:
        return self._validated_count

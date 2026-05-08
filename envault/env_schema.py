"""Schema validation for .env files — enforce required keys, types, and patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


VALID_TYPES = {"str", "int", "float", "bool"}


@dataclass
class SchemaRule:
    key: str
    required: bool = True
    value_type: str = "str"
    pattern: Optional[str] = None
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "required": self.required,
            "value_type": self.value_type,
            "pattern": self.pattern,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SchemaRule":
        return cls(
            key=data["key"],
            required=data.get("required", True),
            value_type=data.get("value_type", "str"),
            pattern=data.get("pattern"),
            description=data.get("description", ""),
        )


@dataclass
class ValidationError:
    key: str
    message: str

    def __str__(self) -> str:
        return f"{self.key}: {self.message}"


def validate_env(env: Dict[str, str], rules: List[SchemaRule]) -> List[ValidationError]:
    """Validate an env dict against a list of SchemaRules.

    Returns a list of ValidationError (empty means valid).
    """
    errors: List[ValidationError] = []

    for rule in rules:
        if rule.value_type not in VALID_TYPES:
            errors.append(ValidationError(rule.key, f"unknown type '{rule.value_type}' in schema"))
            continue

        value = env.get(rule.key)

        if value is None:
            if rule.required:
                errors.append(ValidationError(rule.key, "required key is missing"))
            continue

        # Type coercion check
        if rule.value_type == "int":
            try:
                int(value)
            except ValueError:
                errors.append(ValidationError(rule.key, f"expected int, got '{value}'"))
        elif rule.value_type == "float":
            try:
                float(value)
            except ValueError:
                errors.append(ValidationError(rule.key, f"expected float, got '{value}'"))
        elif rule.value_type == "bool":
            if value.lower() not in {"true", "false", "1", "0", "yes", "no"}:
                errors.append(ValidationError(rule.key, f"expected bool, got '{value}'"))

        # Pattern check
        if rule.pattern and not re.fullmatch(rule.pattern, value):
            errors.append(ValidationError(rule.key, f"value does not match pattern '{rule.pattern}'"))

    return errors

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


FieldSemanticType = Literal["bool", "enum", "int", "float"]
FieldControlFamily = Literal["toggle", "selector", "slider", "stepper"]


@dataclass(frozen=True)
class FieldOption:
    value: Any
    label: str


@dataclass(frozen=True)
class FieldSpec:
    label: str
    attr_name: str
    semantic_type: FieldSemanticType
    control_family: FieldControlFamily
    min_value: int | float | None = None
    max_value: int | float | None = None
    options: tuple[FieldOption, ...] = ()

    def is_numeric(self) -> bool:
        return self.semantic_type in {"int", "float"}

    def is_bool(self) -> bool:
        return self.semantic_type == "bool"

    def is_enum(self) -> bool:
        return self.semantic_type == "enum"

    def uses_slider(self) -> bool:
        if not self.is_numeric() or self.control_family != "slider":
            return False
        if self.min_value is None or self.max_value is None:
            return False
        return float(self.max_value) > float(self.min_value)

    def allows_numeric_text_input(self) -> bool:
        return self.is_numeric()

    def format_value(self, value: object) -> str:
        if self.is_bool():
            return "ON" if bool(value) else "OFF"
        if self.is_enum():
            return self.enum_label(value)
        if self.semantic_type == "int":
            return str(int(value))
        if self.semantic_type == "float":
            return str(float(value))
        return str(value)

    def enum_label(self, value: object) -> str:
        option = self.matching_option(value)
        if option is not None:
            return option.label
        return str(value)

    def matching_option(self, value: object) -> FieldOption | None:
        for option in self.options:
            if option.value == value:
                return option
        if isinstance(value, int) and not isinstance(value, bool):
            if 0 <= int(value) < len(self.options):
                return self.options[int(value)]
        return None

    def cycle_enum_value(self, current: object, delta: int) -> Any:
        if not self.options:
            return current
        option_values = tuple(option.value for option in self.options)
        try:
            current_index = option_values.index(current)
        except ValueError:
            if isinstance(current, int) and not isinstance(current, bool):
                current_index = max(0, min(len(option_values) - 1, int(current)))
            else:
                current_index = 0
        return option_values[(current_index + int(delta)) % len(option_values)]

    def toggle_value(self, current: object) -> Any:
        if isinstance(current, bool):
            return not current
        return 0 if bool(current) else 1

    def clamp_numeric_value(self, value: object) -> int | float:
        if not self.is_numeric():
            raise TypeError("clamp_numeric_value requires a numeric field")
        minimum = 0.0 if self.min_value is None else float(self.min_value)
        maximum = minimum if self.max_value is None else float(self.max_value)
        numeric = float(value)
        clamped = max(minimum, min(maximum, numeric))
        if self.semantic_type == "int":
            return int(round(clamped))
        return clamped

from . import InputHook, OutputHook, Parameter, Metric, Artifact
from typing import Any
import yaml

# Example hooks
class YAMLConfigInput(InputHook):
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
            print("LOADED YAML")

    def load(self, name: str, type_hint: type) -> Any | None:
        print(f"Got {name} from Yaml")
        return self.config.get(name)

    def validate(self, name: str, value: Any, type_hint: type | None = None) -> Any:
        return value  # No validation in YAML loader

class RangeValidationHook(InputHook):
    def __init__(self, param_ranges: dict[str, tuple[float, float]]):
        self.param_ranges = param_ranges

    def load(self, name: str, type_hint: type) -> Any | None:
        return None  # This hook only validates

    def validate(self, name: str, value: Any, type_hint: type | None = None) -> Any:
        if name in self.param_ranges:
            min_val, max_val = self.param_ranges[name]
            if not (min_val <= value <= max_val):
                raise ValueError(
                    f"{name} value {value} must be between {min_val} and {max_val}"
                )
        print(f"Validated range for {name}")
        return value

class TypeValidationHook(InputHook):
    def load(self, name: str, type_hint: type) -> Any | None:
        return None  # This hook only validates

    def validate(self, name: str, value: Any, type_hint: type) -> Any:
        # Get the actual type from the Parameter/Metric/Artifact
        origin = getattr(type_hint, '__origin__', None)
        if origin in (Parameter, Metric, Artifact):
            expected_type = type_hint.__args__[0]
            if not isinstance(value, expected_type):
                raise TypeError(
                    f"{name} must be of type {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )
        print(f"Validated Type of {name} as {type(value).__name__}")
        return value

class MLflowOutput(OutputHook):
    def save(self, name: str, value: Any, type_hint: type) -> None:
        origin = getattr(type_hint, '__origin__', None)
        if origin is Parameter:
            print("mlflow.log_param(", name, value, ")")
        elif origin is Metric:
            print("mlflow.log_metric(", name, value, ")")
        elif origin is Artifact:
            print("mlflow.log_artifact(", name, ")")

from typing import TypeVar, Any
from hooksett import register_tracked_type, InputHook, OutputHook

# Define ML-specific type variables
T = TypeVar('T')

# Register ML-specific types
type Parameter[T] = T
type Metric[T] = T
type Artifact[T] = T

# Register them with hooksett
register_tracked_type('Parameter', Parameter)
register_tracked_type('Metric', Metric)
register_tracked_type('Artifact', Artifact)

# MLflow output hook
class MLflowOutput(OutputHook):
    """Hook that logs values to MLflow"""
    
    def save(self, name: str, value: Any, type_hint: type) -> None:
        """Save a value to MLflow based on its tracked type"""
        origin = getattr(type_hint, '__origin__', None)
        
        if origin is Parameter:
            print(f"mlflow.log_param({name}, {value})")
        elif origin is Metric:
            print(f"mlflow.log_metric({name}, {value})")
        elif origin is Artifact:
            print(f"mlflow.log_artifact({name})")
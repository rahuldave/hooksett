from hooksett import HookManager, tracked
from hooksett import Parameter, Metric, Artifact
from hooksett.hooks import RangeValidationHook, TypeValidationHook, YAMLConfigInput, MLflowOutput


def init_hooks(
    config_path: str | None = None,
    use_mlflow: bool = True,
    param_ranges: dict[str, tuple[float, float]] | None = None
):
    """Initialize the hook system"""
    manager = HookManager()

    # Add validation hooks
    if param_ranges:
        manager.add_input_hook(RangeValidationHook(param_ranges))
    manager.add_input_hook(TypeValidationHook())

    # Add loading hooks
    if config_path:
        manager.add_input_hook(YAMLConfigInput(config_path))

    # Add output hooks
    if use_mlflow:
        manager.add_output_hook(MLflowOutput())

# Example class
@tracked
class Model:
    # Will load from hook if available
    learning_rate: Parameter[float]
    # Will use explicit default
    batch_size: Parameter[int] = 32
    # Will load from hook
    weights: Artifact[list[float]]
    # Metrics always start with default
    accuracy: Metric[float] = 0.0

    def train(self, epochs: int):
        for _ in range(epochs):
            # Values are validated when set
            self.accuracy = self.accuracy + 0.1


# Initialize hooks with validation
init_hooks(
    config_path="examples/config.yaml",
    use_mlflow=True,
    param_ranges={
        'learning_rate': (0.0, 1.0),
        'batch_size': (1, 128)
    }
)

# Class usage
model = Model()  # learning_rate loaded from yaml
model.learning_rate = 0.1  # Validated against range
model.train(epochs=3)

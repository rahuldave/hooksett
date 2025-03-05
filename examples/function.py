from hooksett import HookManager, track_function
from hooksett import Parameter, Metric
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

# Example function
@track_function
def train_model(
    learning_rate: Parameter[float] = None,  # None means "try hooks"
    batch_size: Parameter[int] = 32,         # Explicit default
    epochs: int = 10                         # Regular parameter
) -> float:
    # Use the parameters
    # Now make a metric
    auc: Metric[float] = 0.95
    return auc


# Initialize hooks with validation
init_hooks(
    config_path="examples/config.yaml",
    use_mlflow=True,
    param_ranges={
        'learning_rate': (0.0, 1.0),
        'batch_size': (1, 128)
    }
)


# Function usage
# Uses hook for learning_rate, default for batch_size
print("CALL 1, Uses hook for learning_rate, default for batch_size")
result1 = train_model()

# Uses explicit values, still validates them
print("CALL 2, Uses explicit values, still validates them")
result2 = train_model(learning_rate=0.01, batch_size=64)

# Would raise ValueError due to range validation
print("CALL 3, will error")
try:
    result3 = train_model(learning_rate=2.0)
except ValueError as e:
    print(f"Validation error: {e}")

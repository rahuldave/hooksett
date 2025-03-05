from hooksett import HookManager, track_function
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


# Example function with local tracked variables
@track_function
def process_data(
    learning_rate: Parameter[float] = None,  # Function parameter (from signature)
    epochs: int = 5
) -> float:
    # Local variable with Parameter annotation
    batch_size: Parameter[int] = 32
    
    # Local variable with Metric annotation
    accuracy: Metric[float] = 0.0
    
    # Processing logic
    for i in range(epochs):
        # Update local metrics during processing
        accuracy = accuracy + 0.1 * learning_rate * batch_size / 100
    
    # These annotations will be tracked and output hooks will be called
    return accuracy


# Initialize hooks with validation
init_hooks(
    config_path="examples/config.yaml",
    use_mlflow=True,
    param_ranges={
        'learning_rate': (0.0, 1.0),
        'batch_size': (1, 128)
    }
)

# Function usage with local variable tracking
print("\nRun #1: Using learning rate from config")
result1 = process_data()  # learning_rate from config, batch_size as local default
print(f"Result: {result1}")

print("\nRun #2: Using explicit learning_rate")
result2 = process_data(learning_rate=0.2)  # explicit learning_rate
print(f"Result: {result2}")
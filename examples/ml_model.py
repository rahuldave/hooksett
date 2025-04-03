from hooksett import HookManager, tracked, track_function
from ml_types import Parameter, Metric, Artifact, MLflowOutput
from hooksett.hooks import RangeValidationHook, TypeValidationHook, YAMLConfigInput

def init_hooks(
    config_path: str | None = None,
    use_mlflow: bool = True,
    param_ranges: dict[str, tuple[float, float]] | None = None
):
    """Initialize the hook system for ML tracking"""
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

# Example ML class
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
            
    def evaluate(self):
        # Demonstrate local variable tracking
        precision: Metric[float] = 0.85
        recall: Metric[float] = 0.92
        f1_score: Metric[float] = 2 * (precision * recall) / (precision + recall)
        return f1_score

# Example ML function with tracked parameters
@track_function
def preprocess_data(
    normalize: Parameter[bool] = True,
    augment: Parameter[bool] = False,
    batch_size: Parameter[int] = 64
):
    # Local variables will be tracked
    processed_count: Metric[int] = 1000
    processing_time: Metric[float] = 2.5
    return {"processed": processed_count, "time": processing_time}

# Initialize hooks with validation
init_hooks(
    config_path="config.yaml",
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
f1 = model.evaluate()
print(f"F1 score: {f1}")

# Function usage
stats = preprocess_data()
print(f"Preprocessing stats: {stats}")
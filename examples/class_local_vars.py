"""
Example demonstrating local variable tracking in class methods
"""
from hooksett import HookManager, tracked, Traced
from hooksett.hooks import RangeValidationHook, TypeValidationHook, YAMLConfigInput, TracedOutput
from ml_types import Parameter, Metric, Artifact, MLflowOutput


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
    manager.add_output_hook(TracedOutput())
    if use_mlflow:
        manager.add_output_hook(MLflowOutput())


# Example class with local variables in methods
@tracked
class AdvancedModel:
    # Class attributes
    learning_rate: Parameter[float]  # Will load from hooks
    batch_size: Parameter[int] = 32   # Will use default
    
    def __init__(self):
        self.epochs = 10
    
    def train(self, data_size: int):
        # Local variables with Parameter annotations
        dropout_rate: Parameter[float] = 0.5
        optimizer_lr: Parameter[float] = self.learning_rate * 0.1
        
        # Local variables with Metric annotations
        train_loss: Metric[float] = 0.0
        val_accuracy: Metric[float] = 0.0
        
        # Local variable with basic Traced annotation
        iteration: Traced[int] = 0
        
        # Training simulation
        for epoch in range(self.epochs):
            # Update metrics during processing
            iteration = epoch + 1
            train_loss = train_loss + (1.0 - epoch * self.learning_rate / 100)
            val_accuracy = val_accuracy + (epoch * 0.1 * dropout_rate)
        
        # These local variables will be captured and passed to hooks
        return val_accuracy
    
    def evaluate(self, test_data: list):
        # Local variable with Parameter annotation
        threshold: Parameter[float] = 0.8
        
        # Local variable with Metric annotation
        test_accuracy: Metric[float] = 0.0
        precision: Metric[float] = 0.0
        recall: Metric[float] = 0.0
        
        # Local variable with Traced annotation
        eval_step: Traced[int] = 0
        
        # Simple evaluation simulation
        eval_step = 1
        test_accuracy = len(test_data) * self.learning_rate / 1000
        if test_accuracy > threshold:
            precision = 0.95
            recall = 0.92
        else:
            precision = 0.85
            recall = 0.80
        
        # The final values of these metrics will be tracked
        return {
            "accuracy": test_accuracy, 
            "precision": precision, 
            "recall": recall
        }


# Initialize hooks with validation
init_hooks(
    config_path="config.yaml",
    use_mlflow=True,
    param_ranges={
        'learning_rate': (0.0, 1.0),
        'batch_size': (1, 128),
        'dropout_rate': (0.0, 0.9),
        'threshold': (0.5, 1.0)
    }
)

# Class usage with local variable tracking
model = AdvancedModel()  # learning_rate loaded from YAML
print(f"\nModel initialized with learning_rate={model.learning_rate}, batch_size={model.batch_size}")

# Train model - will track local variables
print("\nTraining model...")
accuracy = model.train(data_size=1000)
print(f"Training completed with accuracy: {accuracy}")

# Evaluate model - will track different local variables
print("\nEvaluating model...")
metrics = model.evaluate(test_data=[1, 2, 3, 4, 5])
print(f"Evaluation metrics: {metrics}")
from hooksett import tracked, track_function, HookManager, Traced
from hooksett.hooks import TracedOutput, YAMLConfigInput, TypeValidationHook

def init_hooks(config_path: str | None = None):
    """Initialize hooks with tracing support"""
    manager = HookManager()
    
    # Add the default tracing output hook
    manager.add_output_hook(TracedOutput())
    
    # Add validation
    manager.add_input_hook(TypeValidationHook())
    
    # Add config loading if needed
    if config_path:
        manager.add_input_hook(YAMLConfigInput(config_path))

# Example class with Traced variables
@tracked
class Calculator:
    initial_value: Traced[float] = 0.0
    result: Traced[float] = 0.0
    
    def add(self, value: Traced[float]):
        self.result = self.result + value
    
    def multiply(self, value: Traced[float]):
        self.result = self.result * value
    
    def calculate(self):
        # This method demonstrates local variable tracking
        x: Traced[float] = self.initial_value
        y: Traced[float] = x * 2
        z: Traced[float] = y + 10
        self.result = z
        return self.result

# Example function with Traced parameters and locals
@track_function
def complex_calculation(a: Traced[int], b: Traced[int]):
    # These local variables will be tracked
    intermediate: Traced[int] = a * b
    result: Traced[int] = intermediate + (a + b)
    return result

# Initialize hooks with config
init_hooks(config_path="config.yaml")

# Use the calculator
calc = Calculator()
calc.initial_value = 5.0
calc.add(10)
calc.multiply(2)
print(f"Final result: {calc.result}")

# Use the function
result = complex_calculation(5, 7)
print(f"Function result: {result}")
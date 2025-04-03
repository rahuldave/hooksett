"""
Example demonstrating how to use Hooksett with custom tracked types
defined completely in client code.
"""
from hooksett import HookManager, tracked, track_function

# Import custom types from respective modules
from ml_types import Parameter, Metric, Artifact, MLflowOutput
from ai_types import Prompt, Response, AITracingHook
from feature_types import Feature, FeatureList, FeatureStoreHook
from hooksett.hooks import TracedOutput, TypeValidationHook, YAMLConfigInput

# Initialize all the hook systems together
def init_hooks(config_path: str | None = None):
    """Initialize a multi-faceted hook system with all custom types"""
    manager = HookManager()
    
    # Add input hooks
    manager.add_input_hook(TypeValidationHook())
    if config_path:
        manager.add_input_hook(YAMLConfigInput(config_path))
        
    # Add output hooks for different tracking systems
    manager.add_output_hook(TracedOutput())  # Core tracing from hooksett
    manager.add_output_hook(MLflowOutput())  # ML tracking
    manager.add_output_hook(AITracingHook())  # AI conversation tracking
    manager.add_output_hook(FeatureStoreHook())  # Feature store tracking

# Define a class that uses multiple custom tracked types
@tracked
class AIModelPipeline:
    # ML Parameters
    learning_rate: Parameter[float] = 0.01
    batch_size: Parameter[int] = 32
    
    # AI Components
    system_prompt: Prompt[str] = "You are a helpful assistant."
    last_response: Response[str] = ""
    
    # Feature tracking
    user_features: FeatureList[list[float]] = []
    content_embedding: Feature[list[float]] = []
    
    # Standard metrics
    accuracy: Metric[float] = 0.0
    
    def process_user_input(self, user_input: str):
        # Local variable tracking of different types
        model_name: Parameter[str] = "gpt-4"
        user_prompt: Prompt[str] = user_input
        
        # Simulate feature extraction
        features: Feature[list[float]] = [0.1, 0.2, 0.3]
        self.user_features.append(features)
        
        # Simulate response generation
        response: Response[str] = f"Processed '{user_input}' with {model_name}"
        self.last_response = response
        
        # Track performance
        latency: Metric[float] = 0.05
        
        return response

# Initialize hooks
init_hooks(config_path="config.yaml")

# Use the multi-type pipeline
pipeline = AIModelPipeline()
response = pipeline.process_user_input("Hello, how can you help me with data science?")
print(f"Response: {response}")

# Function that uses multiple custom types
@track_function
def analyze_conversation(
    prompt: Prompt[str],
    model: Parameter[str] = "gpt-4"
):
    # Track multiple custom types as local variables
    sentiment_score: Metric[float] = 0.75
    key_features: Feature[list[str]] = ["question", "greeting", "data_science"]
    response_draft: Response[str] = f"I'll help with data science questions! (model: {model})"
    
    return {
        "sentiment": sentiment_score,
        "features": key_features,
        "response": response_draft
    }

# Use the multi-type function
results = analyze_conversation("Can you help with data science?")
print(f"Analysis results: {results}")
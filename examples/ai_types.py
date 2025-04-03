from typing import TypeVar, Any
from hooksett import register_tracked_type, InputHook, OutputHook

# Define AI-specific type variables
T = TypeVar('T')

# Define AI-specific types
type Prompt[T] = T
type Response[T] = T

# Register them with hooksett
register_tracked_type('Prompt', Prompt)
register_tracked_type('Response', Response)

# AI tracing hook
class AITracingHook(OutputHook):
    """Hook that tracks AI prompts and responses"""
    
    def __init__(self):
        self.prompts = []
        self.responses = []
    
    def save(self, name: str, value: Any, type_hint: type) -> None:
        """Track AI prompts and responses for analysis"""
        origin = getattr(type_hint, '__origin__', None)
        
        if origin is Prompt:
            print(f"Logging prompt: {name}")
            self.prompts.append((name, value))
        elif origin is Response:
            print(f"Logging response: {name}")
            self.responses.append((name, value))
            
    def get_conversation(self):
        """Return the full conversation history"""
        conversation = []
        for p, r in zip(self.prompts, self.responses):
            conversation.append({"prompt": p[1], "response": r[1]})
        return conversation
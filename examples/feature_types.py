from typing import TypeVar, Any, Dict, List
from hooksett import register_tracked_type, InputHook, OutputHook

# Define feature tracking type variables
T = TypeVar('T')

# Define feature tracking types
type Feature[T] = T
type FeatureList[T] = T

# Register them with hooksett
register_tracked_type('Feature', Feature)
register_tracked_type('FeatureList', FeatureList)

# Feature store hook
class FeatureStoreHook(OutputHook):
    """Hook that logs features to a simulated feature store"""
    
    def __init__(self):
        self.features: Dict[str, Any] = {}
        self.feature_lists: Dict[str, List[Any]] = {}
    
    def save(self, name: str, value: Any, type_hint: type) -> None:
        """Save a feature to the feature store"""
        origin = getattr(type_hint, '__origin__', None)
        
        if origin is Feature:
            print(f"Storing feature '{name}' in feature store")
            self.features[name] = value
        elif origin is FeatureList:
            print(f"Storing feature list '{name}' in feature store")
            self.feature_lists[name] = value
            
    def get_feature(self, name: str) -> Any:
        """Retrieve a feature from the store"""
        if name in self.features:
            return self.features[name]
        elif name in self.feature_lists:
            return self.feature_lists[name]
        return None
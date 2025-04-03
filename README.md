# Hooksett

Hooksett is a Python library that provides a flexible, extensible hook system for managing parameters, metrics, and artifacts in machine learning workflows. It allows you to easily separate configuration from code using a hook-based architecture.

## Overview

Hooksett makes it easy to:

1. Load parameters from configuration files automatically
2. Validate parameters against defined constraints
3. Track metrics and artifacts
4. Integrate with tracking systems like MLflow

The library uses Python's type annotations and descriptors to provide a clean, intuitive API for both class-based and function-based code.

## Core Concepts

- **Traced**: The core tracked type for monitoring variable changes
- **Custom types**: Define your own domain-specific tracked types:
  - **Parameter**, **Metric**, **Artifact**: Examples for ML workflows
  - **Prompt**, **Response**: Examples for AI applications
  - **Feature**, **FeatureList**: Examples for feature tracking
- **Hooks**: Mechanisms to load, validate, and save these values
- **Type Registry**: System to register and manage custom tracked types

## Files Overview

### Core Library

- **`src/hooksett/__init__.py`**: Core implementation with hook protocols, manager, and decorators
  - Defines the `InputHook` and `OutputHook` protocols
  - Implements a singleton `HookManager` for registering hooks
  - Provides the `register_tracked_type` function for adding custom types
  - Manages the type registry system for extensibility
  - Provides decorators for tracking class attributes and function parameters
  - Uses Python descriptors for automatic value loading and validation

- **`src/hooksett/hooks.py`**: Implementation of core hooks
  - `YAMLConfigInput`: Loads values from YAML configuration files
  - `RangeValidationHook`: Validates numeric parameters against min/max ranges
  - `TypeValidationHook`: Ensures values match their type annotations
  - `TracedOutput`: Standard logging-based output hook for the Traced type

### Examples

- **`examples/traced_example.py`**: Demonstrates using the core Traced type
  - Shows basic variable tracing via standard logging
  - Demonstrates the core functionality without domain-specific types

- **`examples/ml_types.py`**: Defines ML-specific types
  - Implements `Parameter`, `Metric`, and `Artifact` types
  - Provides a custom `MLflowOutput` hook for ML tracking

- **`examples/ml_model.py`**: Demonstrates using ML-specific types
  - Shows how to annotate class attributes with ML types
  - Illustrates automatic parameter loading from YAML
  - Demonstrates validation during value assignment

- **`examples/ai_types.py`**: Defines AI-specific types
  - Implements `Prompt` and `Response` types
  - Provides a custom `AITracingHook` for conversation tracking

- **`examples/feature_types.py`**: Defines feature tracking types
  - Implements `Feature` and `FeatureList` types
  - Provides a custom `FeatureStoreHook` for feature tracking

- **`examples/custom_types_demo.py`**: Demonstrates combining all custom types
  - Shows how multiple domain-specific type systems can work together
  - Demonstrates a unified hook system with multiple output hooks

- **`examples/config.yaml`**: Example configuration file
  - Contains values that can be loaded by the hooks

## Getting Started

1. Install the package:
   ```
   pip install hooksett
   ```

2. Create a configuration file (e.g., `config.yaml`)

3. Initialize hooks with the core Traced type:
   ```python
   from hooksett import HookManager
   from hooksett.hooks import YAMLConfigInput, TypeValidationHook, TracedOutput

   def init_hooks(config_path=None):
       manager = HookManager()
       manager.add_input_hook(TypeValidationHook())
       manager.add_output_hook(TracedOutput())
       
       if config_path:
           manager.add_input_hook(YAMLConfigInput(config_path))
   ```

4. Use with classes:
   ```python
   from hooksett import tracked, Traced

   @tracked
   class Calculator:
       initial_value: Traced[float] = 0.0
       result: Traced[float] = 0.0
       
       def calculate(self):
           # This local variable will be tracked
           intermediate: Traced[float] = self.initial_value * 2
           self.result = intermediate + 10
   ```

5. Or use with functions:
   ```python
   from hooksett import track_function, Traced

   @track_function
   def calculate(
       x: Traced[float] = None,  # Load from hook
       y: Traced[float] = 5.0    # Default value
   ):
       # This local variable will be tracked
       result: Traced[float] = x * y
       return result
   ```

6. Create your own custom tracked types:
   ```python
   from typing import TypeVar
   from hooksett import register_tracked_type, OutputHook

   # Define your custom type
   T = TypeVar('T')
   type MyCustomType[T] = T
   
   # Register it with hooksett
   register_tracked_type('MyCustomType', MyCustomType)
   
   # Create a custom hook for your type
   class MyCustomHook(OutputHook):
       def save(self, name: str, value: Any, type_hint: type) -> None:
           if getattr(type_hint, '__origin__', None) is MyCustomType:
               print(f"Custom handling for {name} = {value}")
   
   # Add your hook to the manager
   HookManager().add_output_hook(MyCustomHook())
   ```

## Requirements

- Python 3.11+
- PyYAML 6.0.2+
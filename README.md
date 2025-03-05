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

- **Parameter**: Values used as inputs to your models or functions
- **Metric**: Values that track performance or results
- **Artifact**: Files or data produced by your code
- **Hooks**: Mechanisms to load, validate, and save these values

## Files Overview

### Core Library

- **`src/hooksett/__init__.py`**: Core implementation with hook protocols, manager, and decorators
  - Defines the `InputHook` and `OutputHook` protocols
  - Implements a singleton `HookManager` for registering hooks
  - Provides decorators for tracking class attributes and function parameters
  - Uses Python descriptors for automatic value loading and validation

- **`src/hooksett/hooks.py`**: Implementation of example hooks
  - `YAMLConfigInput`: Loads values from YAML configuration files
  - `RangeValidationHook`: Validates numeric parameters against min/max ranges
  - `TypeValidationHook`: Ensures values match their type annotations
  - `MLflowOutput`: Logs parameters, metrics, and artifacts to MLflow

### Examples

- **`examples/class.py`**: Demonstrates using Hooksett with classes
  - Shows how to annotate class attributes with `Parameter`, `Metric`, and `Artifact`
  - Illustrates automatic parameter loading from YAML
  - Demonstrates validation during value assignment

- **`examples/function.py`**: Demonstrates using Hooksett with functions
  - Shows how to decorate functions with `@track_function`
  - Illustrates parameter loading and validation in function arguments
  - Demonstrates error handling for validation failures

- **`examples/config.yaml`**: Example configuration file
  - Contains parameter values that can be loaded by the hooks
  - Structured in a way that's common for ML projects

## Getting Started

1. Install the package:
   ```
   pip install hooksett
   ```

2. Create a configuration file (e.g., `config.yaml`)

3. Initialize hooks in your code:
   ```python
   from hooksett import HookManager
   from hooksett.hooks import YAMLConfigInput, RangeValidationHook, TypeValidationHook

   def init_hooks(config_path=None):
       manager = HookManager()
       manager.add_input_hook(TypeValidationHook())
       
       if config_path:
           manager.add_input_hook(YAMLConfigInput(config_path))
   ```

4. Use with classes:
   ```python
   from hooksett import tracked, Parameter

   @tracked
   class Model:
       learning_rate: Parameter[float]  # Will load from hook
       batch_size: Parameter[int] = 32  # Default value
   ```

5. Or use with functions:
   ```python
   from hooksett import track_function, Parameter

   @track_function
   def train_model(
       learning_rate: Parameter[float] = None,  # Load from hook
       batch_size: Parameter[int] = 32          # Default value
   ):
       # Your code here
       pass
   ```

## Requirements

- Python 3.11+
- PyYAML 6.0.2+
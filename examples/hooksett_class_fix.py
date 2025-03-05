"""
This file demonstrates how the indentation error fix is applied
in the context of the Hooksett library to properly handle local
variable annotations in class methods.
"""

import ast
import inspect
import textwrap
import types
from typing import TypeVar, Dict, Any, List, Tuple

# -----------------------------------------------------------------
# Simplified version of what's in Hooksett
# -----------------------------------------------------------------

# Simplified version of Hooksett's type aliases
class Parameter:
    def __class_getitem__(cls, item):
        return cls

class Metric:
    def __class_getitem__(cls, item):
        return cls

class Artifact:
    def __class_getitem__(cls, item):
        return cls

# Simplified AST visitor similar to LocalVarVisitor in Hooksett
class TrackedVarVisitor(ast.NodeVisitor):
    def __init__(self):
        self.tracked_vars = {}
        
    def visit_AnnAssign(self, node):
        # Find annotations like: x: Parameter[int] = 5
        if isinstance(node.annotation, ast.Subscript):
            if isinstance(node.annotation.value, ast.Name):
                # Get the annotation type (Parameter, Metric, Artifact)
                anno_type = node.annotation.value.id
                if anno_type in ('Parameter', 'Metric', 'Artifact'):
                    # Get the variable name
                    if isinstance(node.target, ast.Name):
                        var_name = node.target.id
                        # Store this tracked variable
                        self.tracked_vars[var_name] = anno_type
        self.generic_visit(node)

# -----------------------------------------------------------------
# BEFORE: Problematic method for parsing class methods (would fail)
# -----------------------------------------------------------------
def parse_method_before_fix(method):
    """This represents our approach before fixing the indentation issue"""
    print(f"\nTrying to parse method {method.__name__} WITHOUT dedent:")
    try:
        # Get the source code of the method (with indentation)
        source = inspect.getsource(method)
        print(f"Source code snippet: {source.splitlines()[0]}...")
        
        # Try to parse (this will fail due to indentation)
        tree = ast.parse(source)
        
        # This code won't be reached
        visitor = TrackedVarVisitor()
        visitor.visit(tree)
        return visitor.tracked_vars
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return {}

# -----------------------------------------------------------------
# AFTER: Fixed method for parsing class methods with dedent
# -----------------------------------------------------------------
def parse_method_after_fix(method):
    """This represents our approach after fixing the indentation issue"""
    print(f"\nTrying to parse method {method.__name__} WITH dedent:")
    try:
        # Get the source code of the method
        source = inspect.getsource(method)
        print(f"Source code snippet: {source.splitlines()[0]}...")
        
        # Dedent the source code to handle method inside class (THIS IS THE FIX)
        source = textwrap.dedent(source)
        print(f"Dedented snippet: {source.splitlines()[0]}...")
        
        # Parse the source code
        tree = ast.parse(source)
        
        # Find tracked variables
        visitor = TrackedVarVisitor()
        visitor.visit(tree)
        
        # Report success
        if visitor.tracked_vars:
            print(f"SUCCESS: Found {len(visitor.tracked_vars)} tracked variables")
            for name, type_name in visitor.tracked_vars.items():
                print(f"  - {name}: {type_name}")
        else:
            print("SUCCESS: No tracked variables found")
        
        return visitor.tracked_vars
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return {}

# -----------------------------------------------------------------
# SIMPLIFIED VERSION OF TRACKED CLASS METACLASS
# -----------------------------------------------------------------

# Before the fix: Failed to properly process methods
class TrackedClassBeforeFix(type):
    def __new__(cls, name, bases, namespace):
        print(f"\n---- Creating class {name} WITHOUT dedent fix ----")
        
        # Process methods to look for local variable annotations
        for attr_name, attr_value in list(namespace.items()):
            if isinstance(attr_value, types.FunctionType):
                print(f"Processing method {attr_name}")
                tracked_vars = parse_method_before_fix(attr_value)
                # Would wrap methods with tracked vars here if parsing succeeded
        
        return super().__new__(cls, name, bases, namespace)

# After the fix: Successfully processes methods with dedent
class TrackedClassAfterFix(type):
    def __new__(cls, name, bases, namespace):
        print(f"\n---- Creating class {name} WITH dedent fix ----")
        
        # First create the class (avoid parsing methods prematurely)
        created_class = super().__new__(cls, name, bases, namespace)
        
        # Process methods in the created class
        for attr_name in dir(created_class):
            try:
                attr_value = getattr(created_class, attr_name)
                if isinstance(attr_value, types.FunctionType) and not attr_name.startswith('__'):
                    print(f"Processing method {attr_name}")
                    tracked_vars = parse_method_after_fix(attr_value)
                    # Would wrap methods with tracked vars here if any found
            except (AttributeError, TypeError) as e:
                print(f"Skipping {attr_name}: {str(e)}")
                continue
                
        return created_class

# -----------------------------------------------------------------
# Demo classes to show the difference
# -----------------------------------------------------------------

print("\n===== DEMO: BEFORE THE FIX =====")

# This will try to use the broken approach and fail to parse methods
class ModelBroken(metaclass=TrackedClassBeforeFix):
    def __init__(self, learning_rate=0.01):
        self.learning_rate = learning_rate
    
    def train(self, epochs=5):
        # Local tracked variables
        dropout_rate: Parameter[float] = 0.5
        accuracy: Metric[float] = 0.0
        
        for i in range(epochs):
            accuracy += 0.1
        
        return accuracy

print("\n===== DEMO: AFTER THE FIX =====")

# This will use the fixed approach with dedent and successfully parse methods
class ModelFixed(metaclass=TrackedClassAfterFix):
    def __init__(self, learning_rate=0.01):
        self.learning_rate = learning_rate
    
    def train(self, epochs=5):
        # Local tracked variables
        dropout_rate: Parameter[float] = 0.5  
        accuracy: Metric[float] = 0.0
        
        for i in range(epochs):
            accuracy += 0.1
        
        return accuracy

print("\n===== DEMO COMPLETE =====")
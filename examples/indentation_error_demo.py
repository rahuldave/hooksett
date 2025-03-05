"""
This file demonstrates the indentation error that occurs when parsing class methods
and shows how the fix works to resolve it.
"""

import ast
import inspect
import textwrap

# -----------------------------------------------------------------
# PROBLEM DEMONSTRATION: Parsing a class method directly fails
# -----------------------------------------------------------------

class DemoClass:
    def demo_method(self):
        # This method is indented within the class
        x = 10
        y = 20
        return x + y

# Try to parse the method source
print("ATTEMPT 1: Direct parsing (causes error)")
print("-" * 50)

try:
    # Get the source code of the method (includes indentation)
    method = DemoClass.demo_method
    source = inspect.getsource(method)
    
    print(f"Original source code:\n{source}")
    
    # This will fail with an IndentationError
    tree = ast.parse(source)
    print("Successfully parsed the AST (this won't be reached)")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

# -----------------------------------------------------------------
# SOLUTION: Using textwrap.dedent() to fix indentation
# -----------------------------------------------------------------

print("\n\nATTEMPT 2: Using textwrap.dedent() to fix indentation")
print("-" * 50)

try:
    # Get the source code of the method
    method = DemoClass.demo_method
    source = inspect.getsource(method)
    
    print(f"Original source code:\n{source}")
    
    # Dedent the source code to remove leading whitespace
    dedented_source = textwrap.dedent(source)
    print(f"\nDedented source code:\n{dedented_source}")
    
    # Now parsing will succeed
    tree = ast.parse(dedented_source)
    print("\nSuccessfully parsed the AST!")
    
    # Show the AST structure
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            print(f"Found function definition: {node.name}")
        elif isinstance(node, ast.Assign):
            print(f"Found assignment: {ast.unparse(node)}")
        elif isinstance(node, ast.Return):
            print(f"Found return: {ast.unparse(node)}")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

# -----------------------------------------------------------------
# REAL-WORLD EXAMPLE: Tracking annotations in class methods
# -----------------------------------------------------------------

print("\n\nREAL-WORLD EXAMPLE: Tracking annotations in class methods")
print("-" * 50)

# This is similar to what we do in hooksett's TrackedClass metaclass
class AnnotationVisitor(ast.NodeVisitor):
    def __init__(self):
        self.annotations = []
        
    def visit_AnnAssign(self, node):
        # Visit annotated assignments like 'x: int = 5'
        if isinstance(node.target, ast.Name):
            name = node.target.id
            annotation = ast.unparse(node.annotation)
            self.annotations.append((name, annotation))
        self.generic_visit(node)

class AnnotatedClass:
    def method_with_annotations(self):
        # Variables with annotations
        a: int = 1
        b: float = 2.0
        c: str = "hello"
        return a + b

try:
    # Get the source code of the method
    method = AnnotatedClass.method_with_annotations
    source = inspect.getsource(method)
    
    print(f"Original annotated method source:\n{source}")
    
    # This would fail due to indentation
    print("\nWithout dedent: Would fail with IndentationError")
    
    # Dedent the source code first (THIS IS THE FIX)
    dedented_source = textwrap.dedent(source)
    print(f"\nDedented annotated method source:\n{dedented_source}")
    
    # Now parse and extract annotations
    tree = ast.parse(dedented_source)
    visitor = AnnotationVisitor()
    visitor.visit(tree)
    
    print("\nFound annotations:")
    for name, annotation in visitor.annotations:
        print(f"- {name}: {annotation}")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
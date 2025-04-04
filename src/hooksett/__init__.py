from typing import TypeVar, Any, Protocol, Generic
import inspect
from functools import wraps
import ast
import types
import textwrap


T = TypeVar('T')

# Type registry for tracked types
_TRACKED_TYPES = {}

# Core type alias - a basic traced variable
type Traced[T] = T

# Register the core type
_TRACKED_TYPES['Traced'] = Traced

def register_tracked_type(name: str, type_alias: type) -> None:
    """Register a new tracked type in the system.
    
    Args:
        name: The name of the tracked type
        type_alias: The type alias to register
    """
    _TRACKED_TYPES[name] = type_alias
    # Make the type available at the module level
    globals()[name] = type_alias

class HookError(Exception):
    """Raised when a value needs to be loaded but no hooks are available"""
    pass

# Hook protocols
class InputHook(Protocol, Generic[T]):
    def load(self, name: str, type_hint: type) -> T | None:
        """Load a value or return None to try next hook"""
        ...

    def validate(self, name: str, value: Any, type_hint: type | None = None) -> Any:
        """Validate and potentially transform a value"""
        return value

class OutputHook(Protocol, Generic[T]):
    def save(self, name: str, value: T, type_hint: type) -> None:
        ...

# Hook Manager
class HookManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.input_hooks: list[InputHook] = []
            cls._instance.output_hooks: list[OutputHook] = []
        return cls._instance

    def add_input_hook(self, hook: InputHook) -> None:
        self.input_hooks.append(hook)

    def add_output_hook(self, hook: OutputHook) -> None:
        self.output_hooks.append(hook)

    def load_value(self, name: str, type_hint: type) -> Any:
        """Try to load value from hooks, validate through all hooks"""
        if not self.input_hooks:
            raise HookError(f"No input hooks available to load {name}")

        # Try to load from each hook until we get a value
        value = None
        for hook in self.input_hooks:
            value = hook.load(name, type_hint)
            if value is not None:
                break

        if value is None:
            raise HookError(f"No value found for {name} in any input hook")

        # Run value through all validation chains
        for hook in self.input_hooks:
            value = hook.validate(name, value, type_hint)

        return value

    def save_value(self, name: str, value: Any, type_hint: type) -> None:
        for hook in self.output_hooks:
            hook.save(name, value, type_hint)

# Variable Descriptor for class attributes
class TrackedDescriptor:
    def __init__(self, type_hint: type, has_default: bool, default=None):
        self.type_hint = type_hint
        self.has_default = has_default
        self.default = default
        self.hook_manager = HookManager()
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        # Get or create private storage dict
        private_dict = getattr(instance, '_tracked_values', None)
        if private_dict is None:
            private_dict = {}
            object.__setattr__(instance, '_tracked_values', private_dict)

        if self.name not in private_dict:
            if not self.has_default:
                # ... hook loading logic ...
                if not self.hook_manager.input_hooks:
                    raise HookError(
                        f"No input hooks defined but {self.name} requires a value. "
                        f"Either initialize hooks with init_hooks(), provide a default value, "
                        f"or explicitly set the attribute."
                    )
                # No default = try to load from hooks
                try:
                    value = self.hook_manager.load_value(self.name, self.type_hint)
                    private_dict[self.name] = value
                except HookError as e:
                    raise HookError(
                        f"Failed to load required value for {self.name}. "
                        f"Either provide a default value or ensure hooks are properly configured. "
                        f"Original error: {str(e)}"
                    ) from e
            else:
                # Use explicit default
                private_dict[self.name] = self.default

        return private_dict[self.name]


    def __set__(self, instance, value):
        # Validate through hooks
        for hook in self.hook_manager.input_hooks:
            value = hook.validate(self.name, value, self.type_hint)

        # Get or create private storage dict
        private_dict = getattr(instance, '_tracked_values', None)
        if private_dict is None:
            private_dict = {}
            object.__setattr__(instance, '_tracked_values', private_dict)

        private_dict[self.name] = value
        self.hook_manager.save_value(self.name, value, self.type_hint)

# AST visitor to find local variable annotations
class LocalVarVisitor(ast.NodeVisitor):
    def __init__(self):
        self.tracked_vars = {}

    def visit_AnnAssign(self, node):
        # Find annotations like: x: Parameter[int] = 5
        if isinstance(node.annotation, ast.Subscript):
            if isinstance(node.annotation.value, ast.Name):
                # Get the annotation type (any tracked type from registry)
                anno_type = node.annotation.value.id
                if anno_type in _TRACKED_TYPES:
                    # Get the variable name
                    if isinstance(node.target, ast.Name):
                        var_name = node.target.id
                        # Get the default value if it exists
                        has_default = node.value is not None
                        
                        # Store info about this tracked variable
                        self.tracked_vars[var_name] = {
                            'type': anno_type,
                            'has_default': has_default,
                        }
        self.generic_visit(node)

# Function to set up tracking for local variables
def setup_local_var_tracking(func, local_tracked_vars):
    """Set up variable tracking in a function without tracing every access"""
    hook_manager = HookManager()
    
    # Print tracking information - pre-function hook opportunity
    for var_name, info in local_tracked_vars.items():
        print(f"Found local tracked variable: {var_name} of type {info['type']} in {func.__name__}")
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Define a dictionary to store the final values
        final_values = {}
        
        # Define a simple tracer function that only captures the final values
        def trace_func(frame, event, arg):
            if event == 'return':
                # Capture final values of all local variables when function returns
                for var_name in local_tracked_vars:
                    if var_name in frame.f_locals:
                        final_values[var_name] = frame.f_locals[var_name]
            return trace_func
        
        # Set up the trace function
        import sys
        old_trace = sys.gettrace()
        sys.settrace(trace_func)
        
        try:
            # Execute the function
            result = func(*args, **kwargs)
            
            # Process any tracked variables after function completes
            for var_name, value in final_values.items():
                # Get type information
                tracked_type = local_tracked_vars[var_name]['type']
                value_type = type(value)
                
                # Create synthetic type hint
                if tracked_type in _TRACKED_TYPES:
                    tracked_type_alias = _TRACKED_TYPES[tracked_type]
                    type_hint = tracked_type_alias[value_type]
                    
                    # Call hooks to save final value
                    hook_manager.save_value(var_name, value, type_hint)
                    
            return result
        finally:
            # Restore original trace function
            sys.settrace(old_trace)

    return wrapper

# Function to parse method source with proper indentation handling
def parse_method_body(method):
    """Parse a method body handling indentation correctly"""
    try:
        # Get the source code of the method
        source = inspect.getsource(method)
        
        # Dedent the source code to handle method inside class
        source = textwrap.dedent(source)
        
        # Parse the source code
        tree = ast.parse(source)
        
        # Inspect for tracked variables
        visitor = LocalVarVisitor()
        visitor.visit(tree)
        
        return visitor.tracked_vars
    except (OSError, TypeError, SyntaxError) as e:
        print(f"Warning: Could not parse method {method.__name__}: {str(e)}")
        return {}

# Metaclass for tracked classes
class TrackedClass(type):
    def __new__(cls, name, bases, namespace):
        annotations = namespace.get('__annotations__', {})

        # Process class attributes with special annotations
        for var_name, type_hint in annotations.items():
            origin = getattr(type_hint, '__origin__', None)
            # Check if origin is any of our tracked types
            if origin in _TRACKED_TYPES.values():
                has_default = var_name in namespace
                default = namespace.get(var_name)
                namespace[var_name] = TrackedDescriptor(
                    type_hint,
                    has_default,
                    default
                )
        
        # Create the class first to avoid parsing methods prematurely
        created_class = super().__new__(cls, name, bases, namespace)
        
        # Now process methods in the created class
        for attr_name in dir(created_class):
            try:
                attr_value = getattr(created_class, attr_name)
                if isinstance(attr_value, types.FunctionType) and not attr_name.startswith('__'):
                    # Parse method body to find local tracked variables
                    local_tracked_vars = parse_method_body(attr_value)
                    
                    # If we found tracked local vars, wrap the method
                    if local_tracked_vars:
                        wrapped_method = setup_local_var_tracking(attr_value, local_tracked_vars)
                        setattr(created_class, attr_name, wrapped_method)
            except (AttributeError, TypeError):
                # Skip if we can't process this attribute
                continue
                
        return created_class

def tracked(cls):
    """Class decorator to add tracking"""
    return TrackedClass(cls.__name__, cls.__bases__, dict(cls.__dict__))

def track_function(func):
    """Function decorator that handles tracking"""
    hook_manager = HookManager()
    
    # Parse function body to find local tracked variables
    try:
        source = inspect.getsource(func)
        tree = ast.parse(source)
        visitor = LocalVarVisitor()
        visitor.visit(tree)
        local_tracked_vars = visitor.tracked_vars
    except (OSError, TypeError, SyntaxError):
        # If we can't parse the source, assume no local tracked vars
        local_tracked_vars = {}
    
    # Create a wrapper that handles parameter loading/validation and local var tracking
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get function signature
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        # Check if we need hooks
        needs_hooks = any(
            value is None and
            getattr(func.__annotations__.get(name, None), '__origin__', None)
            in _TRACKED_TYPES.values()
            for name, value in bound_args.arguments.items()
        )

        if needs_hooks and not hook_manager.input_hooks:
            raise HookError(
                f"Function {func.__name__} requires input hooks for parameters with None defaults. "
                f"Initialize hooks with init_hooks() before calling."
            )

        # Process parameters
        final_kwargs = {}
        for name, value in bound_args.arguments.items():
            type_hint = func.__annotations__.get(name)
            if type_hint is None:
                final_kwargs[name] = value
                continue

            origin = getattr(type_hint, '__origin__', None)
            if origin not in _TRACKED_TYPES.values():
                final_kwargs[name] = value
                continue

            # If value is None, try to load from hooks
            if value is None:
                value = hook_manager.load_value(name, type_hint)
            else:
                # Validate explicitly provided value
                for hook in hook_manager.input_hooks:
                    value = hook.validate(name, value, type_hint)

            final_kwargs[name] = value
            hook_manager.save_value(name, value, type_hint)

        # Dictionary to capture local variable values
        final_tracked_values = {}
        
        # Define a trace function that captures local variables at function return
        def trace_func(frame, event, arg):
            if event == 'return':
                # When the function returns, capture the final values
                for var_name in local_tracked_vars:
                    if var_name in frame.f_locals:
                        value = frame.f_locals[var_name]
                        final_tracked_values[var_name] = value
            return trace_func
        
        # Set up tracing if we have local variables to track
        import sys
        old_trace = sys.gettrace()
        if local_tracked_vars:
            sys.settrace(trace_func)
        
        try:
            # Execute the function
            result = func(**final_kwargs)
            
            # Process any tracked local variables after function completes
            for var_name, value in final_tracked_values.items():
                # Get type information
                tracked_type = local_tracked_vars[var_name]['type']
                value_type = type(value)
                
                # Create synthetic type hint
                if tracked_type in _TRACKED_TYPES:
                    tracked_type_alias = _TRACKED_TYPES[tracked_type]
                    type_hint = tracked_type_alias[value_type]
                    
                    # Save the final value through hooks
                    hook_manager.save_value(var_name, value, type_hint)
            
            return result
        finally:
            # Restore original trace function
            sys.settrace(old_trace)

    return wrapper
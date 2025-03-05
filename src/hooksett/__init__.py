from typing import TypeVar, Any, Protocol, Generic
from abc import ABC, abstractmethod
import inspect
from functools import wraps
import pathlib

T = TypeVar('T')

# Type aliases
type Parameter[T] = T
type Metric[T] = T
type Artifact[T] = T

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

# Metaclass for tracked classes
class TrackedClass(type):
    def __new__(cls, name, bases, namespace):
        annotations = namespace.get('__annotations__', {})

        for var_name, type_hint in annotations.items():
            origin = getattr(type_hint, '__origin__', None)
            if origin in (Parameter, Metric, Artifact):
                has_default = var_name in namespace
                default = namespace.get(var_name)
                namespace[var_name] = TrackedDescriptor(
                    type_hint,
                    has_default,
                    default
                )

        return super().__new__(cls, name, bases, namespace)

def tracked(cls):
    """Class decorator to add tracking"""
    return TrackedClass(cls.__name__, cls.__bases__, dict(cls.__dict__))

def track_function(func):
    """Function decorator that handles tracking"""
    hook_manager = HookManager()

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
            in (Parameter, Metric, Artifact)
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
            if origin not in (Parameter, Metric, Artifact):
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

        return func(**final_kwargs)

    return wrapper

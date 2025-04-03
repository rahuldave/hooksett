"""
Unit tests for core functionality in hooksett/__init__.py
"""
import pytest
from typing import TypeVar, Any
from hooksett import (
    register_tracked_type, 
    Traced, 
    _TRACKED_TYPES, 
    HookError, 
    InputHook, 
    OutputHook, 
    HookManager, 
    track_function,
    tracked
)

T = TypeVar('T')


class TestTypeRegistry:
    """Test the type registry system"""
    
    def test_traced_registered(self):
        """Test that the Traced type is registered by default"""
        assert 'Traced' in _TRACKED_TYPES
        assert _TRACKED_TYPES['Traced'] is Traced
    
    def test_register_new_type(self):
        """Test registering a new tracked type"""
        # Create a new type
        type TestType[T] = T
        
        # Register it
        register_tracked_type('TestType', TestType)
        
        # Check it's in the registry
        assert 'TestType' in _TRACKED_TYPES
        assert _TRACKED_TYPES['TestType'] is TestType
        
        # Check it's available at module level
        from hooksett import TestType as ImportedTestType
        assert ImportedTestType is TestType


class MockInputHook(InputHook):
    """Mock input hook for testing"""
    
    def __init__(self, values=None):
        self.values = values or {}
        self.load_calls = []
        self.validate_calls = []
    
    def load(self, name: str, type_hint: type) -> Any | None:
        self.load_calls.append((name, type_hint))
        return self.values.get(name)
    
    def validate(self, name: str, value: Any, type_hint: type | None = None) -> Any:
        self.validate_calls.append((name, value, type_hint))
        return value


class MockOutputHook(OutputHook):
    """Mock output hook for testing"""
    
    def __init__(self):
        self.save_calls = []
    
    def save(self, name: str, value: Any, type_hint: type) -> None:
        self.save_calls.append((name, value, type_hint))


class TestHookManager:
    """Test the HookManager singleton"""
    
    def setup_method(self):
        """Reset the HookManager before each test"""
        manager = HookManager()
        manager.input_hooks = []
        manager.output_hooks = []
    
    def test_singleton(self):
        """Test that HookManager is a singleton"""
        manager1 = HookManager()
        manager2 = HookManager()
        assert manager1 is manager2
    
    def test_add_hooks(self):
        """Test adding hooks to the manager"""
        manager = HookManager()
        in_hook = MockInputHook()
        out_hook = MockOutputHook()
        
        manager.add_input_hook(in_hook)
        manager.add_output_hook(out_hook)
        
        assert in_hook in manager.input_hooks
        assert out_hook in manager.output_hooks
    
    def test_load_value(self):
        """Test loading values from hooks"""
        manager = HookManager()
        hook1 = MockInputHook()
        hook2 = MockInputHook({'test_param': 42})
        
        manager.add_input_hook(hook1)
        manager.add_input_hook(hook2)
        
        value = manager.load_value('test_param', Traced[int])
        
        assert value == 42
        assert len(hook1.load_calls) == 1
        assert len(hook1.validate_calls) == 1
        assert len(hook2.load_calls) == 1
        assert len(hook2.validate_calls) == 1
    
    def test_load_value_error(self):
        """Test error when no value is found"""
        manager = HookManager()
        hook = MockInputHook()
        
        manager.add_input_hook(hook)
        
        with pytest.raises(HookError):
            manager.load_value('missing_param', Traced[int])
    
    def test_save_value(self):
        """Test saving values through hooks"""
        manager = HookManager()
        hook1 = MockOutputHook()
        hook2 = MockOutputHook()
        
        manager.add_output_hook(hook1)
        manager.add_output_hook(hook2)
        
        manager.save_value('test_metric', 0.95, Traced[float])
        
        assert len(hook1.save_calls) == 1
        assert hook1.save_calls[0][0] == 'test_metric'
        assert hook1.save_calls[0][1] == 0.95
        
        assert len(hook2.save_calls) == 1
        assert hook2.save_calls[0][0] == 'test_metric'
        assert hook2.save_calls[0][1] == 0.95


class TestFunctionDecorator:
    """Test the track_function decorator"""
    
    def setup_method(self):
        """Set up hooks for each test"""
        manager = HookManager()
        manager.input_hooks = []
        manager.output_hooks = []
        
        self.in_hook = MockInputHook({
            'param1': 'hook_value'
        })
        self.out_hook = MockOutputHook()
        
        manager.add_input_hook(self.in_hook)
        manager.add_output_hook(self.out_hook)
    
    def test_function_params(self):
        """Test tracked function parameters"""
        @track_function
        def test_func(param1: Traced[str] = None, param2: Traced[int] = 42):
            return f"{param1}-{param2}"
        
        result = test_func()
        
        assert result == "hook_value-42"
        assert len(self.in_hook.load_calls) == 1
        assert self.in_hook.load_calls[0][0] == 'param1'
        
        assert len(self.out_hook.save_calls) == 2
        assert self.out_hook.save_calls[0][0] == 'param1'
        assert self.out_hook.save_calls[0][1] == 'hook_value'
        assert self.out_hook.save_calls[1][0] == 'param2'
        assert self.out_hook.save_calls[1][1] == 42
    
    def test_explicit_params(self):
        """Test explicitly provided parameters"""
        @track_function
        def test_func(param1: Traced[str] = None):
            return param1
        
        result = test_func(param1="explicit")
        
        assert result == "explicit"
        assert len(self.in_hook.validate_calls) == 1
        assert self.in_hook.validate_calls[0][1] == "explicit"
        
        assert len(self.out_hook.save_calls) == 1
        assert self.out_hook.save_calls[0][0] == 'param1'
        assert self.out_hook.save_calls[0][1] == 'explicit'


class TestClassDecorator:
    """Test the tracked class decorator"""
    
    def setup_method(self):
        """Set up hooks for each test"""
        manager = HookManager()
        manager.input_hooks = []
        manager.output_hooks = []
        
        self.in_hook = MockInputHook({
            'value1': 'hook_value'
        })
        self.out_hook = MockOutputHook()
        
        manager.add_input_hook(self.in_hook)
        manager.add_output_hook(self.out_hook)
    
    def test_class_attributes(self):
        """Test tracked class attributes"""
        @tracked
        class TestClass:
            value1: Traced[str]
            value2: Traced[int] = 42
        
        obj = TestClass()
        
        # Check value loaded from hook
        assert obj.value1 == 'hook_value'
        assert len(self.in_hook.load_calls) == 1
        assert self.in_hook.load_calls[0][0] == 'value1'
        
        # Check default value
        assert obj.value2 == 42
        
        # Check saving when attribute is set
        obj.value2 = 100
        assert len(self.out_hook.save_calls) >= 1
        save_call = next((call for call in self.out_hook.save_calls if call[0] == 'value2' and call[1] == 100), None)
        assert save_call is not None
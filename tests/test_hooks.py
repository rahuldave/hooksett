"""
Unit tests for hooks in hooksett/hooks.py
"""
import pytest
import os
import tempfile
import logging
from typing import Any
from hooksett import Traced, register_tracked_type, HookManager, InputHook, OutputHook
from hooksett.hooks import YAMLConfigInput, RangeValidationHook, TypeValidationHook, TracedOutput


class TestYAMLConfigInput:
    """Test the YAML config input hook"""
    
    def test_load_config(self):
        """Test loading values from YAML config"""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
            test_param: 42
            test_string: "hello"
            nested:
              value: "nested value"
            """)
            config_path = f.name
        
        try:
            # Create and test the hook
            hook = YAMLConfigInput(config_path)
            
            # Test loading values
            assert hook.load('test_param', Traced[int]) == 42
            assert hook.load('test_string', Traced[str]) == "hello"
            assert hook.load('nested', Traced[dict]) == {"value": "nested value"}
            assert hook.load('missing', Traced[str]) is None
            
            # Test validation (no-op in this hook)
            value = "test"
            assert hook.validate('any_param', value, Traced[str]) is value
        finally:
            # Clean up
            os.unlink(config_path)


class TestRangeValidationHook:
    """Test the range validation hook"""
    
    def setup_method(self):
        """Set up the hook for each test"""
        self.hook = RangeValidationHook({
            'int_param': (1, 10),
            'float_param': (0.0, 1.0)
        })
    
    def test_load_returns_none(self):
        """Test that load always returns None"""
        assert self.hook.load('any_param', Traced[int]) is None
    
    def test_validate_in_range(self):
        """Test validation with values in range"""
        assert self.hook.validate('int_param', 5, Traced[int]) == 5
        assert self.hook.validate('float_param', 0.5, Traced[float]) == 0.5
    
    def test_validate_out_of_range(self):
        """Test validation with values out of range"""
        with pytest.raises(ValueError):
            self.hook.validate('int_param', 0, Traced[int])
        
        with pytest.raises(ValueError):
            self.hook.validate('int_param', 11, Traced[int])
        
        with pytest.raises(ValueError):
            self.hook.validate('float_param', -0.1, Traced[float])
        
        with pytest.raises(ValueError):
            self.hook.validate('float_param', 1.1, Traced[float])
    
    def test_validate_unregistered_param(self):
        """Test validation for params not in the range dict"""
        # Should pass through unmodified
        assert self.hook.validate('other_param', 100, Traced[int]) == 100


class TestTypeValidationHook:
    """Test the type validation hook"""
    
    def setup_method(self):
        """Set up the hook and a test type for each test"""
        self.hook = TypeValidationHook()
        
        # Define and register a test type
        type TestType[T] = T
        register_tracked_type('TestType', TestType)
    
    def test_load_returns_none(self):
        """Test that load always returns None"""
        assert self.hook.load('any_param', Traced[int]) is None
    
    def test_validate_correct_type(self):
        """Test validation with correct types"""
        from hooksett import TestType
        
        # Different type checks
        assert self.hook.validate('int_param', 5, TestType[int]) == 5
        assert self.hook.validate('str_param', "test", TestType[str]) == "test"
        assert self.hook.validate('list_param', [1, 2, 3], TestType[list]) == [1, 2, 3]
    
    def test_validate_incorrect_type(self):
        """Test validation with incorrect types"""
        from hooksett import TestType
        
        with pytest.raises(TypeError):
            self.hook.validate('int_param', "not an int", TestType[int])
        
        with pytest.raises(TypeError):
            self.hook.validate('str_param', 42, TestType[str])
        
        with pytest.raises(TypeError):
            self.hook.validate('list_param', "not a list", TestType[list])
    
    def test_validate_without_type_hint(self):
        """Test validation without a proper type hint"""
        # Should pass through unmodified without error
        assert self.hook.validate('param', 42, str) == 42


class TestTracedOutput:
    """Test the traced output hook"""
    
    def setup_method(self):
        """Set up a hook and capture logs for each test"""
        self.logger = logging.getLogger('test_logger')
        self.hook = TracedOutput(logger_name='test_logger')
        
        # Capture log messages
        self.log_capture = []
        
        class TestHandler(logging.Handler):
            def __init__(self, capture_list):
                super().__init__()
                self.capture_list = capture_list
            
            def emit(self, record):
                self.capture_list.append(record.getMessage())
        
        self.handler = TestHandler(self.log_capture)
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.INFO)
    
    def teardown_method(self):
        """Clean up after each test"""
        self.logger.removeHandler(self.handler)
    
    def test_save_traced_value(self):
        """Test saving a traced value"""
        self.hook.save('test_value', 42, Traced[int])
        
        assert len(self.log_capture) == 1
        assert "Variable 'test_value' of type 'Traced' updated to 42" in self.log_capture[0]
    
    def test_save_custom_type(self):
        """Test saving a custom tracked type"""
        # Define and register a test type
        type TestType[T] = T
        register_tracked_type('TestType', TestType)
        
        from hooksett import TestType
        self.hook.save('test_value', "custom", TestType[str])
        
        assert len(self.log_capture) == 1
        assert "Variable 'test_value' of type 'TestType' updated to custom" in self.log_capture[0]
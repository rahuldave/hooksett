"""
PyTest configuration file for Hooksett tests
"""
import pytest
from hooksett import HookManager


@pytest.fixture(autouse=True)
def reset_hook_manager():
    """Reset the HookManager singleton between tests"""
    manager = HookManager()
    manager.input_hooks = []
    manager.output_hooks = []
    yield
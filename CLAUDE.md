# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test Commands
- Run all tests: `pixi run test`
- Run integration tests: `pixi run integration`
- Run a single test: `pytest tests/test_file.py::TestClass::test_method`
- Run example file: `pixi run python examples/file_name.py`

## Code Style Guidelines
- Indentation: 4 spaces
- Naming: snake_case for functions/variables, PascalCase for classes
- Imports: standard library first, then third-party, then local modules
- Type annotations: required for all function parameters and return types
- Docstrings: use triple quotes with clear descriptions
- Error handling: use appropriate exception types with informative messages

## Variable Tracking Behavior
- Local variables annotated with `Traced[Type]` are tracked automatically
- Variables are saved to hooks only ONCE at function/method exit
- The final value of variables (after all modifications) is what gets saved
- This behavior enables clean integration with databases and logging systems

## Project Structure
- Main code in `src/hooksett/`
- Examples in `examples/`
- Tests in `tests/` using pytest
- Python 3.11+ required
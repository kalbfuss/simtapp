# Python Best Practices Instructions

## Overview
This document outlines the best practices to be followed across all files in the project. These guidelines ensure consistency, readability, and maintainability of the codebase.

## General Guidelines

### Code Style
- **Indentation**: Use 4 spaces per indentation level. Do not use tabs.
- **Line Length**: Limit lines to 79 characters for code and 72 characters for comments and docstrings.
- **Imports**: Group imports in the following order:
  1. Standard library imports
  2. Related third-party imports
  3. Local application/library-specific imports

### Naming Conventions
- **Variables and Functions**: Use `snake_case` for variable and function names.
- **Classes**: Use `PascalCase` for class names.
- **Constants**: Use `UPPER_CASE` for constant names.
- **Private Members**: Use a leading underscore `_` for private members.

### Documentation
- **Docstrings**: Use docstrings to document modules, classes, and functions. Follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for docstring format.
- **Comments**: Use comments sparingly and only to explain complex logic or non-obvious code.

### Error Handling
- Use exceptions to handle errors gracefully.
- Avoid using bare `except:` clauses. Instead, catch specific exceptions.
- Use custom exceptions for application-specific errors.

### Testing
- Write unit tests for all functions and classes.
- Use descriptive test names that explain the purpose of the test.
- Follow the Arrange-Act-Assert pattern in tests.

### Performance
- Avoid premature optimization.
- Use built-in functions and libraries where possible.
- Profile code to identify performance bottlenecks before optimizing.

### Security
- Avoid using `eval()` or `exec()` with untrusted input.
- Use environment variables for sensitive information like API keys and passwords.
- Validate and sanitize all user inputs.

## Project-Specific Guidelines

### File Structure
- **Models**: Place in `./plog/models`
- **Controllers**: Place in `./plog/controllers`
- **Views**: Place in `./plog/pages`
- **Tests**: Place in `./tests`

### Interface Design
- **Tables**: Use `st.aggrid`. Do **not** use `st.dataframe`. Limit the number of displayed rows to `NUM_ROWS` (default value: 20). Use scroll bar where necessary.
- **Toolbars**: Use `st_segmented_control` (https://docs.streamlit.io/develop/api-reference/widgets/st.segmented_control). Do **not** use buttons. Add at the top and bottom of a page.
- Minimize page reloads.

### Commands
- Always activate virtual environment prior to running any command: `source .venv/bin/activate`

## Tools and Libraries
- **Streamlit**: For building the user interface.
- **streamlit-aggrid**: For rendering tables.
- **SQLAlchemy**: For database operations.
- **sqlalchemy-history**: For tracking changes in the database.

## References
- [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)
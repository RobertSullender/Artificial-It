# 🤖 Contribution Guidelines for Artificial-It

Thank you for your interest in contributing to Artificial-It! This project is an open-source AI image generation application built with Stable Diffusion, PyTorch, and PyQt6.

## 🚀 Getting Started

### Development Setup

**Prerequisites:**
- Python 3.9 or higher
- Git
- Code editor (VS Code recommended)

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/RobertSullender/Artificial-It.git
cd Artificial-It

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Run Development Mode

```bash
# Start the application
python src/main.py

# Test specific components
pytest  # Run unit tests
black --check src/  # Check code formatting
flake8 src/  # Check linting rules
```

## 📝 Code Style Guidelines

We use **Black** for consistent code formatting:

- **Line length**: 120 characters maximum
- **Imports**: Grouped and sorted (using `isort`)
- **Type hints**: Required for all public functions
- **Docstrings**: Google-style or NumPy-style preferred

### Example

```python
from typing import Dict, Any

def process_image(image: Any) -> str:
    """Process image and return result.

    Args:
        image: The input image to process

    Returns:
        Path to the processed image file
    """
    ...
```

## 🐛 Bug Reports

When reporting bugs, please include:

- **Description**: Clear explanation of the bug
- **Steps to Reproduce**: Numbered steps showing how to reproduce
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**: Python version, OS, PyQt6 version, etc.
- **Screenshots/Error Logs**: If applicable

### Example Bug Report

```markdown
## 🐛 Describe the bug

**Description:** Progress bar stuck at 0% during generation

**Steps to Reproduce:**
1. Open application and click "Generate"
2. Enter any prompt
3. Observe progress bar

**Expected behavior:** Progress should show percentages (5%, 10%, etc.)

**Environment:**
- Python: 3.11.0
- OS: Ubuntu 22.04
- PyQt6: 6.5.0

**Error logs:** None, but progress text updates correctly
```

## ✨ Feature Requests

We welcome feature suggestions! When proposing new features:

### Include the Following:

1. **Problem Statement**: What issue are you trying to solve?
2. **Proposed Solution**: How should the feature work?
3. **Alternatives Considered**: What other approaches have you thought of?
4. **Use Cases**: Who will benefit from this feature?
5. **Technical Considerations** (optional): Design suggestions, API changes

### Example Feature Request

```markdown
## 🌟 Feature Proposal

**Problem:** Currently unable to generate multiple images at once

**Proposed Solution:** Add batch generation capability that accepts a list of prompts and generates all images sequentially

**Use Cases:**
- Artists who need consistent style variations
- Designers creating mood boards
- Developers testing different parameters
```

## 🧪 Testing Requirements

All contributions must include tests where applicable:

### Test Files Location
```
tests/
├── unit/         # Unit tests for individual components
├── integration/  # Integration tests for workflows
└── fixtures/     # Test data and mock objects
```

### Test Structure

```python
import pytest
from src.core.engine import ExecutionEngine

class TestExecutionEngine:
    def test_basic_generation(self):
        """Test successful image generation."""
        engine = ExecutionEngine(...)
        result = engine.run_task("test-1", {"prompt": "test"})
        assert result is not None
```

## 📋 Pull Request Checklist

Before submitting your PR, ensure:

- [ ] Code follows project style guidelines (Black formatted)
- [ ] All tests pass (`pytest`)
- [ ] New features include tests
- [ ] Bug fixes verified in test suite
- [ ] Documentation updated if needed
- [ ] No new linting warnings introduced
- [ ] Changes are backward compatible

### PR Template

When opening a pull request, use the following template:

```markdown
## Description
Please include a summary of changes and reference any issues fixed.

Fixes #<issue-number>

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested your changes:
- [ ] Unit tests added/updated
- [ ] Integration tests passed
- [ ] Manual testing completed
```

## 🎓 Learning Resources

If you're new to contributing, check out:

- [Python Black Style Guide](https://black.readthedocs.io/)
- [Flake8 Linting Rules](https://flake8.pycqa.org/)
- [pytest Documentation](https://docs.pytest.org/)

## 💬 Questions?

Reach out via:
- GitHub Issues (for bugs)
- Email: contact@github.com/RobertSullender

---

**Thank you for contributing to Artificial-It! 🎨✨**

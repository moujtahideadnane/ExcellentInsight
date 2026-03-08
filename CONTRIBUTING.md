# Contributing to ExcellentInsight

Thank you for your interest in contributing to ExcellentInsight! This document provides guidelines and instructions for contributing to the project.

---

## 🎯 Ways to Contribute

There are many ways you can contribute to ExcellentInsight:

1. **🐛 Report Bugs** - Help us identify and fix issues
2. **💡 Suggest Features** - Share ideas for new capabilities
3. **📝 Improve Documentation** - Make our docs clearer and more comprehensive
4. **🔧 Submit Code** - Fix bugs or implement new features
5. **🧪 Write Tests** - Improve test coverage
6. **🎨 Design Improvements** - Enhance UI/UX
7. **🌍 Translations** - Help make ExcellentInsight accessible worldwide

---

## 📋 Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- **Be Respectful**: Treat everyone with respect and kindness
- **Be Collaborative**: Work together and help each other
- **Be Professional**: Keep discussions constructive and on-topic
- **Be Inclusive**: Welcome contributors from all backgrounds

---

## 🚀 Getting Started

### Prerequisites

- **Git**: Version control
- **Python**: 3.12 or higher
- **Node.js**: 20 or higher
- **Docker**: For local development (recommended)
- **PostgreSQL**: 16+ (if not using Docker)
- **Redis**: 7+ (if not using Docker)

### Local Development Setup

1. **Fork the Repository**
   ```bash
   # Click "Fork" on GitHub, then:
   git clone https://github.com/YOUR_USERNAME/ExcellentInsight.git
   cd ExcellentInsight
   ```

2. **Set Up Remote**
   ```bash
   git remote add upstream https://github.com/moadnane/ExcellentInsight.git
   ```

3. **Create Environment Files**
   ```bash
   cp .env.example .env
   cp frontend/.env.local.example frontend/.env.local
   # Edit these files with your configuration
   ```

4. **Start with Docker (Recommended)**
   ```bash
   docker-compose up -d
   docker-compose exec backend alembic upgrade head
   ```

5. **Or Run Manually**
   ```bash
   # Backend
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --reload

   # Worker (separate terminal)
   arq app.workers.settings.WorkerSettings

   # Frontend (separate terminal)
   cd frontend
   npm install
   npm run dev
   ```

6. **Verify Setup**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## 🐛 Reporting Bugs

### Before Submitting

1. **Search Existing Issues**: Check if the bug has already been reported
2. **Update to Latest**: Ensure you're using the latest version
3. **Reproduce Consistently**: Confirm the bug is reproducible

### Bug Report Template

```markdown
**Description**
A clear description of the bug.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Screenshots**
If applicable, add screenshots.

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.12.1]
- Node version: [e.g., 20.10.0]
- Browser: [e.g., Chrome 120]

**Additional Context**
Any other relevant information.
```

---

## 💡 Suggesting Features

### Feature Request Template

```markdown
**Problem Statement**
Describe the problem you're trying to solve.

**Proposed Solution**
Describe your proposed solution.

**Alternatives Considered**
Other solutions you've considered.

**Use Cases**
Real-world scenarios where this would be useful.

**Additional Context**
Mockups, diagrams, or related issues.
```

---

## 🔧 Submitting Code Changes

### Development Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

   **Branch Naming Conventions**:
   - `feature/` - New features
   - `fix/` - Bug fixes
   - `docs/` - Documentation changes
   - `refactor/` - Code refactoring
   - `test/` - Test improvements
   - `chore/` - Maintenance tasks

2. **Make Your Changes**
   - Write clear, concise code
   - Follow the project's coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   # Backend tests
   pytest -v --cov=app tests/

   # Frontend tests
   cd frontend
   npm test

   # Linting
   ruff check app/
   npm run lint
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add awesome new feature"
   ```

   **Commit Message Convention** (Conventional Commits):
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `style:` - Code style changes (formatting, etc.)
   - `refactor:` - Code refactoring
   - `test:` - Adding or updating tests
   - `chore:` - Maintenance tasks

   **Examples**:
   ```
   feat: add natural language query interface
   fix: resolve memory leak in parser
   docs: update API documentation for webhooks
   refactor: optimize database queries for performance
   test: add unit tests for formula engine
   ```

5. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Go to your fork on GitHub
   - Click "Compare & pull request"
   - Fill out the PR template
   - Link any related issues

---

## 📝 Pull Request Guidelines

### PR Checklist

Before submitting your PR, ensure:

- [ ] Code follows project style guidelines
- [ ] All tests pass (`pytest` and `npm test`)
- [ ] New code has tests
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] PR description is clear and detailed
- [ ] No merge conflicts with main branch

### PR Template

```markdown
## Description
Brief description of the changes.

## Motivation
Why are these changes needed?

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
How was this tested?

## Screenshots (if applicable)
Add screenshots for UI changes.

## Related Issues
Closes #123
Relates to #456

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

### Review Process

1. **Automated Checks**: CI/CD runs tests and linting
2. **Code Review**: Maintainers review your code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, maintainers will merge

---

## 🧪 Writing Tests

### Backend Tests (pytest)

```python
# tests/test_feature.py
import pytest
from app.services.my_service import my_function

def test_my_function():
    """Test that my_function works correctly."""
    result = my_function(input_data)
    assert result == expected_output

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result is not None
```

### Frontend Tests (Jest + React Testing Library)

```typescript
// components/__tests__/MyComponent.test.tsx
import { render, screen } from '@testing-library/react';
import MyComponent from '../MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

---

## 📚 Documentation Guidelines

### Code Documentation

**Python (Google Style)**:
```python
def process_data(data: pd.DataFrame, options: dict) -> pd.DataFrame:
    """Process dataframe with given options.

    Args:
        data: Input dataframe to process
        options: Processing configuration options

    Returns:
        Processed dataframe with transformations applied

    Raises:
        ValueError: If data is empty or options invalid

    Example:
        >>> data = pd.DataFrame({'col': [1, 2, 3]})
        >>> result = process_data(data, {'normalize': True})
    """
    pass
```

**TypeScript (JSDoc)**:
```typescript
/**
 * Fetches dashboard data from API
 * @param jobId - Unique job identifier
 * @param options - Optional fetch configuration
 * @returns Promise resolving to dashboard data
 * @throws {APIError} If request fails
 */
async function fetchDashboard(
  jobId: string,
  options?: RequestOptions
): Promise<Dashboard> {
  // Implementation
}
```

### README & Markdown

- Use clear headings
- Include code examples
- Add diagrams where helpful
- Keep formatting consistent
- Test all code examples

---

## 🎨 Code Style Guidelines

### Python Style

- **PEP 8**: Follow Python style guide
- **Type Hints**: Use type hints everywhere
- **Line Length**: Max 120 characters
- **Imports**: Group and sort (stdlib, third-party, local)
- **Naming**:
  - `snake_case` for functions/variables
  - `PascalCase` for classes
  - `UPPER_CASE` for constants

**Example**:
```python
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_by_id(
    db: AsyncSession,
    user_id: str,
) -> Optional[User]:
    """Retrieve user by ID."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

### TypeScript Style

- **ESLint**: Follow project ESLint rules
- **Prettier**: Auto-format with Prettier
- **Naming**:
  - `camelCase` for variables/functions
  - `PascalCase` for components/classes
  - `UPPER_CASE` for constants

**Example**:
```typescript
interface DashboardProps {
  jobId: string;
  onUpdate?: (data: Dashboard) => void;
}

export function DashboardView({ jobId, onUpdate }: DashboardProps) {
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchDashboard(jobId).then(onUpdate);
  }, [jobId, onUpdate]);

  return <div>{/* JSX */}</div>;
}
```

---

## 🔍 Code Review Process

### What We Look For

✅ **Good**:
- Clear, self-documenting code
- Comprehensive tests
- Updated documentation
- No breaking changes (or well-documented)
- Performance considerations
- Security best practices

❌ **Avoid**:
- Uncommitted debug code
- Hardcoded credentials
- Commented-out code
- Breaking changes without discussion
- Missing tests
- Unrelated changes in PR

### Response Times

- **Initial Review**: Within 2-3 business days
- **Follow-up**: Within 1-2 business days
- **Urgent Fixes**: Within 24 hours

---

## 🏗️ Architecture Decisions

### When to Discuss First

For these types of changes, **create an issue first** before coding:

- Major architectural changes
- New dependencies
- Breaking API changes
- Database schema changes
- Performance-critical modifications

### Decision Process

1. **Issue Discussion**: Propose change in GitHub issue
2. **Community Feedback**: Gather input from maintainers/community
3. **Design Document**: Create detailed design doc if needed
4. **Approval**: Get maintainer approval
5. **Implementation**: Code and submit PR

---

## 🌟 Recognition

Contributors are recognized in:
- **CHANGELOG.md**: Major contributions noted
- **GitHub Contributors**: Automatic recognition
- **README.md**: Special thanks section
- **Release Notes**: Feature attribution

---

## 📞 Getting Help

### Where to Ask Questions

- **General Questions**: [GitHub Discussions Q&A](https://github.com/moadnane/ExcellentInsight/discussions/categories/q-a)
- **Bug Reports**: [GitHub Issues](https://github.com/moadnane/ExcellentInsight/issues)
- **Feature Ideas**: [GitHub Discussions Ideas](https://github.com/moadnane/ExcellentInsight/discussions/categories/ideas)
- **Security Issues**: security@excellentinsight.com (private)

### Maintainers

- **@moadnane** - Project Lead

---

## 📜 License

By contributing to ExcellentInsight, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to ExcellentInsight! 🎉**

Together, we're building the best open-source spreadsheet intelligence platform.

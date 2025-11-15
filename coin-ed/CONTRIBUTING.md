# Contributing to Coin'ed

Thank you for your interest in contributing to Coin'ed! This document provides guidelines and instructions for contributing.

## 🤝 How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/YOUR_USERNAME/coin-ed/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable
   - Your environment (OS, Node version, browser)

### Suggesting Features

1. Check [Issues](https://github.com/YOUR_USERNAME/coin-ed/issues) for existing suggestions
2. Create a new issue with the `enhancement` label
3. Describe the feature and its benefits
4. Provide examples or mockups if possible

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/coin-ed.git
   cd coin-ed
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Make your changes**
   - Follow the code style guidelines below
   - Write clear commit messages
   - Add tests if applicable
   - Update documentation

4. **Test your changes**
   ```bash
   npm test
   npm run build
   npm start
   ```

5. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Go to the repository on GitHub
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template
   - Wait for review

## 📝 Code Style Guidelines

### TypeScript/Angular

- Use TypeScript strict mode
- Follow Angular style guide
- Use meaningful variable names
- Add JSDoc comments for public methods
- Keep components focused and single-purpose

### Example:
```typescript
/**
 * Parse incoming JSON data from scrapers
 * @param jsonData - Raw data from web scraper
 */
parseScrapedData(jsonData: any): void {
  // Implementation
}
```

### File Naming

- Components: `kebab-case.component.ts`
- Services: `kebab-case.service.ts`
- Models: `kebab-case.model.ts`
- Use meaningful, descriptive names

### CSS

- Use BEM naming convention when applicable
- Mobile-first responsive design
- Keep specificity low
- Use CSS variables for theming

## 🧪 Testing

- Write unit tests for new components
- Write integration tests for services
- Ensure all tests pass before submitting PR
- Aim for high code coverage

```bash
npm test
```

## 📚 Documentation

- Update README.md if adding features
- Add JSDoc comments to new methods
- Update INTEGRATION_GUIDE.md for API changes
- Include examples in documentation

## 🌿 Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates

## 💬 Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add sentiment analysis for Ethereum
fix: correct chart rendering on mobile
docs: update integration guide
refactor: simplify data parsing logic
test: add tests for portfolio component
```

## 🎯 Development Workflow

1. Check existing issues/PRs to avoid duplicates
2. Discuss major changes in an issue first
3. Keep PRs focused and small
4. Write clear descriptions
5. Be responsive to feedback
6. Update your PR based on reviews

## 🐛 Bug Fix Process

1. Reproduce the bug
2. Write a failing test
3. Fix the bug
4. Ensure test passes
5. Submit PR with test and fix

## ✨ Feature Development Process

1. Discuss feature in an issue
2. Get approval from maintainers
3. Design the implementation
4. Implement with tests
5. Update documentation
6. Submit PR

## 🔍 Code Review Process

- All PRs require at least one approval
- Address all review comments
- Keep discussions professional and constructive
- Don't take feedback personally
- Learn and improve

## 📋 PR Checklist

Before submitting your PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New code has tests
- [ ] Documentation is updated
- [ ] No console.log statements
- [ ] No commented-out code
- [ ] Commit messages are clear
- [ ] PR description explains changes

## 🚀 Areas Needing Contribution

### High Priority
- Backend scraper implementation
- Sentiment analysis AI
- WebSocket real-time updates
- User authentication

### Medium Priority
- Additional chart types
- More cryptocurrency support
- Historical data visualization
- Trading alerts

### Low Priority
- Dark/light theme toggle
- Internationalization (i18n)
- Mobile app version
- Browser extension

## 💡 Tips for Contributors

- Start with small contributions
- Ask questions if unclear
- Read existing code to understand patterns
- Test thoroughly before submitting
- Be patient with the review process

## 🙋 Getting Help

- Ask in [Discussions](https://github.com/YOUR_USERNAME/coin-ed/discussions)
- Comment on related issues
- Check documentation first
- Be specific about your problem

## 📜 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- No harassment or discrimination
- Follow GitHub's Community Guidelines

## 🎉 Recognition

Contributors will be:
- Listed in README.md
- Mentioned in release notes
- Given credit in commit history

## 📞 Contact

Questions? Reach out:
- GitHub Issues
- GitHub Discussions
- Project maintainers

---

Thank you for contributing to Coin'ed! Your help makes this project better for everyone. 🚀


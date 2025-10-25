# Contributing to Strapi Plugin Action Buttons

Thank you for your interest in contributing to this project! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue on GitHub with:

- A clear title and description
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment (Strapi version, Node version, OS)
- Screenshots if applicable

### Suggesting Features

Feature requests are welcome! Please:

- Check if the feature has already been requested
- Provide a clear use case
- Explain why this feature would be useful

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Test your changes thoroughly
5. Commit with clear, descriptive messages
6. Push to your fork
7. Create a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/strapi-plugin-action-buttons.git
cd strapi-plugin-action-buttons

# Install dependencies
npm install

# Link to a test Strapi project
cd /path/to/test-strapi-project
npm install /path/to/strapi-plugin-action-buttons

# Start development
npm run develop
```

### Code Style

- Use TypeScript for type safety
- Follow existing code formatting
- Add comments for complex logic
- Keep functions small and focused

### Testing

Before submitting a PR:

- Test the plugin in a fresh Strapi project
- Verify it works with different content types
- Test error scenarios
- Ensure no console errors

## Code of Conduct

Be respectful and constructive in all interactions.

## Questions?

Feel free to open a discussion on GitHub if you have questions.

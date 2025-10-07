# WonkaChat Documentation

Official documentation and user guide for WonkaChat - the AI-powered collaboration platform.

This repository contains the complete documentation site built with Mintlify, covering everything users need to know about using WonkaChat effectively.

## 📚 Documentation Structure

The documentation is organized into the following sections:

- **Welcome** - Introduction, quick start, and why WonkaChat
- **AI Agents** - Creating, finding, using, and teaching agents
- **Tools Connection** - MCP setup and tool integration
- **Improved Usage** - Best practices, prompt engineering, and prompt library
- **Security & Governance** - Security overview, access control, best practices, and compliance
- **Support & Resources** - Troubleshooting, FAQs, and getting help
- **Learning** - Foundations of AI agents and MCP concepts
- **Use Cases** - Practical examples and applications
- **Updates** - Changelog and version history
- **Roadmap** - Upcoming features and development plans

## 🛠️ Development

### Prerequisites

Install the [Mintlify CLI](https://www.npmjs.com/package/mint) to preview documentation changes locally:

```bash
npm i -g mint
```

### Local Development

Run the following command at the root of the documentation (where `docs.json` is located):

```bash
mint dev
```

View your local preview at `http://localhost:3000`

### File Structure

```
.
├── docs.json                 # Navigation and site configuration
├── welcome/                  # Getting started pages
├── ai-agents/               # AI agent documentation
├── tools-connection/        # MCP and tool integration
├── improved-usage/          # Usage best practices
├── security-governance/     # Security and compliance
├── support-resources/       # Help and troubleshooting
├── learn/                   # Educational content
├── use/                     # Use cases
├── updates/                 # Changelog
├── roadmap/                 # Future development
└── images/                  # Documentation images
```

## ✍️ Writing Guidelines

### Technical Writing Standards

This documentation follows Mintlify technical writing best practices:

- Use clear, direct language appropriate for technical audiences
- Write in second person ("you") for instructions
- Lead with the most important information
- Break complex procedures into numbered steps
- Include code examples and screenshots where helpful
- Use Mintlify components (Cards, Accordions, Tabs, etc.) for better organization

### Mintlify Components

Common components used throughout:

- `<Steps>` - Sequential instructions
- `<Tabs>` - Alternative content or platform-specific info
- `<Accordion>` - Collapsible detailed information
- `<Card>` / `<CardGroup>` - Visual navigation and highlights
- `<Frame>` - Image containers with captions
- `<Info>` / `<Tip>` / `<Warning>` / `<Check>` - Callout boxes
- `<CodeGroup>` - Multi-language code examples

### Content Requirements

Every documentation page must include:

1. **YAML frontmatter** with title and description
2. **Clear headings** following logical hierarchy
3. **Practical examples** that users can follow
4. **Visual aids** (screenshots, diagrams) where appropriate
5. **No placeholder content** - all information must be accurate and verified

### Accuracy Policy

⚠️ **Important**: Only document features that actually exist in WonkaChat. Do not create speculative or placeholder content. All features, UI elements, and workflows must be verified against the actual product.

## 🚀 Publishing Changes

### Automatic Deployment

Install the Mintlify GitHub app from your [dashboard](https://dashboard.mintlify.com/settings/organization/github-app) to automatically deploy changes. Updates to the default branch are deployed to production automatically.

### Manual Review

Before committing:

1. Test locally with `mint dev`
2. Check for broken links and images
3. Verify all code examples work
4. Ensure screenshots are up-to-date
5. Review for spelling and grammar

## 🆘 Need Help?

### Troubleshooting

- **Dev environment not running**: Run `mint update` to get the latest CLI version
- **Page loads as 404**: Ensure you're running in a folder with a valid `docs.json`
- **Images not loading**: Check that image paths are correct and files exist in `/images/`
- **Navigation issues**: Verify all pages referenced in `docs.json` exist

### Resources

- [Mintlify Documentation](https://mintlify.com/docs)
- [Mintlify Components Reference](https://mintlify.com/docs/content/components)
- [WonkaChat Website](https://www.meetwonka.com)

## 📝 Contributing

When contributing to the documentation:

1. Create a new branch for your changes
2. Test locally before committing
3. Use descriptive commit messages
4. Follow the established writing style
5. Ensure all information is accurate and current

## 📄 License

See [LICENSE](LICENSE) file for details.

---

**Built with [Mintlify](https://mintlify.com)** 📘


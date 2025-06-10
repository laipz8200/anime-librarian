<div align="center">

# AnimeLibrarian

[![Code Quality](https://github.com/laipz8200/anime-librarian/actions/workflows/code-quality.yml/badge.svg)](https://github.com/laipz8200/anime-librarian/actions/workflows/code-quality.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

🎬 AI-powered video file organizer that makes your media library beautiful

[Getting Started](#-quick-start) • [Features](#-key-features) • [Documentation](#-documentation) • [Development](#-development)

![anime-librarian-preview](https://github.com/user-attachments/assets/8e7cd70f-bf70-4dd4-8c05-745287e368e1)

</div>

---

## ✨ Key Features

- 🤖 **AI-Powered Naming**: Intelligently renames files using LLM technology
- 📁 **Smart Organization**: Automatically moves files to appropriate directories
- 🎯 **Media Player Compatible**: Ensures compatibility with Infuse, Plex, and more
- 🔍 **Preview Changes**: Dry-run option to review changes before applying
- 🚀 **Easy to Use**: Simple CLI interface with sensible defaults
- 📺 **Universal Support**: Works with anime, movies, TV shows, and more

## 🚀 Quick Start

```bash
# Install AnimeLibrarian
pip install git+https://github.com/laipz8200/anime-librarian.git

# Set up your environment
cp .env.example .env
# Edit .env with your Dify API credentials

# Run with default settings
anime-librarian

# Or specify custom paths
anime-librarian --source ~/Downloads --target ~/Media
```

## 📋 Prerequisites

- [Dify](https://cloud.dify.ai) account
- Language model access through Dify
- AnimeLibrarian workflow in your Dify account

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/laipz8200/anime-librarian.git
cd anime-librarian

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install .
```

## 📖 Documentation

### Dify Workflow Setup

1. Sign up at [Dify](https://cloud.dify.ai)
2. Configure your language model
3. Import the workflow:
   - Use DSL import
   - Import `Anime Librarian.yml` from `Dify DSL File`
4. Create an API key
5. Copy API key and endpoint URL

> [!TIP]
> Add a TMDB API key to enhance media identification accuracy!

### Configuration

1. Copy and edit the environment file:

   ```bash
   cp .env.example .env
   ```

2. Update `.env` values per the comments

⚠️ **Important**: Create media category subdirectories in your `ANIMELIBRARIAN_TARGET_PATH` for optimal AI organization.

### Advanced Usage

```bash
# Preview changes (dry run)
anime-librarian --dry-run

# Auto-confirm all prompts
anime-librarian --yes

# Enable detailed logging
anime-librarian --verbose

# View all options
anime-librarian --help
```

## 🔄 How It Works

1. 📂 Scans source directory for videos
2. 🗂️ Identifies existing media categories
3. 🤖 AI analyzes filenames via Dify
4. ✨ Generates standardized names
5. 📝 Shows proposed changes
6. ✅ Moves and renames upon confirmation

## 👩‍💻 Development

```bash
# Setup development environment
pip install -e ".[dev]"
pre-commit install

# Quality checks
pytest                    # Run tests
pytest --cov             # Test coverage
ruff check .             # Linting
ruff format .            # Formatting
mypy .                   # Type checking
```

### Quality Assurance

- **Pre-commit Hooks**: Automatic code quality checks
  - Linting (ruff)
  - Formatting (ruff)
  - Type checking (mypy)

- **CI/CD**: GitHub Actions workflow
  - Code quality checks
  - Test suite execution
  - Automated PR validation

## 🔍 Troubleshooting

Common solutions for:

- 🔑 **API Issues**: Verify Dify credentials in `.env`
- 📁 **Access Errors**: Check directory permissions
- 🤖 **AI Problems**: Validate Dify workflow setup
- 📂 **Organization**: Ensure target directories exist
- 🔍 **Testing**: Use `--dry-run` to preview changes
- 📝 **Debugging**: Enable `--verbose` logging

## 🤝 Contributing

Contributions are welcome! Feel free to:

- 🐛 Report bugs
- 💡 Suggest features
- 🔧 Submit pull requests

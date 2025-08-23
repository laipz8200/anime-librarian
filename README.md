<div align="center">

# AnimeLibrarian

[![Code Quality](https://github.com/laipz8200/anime-librarian/actions/workflows/code-quality.yml/badge.svg)](https://github.com/laipz8200/anime-librarian/actions/workflows/code-quality.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

🎬 AI-powered video file organizer that makes your media library beautiful

[Getting Started](#-quick-start) • [Features](#-key-features) • [Documentation](#-documentation) • [Development](#-development)

![anime-librarian-preview](https://github.com/user-attachments/assets/8e7cd70f-bf70-4dd4-8c05-745287e368e1)

</div>

______________________________________________________________________

## ✨ Key Features

- 🤖 **AI-Powered Naming**: Intelligently renames files using LLM technology
- 📁 **Smart Organization**: Automatically moves files to appropriate directories
- 🎯 **Media Player Compatible**: Ensures compatibility with Infuse, Plex, and more
- 🔍 **Preview Changes**: Dry-run option to review changes before applying
- 🚀 **Beautiful CLI**: Rich terminal interface with tables, progress bars, and styled output
- 📺 **Universal Support**: Works with anime, movies, TV shows, and more
- 🎨 **Interactive UX**: Color-coded output, confirmation prompts, and clear progress indicators

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

### Using pip (for users)

```bash
# Install directly from GitHub
pip install git+https://github.com/laipz8200/anime-librarian.git
```

### Using uv (recommended for development)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/laipz8200/anime-librarian.git
cd anime-librarian

# Install dependencies with uv
uv sync
```

### Traditional pip setup

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
1. Configure your language model
1. Import the workflow:
   - Use DSL import
   - Import `Anime Librarian.yml` from `Dify DSL File`
1. Create an API key
1. Copy API key and endpoint URL

> [!TIP]
> Add a TMDB API key to enhance media identification accuracy!

### Configuration

1. Copy and edit the environment file:

   ```bash
   cp .env.example .env
   ```

1. Update `.env` values per the comments

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
1. 🗂️ Identifies existing media categories
1. 🤖 AI analyzes filenames via Dify (with progress indicator)
1. ✨ Generates standardized names
1. 📝 Shows proposed changes in a formatted table
1. ✅ Moves and renames with real-time progress bar

## 🎨 Enhanced User Experience

AnimeLibrarian now features a beautiful Rich-powered terminal interface:

- **Color-coded Messages**:

  - 🟢 Success messages in green
  - 🔴 Errors in red
  - 🟡 Warnings in yellow
  - 🔵 Info messages in blue

- **Interactive Tables**: File moves displayed in formatted tables with clear source → target mapping

- **Progress Indicators**:

  - Spinning indicators for AI analysis
  - Progress bars for file operations
  - Real-time status updates

- **Smart Prompts**: Interactive confirmation dialogs with sensible defaults

- **Summary Panels**: Operation summaries in styled panels after completion

- **Terminal Compatibility**: Colors and formatting are automatically enabled, even in non-standard terminal environments

## 👩‍💻 Development

### Setup Development Environment

```bash
# Install uv package manager (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/laipz8200/anime-librarian.git
cd anime-librarian

# Install dependencies with uv
uv sync

# Install pre-commit hooks
pre-commit install
```

### Development Workflow

```bash
# Run linting and formatting
make lint                 # Format code and fix issues
make format              # Just format code
make check               # Check code without fixes

# Run tests
make test                # Run all tests
make test-mock           # Run mock server tests only
pytest --cov             # Run with coverage report

# Clean up
make clean               # Remove generated files
```

### Testing with Mock Server

The project includes a comprehensive mock Dify server for testing without API access:

```bash
# Run integration tests with mock server
uv run pytest tests/test_integration_with_mock_server.py -v

# Use mock server in your tests
from tests.fixtures.mock_server_fixtures import run_mock_server

with run_mock_server() as server_url:
    # Your test code here
    pass
```

See `tests/README_MOCK_SERVER.md` for detailed mock server documentation.

### Quality Assurance

- **Pre-commit Hooks**: Automatic code quality checks

  - Linting (ruff)
  - Formatting (ruff)
  - Type checking (mypy)

- **CI/CD**: GitHub Actions workflow

  - Code quality checks
  - Test suite execution (98+ tests)
  - Automated PR validation

- **Make Commands**: Quick development tasks

  ```bash
  make help     # Show all available commands
  make lint     # Run full linting
  make test     # Run all tests
  ```

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

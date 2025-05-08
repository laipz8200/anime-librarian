# AnimeLibrarian

[![Code Quality](https://github.com/laipz8200/anime-librarian/actions/workflows/code-quality.yml/badge.svg)](https://github.com/laipz8200/anime-librarian/actions/workflows/code-quality.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A command-line tool that uses AI to rename and organize video files.

This project aims to facilitate moving local video files to corresponding directories and renaming them to be recognizable by software like Infuse. While originally focused on anime, it works for all types of video content including movies and TV shows. Since original filenames often differ from standard naming conventions, this project uses LLM to automate this conversion process.

## Prerequisites

Before you begin, you'll need:

1. A [Dify](https://cloud.dify.ai) account
2. Access to a language model through Dify
3. The AnimeLibrarian workflow imported into your Dify account

## Installation

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

## Dify Workflow Setup

Before configuring the application, you need to set up the required workflow in Dify:

1. Sign up for an account at [Dify](https://cloud.dify.ai) if you don't already have one
2. Configure a language model in your Dify account according to their documentation
3. Import the AnimeLibrarian workflow:
   - Use the DSL import feature
   - Import the `Anime Librarian.yml` file from the `Dify DSL File` directory in this repository
4. Open the imported workflow
5. Navigate to the API section and create a new API key
6. Copy the API key and workflow endpoint URL for use in the next section

## Configuration

This application uses environment variables for configuration. You can set these in a `.env` file in the root directory of the project.

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and update the values:

   ```env
   # API configuration
   ANIMELIBRARIAN_DIFY_WORKFLOW_RUN_ENDPOINT=https://api.dify.ai/v1/workflows/run
   ANIMELIBRARIAN_DIFY_API_KEY=your-api-key-here

   # Default paths - update these to your actual directories
   ANIMELIBRARIAN_SOURCE_PATH=/path/to/your/downloads
   ANIMELIBRARIAN_TARGET_PATH=/path/to/your/video/collection

   # API request timeout in seconds
   ANIMELIBRARIAN_API_TIMEOUT=300
   ```

   Make sure to update:
   - `ANIMELIBRARIAN_DIFY_WORKFLOW_RUN_ENDPOINT` with your Dify workflow endpoint URL
   - `ANIMELIBRARIAN_DIFY_API_KEY` with your Dify API key
   - `ANIMELIBRARIAN_SOURCE_PATH` with the path to your downloads folder
   - `ANIMELIBRARIAN_TARGET_PATH` with the path to your video collection

   **Important**: Before running the application, you should create subdirectories in your `ANIMELIBRARIAN_TARGET_PATH` with the expected names for your media categories. This helps the AI make more stable and accurate file organization decisions.

## Usage

```bash
# Basic usage
python -m anime_librarian.main

# With custom source and target directories
python -m anime_librarian.main --source /path/to/downloads --target /path/to/videos

# Dry run (show what would be done without actually renaming files)
python -m anime_librarian.main --dry-run

# Automatically answer yes to all prompts
python -m anime_librarian.main --yes

# Enable verbose logging
python -m anime_librarian.main --verbose

# View command-line help and all available options
python -m anime_librarian.main --help
```

## How It Works

AnimeLibrarian uses AI to intelligently rename and organize your video files:

1. The application scans your source directory for video files
2. It also scans your target directory to identify existing media category folders
3. It sends both the source filenames and target directory names to a Dify workflow powered by a language model
4. The AI analyzes each filename and suggests:
   - A proper standardized name for the file
   - The appropriate target directory for the file (chosen from your existing directories)
5. The application shows you the proposed changes before making them
6. Upon confirmation, it moves and renames the files according to the AI suggestions

This process helps maintain a well-organized media library that's compatible with media players like Infuse, Plex, and others.

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run tests with coverage
pytest --cov

# Run linting
ruff check .

# Run formatting
ruff format .

# Run type checking
mypy .

# Run all pre-commit hooks manually
pre-commit run --all-files
```

### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality before committing changes. The hooks include:

- **ruff check**: Lints the code for errors and style issues
- **ruff format**: Automatically formats the code
- **mypy**: Performs static type checking

These hooks run automatically when you commit changes, but you can also run them manually with `pre-commit run --all-files`.

### Continuous Integration

This project uses GitHub Actions for continuous integration:

- **Code Quality**: Runs on every push to main and pull requests
  - Linting with ruff
  - Formatting check with ruff
  - Type checking with mypy
  - Unit tests with pytest

The workflow ensures that all code merged into the main branch meets the project's quality standards.

## Troubleshooting

If you encounter issues:

1. **API Connection Problems**: Verify your Dify API key and endpoint URL are correct in the `.env` file
2. **Permission Errors**: Ensure the application has read/write access to both source and target directories
3. **Workflow Issues**: Check that the Dify workflow is properly configured and the language model is responding correctly
4. **Incorrect File Organization**: Make sure you have created appropriate subdirectories in your target path before running the application
5. **Missing Target Directories**: If the AI suggests moving files to directories that don't exist, create those directories first or use the `--dry-run` option to preview changes
6. **Logging**: Use the `--verbose` flag to enable detailed logging for troubleshooting

You can also run `python -m anime_librarian.main --help` to see all available command-line options that might help address specific issues.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

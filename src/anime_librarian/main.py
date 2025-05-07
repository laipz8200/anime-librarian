"""
Main module for the AnimeLibrarian application.

This module provides the command-line interface for the AnimeLibrarian application,
which uses AI to rename and organize video files. It uses the FileRenamer class
to handle the file renaming logic.
"""

import argparse
import sys
from pathlib import Path

from . import config
from .file_renamer import FileRenamer
from .logger import logger, set_verbose_mode


def _parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Rename and organize video files using AI suggestions."
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Source directory containing files to rename "
        f"(default: {config.DEFAULT_SOURCE_PATH})",
    )
    parser.add_argument(
        "--target",
        type=Path,
        help="Target directory containing video folders "
        f"(default: {config.DEFAULT_TARGET_PATH})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually renaming files",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Automatically answer yes to all prompts",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def main():
    """
    Execute the main program flow for renaming and organizing video files.

    This function:
    1. Parses command-line arguments
    2. Creates a FileRenamer instance
    3. Gets file name pairs from the AI service
    4. Displays the planned file moves to the user
    5. Asks for confirmation before proceeding
    6. Checks for conflicts and missing directories
    7. Performs the file moves
    """
    # Parse command-line arguments
    args = _parse_arguments()

    # Configure logging level
    if args.verbose:
        set_verbose_mode(True)

    # Get source and target paths
    source_path = args.source or config.get_source_path()
    target_path = args.target or config.get_target_path()

    logger.info(f"Source path: {source_path}")
    logger.info(f"Target path: {target_path}")

    # Create the FileRenamer instance
    renamer = FileRenamer(source_path=source_path, target_path=target_path)

    # Get file pairs
    try:
        file_pairs = renamer.get_file_pairs()
    except Exception as e:
        logger.exception("Error getting file pairs")
        print(f"Error: {e}")
        sys.exit(1)

    # List move plan for user check
    if not file_pairs:
        print("No files to rename. Exiting.")
        return

    print("\nPlanned file moves:")
    for source, target in file_pairs:
        print(f"  {source.name} -> {target.name}")

    # If dry run, exit here
    if args.dry_run:
        print("\nDry run completed. No files were renamed.")
        return

    # Before doing move, wait for user confirmation
    if not args.yes:
        response = input("\nContinue with the file moves? (y/n): ").strip().lower()
        if response != "y":
            print("Operation cancelled by user.")
            return

    # Check for conflicts
    conflicts = renamer.check_for_conflicts(file_pairs)

    # If any file will be overwritten, ask user to confirm
    if conflicts and not args.yes:
        print("\nWarning: The following files will be overwritten:")
        for conflict in conflicts:
            print(f"  {conflict}")

        response = input("\nDo you want to continue? (y/n): ").strip().lower()
        if response != "y":
            print("Operation cancelled by user.")
            return

    # Check for missing directories
    missing_dirs = renamer.find_missing_directories(file_pairs)

    # If directories need to be created, ask for confirmation
    if missing_dirs:
        print("\nThe following directories need to be created:")
        for directory in missing_dirs:
            print(f"  {directory}")

        if not args.yes:
            dir_response = input("\nCreate these directories? (y/n): ").strip().lower()
            if dir_response != "y":
                print("Operation cancelled by user.")
                return

        # Create the directories
        if not renamer.create_directories(missing_dirs):
            print("Failed to create directories. Operation cancelled.")
            return

    # Perform the file moves
    errors = renamer.rename_files(file_pairs)

    # Report results
    if errors:
        print("\nThe following errors occurred during file renaming:")
        for source, target, error in errors:
            print(f"  Error moving {source} to {target}: {error}")
        print(f"\nCompleted with {len(errors)} errors.")
    else:
        print("\nFile renaming completed successfully.")


if __name__ == "__main__":
    main()

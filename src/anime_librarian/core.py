"""Core functionality for the AnimeLibrarian application."""

from collections.abc import Callable
from pathlib import Path

from .file_renamer import FileRenamer
from .logger import logger, set_verbose_mode
from .types import ArgumentParser, ConfigProvider, HttpClient, InputReader, OutputWriter


class AnimeLibrarian:
    """Main application class for the AnimeLibrarian application."""

    def __init__(
        self,
        arg_parser: ArgumentParser,
        input_reader: InputReader,
        config_provider: ConfigProvider,
        file_renamer_factory: Callable[[Path, Path, HttpClient | None], FileRenamer],
        output_writer_factory: Callable[[bool], OutputWriter],
        set_verbose_mode_fn: Callable[[bool], None] = set_verbose_mode,
    ):
        """
        Initialize the AnimeLibrarian.

        Args:
            arg_parser: The argument parser to use
            input_reader: The input reader to use
            config_provider: The configuration provider to use
            file_renamer_factory: Factory function to create FileRenamer instances
            output_writer_factory: Factory function to create OutputWriter instances
            set_verbose_mode_fn: Function to set verbose mode
        """
        self.arg_parser = arg_parser
        self.input_reader = input_reader
        self.config_provider = config_provider
        self.file_renamer_factory = file_renamer_factory
        self.output_writer_factory = output_writer_factory
        self.set_verbose_mode_fn = set_verbose_mode_fn

    def run(self) -> int:
        """
        Run the application.

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Parse command-line arguments
        args = self.arg_parser.parse_args()

        # Configure logging level
        if args.verbose:
            self.set_verbose_mode_fn(True)

        # Create output handler
        writer = self.output_writer_factory(args.verbose)

        # Get source and target paths
        source_path = args.source or self.config_provider.get_source_path()
        target_path = args.target or self.config_provider.get_target_path()

        logger.debug(f"Source path: {source_path}")
        logger.debug(f"Target path: {target_path}")

        # Create the FileRenamer instance
        renamer = self.file_renamer_factory(source_path, target_path, None)

        # Get file pairs
        try:
            file_pairs = renamer.get_file_pairs()
        except Exception as e:
            logger.exception("Error getting file pairs")
            writer.notice(f"Error: {e}")
            return 1

        # List move plan for user check
        if not file_pairs:
            writer.message("No files to rename. Exiting.")
            return 0

        # Display planned file moves
        file_move_pairs = [(source.name, target.name) for source, target in file_pairs]
        move_descriptions = [f"{src} -> {dst}" for src, dst in file_move_pairs]
        writer.list_items(
            "\nPlanned file moves:", move_descriptions, always_show=not args.yes
        )

        # If dry run, exit here
        if args.dry_run:
            writer.message("\nDry run completed. No files were renamed.")
            return 0

        # Before doing move, wait for user confirmation
        if not args.yes:
            prompt = "\nContinue with the file moves? (y/n): "
            response = self.input_reader.read_input(prompt)
            if response != "y":
                writer.message("Operation cancelled by user.")
                return 0

        # Check for conflicts
        conflicts = renamer.check_for_conflicts(file_pairs)

        # If any file will be overwritten, ask user to confirm
        if conflicts and not args.yes:
            writer.notice("\nWarning: The following files will be overwritten:")
            for conflict in conflicts:
                writer.notice(f"  {conflict}")

            prompt = "\nDo you want to continue? (y/n): "
            response = self.input_reader.read_input(prompt)
            if response != "y":
                writer.message("Operation cancelled by user.")
                return 0

        # Check for missing directories
        missing_dirs = renamer.find_missing_directories(file_pairs)

        # If directories need to be created, ask for confirmation
        if missing_dirs:
            header = "\nThe following directories need to be created:"
            writer.list_items(header, missing_dirs, always_show=not args.yes)

            if not args.yes:
                prompt = "\nCreate these directories? (y/n): "
                dir_response = self.input_reader.read_input(prompt)
                if dir_response != "y":
                    writer.message("Operation cancelled by user.")
                    return 0

            # Create the directories
            if not renamer.create_directories(missing_dirs):
                writer.notice("Failed to create directories. Operation cancelled.")
                return 1

        # Perform the file moves
        errors = renamer.rename_files(file_pairs)

        # Report results
        if errors:
            writer.notice("\nThe following errors occurred during file renaming:")
            for source, target, error in errors:
                writer.notice(f"  Error moving {source} to {target}: {error}")
            writer.notice(f"\nCompleted with {len(errors)} errors.")
            return 1
        else:
            writer.message("\nFile renaming completed successfully.")
            return 0

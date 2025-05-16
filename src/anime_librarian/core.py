"""Core functionality for the AnimeLibrarian application."""

from collections.abc import Callable, Sequence
from pathlib import Path

from . import __version__
from .errors import FilePairsNotFoundError
from .file_renamer import FileRenamer
from .logger import logger, set_verbose_mode
from .types import (
    ArgumentParser,
    CommandLineArgs,
    ConfigProvider,
    HttpClient,
    InputReader,
    OutputWriter,
)


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

    def _initialize_application(
        self, args: CommandLineArgs
    ) -> tuple[OutputWriter, Path, Path, FileRenamer]:
        """
        Initialize the application with command line arguments.

        Args:
            args: Parsed command line arguments

        Returns:
            Tuple of (writer, source_path, target_path, renamer)
        """
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

        return writer, source_path, target_path, renamer

    def _get_file_pairs(
        self, renamer: FileRenamer, writer: OutputWriter
    ) -> tuple[Sequence[tuple[Path, Path]] | None, int | None]:
        """
        Get file pairs from the renamer.

        Args:
            renamer: The FileRenamer instance
            writer: The OutputWriter instance

        Returns:
            Tuple of (file_pairs, exit_code) where exit_code is None if successful
            or an integer if the operation should exit
        """
        try:
            file_pairs = renamer.get_file_pairs()
        except Exception as e:
            logger.exception("Error getting file pairs")
            writer.notice(f"Error: {e}")
            return None, 1

        if not file_pairs:
            writer.message("No files to rename. Exiting.")
            return None, 0

        return file_pairs, None

    def _display_move_plan(
        self,
        file_pairs: Sequence[tuple[Path, Path]],
        writer: OutputWriter,
        args: CommandLineArgs,
    ) -> int | None:
        """
        Display the planned file moves.

        Args:
            file_pairs: List of (source, target) file path pairs
            writer: The OutputWriter instance
            args: Parsed command line arguments

        Returns:
            Exit code if the operation should exit, None otherwise
        """
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

        return None

    def _confirm_operation(
        self, prompt: str, writer: OutputWriter, args: CommandLineArgs
    ) -> bool:
        """
        Ask for user confirmation if not in auto-yes mode.

        Args:
            prompt: The prompt to display to the user
            writer: The OutputWriter instance
            args: Parsed command line arguments

        Returns:
            True if confirmed, False otherwise
        """
        if args.yes:
            return True

        response = self.input_reader.read_input(prompt)
        if response != "y":
            writer.message("Operation cancelled by user.")
            return False

        return True

    def _handle_conflicts(
        self,
        renamer: FileRenamer,
        file_pairs: Sequence[tuple[Path, Path]],
        writer: OutputWriter,
        args: CommandLineArgs,
    ) -> int | None:
        """
        Handle file conflicts.

        Args:
            renamer: The FileRenamer instance
            file_pairs: List of (source, target) file path pairs
            writer: The OutputWriter instance
            args: Parsed command line arguments

        Returns:
            Exit code if the operation should exit, None otherwise
        """
        conflicts = renamer.check_for_conflicts(file_pairs)

        if conflicts and not args.yes:
            writer.notice("\nWarning: The following files will be overwritten:")
            for conflict in conflicts:
                writer.notice(f"  {conflict}")

            if not self._confirm_operation(
                "\nDo you want to continue? (y/n): ", writer, args
            ):
                return 0

        return None

    def _handle_directories(
        self,
        renamer: FileRenamer,
        file_pairs: Sequence[tuple[Path, Path]],
        writer: OutputWriter,
        args: CommandLineArgs,
    ) -> int | None:
        """
        Handle directory creation.

        Args:
            renamer: The FileRenamer instance
            file_pairs: List of (source, target) file path pairs
            writer: The OutputWriter instance
            args: Parsed command line arguments

        Returns:
            Exit code if the operation should exit, None otherwise
        """
        missing_dirs = renamer.find_missing_directories(file_pairs)

        if missing_dirs:
            header = "\nThe following directories need to be created:"
            writer.list_items(header, missing_dirs, always_show=not args.yes)

            if not args.yes and not self._confirm_operation(
                "\nCreate these directories? (y/n): ", writer, args
            ):
                return 0

            # Create the directories
            if not renamer.create_directories(missing_dirs):
                writer.notice("Failed to create directories. Operation cancelled.")
                return 1

        return None

    def _rename_files_and_report(
        self,
        renamer: FileRenamer,
        file_pairs: Sequence[tuple[Path, Path]],
        writer: OutputWriter,
    ) -> int:
        """
        Rename files and report results.

        Args:
            renamer: The FileRenamer instance
            file_pairs: List of (source, target) file path pairs
            writer: The OutputWriter instance

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        errors = renamer.rename_files(file_pairs)

        if errors:
            writer.notice("\nThe following errors occurred during file renaming:")
            for source, target, error in errors:
                writer.notice(f"  Error moving {source} to {target}: {error}")
            writer.notice(f"\nCompleted with {len(errors)} errors.")
            return 1
        else:
            writer.message("\nFile renaming completed successfully.")
            return 0

    def run(self) -> int:
        """
        Run the application.

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Parse command-line arguments
        args = self.arg_parser.parse_args()

        # Check if version flag is set
        if args.version:
            # Create output writer for version display
            writer = self.output_writer_factory(args.verbose)
            writer.notice(f"{__version__}")
            return 0

        # Initialize application components
        writer, _, _, renamer = self._initialize_application(args)

        # Get file pairs
        file_pairs_result, exit_code = self._get_file_pairs(renamer, writer)
        if exit_code is not None:
            return exit_code

        # At this point, file_pairs_result is guaranteed to be not None
        if file_pairs_result is None:
            raise FilePairsNotFoundError()
        file_pairs = file_pairs_result

        # Display move plan and handle dry run
        exit_code = self._display_move_plan(file_pairs, writer, args)
        if exit_code is not None:
            return exit_code

        # Confirm operation with user
        if not self._confirm_operation(
            "\nContinue with the file moves? (y/n): ", writer, args
        ):
            return 0

        # Handle conflicts
        exit_code = self._handle_conflicts(renamer, file_pairs, writer, args)
        if exit_code is not None:
            return exit_code

        # Handle directory creation
        exit_code = self._handle_directories(renamer, file_pairs, writer, args)
        if exit_code is not None:
            return exit_code

        # Perform file renaming and report results
        return self._rename_files_and_report(renamer, file_pairs, writer)

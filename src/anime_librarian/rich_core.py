"""Core functionality for the AnimeLibrarian application with Rich UX enhancements."""

from collections.abc import Callable, Sequence
from pathlib import Path

from . import __version__

# Removed verbose mode import
from .enums import FileOperation
from .errors import FilePairsNotFoundError
from .file_renamer import FileRenamer
from .rich_output_writer import RichInputReader, RichOutputWriter
from .types import (
    ArgumentParser,
    CommandLineArgs,
    ConfigProvider,
    Console,
    HttpClient,
)


class RichAnimeLibrarian:
    """Main application class for the AnimeLibrarian with Rich UX."""

    arg_parser: ArgumentParser
    config_provider: ConfigProvider
    file_renamer_factory: Callable[
        [Path, Path, HttpClient | None, Console | None], FileRenamer
    ]
    _args: CommandLineArgs | None
    _console: Console

    def __init__(
        self,
        arg_parser: ArgumentParser,
        config_provider: ConfigProvider,
        file_renamer_factory: Callable[
            [Path, Path, HttpClient | None, Console | None], FileRenamer
        ],
        console: Console | None = None,
    ):
        """
        Initialize the RichAnimeLibrarian.

        Args:
            arg_parser: The argument parser to use
            config_provider: The configuration provider to use
            file_renamer_factory: Factory function to create FileRenamer instances
            console: Console instance to use (defaults to global console)
        """
        self.arg_parser = arg_parser
        self.config_provider = config_provider
        self.file_renamer_factory = file_renamer_factory
        # Initialize _args to None - will be set in run()
        self._args = None
        # Use injected console or import default
        if console is None:
            from .console import console as default_console

            self._console = default_console
        else:
            self._console = console

    def _initialize_application(
        self, args: CommandLineArgs
    ) -> tuple[RichOutputWriter, RichInputReader, Path, Path, FileRenamer]:
        """
        Initialize the application with command line arguments.

        Args:
            args: Parsed command line arguments

        Returns:
            Tuple of (writer, reader, source_path, target_path, renamer)
        """
        # Create Rich output and input handlers
        writer = RichOutputWriter()
        reader = RichInputReader()

        # Get source and target paths
        source_path = args.source or self.config_provider.get_source_path()
        target_path = args.target or self.config_provider.get_target_path()

        self._console.debug("=== Configuration loaded ===")
        self._console.debug(f"  📁 Source path: {source_path}")
        self._console.debug(f"  📂 Target path: {target_path}")
        self._console.debug("--- Command Options ---")
        self._console.debug(f"  🧪 Dry run: {args.dry_run}")
        self._console.debug(
            f"  📋 Output format: {args.output_format or 'table (default)'}"
        )
        self._console.debug("  🎨 Color output: enabled")

        # Create the FileRenamer instance with console
        renamer = self.file_renamer_factory(
            source_path, target_path, None, self._console
        )

        return writer, reader, source_path, target_path, renamer

    def _get_file_pairs_with_progress(
        self, renamer: FileRenamer, writer: RichOutputWriter
    ) -> tuple[Sequence[tuple[Path, Path]] | None, int | None]:
        """
        Get file pairs from the renamer with progress indication.

        Args:
            renamer: The FileRenamer instance
            writer: The RichOutputWriter instance

        Returns:
            Tuple of (file_pairs, exit_code) where exit_code is None if successful
            or an integer if the operation should exit
        """
        self._console.debug("=== Starting file analysis ===")
        self._console.debug(f"  🔍 Scanning source: {renamer.source_path}")
        self._console.debug(f"  🎯 Scanning target: {renamer.target_path}")

        try:
            file_pairs = renamer.get_file_pairs()

            # Debug output removed (was verbose-only)
        except (OSError, ValueError, TypeError) as e:
            self._console.exception("Error getting file pairs", e)
            writer.error(f"Error: {e}")
            return None, 1

        if not file_pairs:
            # Check what might be the issue
            source_path = renamer.source_path
            target_path = renamer.target_path

            # Check for source files
            source_files = (
                list(source_path.glob("*.mp4"))
                + list(source_path.glob("*.mkv"))
                + list(source_path.glob("*.avi"))
                + list(source_path.glob("*.srt"))
            )
            target_dirs = [d for d in target_path.glob("*") if d.is_dir()]

            if self._args:
                if not source_files:
                    writer.info(f"No media files found in: {source_path}")
                elif not target_dirs:
                    writer.info(f"No target directories found in: {target_path}")
                else:
                    writer.info("No files matched for renaming")
            return None, 0

        return file_pairs, None

    def _display_move_plan(
        self,
        file_pairs: Sequence[tuple[Path, Path]],
        writer: RichOutputWriter,
        args: CommandLineArgs,
    ) -> int | None:
        """
        Display the planned file moves using Rich table.

        Args:
            file_pairs: List of (source, target) file path pairs
            writer: The RichOutputWriter instance
            args: Parsed command line arguments

        Returns:
            Exit code if the operation should exit, None otherwise
        """
        # Sort file pairs by source file name
        sorted_file_pairs = sorted(file_pairs, key=lambda pair: pair[0].name)

        # Display planned file moves in a table
        file_move_pairs = [
            (source.name, target.name) for source, target in sorted_file_pairs
        ]

        if self._args:
            writer.display_file_moves_table(
                file_move_pairs, output_format=self._args.output_format
            )

        # If dry run, exit here
        if args.dry_run:
            writer.info("Dry run completed. No files were renamed.")
            return 0

        return None

    def _handle_conflicts(
        self,
        renamer: FileRenamer,
        file_pairs: Sequence[tuple[Path, Path]],
        writer: RichOutputWriter,
        reader: RichInputReader,
    ) -> int | None:
        """
        Handle file conflicts with Rich formatting.

        Args:
            renamer: The FileRenamer instance
            file_pairs: List of (source, target) file path pairs
            writer: The RichOutputWriter instance
            reader: The RichInputReader instance

        Returns:
            Exit code if the operation should exit, None otherwise
        """
        conflicts = renamer.check_for_conflicts(file_pairs)

        if conflicts:
            writer.warning("The following files will be overwritten:")
            writer.console.show_file_list(
                "Conflicts", [str(c) for c in conflicts], style="yellow"
            )

            if not reader.confirm("Do you want to continue?", default=False):
                writer.info("Operation cancelled by user.")
                return 0

        return None

    def _handle_directories(
        self,
        renamer: FileRenamer,
        file_pairs: Sequence[tuple[Path, Path]],
        writer: RichOutputWriter,
        reader: RichInputReader,
    ) -> int | None:
        """
        Handle directory creation with Rich formatting.

        Args:
            renamer: The FileRenamer instance
            file_pairs: List of (source, target) file path pairs
            writer: The RichOutputWriter instance
            reader: The RichInputReader instance

        Returns:
            Exit code if the operation should exit, None otherwise
        """
        missing_dirs = renamer.find_missing_directories(file_pairs)

        if missing_dirs:
            if True:
                writer.info("The following directories need to be created:")
                writer.console.show_file_list(
                    "Directories", [str(d) for d in missing_dirs], style="cyan"
                )

                if not reader.confirm("Create these directories?", default=True):
                    writer.info("Operation cancelled by user.")
                    return 0

            # Create the directories with progress
            if self._args:
                self._console.debug(f"📁 Creating {len(missing_dirs)} directories...")

            for dir_path in missing_dirs:
                if self._args:
                    self._console.debug(f"  📂 Creating: {dir_path}")

                if not renamer.create_directories([dir_path]):
                    writer.error("Failed to create directories. Operation cancelled.")
                    return 1

        return None

    def _rename_files_with_progress(
        self,
        file_pairs: Sequence[tuple[Path, Path]],
        writer: RichOutputWriter,
        renamer: FileRenamer,
    ) -> int:
        """
        Rename files with progress bar and report results.

        Args:
            file_pairs: List of (source, target) file path pairs
            writer: The RichOutputWriter instance
            renamer: The FileRenamer instance to use for moving files

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        errors: list[tuple[Path, Path, str]] = []

        if self._args:
            self._console.debug("=== Starting file operations ===")
            self._console.debug(f"  📦 Total files to move: {len(file_pairs)}")

        for idx, (source_file, target_file) in enumerate(file_pairs, 1):
            filename = source_file.name

            if self._args:
                total = len(file_pairs)
                self._console.debug(f"[{idx}/{total}] Processing: {filename}")

            # Process single file pair using FileRenamer
            file_errors = renamer.rename_files([(source_file, target_file)])

            if file_errors:
                error_msg = file_errors[0][2]
                if self._args:
                    self._console.debug(f"    ❌ Failed: {error_msg}")
                errors.extend(file_errors)
            else:
                if self._args:
                    parent_name = target_file.parent.name
                    file_name = target_file.name
                    self._console.debug(f"    ✅ Moved to: {parent_name}/{file_name}")

        if errors:
            writer.error(f"Completed with {len(errors)} errors:")
            if self._args:
                for source, target, error in errors:
                    writer.console.show_operation_result(
                        FileOperation.MOVE,
                        source.name,
                        target.name,
                        success=False,
                        message=error,
                    )
            return 1
        else:
            if self._args:
                writer.success(f"Successfully moved {len(file_pairs)} file(s)")

                # Summary removed (was verbose-only)
                if False:  # verbose mode removed
                    self._console.debug("=== Operation Summary ===")
                    self._console.debug(f"  ✅ Files moved: {len(file_pairs)}")
                    self._console.debug("  ❌ Errors: 0")
                    self._console.debug(f"  📁 Source: {renamer.source_path}")
                    self._console.debug(f"  📂 Target: {renamer.target_path}")
            return 0

    def run(self) -> int:
        """
        Run the application with Rich UX enhancements.

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Parse command-line arguments
        args = self.arg_parser.parse_args()
        # Persist args for helper methods
        self._args = args

        # Check if version flag is set
        if args.version:
            writer = RichOutputWriter()
            writer.console.info(
                f"anime-librarian version {__version__}", title="Version"
            )
            return 0

        # Initialize application components
        writer, reader, _, _, renamer = self._initialize_application(args)

        # Display header
        # Suppress startup banner entirely to keep output minimal

        # Get file pairs with progress
        file_pairs_result, exit_code = self._get_file_pairs_with_progress(
            renamer, writer
        )
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
        if not reader.confirm("Continue with the file moves?", default=True):
            writer.info("Operation cancelled by user.")
            return 0

        # Handle conflicts
        exit_code = self._handle_conflicts(renamer, file_pairs, writer, reader)
        if exit_code is not None:
            return exit_code

        # Handle directory creation
        exit_code = self._handle_directories(renamer, file_pairs, writer, reader)
        if exit_code is not None:
            return exit_code

        # Perform file renaming with progress and report results
        return self._rename_files_with_progress(file_pairs, writer, renamer)

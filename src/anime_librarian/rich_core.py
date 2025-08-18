"""Core functionality for the AnimeLibrarian application with Rich UX enhancements."""

from collections.abc import Callable, Sequence
from pathlib import Path

from . import __version__
from . import console as console_module
from .console import set_verbose_mode
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

    def __init__(
        self,
        arg_parser: ArgumentParser,
        config_provider: ConfigProvider,
        file_renamer_factory: Callable[
            [Path, Path, HttpClient | None, Console | None], FileRenamer
        ],
        set_verbose_mode_fn: Callable[[bool], None] = set_verbose_mode,
    ):
        """
        Initialize the RichAnimeLibrarian.

        Args:
            arg_parser: The argument parser to use
            config_provider: The configuration provider to use
            file_renamer_factory: Factory function to create FileRenamer instances
            set_verbose_mode_fn: Function to set verbose mode
        """
        self.arg_parser = arg_parser
        self.config_provider = config_provider
        self.file_renamer_factory = file_renamer_factory
        self.set_verbose_mode_fn = set_verbose_mode_fn

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
        # Configure logging level
        if args.verbose:
            self.set_verbose_mode_fn(True)

        # Create Rich output and input handlers
        writer = RichOutputWriter(args.verbose)
        reader = RichInputReader()

        # Get source and target paths
        source_path = args.source or self.config_provider.get_source_path()
        target_path = args.target or self.config_provider.get_target_path()

        if console_module.console.verbose:
            console_module.console.debug("Configuration loaded:")
            console_module.console.debug(f"  Source path: {source_path}")
            console_module.console.debug(f"  Target path: {target_path}")
            console_module.console.debug(f"  Verbose mode: {args.verbose}")
            console_module.console.debug(f"  Dry run: {args.dry_run}")
            console_module.console.debug(f"  Auto-confirm: {args.yes}")

        # Create the FileRenamer instance with console
        renamer = self.file_renamer_factory(
            source_path, target_path, None, console_module.console
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
        if console_module.console.verbose:
            console_module.console.debug("Starting file analysis...")
            console_module.console.debug(f"Scanning source: {renamer.source_path}")
            console_module.console.debug(f"Scanning target: {renamer.target_path}")

        msg = "Analyzing files and fetching AI suggestions..."
        with console_module.console.create_progress(msg) as progress:
            task = progress.add_task("", total=None)

            try:
                file_pairs = renamer.get_file_pairs()
                progress.update(task, completed=100)

                if console_module.console.verbose and file_pairs:
                    console_module.console.debug(
                        f"Found {len(file_pairs)} file(s) to process"
                    )
                    for src, tgt in file_pairs[:3]:  # Show first 3 as examples
                        console_module.console.debug(f"  • {src.name} → {tgt.name}")
                    if len(file_pairs) > 3:
                        console_module.console.debug(
                            f"  ... and {len(file_pairs) - 3} more"
                        )
            except (OSError, ValueError, TypeError) as e:
                console_module.console.exception("Error getting file pairs", e)
                writer.error(f"Error: {e}")
                return None, 1

        if not file_pairs:
            # Display a prominent message when no files need renaming
            writer.console.print()

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

            if not source_files:
                message = (
                    f"📂 No media files found in:\n{source_path}\n\n"
                    "Supported formats:\n"
                    "• Video: .mp4, .mkv, .avi, .mov, .wmv, .flv, .webm\n"
                    "• Subtitles: .srt, .ass, .ssa, .sub, .vtt"
                )
            elif not target_dirs:
                message = (
                    f"📁 No target directories found in:\n{target_path}\n\n"
                    "Please create subdirectories for your media categories:\n"
                    "• Example: Anime/, Movies/, TV Shows/"
                )
            else:
                message = (
                    "🔍 No files matched for renaming.\n\n"
                    "Possible reasons:\n"
                    "• Files already have correct names\n"
                    "• AI couldn't match files to directories\n"
                    "• Check your Dify API configuration"
                )

            writer.display_summary_panel("No Files to Process", message)
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

        if not args.yes or args.dry_run:
            writer.display_file_moves_table(file_move_pairs)

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
        args: CommandLineArgs,
    ) -> int | None:
        """
        Handle file conflicts with Rich formatting.

        Args:
            renamer: The FileRenamer instance
            file_pairs: List of (source, target) file path pairs
            writer: The RichOutputWriter instance
            reader: The RichInputReader instance
            args: Parsed command line arguments

        Returns:
            Exit code if the operation should exit, None otherwise
        """
        conflicts = renamer.check_for_conflicts(file_pairs)

        if conflicts and not args.yes:
            writer.warning("The following files will be overwritten:")
            for conflict in conflicts:
                writer.console.print(f"  • {conflict}", style="yellow")

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
        args: CommandLineArgs,
    ) -> int | None:
        """
        Handle directory creation with Rich formatting.

        Args:
            renamer: The FileRenamer instance
            file_pairs: List of (source, target) file path pairs
            writer: The RichOutputWriter instance
            reader: The RichInputReader instance
            args: Parsed command line arguments

        Returns:
            Exit code if the operation should exit, None otherwise
        """
        missing_dirs = renamer.find_missing_directories(file_pairs)

        if missing_dirs:
            if not args.yes:
                writer.info("The following directories need to be created:")
                for dir_path in missing_dirs:
                    writer.console.print(f"  • {dir_path}", style="cyan")

                if not reader.confirm("Create these directories?", default=True):
                    writer.info("Operation cancelled by user.")
                    return 0

            # Create the directories with progress
            if console_module.console.verbose:
                console_module.console.debug(
                    f"Creating {len(missing_dirs)} directories..."
                )

            with console_module.console.create_progress(
                "Creating directories..."
            ) as progress:
                task = progress.add_task("", total=len(missing_dirs))

                for dir_path in missing_dirs:
                    progress.update(task, description=f"[cyan]{dir_path.name}[/cyan]")
                    if console_module.console.verbose:
                        console_module.console.debug(f"Creating: {dir_path}")

                    if not renamer.create_directories([dir_path]):
                        writer.error(
                            "Failed to create directories. Operation cancelled."
                        )
                        return 1
                    progress.advance(task)

        return None

    def _rename_files_with_progress(
        self,
        file_pairs: Sequence[tuple[Path, Path]],
        writer: RichOutputWriter,
    ) -> int:
        """
        Rename files with progress bar and report results.

        Args:
            file_pairs: List of (source, target) file path pairs
            writer: The RichOutputWriter instance

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        errors = []

        # Display progress header
        writer.console.print()
        writer.console.print("[bold]Moving files...[/bold]")

        if console_module.console.verbose:
            console_module.console.debug(f"Starting to move {len(file_pairs)} file(s)")

        with console_module.console.create_progress("Processing files") as progress:
            task = progress.add_task("", total=len(file_pairs))

            for idx, (source_file, target_file) in enumerate(file_pairs, 1):
                # Update progress description with current file
                filename = source_file.name
                progress.update(task, description=f"[cyan]{filename}[/cyan]")

                if console_module.console.verbose:
                    total = len(file_pairs)
                    console_module.console.debug(
                        f"Processing file {idx}/{total}: {filename}"
                    )

                try:
                    import shutil

                    shutil.move(str(source_file), str(target_file))
                    if console_module.console.verbose:
                        console_module.console.debug(
                            f"  ✅ Successfully moved to: {target_file}"
                        )
                    progress.advance(task)
                except (OSError, shutil.Error) as e:
                    error_msg = str(e)
                    if console_module.console.verbose:
                        console_module.console.debug(f"  ❌ Failed: {error_msg}")
                    errors.append((source_file, target_file, error_msg))
                    progress.advance(task)

        if errors:
            writer.error(f"Completed with {len(errors)} errors:")
            for source, target, error in errors:
                writer.console.print(
                    f"  • {source.name} → {target.name}: {error}", style="red"
                )
            return 1
        else:
            writer.success("File renaming completed successfully!")

            # Display summary
            summary = f"✅ Successfully moved {len(file_pairs)} file(s)"
            writer.display_summary_panel("Operation Complete", summary)
            return 0

    def run(self) -> int:
        """
        Run the application with Rich UX enhancements.

        Returns:
            Exit code (0 for success, non-zero for error)
        """
        # Parse command-line arguments
        args = self.arg_parser.parse_args()

        # Check if version flag is set
        if args.version:
            writer = RichOutputWriter(args.verbose)
            writer.console.print(
                f"[bold cyan]anime-librarian[/bold cyan] "
                f"version [yellow]{__version__}[/yellow]"
            )
            return 0

        # Initialize application components
        writer, reader, _, _, renamer = self._initialize_application(args)

        # Display header
        console_module.console.print_header(
            "🎬 Anime Librarian", "AI-powered video file organizer"
        )

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
        if not args.yes and not reader.confirm(
            "Continue with the file moves?", default=True
        ):
            writer.info("Operation cancelled by user.")
            return 0

        # Handle conflicts
        exit_code = self._handle_conflicts(renamer, file_pairs, writer, reader, args)
        if exit_code is not None:
            return exit_code

        # Handle directory creation
        exit_code = self._handle_directories(renamer, file_pairs, writer, reader, args)
        if exit_code is not None:
            return exit_code

        # Perform file renaming with progress and report results
        return self._rename_files_with_progress(file_pairs, writer)

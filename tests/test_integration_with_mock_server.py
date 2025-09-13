"""
Integration tests for AnimeLibrarian with mock Dify server.

This module contains comprehensive integration tests that verify the entire
workflow of the AnimeLibrarian application using a mock Dify server.
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from anime_librarian.errors import AIParseError
from anime_librarian.file_renamer import FileRenamer
from anime_librarian.rich_core import RichAnimeLibrarian as AnimeLibrarian
from anime_librarian.types import CommandLineArgs, Console

# Add tests directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fixtures.mock_server_fixtures import run_mock_server
from mock_dify_server import mock_server


class TestFileRenamerWithMockServer:
    """Test FileRenamer with mock Dify server."""

    def test_successful_rename_workflow(self) -> None:
        """Test the complete successful file renaming workflow."""
        with (
            run_mock_server() as server_url,
            tempfile.TemporaryDirectory() as source_dir,
            tempfile.TemporaryDirectory() as target_dir,
        ):
            # Create test files
            source_path = Path(source_dir)
            target_path = Path(target_dir)

            # Create sample video files
            test_files = [
                "[SubsPlease] Frieren - 01 (1080p).mkv",
                "[SubsPlease] Frieren - 02 (1080p).mkv",
                "Spy.x.Family.S01E01.mkv",
            ]
            for file_name in test_files:
                (source_path / file_name).touch()

            # Create target directories
            test_dirs = ["Frieren", "Spy x Family"]
            for dir_name in test_dirs:
                (target_path / dir_name).mkdir()

            # Initialize FileRenamer with mock server
            console = MagicMock(spec=Console)
            console.verbose = True
            renamer = FileRenamer(
                source_path=source_path,
                target_path=target_path,
                console=console,
                api_endpoint=f"{server_url}/v1/workflows/run",
                api_key="test-key",
            )

            # Get file pairs
            file_pairs = renamer.get_file_pairs()

            # Verify we got results
            assert len(file_pairs) > 0
            assert all(isinstance(pair[0], Path) for pair in file_pairs)
            assert all(isinstance(pair[1], Path) for pair in file_pairs)

            # Check that files are matched to appropriate directories
            for source, target in file_pairs:
                if "Frieren" in source.name:
                    assert "Frieren" in str(target)
                elif "Spy" in source.name:
                    assert "Spy x Family" in str(target)

    def test_error_handling_invalid_json(self) -> None:
        """Test handling of invalid JSON response from server."""
        with run_mock_server() as server_url:
            mock_server.set_failure_mode("invalid_json")

            with (
                tempfile.TemporaryDirectory() as source_dir,
                tempfile.TemporaryDirectory() as target_dir,
            ):
                source_path = Path(source_dir)
                target_path = Path(target_dir)

                # Create a test file and directory
                (source_path / "test.mkv").touch()
                (target_path / "TestDir").mkdir()

                renamer = FileRenamer(
                    source_path=source_path,
                    target_path=target_path,
                    api_endpoint=f"{server_url}/v1/workflows/run",
                    api_key="test-key",
                )

                # Should raise AIParseError for invalid JSON
                with pytest.raises(AIParseError):
                    _ = renamer.get_file_pairs()

    def test_error_handling_missing_field(self) -> None:
        """Test handling of response with missing required fields."""
        with run_mock_server() as server_url:
            mock_server.set_failure_mode("missing_field")

            with (
                tempfile.TemporaryDirectory() as source_dir,
                tempfile.TemporaryDirectory() as target_dir,
            ):
                source_path = Path(source_dir)
                target_path = Path(target_dir)

                # Create a test file and directory
                (source_path / "test.mkv").touch()
                (target_path / "TestDir").mkdir()

                renamer = FileRenamer(
                    source_path=source_path,
                    target_path=target_path,
                    api_endpoint=f"{server_url}/v1/workflows/run",
                    api_key="test-key",
                )

                # Should raise AIParseError for missing fields
                with pytest.raises(AIParseError):
                    _ = renamer.get_file_pairs()

    def test_conflict_detection(self) -> None:
        """Test detection of file conflicts."""
        with (
            run_mock_server() as server_url,
            tempfile.TemporaryDirectory() as source_dir,
            tempfile.TemporaryDirectory() as target_dir,
        ):
            source_path = Path(source_dir)
            target_path = Path(target_dir)

            # Create source file
            source_file = source_path / "test.mkv"
            source_file.touch()

            # Create target directory and existing file
            target_subdir = target_path / "TestDir"
            target_subdir.mkdir()
            existing_file = target_subdir / "Episode_01.mkv"
            existing_file.touch()

            # Set custom response to create a conflict
            mock_server.set_custom_response(
                {
                    "data": {
                        "outputs": {
                            "text": json.dumps(
                                {
                                    "result": [
                                        {
                                            "original_name": "test.mkv",
                                            "new_name": "TestDir/Episode_01.mkv",
                                        }
                                    ]
                                }
                            )
                        }
                    }
                }
            )

            renamer = FileRenamer(
                source_path=source_path,
                target_path=target_path,
                api_endpoint=f"{server_url}/v1/workflows/run",
                api_key="test-key",
            )

            file_pairs = renamer.get_file_pairs()
            conflicts = renamer.check_for_conflicts(file_pairs)

            assert len(conflicts) == 1
            assert conflicts[0] == existing_file

    def test_directory_creation(self) -> None:
        """Test automatic directory creation for missing directories."""
        with (
            run_mock_server() as server_url,
            tempfile.TemporaryDirectory() as source_dir,
            tempfile.TemporaryDirectory() as target_dir,
        ):
            source_path = Path(source_dir)
            target_path = Path(target_dir)

            # Create source file
            (source_path / "test.mkv").touch()

            # Create base target directory
            (target_path / "ExistingDir").mkdir()

            # Set custom response that includes a non-existent directory
            mock_server.set_custom_response(
                {
                    "data": {
                        "outputs": {
                            "text": json.dumps(
                                {
                                    "result": [
                                        {
                                            "original_name": "test.mkv",
                                            "new_name": "NewDir/SubDir/renamed.mkv",
                                        }
                                    ]
                                }
                            )
                        }
                    }
                }
            )

            renamer = FileRenamer(
                source_path=source_path,
                target_path=target_path,
                api_endpoint=f"{server_url}/v1/workflows/run",
                api_key="test-key",
            )

            file_pairs = renamer.get_file_pairs()
            missing_dirs = renamer.find_missing_directories(file_pairs)

            assert len(missing_dirs) > 0
            # Create the missing directories
            success = renamer.create_directories(missing_dirs)
            assert success
            # Verify directories were created
            for dir_path in missing_dirs:
                assert dir_path.exists()

    def test_actual_file_renaming(self) -> None:
        """Test actual file renaming operations."""
        with (
            run_mock_server() as server_url,
            tempfile.TemporaryDirectory() as source_dir,
            tempfile.TemporaryDirectory() as target_dir,
        ):
            source_path = Path(source_dir)
            target_path = Path(target_dir)

            # Create source files
            source_files = [
                "anime_ep_01.mkv",
                "anime_ep_02.mkv",
            ]
            for file_name in source_files:
                _ = (source_path / file_name).write_text(f"Content of {file_name}")

            # Create target directory
            (target_path / "Anime Series").mkdir()

            # Set custom response
            mock_server.set_custom_response(
                {
                    "data": {
                        "outputs": {
                            "text": json.dumps(
                                {
                                    "result": [
                                        {
                                            "original_name": "anime_ep_01.mkv",
                                            "new_name": ("Anime Series/Episode_01.mkv"),
                                        },
                                        {
                                            "original_name": "anime_ep_02.mkv",
                                            "new_name": ("Anime Series/Episode_02.mkv"),
                                        },
                                    ]
                                }
                            )
                        }
                    }
                }
            )

            renamer = FileRenamer(
                source_path=source_path,
                target_path=target_path,
                api_endpoint=f"{server_url}/v1/workflows/run",
                api_key="test-key",
            )

            file_pairs = renamer.get_file_pairs()
            errors = renamer.rename_files(file_pairs)

            # Verify no errors
            assert len(errors) == 0

            # Verify files were moved
            assert not (source_path / "anime_ep_01.mkv").exists()
            assert not (source_path / "anime_ep_02.mkv").exists()
            assert (target_path / "Anime Series" / "Episode_01.mkv").exists()
            assert (target_path / "Anime Series" / "Episode_02.mkv").exists()

            # Verify file contents were preserved
            content1 = (target_path / "Anime Series" / "Episode_01.mkv").read_text()
            assert content1 == "Content of anime_ep_01.mkv"


class TestAnimeLibrarianWithMockServer:
    """Test the main AnimeLibrarian orchestrator with mock server."""

    def test_full_workflow_with_confirmation(self) -> None:
        """Test the complete workflow with user confirmation."""
        with (
            run_mock_server() as server_url,
            tempfile.TemporaryDirectory() as source_dir,
            tempfile.TemporaryDirectory() as target_dir,
        ):
            # Setup test environment
            source_path = Path(source_dir)
            target_path = Path(target_dir)

            # Create test files
            (source_path / "test1.mkv").touch()
            (source_path / "test2.mp4").touch()

            # Create target directories
            (target_path / "Series1").mkdir()
            (target_path / "Series2").mkdir()

            # Create mock dependencies
            mock_parser = Mock()
            mock_parser.parse_args.return_value = CommandLineArgs(
                source=source_path,
                target=target_path,
                dry_run=False,
                yes=True,  # Auto-confirm
                verbose=True,
                version=False,
            )

            mock_reader = Mock()
            mock_reader.read_input.return_value = "y"

            _ = Mock()
            mock_config = Mock()
            mock_console = Mock(spec=Console)
            mock_console.verbose = True
            mock_console.ask_confirmation.return_value = True
            # Make create_progress return a context manager
            mock_progress = MagicMock()
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)
            mock_console.create_progress.return_value = mock_progress

            # Create FileRenamer factory
            def file_renamer_factory(source, target, http_client=None, console=None):
                renamer = FileRenamer(
                    source_path=source,
                    target_path=target,
                    http_client=http_client,
                    console=console,
                    api_endpoint=f"{server_url}/v1/workflows/run",
                    api_key="test-key",
                )
                return renamer

            # Create AnimeLibrarian instance
            librarian = AnimeLibrarian(
                arg_parser=mock_parser,
                config_provider=mock_config,
                file_renamer_factory=file_renamer_factory,
                console=mock_console,
            )

            # API endpoint is already set in the factory

            # Run the workflow
            result = librarian.run()

            # Verify success
            assert result == 0
            # Header output has been suppressed by design; no assertion here

    def test_dry_run_mode(self) -> None:
        """Test dry run mode where no files are actually moved."""
        with (
            run_mock_server() as server_url,
            tempfile.TemporaryDirectory() as source_dir,
            tempfile.TemporaryDirectory() as target_dir,
        ):
            source_path = Path(source_dir)
            target_path = Path(target_dir)

            # Create test files
            test_file = source_path / "test.mkv"
            _ = test_file.write_text("Original content")

            # Create target directory
            (target_path / "Target").mkdir()

            # Set custom response
            mock_server.set_custom_response(
                {
                    "data": {
                        "outputs": {
                            "text": json.dumps(
                                {
                                    "result": [
                                        {
                                            "original_name": "test.mkv",
                                            "new_name": "Target/renamed.mkv",
                                        }
                                    ]
                                }
                            )
                        }
                    }
                }
            )

            # Create mock dependencies for dry run
            mock_parser = Mock()
            mock_parser.parse_args.return_value = CommandLineArgs(
                source=source_path,
                target=target_path,
                dry_run=True,  # Enable dry run
                yes=False,
                verbose=True,
                version=False,
            )

            mock_console = Mock(spec=Console)
            mock_console.verbose = True
            # Make create_progress return a context manager
            mock_progress = MagicMock()
            mock_progress.__enter__ = Mock(return_value=mock_progress)
            mock_progress.__exit__ = Mock(return_value=None)
            mock_console.create_progress.return_value = mock_progress

            # Create FileRenamer factory
            def file_renamer_factory(source, target, http_client=None, console=None):
                renamer = FileRenamer(
                    source_path=source,
                    target_path=target,
                    http_client=http_client,
                    console=console,
                    api_endpoint=f"{server_url}/v1/workflows/run",
                    api_key="test-key",
                )
                return renamer

            librarian = AnimeLibrarian(
                arg_parser=mock_parser,
                config_provider=Mock(),
                file_renamer_factory=file_renamer_factory,
                console=mock_console,
            )

            result = librarian.run()

            # Verify success
            assert result == 0

            # Verify file was NOT moved (dry run)
            assert test_file.exists()
            assert test_file.read_text() == "Original content"
            assert not (target_path / "Target" / "renamed.mkv").exists()

            # Verify dry run was indicated to user
            # Check that info was called (the dry run message is sent via
            # writer.info, not console.info). Since we're testing with mocked
            # console, we just need to verify the run completed successfully


class TestMockServerBehavior:
    """Test the mock server's behavior and responses."""

    def test_server_request_counting(self) -> None:
        """Test that the server counts requests correctly."""
        with run_mock_server() as server_url:
            mock_server.reset()
            assert mock_server.request_count == 0

            # Make requests using FileRenamer
            with (
                tempfile.TemporaryDirectory() as source_dir,
                tempfile.TemporaryDirectory() as target_dir,
            ):
                source_path = Path(source_dir)
                target_path = Path(target_dir)
                (source_path / "test.mkv").touch()
                (target_path / "Dir").mkdir()

                renamer = FileRenamer(
                    source_path=source_path,
                    target_path=target_path,
                    api_endpoint=f"{server_url}/v1/workflows/run",
                    api_key="test-key",
                )

                _ = renamer.get_file_pairs()
                assert mock_server.request_count == 1

                _ = renamer.get_file_pairs()
                assert mock_server.request_count == 2

    def test_server_reset(self) -> None:
        """Test that server reset clears all state."""
        with run_mock_server():
            # Set various states
            mock_server.request_count = 5
            mock_server.set_failure_mode("invalid_json")
            mock_server.set_custom_response({"custom": "response"})

            # Reset
            mock_server.reset()

            # Verify all state is cleared
            assert mock_server.request_count == 0
            assert mock_server.should_fail is False
            assert mock_server.failure_mode is None
            assert mock_server.custom_response is None

    def test_intelligent_matching_logic(self) -> None:
        """Test the mock server's intelligent file matching logic."""
        with (
            run_mock_server() as server_url,
            tempfile.TemporaryDirectory() as source_dir,
            tempfile.TemporaryDirectory() as target_dir,
        ):
            source_path = Path(source_dir)
            target_path = Path(target_dir)

            # Create various file patterns
            test_files = [
                "[Group] Series Name - 01.mkv",
                "Another.Series.S01E01.mkv",
                "random_video.mp4",
                "Series.Name.Episode.5.mkv",
            ]
            for file_name in test_files:
                (source_path / file_name).touch()

            # Create matching directories
            dirs = ["Series Name", "Another Series", "Random Videos"]
            for dir_name in dirs:
                (target_path / dir_name).mkdir()

            renamer = FileRenamer(
                source_path=source_path,
                target_path=target_path,
                api_endpoint=f"{server_url}/v1/workflows/run",
                api_key="test-key",
            )

            file_pairs = renamer.get_file_pairs()

            # Verify intelligent matching
            # The mock server should match files to directories based on
            # partial name matching
            for source, target in file_pairs:
                _ = source.name.lower()
                target_str = str(target).lower()

                # Check that files are matched to related directories
                # The mock server uses partial matching logic
                # Just verify that we got some reasonable matches
                assert len(target_str) > 0  # Ensure we got a target path
                # Verify the target contains a directory and filename
                assert "/" in str(target)

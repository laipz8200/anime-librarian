"""Tests for filesystem-safe media organization."""

from collections.abc import Sequence
from pathlib import Path

import pytest

from anime_librarian.errors import ConfigurationError, InvalidMovePlanError
from anime_librarian.file_renamer import FileOrganizer
from anime_librarian.models import FileMove, NamePair


def create_symlink(
    link: Path, target: Path, *, target_is_directory: bool = False
) -> None:
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"symlinks are unavailable: {error}")


def test_plan_moves_scans_supported_files_in_sorted_order(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    extensions = (
        ".mkv",
        ".mp4",
        ".avi",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
        ".mpg",
        ".mpeg",
        ".srt",
        ".ass",
        ".ssa",
        ".sub",
        ".idx",
        ".vtt",
    )
    expected_names = sorted(
        f"episode-{index:02}{suffix}" for index, suffix in enumerate(extensions)
    )
    for name in expected_names:
        (source / name).touch()
    (source / "ignored.txt").touch()
    (source / "directory.mp4").mkdir()
    (target / "Zulu").mkdir()
    (target / "Alpha").mkdir()
    (target / "not-a-directory").touch()
    received: dict[str, list[str]] = {}

    def suggest_names(
        source_names: list[str], target_names: list[str]
    ) -> Sequence[NamePair]:
        received["source"] = source_names
        received["target"] = target_names
        return [
            NamePair(original_name=name, new_name=f"Alpha/{name}")
            for name in source_names
        ]

    moves = FileOrganizer(source, target, suggest_names).plan_moves()

    assert received == {"source": expected_names, "target": ["Alpha", "Zulu"]}
    assert [move.source.name for move in moves] == expected_names


def test_plan_moves_ignores_source_symlinks(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    payload = source / "payload.bin"
    payload.write_text("video")
    create_symlink(source / "episode.mkv", payload)
    (target / "Series").mkdir()
    organizer = FileOrganizer(
        source,
        target,
        lambda _source, _target: pytest.fail("source symlink reached Dify"),
    )

    assert organizer.plan_moves() == []
    assert payload.read_text() == "video"


def test_plan_moves_resolves_relative_targets(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    (target / "Series").mkdir()
    source_file = source / "raw.mkv"
    source_file.touch()

    organizer = FileOrganizer(
        source,
        target,
        lambda _source, _target: [
            NamePair(
                original_name="raw.mkv",
                new_name="Series/Season 01/Episode 01.mkv",
            )
        ],
    )

    assert organizer.plan_moves() == [
        FileMove(
            source=source_file,
            target=target / "Series" / "Season 01" / "Episode 01.mkv",
        )
    ]


def test_plan_moves_rejects_unknown_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    (target / "Series").mkdir()
    (source / "known.mkv").touch()
    organizer = FileOrganizer(
        source,
        target,
        lambda _source, _target: [
            NamePair(original_name="unknown.mkv", new_name="Series/episode.mkv")
        ],
    )

    with pytest.raises(InvalidMovePlanError):
        organizer.plan_moves()


@pytest.mark.parametrize(
    "new_name",
    [
        "../escape.mkv",
        "/absolute/escape.mkv",
        "Series/bad\nname.mkv",
        "Series/bad\u2028name.mkv",
        "Series/\x7fname.mkv",
        "Series/\u202ename.mkv",
        "Series/CON.mkv",
        "Series/bad?.mkv",
        "Series/cover:episode.mkv",
        "Series./episode.mkv",
    ],
    ids=[
        "parent-traversal",
        "absolute",
        "control-character",
        "line-separator",
        "delete-character",
        "format-character",
        "windows-device",
        "windows-wildcard",
        "windows-stream",
        "windows-trailing-dot",
    ],
)
def test_plan_moves_rejects_unsafe_targets(tmp_path: Path, new_name: str) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    (target / "Series").mkdir()
    (source / "episode.mkv").touch()
    organizer = FileOrganizer(
        source,
        target,
        lambda _source, _target: [
            NamePair(original_name="episode.mkv", new_name=new_name)
        ],
    )

    with pytest.raises(InvalidMovePlanError):
        organizer.plan_moves()


def test_plan_moves_rejects_control_characters_in_catalog(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    (source / "forged\nentry.mkv").touch()
    (target / "Series").mkdir()
    organizer = FileOrganizer(
        source,
        target,
        lambda _source, _target: pytest.fail("unsafe catalog reached Dify"),
    )

    with pytest.raises(ConfigurationError):
        organizer.plan_moves()


def test_plan_moves_rejects_symlink_escape(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    outside = tmp_path / "outside"
    source.mkdir()
    target.mkdir()
    outside.mkdir()
    create_symlink(target / "Linked", outside, target_is_directory=True)
    (source / "episode.mkv").touch()
    organizer = FileOrganizer(
        source,
        target,
        lambda _source, _target: [
            NamePair(
                original_name="episode.mkv",
                new_name="Linked/episode.mkv",
            )
        ],
    )

    with pytest.raises(InvalidMovePlanError):
        organizer.plan_moves()


def test_plan_moves_rejects_symlink_alias_collision(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    (source / "a.mkv").touch()
    (source / "b.mkv").touch()
    real_directory = target / "Real"
    real_directory.mkdir()
    create_symlink(target / "Alias", real_directory, target_is_directory=True)
    organizer = FileOrganizer(
        source,
        target,
        lambda _source, _target: [
            NamePair(original_name="a.mkv", new_name="Real/episode.mkv"),
            NamePair(original_name="b.mkv", new_name="Alias/episode.mkv"),
        ],
    )

    with pytest.raises(InvalidMovePlanError):
        organizer.plan_moves()


@pytest.mark.parametrize(
    "pairs",
    [
        [
            NamePair(original_name="a.mkv", new_name="Series/a.mkv"),
            NamePair(original_name="a.mkv", new_name="Series/a-copy.mkv"),
        ],
        [
            NamePair(original_name="a.mkv", new_name="Series/episode.mkv"),
            NamePair(original_name="b.mkv", new_name="Series/episode.mkv"),
        ],
        [
            NamePair(original_name="a.mkv", new_name="Series/Episode.mkv"),
            NamePair(original_name="b.mkv", new_name="series/episode.mkv"),
        ],
        [
            NamePair(original_name="a.mkv", new_name="Series/Café.mkv"),
            NamePair(original_name="b.mkv", new_name="Series/Cafe\u0301.mkv"),
        ],
    ],
    ids=[
        "duplicate-source",
        "duplicate-target",
        "case-collision",
        "unicode-collision",
    ],
)
def test_plan_moves_rejects_duplicates(
    tmp_path: Path, pairs: Sequence[NamePair]
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    (target / "Series").mkdir()
    (source / "a.mkv").touch()
    (source / "b.mkv").touch()
    organizer = FileOrganizer(source, target, lambda _source, _target: pairs)

    with pytest.raises(InvalidMovePlanError):
        organizer.plan_moves()


def test_plan_moves_rejects_another_source_as_target(tmp_path: Path) -> None:
    library = tmp_path / "library"
    library.mkdir()
    (library / "Catalog").mkdir()
    (library / "a.mkv").touch()
    (library / "b.mkv").touch()
    organizer = FileOrganizer(
        library,
        library,
        lambda _source, _target: [NamePair(original_name="a.mkv", new_name="b.mkv")],
    )

    with pytest.raises(InvalidMovePlanError):
        organizer.plan_moves()


def test_plan_moves_rejects_extension_changes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    (source / "episode.mkv").touch()
    (target / "Series").mkdir()
    organizer = FileOrganizer(
        source,
        target,
        lambda _source, _target: [
            NamePair(
                original_name="episode.mkv",
                new_name="Series/episode.mp4",
            )
        ],
    )

    with pytest.raises(InvalidMovePlanError):
        organizer.plan_moves()


def test_plan_moves_rejects_directory_destination(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    (source / "episode.mkv").touch()
    (target / "Series").mkdir()
    (target / "Series" / "episode.mkv").mkdir()
    organizer = FileOrganizer(
        source,
        target,
        lambda _source, _target: [
            NamePair(
                original_name="episode.mkv",
                new_name="Series/episode.mkv",
            )
        ],
    )

    with pytest.raises(InvalidMovePlanError):
        organizer.plan_moves()


def test_plan_moves_rejects_source_changed_during_dify(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    source_file = source / "episode.mkv"
    source_file.write_text("original")
    (target / "Series").mkdir()

    def replace_source(_source: list[str], _target: list[str]) -> Sequence[NamePair]:
        source_file.unlink()
        source_file.write_text("replacement")
        return [
            NamePair(
                original_name="episode.mkv",
                new_name="Series/Episode.mkv",
            )
        ]

    organizer = FileOrganizer(source, target, replace_source)

    with pytest.raises(InvalidMovePlanError, match="Source changed"):
        organizer.plan_moves()

    assert source_file.read_text() == "replacement"


def test_plan_moves_rejects_target_root_replaced_during_dify(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    first_target = tmp_path / "first-target"
    second_target = tmp_path / "second-target"
    target = tmp_path / "target"
    source.mkdir()
    first_target.mkdir()
    second_target.mkdir()
    (source / "episode.mkv").touch()
    (first_target / "Series").mkdir()
    create_symlink(target, first_target, target_is_directory=True)

    def replace_target(_source: list[str], _target: list[str]) -> Sequence[NamePair]:
        target.unlink()
        create_symlink(target, second_target, target_is_directory=True)
        return [
            NamePair(
                original_name="episode.mkv",
                new_name="Series/Episode.mkv",
            )
        ]

    organizer = FileOrganizer(source, target, replace_target)

    with pytest.raises(PermissionError, match="Target directory changed"):
        organizer.plan_moves()


@pytest.mark.parametrize(
    ("source_kind", "target_kind"),
    [
        ("missing", "directory"),
        ("file", "directory"),
        ("directory", "missing"),
        ("directory", "file"),
    ],
)
def test_roots_must_be_existing_directories(
    tmp_path: Path, source_kind: str, target_kind: str
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    for path, kind in ((source, source_kind), (target, target_kind)):
        if kind == "directory":
            path.mkdir()
        elif kind == "file":
            path.touch()

    with pytest.raises(ConfigurationError):
        FileOrganizer(source, target, lambda _source, _target: [])


def test_conflicts_and_missing_directories_are_sorted(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    first_conflict = target / "a-existing.mkv"
    second_conflict = target / "z-existing.mkv"
    first_conflict.touch()
    second_conflict.touch()
    moves = [
        FileMove(source=source / "1.mkv", target=target / "z-missing" / "1.mkv"),
        FileMove(source=source / "2.mkv", target=second_conflict),
        FileMove(source=source / "3.mkv", target=target / "a-missing" / "3.mkv"),
        FileMove(source=source / "4.mkv", target=first_conflict),
        FileMove(source=source / "5.mkv", target=target / "a-missing" / "5.mkv"),
    ]
    organizer = FileOrganizer(source, target, lambda _source, _target: [])

    assert organizer.conflicts(moves) == [first_conflict, second_conflict]
    assert organizer.missing_directories(moves) == [
        target / "a-missing",
        target / "z-missing",
    ]


def test_create_directories_and_move(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    source_file = source / "episode.mkv"
    source_file.write_text("video")
    target_file = target / "Series" / "episode.mkv"
    organizer = FileOrganizer(source, target, lambda _source, _target: [])

    assert organizer.create_directories([target_file.parent]) is None
    assert organizer.move(FileMove(source_file, target_file)) is None
    assert target_file.read_text() == "video"
    assert not source_file.exists()


def test_dangling_symlink_is_a_conflict(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    destination = target / "dangling.mkv"
    create_symlink(destination, target / "missing.mkv")
    move = FileMove(source / "episode.mkv", destination)
    organizer = FileOrganizer(source, target, lambda _source, _target: [])

    assert organizer.conflicts([move]) == [destination]


def test_move_refuses_destination_created_after_preflight(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    source_file = source / "episode.mkv"
    source_file.write_text("source")
    target_file = target / "episode.mkv"
    move = FileMove(source_file, target_file)
    organizer = FileOrganizer(source, target, lambda _source, _target: [])
    target_file.write_text("late arrival")

    with pytest.raises(FileExistsError):
        organizer.move(move)

    assert source_file.read_text() == "source"
    assert target_file.read_text() == "late arrival"


def test_move_allows_approved_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    source_file = source / "episode.mkv"
    source_file.write_text("source")
    target_file = target / "episode.mkv"
    target_file.write_text("old")
    move = FileMove(source_file, target_file)
    organizer = FileOrganizer(source, target, lambda _source, _target: [])
    assert organizer.conflicts([move]) == [target_file]

    organizer.move(move, overwrite=True)

    assert not source_file.exists()
    assert target_file.read_text() == "source"


def test_move_refuses_conflict_replaced_after_preflight(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    source_file = source / "episode.mkv"
    source_file.write_text("source")
    target_file = target / "episode.mkv"
    target_file.write_text("approved conflict")
    move = FileMove(source_file, target_file)
    organizer = FileOrganizer(source, target, lambda _source, _target: [])
    assert organizer.conflicts([move]) == [target_file]
    target_file.rename(target / "original-conflict.mkv")
    target_file.write_text("replacement")

    with pytest.raises(FileExistsError, match="changed after confirmation"):
        organizer.move(move, overwrite=True)

    assert source_file.read_text() == "source"
    assert target_file.read_text() == "replacement"


def test_move_rechecks_symlink_containment(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    outside = tmp_path / "outside"
    source.mkdir()
    target.mkdir()
    outside.mkdir()
    source_file = source / "episode.mkv"
    source_file.write_text("source")
    move = FileMove(source_file, target / "Late" / "episode.mkv")
    organizer = FileOrganizer(source, target, lambda _source, _target: [])
    create_symlink(target / "Late", outside, target_is_directory=True)

    with pytest.raises(PermissionError):
        organizer.move(move)

    assert source_file.exists()
    assert not (outside / "episode.mkv").exists()


def test_move_rejects_replaced_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    source_file = source / "episode.mkv"
    source_file.write_text("original")
    (target / "Series").mkdir()
    organizer = FileOrganizer(
        source,
        target,
        lambda _source, _target: [
            NamePair(
                original_name="episode.mkv",
                new_name="Series/Episode.mkv",
            )
        ],
    )
    move = organizer.plan_moves()[0]
    source_file.unlink()
    source_file.write_text("replacement")

    with pytest.raises(OSError, match="Source changed"):
        organizer.move(move)

    assert source_file.read_text() == "replacement"
    assert not move.target.exists()


def test_move_rejects_source_replaced_by_directory(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    source_file = source / "episode.mkv"
    source_file.touch()
    (target / "Series").mkdir()
    organizer = FileOrganizer(
        source,
        target,
        lambda _source, _target: [
            NamePair(
                original_name="episode.mkv",
                new_name="Series/Episode.mkv",
            )
        ],
    )
    move = organizer.plan_moves()[0]
    source_file.unlink()
    source_file.mkdir()

    with pytest.raises(IsADirectoryError):
        organizer.move(move)

    assert source_file.is_dir()
    assert not move.target.exists()


def test_directory_creation_rechecks_symlink_containment(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    outside = tmp_path / "outside"
    source.mkdir()
    target.mkdir()
    outside.mkdir()
    organizer = FileOrganizer(source, target, lambda _source, _target: [])
    create_symlink(target / "Late", outside, target_is_directory=True)

    with pytest.raises(PermissionError):
        organizer.create_directories([target / "Late" / "Season 01"])

    assert not (outside / "Season 01").exists()


def test_operations_reject_replaced_target_root(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    old_target = tmp_path / "old-target"
    source.mkdir()
    target.mkdir()
    organizer = FileOrganizer(source, target, lambda _source, _target: [])
    target.rename(old_target)
    target.mkdir()

    with pytest.raises(PermissionError, match="Target directory changed"):
        organizer.create_directories([target / "Series"])

    assert not (target / "Series").exists()


def test_move_refuses_late_directory_destination(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    source_file = source / "episode.mkv"
    source_file.touch()
    target_path = target / "episode.mkv"
    target_path.mkdir()
    organizer = FileOrganizer(source, target, lambda _source, _target: [])

    with pytest.raises(IsADirectoryError):
        organizer.move(FileMove(source_file, target_path))

    assert source_file.exists()

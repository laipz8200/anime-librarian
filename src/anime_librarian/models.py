"""Values exchanged between the Dify and filesystem boundaries."""

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel


class NamePair(BaseModel):
    """A source name and relative destination suggested by Dify."""

    original_name: str
    new_name: str


@dataclass(frozen=True, slots=True)
class FileMove:
    """A validated file move."""

    source: Path
    target: Path

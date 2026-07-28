"""Application errors presented cleanly by the CLI."""


class AnimeLibrarianError(Exception):
    """Base class for expected application failures."""


class ConfigurationError(AnimeLibrarianError, ValueError):
    """The local configuration cannot start an organization run."""


class DifyError(AnimeLibrarianError):
    """A Dify workflow request failed."""


class AIResponseError(DifyError):
    """Dify returned an unusable workflow response."""


class InvalidMovePlanError(AnimeLibrarianError, ValueError):
    """The suggested file moves are unsafe or internally inconsistent."""

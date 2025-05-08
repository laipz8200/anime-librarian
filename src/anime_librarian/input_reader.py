"""Input reader implementation for the AnimeLibrarian application."""

from .types import InputReader


class ConsoleInputReader(InputReader):
    """Default implementation of InputReader using the built-in input function."""

    def read_input(self, prompt: str) -> str:
        """
        Read user input with the given prompt.

        Args:
            prompt: The prompt to display to the user

        Returns:
            The user's input as a string
        """
        return input(prompt).strip().lower()

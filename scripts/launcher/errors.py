"""User-facing operational errors for the launcher."""


class LauncherError(RuntimeError):
    """An expected operational failure with an actionable exit code."""

    def __init__(self, message: str, fix: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.fix = fix
        self.exit_code = exit_code

"""Small, consistent console presentation helpers."""

from collections.abc import Callable

from .errors import LauncherError


class Console:
    def banner(self) -> None:
        print("=" * 60)
        print("AI Job Agent Launcher")
        print("=" * 60)

    def step(self, name: str, action: Callable[[], object]) -> object:
        print(f"{name:.<31}", end="", flush=True)
        try:
            result = action()
        except LauncherError:
            print("FAIL")
            raise
        except Exception as exc:  # Defensive boundary: never dump a trace by default.
            print("FAIL")
            raise LauncherError(str(exc), "Run again with --debug for diagnostic output.") from exc
        print("OK")
        return result

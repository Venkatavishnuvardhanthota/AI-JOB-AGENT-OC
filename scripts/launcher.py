#!/usr/bin/env python3
"""Cross-platform development environment launcher for AI Job Agent.

This module deliberately only uses the Python standard library.  The platform
wrappers are intentionally thin; all operational decisions live here.
"""

from __future__ import annotations

import argparse
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Callable, Sequence

from launcher.config import COMPOSE_FILE, DEFAULT_TIMEOUT, ENV_FILE, ENV_TEMPLATE, ROOT
from launcher.console import Console
from launcher.errors import LauncherError


class Launcher:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.timeout = args.timeout
        self.debug = args.debug
        self.console = Console()

    def print_banner(self) -> None:
        self.console.banner()

    def command(self, command: Sequence[str], *, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
        if self.debug:
            print(f"[debug] $ {' '.join(map(str, command))}")
        result = subprocess.run(
            list(map(str, command)),
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.STDOUT if capture else None,
            check=False,
        )
        if self.debug and capture and result.stdout:
            print(result.stdout.rstrip())
        if check and result.returncode:
            detail = (result.stdout or "").strip()
            raise LauncherError(
                f"Command failed: {' '.join(map(str, command))}",
                detail if self.debug and detail else "Run the command again with --debug for command output.",
            )
        return result

    def compose(self, *arguments: str, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return self.command(
            ["docker", "compose", "--project-directory", str(ROOT), "-f", str(COMPOSE_FILE), *arguments],
            **kwargs,
        )

    def step(self, name: str, action: Callable[[], object]) -> object:
        return self.console.step(name, action)

    def ensure_docker_cli(self) -> None:
        if not shutil.which("docker"):
            raise LauncherError(
                "Docker Desktop / Docker CLI was not found.",
                "Install Docker Desktop from https://www.docker.com/products/docker-desktop/ and restart this command.",
                2,
            )
        result = self.command(["docker", "compose", "version"], check=False)
        if result.returncode:
            raise LauncherError(
                "Docker Compose v2 is not available.",
                "Update Docker Desktop so that `docker compose version` succeeds.",
                2,
            )

    def docker_ready(self) -> bool:
        return self.command(["docker", "info"], check=False).returncode == 0

    def start_docker_desktop(self) -> bool:
        """Best-effort engine start. It never elevates privileges or prompts for sudo."""
        try:
            if sys.platform.startswith("win"):
                candidates = [
                    Path(os.environ.get("ProgramFiles", "")) / "Docker" / "Docker" / "Docker Desktop.exe",
                    Path(os.environ.get("LOCALAPPDATA", "")) / "Docker" / "Docker Desktop.exe",
                ]
                desktop = next((path for path in candidates if path.is_file()), None)
                if desktop:
                    subprocess.Popen([str(desktop)], cwd=ROOT)  # noqa: S603
                    return True
            elif sys.platform == "darwin":
                if shutil.which("open"):
                    subprocess.Popen(["open", "-a", "Docker"], cwd=ROOT)  # noqa: S603
                    return True
            else:
                for command in (("systemctl", "--user", "start", "docker-desktop"), ("systemctl", "start", "docker")):
                    result = self.command(command, check=False)
                    if result.returncode == 0:
                        return True
        except OSError:
            return False
        return False

    def ensure_docker_engine(self) -> None:
        if self.docker_ready():
            return
        print("\n  Docker Engine is unavailable; attempting to start it...", flush=True)
        started = self.start_docker_desktop()
        if not started:
            raise LauncherError(
                "Docker is installed but its engine is not running.",
                "Start Docker Desktop manually, wait until it reports 'Engine running', then run this command again.",
                3,
            )
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            if self.docker_ready():
                return
            print(".", end="", flush=True)
            time.sleep(2)
        raise LauncherError(
            f"Docker Engine did not become ready within {self.timeout} seconds.",
            "Open Docker Desktop, resolve its startup error, then run this command again."
            " Use --timeout to allow a longer startup window.",
            3,
        )

    def ensure_project_env(self) -> None:
        if not ENV_FILE.exists():
            if not ENV_TEMPLATE.exists():
                raise LauncherError("Project .env is missing and no template is available.", "Restore backend/.env.example, then retry.")
            ENV_FILE.write_text(ENV_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
            print("\n  Created .env from backend/.env.example.")

        content = ENV_FILE.read_text(encoding="utf-8")
        match = re.search(r"(?m)^APP_SECRET_KEY\s*=\s*(.*)$", content)
        needs_secret = not match or not match.group(1).strip() or match.group(1).strip() == "change-me-to-a-secure-random-key"
        if needs_secret:
            value = secrets.token_urlsafe(48)
            if match:
                content = content[: match.start(1)] + value + content[match.end(1) :]
            else:
                content += f"\nAPP_SECRET_KEY={value}\n"
            ENV_FILE.write_text(content, encoding="utf-8")
            print("\n  Generated APP_SECRET_KEY in .env.")

    def container_exists(self, name: str) -> bool:
        return self.command(["docker", "inspect", name], check=False).returncode == 0

    def container_state(self, name: str) -> str:
        result = self.command(["docker", "inspect", "--format", "{{.State.Status}}/{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}", name], check=False)
        return result.stdout.strip() if result.returncode == 0 else "missing"

    def http_ready(self, url: str) -> bool:
        try:
            with urllib.request.urlopen(url, timeout=3) as response:  # noqa: S310 - only launcher localhost URLs
                return 200 <= response.status < 400
        except (urllib.error.URLError, TimeoutError, ValueError):
            return False

    def service_url(self, service: str, container_port: int, fallback: str) -> str:
        result = self.compose("port", service, str(container_port), check=False)
        if result.returncode != 0 or not result.stdout.strip():
            return fallback
        binding = result.stdout.strip().splitlines()[0]
        port_match = re.search(r":(\d+)$", binding)
        if not port_match:
            return fallback
        return f"http://localhost:{port_match.group(1)}" if port_match.group(1) != "80" else "http://localhost"

    @staticmethod
    def port_open(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            return sock.connect_ex(("127.0.0.1", port)) == 0

    def assert_port_ownership(self) -> None:
        # The named containers are the only processes this launcher is allowed to manage.
        expected = {80: "aja-frontend", 8000: "aja-backend", 5432: "aja-db"}
        conflicts = [
            str(port)
            for port, container in expected.items()
            if self.port_open(port) and not self.container_state(container).startswith("running")
        ]
        if conflicts:
            ports = ", ".join(conflicts)
            raise LauncherError(
                f"Required port(s) already have a non-AI-Job-Agent listener: {ports}.",
                "Stop the process using the port(s), or change the host port mappings in docker-compose.yml. "
                "The launcher will not terminate processes it does not own.",
                4,
            )

    def wait_for_database(self) -> None:
        deadline = time.monotonic() + self.timeout
        recovered = False
        while time.monotonic() < deadline:
            state = self.container_state("aja-db")
            check = self.command(["docker", "exec", "aja-db", "pg_isready", "-U", "postgres", "-d", "ai_job_agent"], check=False)
            if check.returncode == 0:
                return
            if state.startswith("exited"):
                self.show_logs("db")
                raise LauncherError("PostgreSQL container exited during startup.", "Review the database logs above and fix its configuration or data volume.")
            if state.endswith("/unhealthy") and not recovered:
                self.compose("restart", "db")
                recovered = True
            time.sleep(1)
        self.show_logs("db")
        raise LauncherError(
            f"PostgreSQL did not become ready within {self.timeout} seconds.",
            "Review the database logs above. If this is a local-data issue, stop the stack and inspect the aja-postgres-data volume.",
        )

    def wait_for_http_service(self, service: str, url: str) -> None:
        container = f"aja-{service}"
        deadline = time.monotonic() + self.timeout
        recovered = False
        while time.monotonic() < deadline:
            if self.http_ready(url):
                return
            state = self.container_state(container)
            if state.startswith("exited"):
                self.show_logs(service)
                raise LauncherError(f"{service.capitalize()} container exited during startup.", "Review the logs above and retry with --debug if needed.")
            if state.endswith("/unhealthy") and not recovered:
                self.compose("restart", service)
                recovered = True
            time.sleep(1)
        self.show_logs(service)
        raise LauncherError(
            f"{service.capitalize()} did not become ready at {url} within {self.timeout} seconds.",
            "Review the logs above, then retry with --debug for Docker command output.",
        )

    def show_logs(self, service: str) -> None:
        result = self.compose("logs", "--tail", "40", service, check=False)
        if result.stdout.strip():
            print(f"\n--- {service} logs (last 40 lines) ---\n{result.stdout.rstrip()}\n--- end logs ---")

    def start(self) -> None:
        self.print_banner()
        self.step("Checking Docker", self.ensure_docker_cli)
        self.step("Docker Engine", self.ensure_docker_engine)
        self.step("Project configuration", self.ensure_project_env)
        self.step("Checking ports", self.assert_port_ownership)

        frontend_was_ready = self.http_ready("http://localhost")
        self.step("Starting PostgreSQL", lambda: self.compose("up", "-d", "db"))
        self.step("Database readiness", self.wait_for_database)
        self.step("Preparing service images", lambda: self.compose("build", "backend", "frontend"))
        self.step("Database migrations", lambda: self.compose("run", "--rm", "--no-deps", "backend", "alembic", "upgrade", "head"))
        self.step("Starting backend and frontend", lambda: self.compose("up", "-d", "--no-build", "backend", "frontend"))

        backend_url = self.service_url("backend", 8000, "http://localhost:8000")
        frontend_url = self.service_url("frontend", 80, "http://localhost")
        self.step("Backend health", lambda: self.wait_for_http_service("backend", f"{backend_url}/health"))
        self.step("Frontend health", lambda: self.wait_for_http_service("frontend", f"{frontend_url}/health"))
        if not self.args.no_open and not frontend_was_ready:
            self.step("Opening browser", lambda: webbrowser.open(frontend_url, new=2))

        print("\nApplication Ready")
        print(f"Frontend: {frontend_url}")
        print(f"Backend:  {backend_url}")
        print("=" * 60)

    def stop(self) -> None:
        self.print_banner()
        self.step("Checking Docker", self.ensure_docker_cli)
        if not self.docker_ready():
            raise LauncherError("Docker Engine is not running, so containers cannot be stopped.", "Start Docker Desktop and run stop again.", 3)
        services = ["backend", "frontend"] if self.args.keep_database else ["backend", "frontend", "db"]
        self.step("Stopping services", lambda: self.compose("stop", *services))
        print("\nServices stopped. Containers and database data were preserved.")
        if self.args.keep_database:
            print("PostgreSQL was kept running (--keep-database).")

    def status(self) -> None:
        self.print_banner()
        if not shutil.which("docker"):
            raise LauncherError("Docker CLI was not found.", "Install Docker Desktop, then retry.", 2)
        print(f"Docker Engine................ {'OK' if self.docker_ready() else 'NOT RUNNING'}")
        if not self.docker_ready():
            print("Overall project status....... STOPPED")
            return
        for label, container in (("PostgreSQL container", "aja-db"), ("Backend container", "aja-backend"), ("Frontend container", "aja-frontend")):
            print(f"{label:.<29} {self.container_state(container)}")
        backend_url = self.service_url("backend", 8000, "http://localhost:8000")
        frontend_url = self.service_url("frontend", 80, "http://localhost")
        db_ready = self.command(["docker", "exec", "aja-db", "pg_isready", "-U", "postgres", "-d", "ai_job_agent"], check=False).returncode == 0
        print(f"Database readiness........... {'OK' if db_ready else 'UNAVAILABLE'}")
        backend_ready = self.http_ready(backend_url + "/health")
        frontend_ready = self.http_ready(frontend_url + "/health")
        print(f"Backend health............... {'OK' if backend_ready else 'UNAVAILABLE'} ({backend_url})")
        print(f"Frontend health.............. {'OK' if frontend_ready else 'UNAVAILABLE'} ({frontend_url})")
        print(f"Ports........................ 80={'OPEN' if self.port_open(80) else 'closed'}, 8000={'OPEN' if self.port_open(8000) else 'closed'}, 5432={'OPEN' if self.port_open(5432) else 'closed'}")
        print(f"Overall project status....... {'RUNNING' if db_ready and backend_ready and frontend_ready else 'DEGRADED'}")

    def restart(self) -> None:
        self.stop()
        self.start()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Job Agent development environment launcher")
    parser.add_argument("command", nargs="?", choices=("start", "stop", "restart", "status"), default="start")
    parser.add_argument("--debug", "--verbose", action="store_true", help="show Docker command output")
    parser.add_argument("--no-open", action="store_true", help="do not open a browser after startup")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"readiness timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--keep-database", action="store_true", help="with stop/restart, leave PostgreSQL running")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    return args


def main() -> int:
    args = parse_args()
    launcher = Launcher(args)
    try:
        getattr(launcher, args.command)()
        return 0
    except LauncherError as error:
        print(f"\nStartup failed: {error}")
        print(f"Suggested fix: {error.fix}")
        return error.exit_code
    except KeyboardInterrupt:
        print("\nCancelled. Existing containers were left unchanged.")
        return 130


if __name__ == "__main__":
    sys.exit(main())

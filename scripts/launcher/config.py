"""Central launcher configuration and repository paths."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = ROOT / "docker-compose.yml"
ENV_FILE = ROOT / ".env"
ENV_TEMPLATE = ROOT / "backend" / ".env.example"
DEFAULT_TIMEOUT = 180

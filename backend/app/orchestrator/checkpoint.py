from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from threading import Lock
from typing import Any

from app.orchestrator.exceptions import CheckpointError
from app.orchestrator.schemas import CheckpointData, OrchestrationContext, PipelineStage


class CheckpointManager:
    def __init__(self, checkpoint_dir: str = ".orchestrator_checkpoints") -> None:
        self._checkpoint_dir = checkpoint_dir
        self._lock = Lock()
        os.makedirs(self._checkpoint_dir, exist_ok=True)

    def create_checkpoint(self, context: OrchestrationContext, stage: PipelineStage) -> CheckpointData:
        snapshot = context.model_dump()
        snapshot.pop("checkpoint", None)
        checkpoint = CheckpointData(
            orchestration_id=context.orchestration_id,
            stage=stage,
            context_snapshot=snapshot,
        )
        try:
            path = self._path(checkpoint.orchestration_id, checkpoint.checkpoint_id)
            with self._lock, open(path, "w") as f:
                json.dump(checkpoint.model_dump(), f, default=str)
        except OSError as e:
            raise CheckpointError(f"Failed to save checkpoint: {e}") from e
        context.checkpoint = checkpoint
        return checkpoint

    def load_checkpoint(self, checkpoint_id: str) -> CheckpointData | None:
        path = self._find_path(checkpoint_id)
        if path is None:
            return None
        try:
            with self._lock, open(path) as f:
                data = json.load(f)
            return CheckpointData(**data)
        except (OSError, json.JSONDecodeError) as e:
            raise CheckpointError(f"Failed to load checkpoint: {e}") from e

    def restore_context(self, checkpoint: CheckpointData) -> OrchestrationContext:
        snapshot = checkpoint.context_snapshot.copy()
        snapshot["state"] = "idle"
        snapshot["checkpoint"] = checkpoint
        return OrchestrationContext(**snapshot)

    def list_checkpoints(self, orchestration_id: str) -> list[CheckpointData]:
        results: list[CheckpointData] = []
        prefix = f"{orchestration_id}__"
        try:
            for name in os.listdir(self._checkpoint_dir):
                if name.startswith(prefix) and name.endswith(".json"):
                    ck_id = name[len(prefix):-5]
                    data = self.load_checkpoint(ck_id)
                    if data is not None:
                        results.append(data)
        except OSError:
            pass
        return sorted(results, key=lambda c: c.timestamp)

    def delete_checkpoint(self, checkpoint_id: str) -> None:
        path = self._find_path(checkpoint_id)
        if path is None:
            return
        try:
            with self._lock:
                if os.path.isfile(path):
                    os.remove(path)
        except OSError:
            pass

    def clear_all(self, orchestration_id: str) -> None:
        for ck in self.list_checkpoints(orchestration_id):
            self.delete_checkpoint(ck.checkpoint_id)

    def _path(self, orchestration_id: str, checkpoint_id: str) -> str:
        return os.path.join(self._checkpoint_dir, f"{orchestration_id}__{checkpoint_id}.json")

    def _find_path(self, checkpoint_id: str) -> str | None:
        try:
            for name in os.listdir(self._checkpoint_dir):
                if name.endswith(f"__{checkpoint_id}.json") or name == f"{checkpoint_id}.json":
                    return os.path.join(self._checkpoint_dir, name)
        except OSError:
            pass
        return None

from __future__ import annotations


class OrchestratorError(Exception):
    pass


class RecoverableError(OrchestratorError):
    pass


class NonRecoverableError(OrchestratorError):
    pass


class ManualInterventionError(OrchestratorError):
    pass


class StageExecutionError(OrchestratorError):
    def __init__(self, stage: str, message: str, recoverable: bool = True) -> None:
        self.stage = stage
        self.recoverable = recoverable
        super().__init__(f"[{stage}] {message}")


class PipelineExecutionError(OrchestratorError):
    pass


class CheckpointError(OrchestratorError):
    pass


class RecoveryFailedError(OrchestratorError):
    pass


class ValidationError(OrchestratorError):
    pass


class DispatchError(OrchestratorError):
    pass

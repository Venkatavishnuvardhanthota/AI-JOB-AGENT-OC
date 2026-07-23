from __future__ import annotations

from app.automation.schemas import AutomationJob, JobPriority, JobState


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, AutomationJob] = {}

    def add(self, job: AutomationJob) -> None:
        self._jobs[job.id] = job

    def get(self, job_id: str) -> AutomationJob | None:
        return self._jobs.get(job_id)

    def update(self, job: AutomationJob) -> None:
        self._jobs[job.id] = job

    def remove(self, job_id: str) -> bool:
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False

    def list_jobs(
        self,
        state: JobState | None = None,
        priority: JobPriority | None = None,
    ) -> list[AutomationJob]:
        jobs = list(self._jobs.values())
        if state is not None:
            jobs = [j for j in jobs if j.state == state]
        if priority is not None:
            jobs = [j for j in jobs if j.priority == priority]
        return sorted(jobs, key=lambda j: (-j.priority.value, j.created_at))

    def get_enabled_jobs(self) -> list[AutomationJob]:
        return [j for j in self._jobs.values() if j.enabled and j.state == JobState.ACTIVE]

    def count(self) -> int:
        return len(self._jobs)

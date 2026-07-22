from __future__ import annotations

import re


class CultureAnalyzer:
    def analyze(self, job) -> dict:
        description = (getattr(job, "description", None) or "").lower()
        result: dict = {
            "work_environment": self._infer_work_environment(description),
            "team_culture": self._infer_team_culture(description),
            "growth_indicators": self._infer_growth_indicators(description),
        }
        return result

    def _infer_work_environment(self, description: str) -> list[str]:
        signals: list[str] = []
        fast_paced = re.search(r"(?:fast.paced|fastpaced|rapid|agile|startup environment)", description)
        if fast_paced:
            signals.append("fast_paced")

        collaborative = re.search(r"(?:collaborative|team.player|teamwork|pair programming)", description)
        if collaborative:
            signals.append("collaborative")

        autonomous = re.search(r"(?:autonomous|self.starter|independent|ownership|take ownership)", description)
        if autonomous:
            signals.append("autonomous")

        structured = re.search(r"(?:structured|process.driven|formal|regulated|compliant)", description)
        if structured:
            signals.append("structured")

        return signals if signals else ["unknown"]

    def _infer_team_culture(self, description: str) -> list[str]:
        signals: list[str] = []

        innovative = re.search(r"(?:innovative|innovation|cutting.edge|modern|forward.thinking)", description)
        if innovative:
            signals.append("innovative")

        inclusive = re.search(r"(?:diverse|inclusive|diversity|inclusion|belonging|equal opportunity)", description)
        if inclusive:
            signals.append("inclusive")

        learning = re.search(r"(?:learning|growth|development|mentorship|training|upskill)", description)
        if learning:
            signals.append("learning_oriented")

        result_driven = re.search(r"(?:result.driven|impact|data.driven|metrics|outcome)", description)
        if result_driven:
            signals.append("result_driven")

        return signals if signals else ["unknown"]

    def _infer_growth_indicators(self, description: str) -> dict:
        learning_budget = bool(
            re.search(
                r"(?:learning budget|training budget|conference budget|education stipend)",
                description,
            )
        )
        mentorship = bool(
            re.search(
                r"(?:mentorship|mentor program|buddy system|onboarding program)",
                description,
            )
        )
        career_progression = bool(
            re.search(
                r"(?:career progression|growth path|promotion|advancement)",
                description,
            )
        )
        return {
            "has_learning_budget": learning_budget,
            "has_mentorship": mentorship,
            "has_career_progression": career_progression,
        }

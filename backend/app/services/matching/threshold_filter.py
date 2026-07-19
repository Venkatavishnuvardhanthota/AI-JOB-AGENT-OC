import logging

from app.schemas.matching import MatchScore, ScoringConfig

logger = logging.getLogger(__name__)


class ThresholdFilter:
    def is_above_threshold(
        self,
        score: MatchScore,
        config: ScoringConfig,
    ) -> bool:
        if score.overall < config.overall_threshold:
            return False
        if score.skill.score < config.skill_threshold:
            return False
        if score.keyword.score < config.keyword_threshold:
            return False
        if score.experience.score < config.experience_threshold:
            return False
        return score.education.score >= config.education_threshold

    def filter_scores(
        self,
        scores: list[MatchScore],
        config: ScoringConfig,
    ) -> list[MatchScore]:
        return [s for s in scores if self.is_above_threshold(s, config)]

from app.core.exceptions import AppError


class IntelligenceError(AppError):
    status_code = 500
    code = "INTELLIGENCE_ERROR"
    message = "An intelligence operation failed."


class AnalyticsError(IntelligenceError):
    code = "ANALYTICS_ERROR"
    message = "Analytics computation failed."


class AnalyticsDataError(AnalyticsError):
    status_code = 400
    code = "ANALYTICS_DATA_ERROR"
    message = "Insufficient or invalid data for analytics."


class RecommendationError(IntelligenceError):
    code = "RECOMMENDATION_ERROR"
    message = "Recommendation generation failed."


class RecommendationDataError(RecommendationError):
    status_code = 400
    code = "RECOMMENDATION_DATA_ERROR"
    message = "Insufficient data to generate recommendations."


class LearningError(IntelligenceError):
    code = "LEARNING_ERROR"
    message = "Learning operation failed."


class OptimizationError(IntelligenceError):
    code = "OPTIMIZATION_ERROR"
    message = "Optimization operation failed."


class OptimizationDataError(OptimizationError):
    status_code = 400
    code = "OPTIMIZATION_DATA_ERROR"
    message = "Insufficient data for optimization."


class ScoringError(IntelligenceError):
    code = "SCORING_ERROR"
    message = "Scoring operation failed."


class FeedbackError(IntelligenceError):
    code = "FEEDBACK_ERROR"
    message = "Feedback processing failed."


class HistoryError(IntelligenceError):
    code = "HISTORY_ERROR"
    message = "History tracking failed."


class ExperimentError(IntelligenceError):
    code = "EXPERIMENT_ERROR"
    message = "Experiment operation failed."


class ExperimentDataError(ExperimentError):
    status_code = 400
    code = "EXPERIMENT_DATA_ERROR"
    message = "Insufficient data for experiment."

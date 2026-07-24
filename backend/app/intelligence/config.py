from pydantic import BaseModel, Field


class IntelligenceConfig(BaseModel):
    enabled: bool = Field(default=True, description="Enable intelligence engine")
    analytics_enabled: bool = Field(default=True, description="Enable analytics")
    learning_enabled: bool = Field(default=True, description="Enable learning")
    recommendations_enabled: bool = Field(default=True, description="Enable recommendations")
    optimization_enabled: bool = Field(default=True, description="Enable optimization")
    experimentation_enabled: bool = Field(default=True, description="Enable experimentation")
    feedback_enabled: bool = Field(default=True, description="Enable feedback processing")
    history_enabled: bool = Field(default=True, description="Enable history tracking")

    scoring_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "resume_quality": 1.0,
            "application_quality": 1.0,
            "provider_quality": 1.0,
            "job_quality": 1.0,
            "workflow_quality": 1.0,
        },
        description="Default scoring weights",
    )

    min_data_points_for_analytics: int = Field(
        default=5, ge=1, description="Minimum data points required for analytics"
    )
    min_data_points_for_recommendations: int = Field(
        default=3, ge=1, description="Minimum data points for recommendations"
    )
    min_data_points_for_learning: int = Field(default=5, ge=1, description="Minimum data points for learning")
    min_data_points_for_optimization: int = Field(default=3, ge=1, description="Minimum data points for optimization")

    recommendation_confidence_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum confidence for auto-recommendations"
    )
    experiment_sample_size_target: int = Field(default=20, ge=1, description="Target sample size for experiments")

    history_max_entries: int = Field(default=10000, ge=100, description="Maximum history entries to retain")
    history_retention_days: int = Field(default=365, ge=30, description="History retention period in days")

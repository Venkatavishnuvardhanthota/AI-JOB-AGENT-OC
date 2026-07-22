from __future__ import annotations

from app.profile_intelligence.schemas import CareerLevel, UserIntelligenceProfile


class ProfileSummarizer:
    def generate_personal_summary(self, profile: UserIntelligenceProfile) -> str | None:
        parts: list[str] = []
        role = profile.current_role
        years = profile.years_of_experience
        level = profile.career_level

        if role and years is not None:
            level_str = self._level_display(level)
            parts.append(f"{level_str} {role} with {years:.0f} year{'s' if years >= 2 else ''} of experience")
        elif role:
            level_str = self._level_display(level)
            parts.append(f"{level_str} {role}")
        elif years is not None:
            parts.append(f"Professional with {years:.0f} year{'s' if years >= 2 else ''} of experience")

        if profile.primary_skills:
            skills_str = ", ".join(profile.primary_skills[:3])
            if len(profile.primary_skills) > 3:
                skills_str += f" and {len(profile.primary_skills) - 3} more"
            parts.append(f"Skilled in {skills_str}")

        if profile.industries:
            ind_str = ", ".join(profile.industries[:2])
            if len(profile.industries) > 2:
                ind_str += f" and {len(profile.industries) - 2} more"
            parts.append(f"Industry experience in {ind_str}")

        if profile.preferred_locations:
            loc_str = ", ".join(profile.preferred_locations)
            parts.append(f"Open to opportunities in {loc_str}")

        if not parts:
            return None

        return ". ".join(parts) + "."

    def _level_display(self, level: CareerLevel) -> str:
        mapping = {
            CareerLevel.ENTRY: "Entry-level",
            CareerLevel.JUNIOR: "Junior",
            CareerLevel.MID: "Mid-level",
            CareerLevel.SENIOR: "Senior",
            CareerLevel.LEAD: "Lead",
            CareerLevel.EXECUTIVE: "Executive",
            CareerLevel.UNKNOWN: "Professional",
        }
        return mapping.get(level, "Professional")

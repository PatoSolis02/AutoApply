from __future__ import annotations

from autoapply.contracts import ClaimMapEntry, ComplianceResult, UserProfile


class ComplianceGate:
    def validate(
        self,
        profile: UserProfile,
        claims_map: list[ClaimMapEntry],
    ) -> ComplianceResult:
        blocked: list[str] = []

        if not profile.full_name.strip():
            blocked.append("user profile full_name is required")

        if (
            len(profile.experiences) == 0
            and len(profile.projects) == 0
            and len(profile.skills) == 0
            and len(profile.education) == 0
        ):
            blocked.append("user profile content is empty")

        if any(item.verification_status == "rejected" for item in claims_map):
            blocked.append("unsupported claims detected")

        bullet_ids = [item.bullet_id for item in claims_map]
        if len(set(bullet_ids)) != len(bullet_ids):
            blocked.append("duplicate bullet mappings detected")

        if any(not item.source_id for item in claims_map):
            blocked.append("claim missing source mapping")

        return ComplianceResult(ok=(len(blocked) == 0), blocked_reasons=blocked)

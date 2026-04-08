from app.constants import MAX_SCORE_PER_CHECK
from app.models.schemas import CheckResult, HtagDetails
from app.services.aeo_checks.base import BaseCheck
from app.services.content_parser import ParsedContent


class HtagHierarchyCheck(BaseCheck):
    check_id = "htag_hierarchy"
    name = "H-tag Hierarchy"

    def run(self, content: ParsedContent) -> CheckResult:
        headings = content.headings
        h_tags_found = [tag for tag, _ in headings]
        violations = self._find_violations(headings=headings)
        no_h1 = not any(tag == "h1" for tag, _ in headings)
        score = self._compute_score(violations=violations, no_h1=no_h1)

        return CheckResult(
            check_id=self.check_id,
            name=self.name,
            passed=score == MAX_SCORE_PER_CHECK,
            score=score,
            max_score=MAX_SCORE_PER_CHECK,
            details=HtagDetails(
                violations=violations,
                h_tags_found=h_tags_found,
            ),
            recommendation=self._recommendation(violations=violations, no_h1=no_h1),
        )

    def _find_violations(self, headings: list[tuple[str, str]]) -> list[str]:
        violations = []

        h1_count = sum(1 for tag, _ in headings if tag == "h1")
        if h1_count == 0:
            violations.append("Missing H1 tag")
        elif h1_count > 1:
            violations.append(f"Multiple H1 tags found ({h1_count})")

        for tag, text in headings:
            if tag == "h1":
                break
            violations.append(f"{tag.upper()} '{text}' appears before the first H1")

        levels = [int(tag[1]) for tag, _ in headings]
        for i in range(1, len(levels)):
            if levels[i] > levels[i - 1] + 1:
                prev_tag = f"H{levels[i - 1]}"
                curr_tag = f"H{levels[i]}"
                skipped = f"H{levels[i - 1] + 1}"
                violations.append(f"{curr_tag} found after {prev_tag} — skipped {skipped}")

        return violations

    def _compute_score(self, violations: list[str], no_h1: bool) -> int:
        if no_h1:
            return 0
        count = len(violations)
        if count == 0:
            return 20
        if count <= 2:
            return 12
        return 0

    def _recommendation(self, violations: list[str], no_h1: bool) -> str | None:
        if not violations:
            return None
        if no_h1:
            return "Add a single H1 tag as the main page title before any other headings."
        if any("skipped" in v for v in violations):
            return "Fix heading hierarchy: ensure no levels are skipped (H2 should follow H1, not H3)."
        if any("before the first H1" in v for v in violations):
            return "Move the H1 tag to appear before all other headings."
        return "Fix heading structure: ensure a single H1 comes first with no skipped levels."

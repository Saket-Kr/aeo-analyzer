import textstat

from app.constants import (
    COMPLEX_SENTENCE_COUNT,
    FK_GRADE_DEFAULT_SCORE,
    FK_GRADE_SCORES,
    FK_GRADE_TARGET_MAX,
    FK_GRADE_TARGET_MIN,
    MAX_SCORE_PER_CHECK,
)
from app.models.schemas import CheckResult, ReadabilityDetails
from app.services.aeo_checks.base import BaseCheck
from app.services.content_parser import ParsedContent


class ReadabilityCheck(BaseCheck):
    check_id = "readability"
    name = "Snippet Readability"

    def run(self, content: ParsedContent) -> CheckResult:
        text = content.clean_text
        grade = round(textstat.flesch_kincaid_grade(text), 1) if text else 0.0
        score = self._compute_score(grade=grade)
        complex_sents = self._find_complex_sentences(sentences=content.sentences)

        return CheckResult(
            check_id=self.check_id,
            name=self.name,
            passed=score == MAX_SCORE_PER_CHECK,
            score=score,
            max_score=MAX_SCORE_PER_CHECK,
            details=ReadabilityDetails(
                fk_grade_level=grade,
                target_range=f"{FK_GRADE_TARGET_MIN:.0f}-{FK_GRADE_TARGET_MAX:.0f}",
                complex_sentences=complex_sents,
            ),
            recommendation=self._recommendation(grade=grade, score=score),
        )

    def _compute_score(self, grade: float) -> int:
        for low, high, points in FK_GRADE_SCORES:
            if low <= grade <= high:
                return points
        return FK_GRADE_DEFAULT_SCORE

    def _find_complex_sentences(self, sentences: list[str]) -> list[str]:
        scored = []
        for sent in sentences:
            words = sent.split()
            if not words:
                continue
            syllables = textstat.syllable_count(sent)
            complexity = syllables / len(words)
            scored.append((complexity, sent))

        scored.sort(reverse=True)
        return [sent for _, sent in scored[:COMPLEX_SENTENCE_COUNT]]

    def _recommendation(self, grade: float, score: int) -> str | None:
        if score == MAX_SCORE_PER_CHECK:
            return None
        if grade > FK_GRADE_TARGET_MAX:
            return (
                f"Content reads at Grade {grade}. "
                f"Shorten sentences and replace technical jargon with plain language "
                f"to reach Grade {FK_GRADE_TARGET_MIN:.0f}-{FK_GRADE_TARGET_MAX:.0f}."
            )
        return (
            f"Content reads at Grade {grade}. "
            f"Add more specific, substantive language "
            f"to reach Grade {FK_GRADE_TARGET_MIN:.0f}-{FK_GRADE_TARGET_MAX:.0f}."
        )

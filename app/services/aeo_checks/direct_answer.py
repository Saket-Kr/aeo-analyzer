from app.constants import (
    DIRECT_ANSWER_SCORES,
    DIRECT_ANSWER_WORD_LIMIT,
    DIRECT_ANSWER_WORD_UPPER,
    HEDGE_PHRASES,
    MAX_SCORE_PER_CHECK,
)
from app.models.schemas import CheckResult, DirectAnswerDetails
from app.services.aeo_checks.base import BaseCheck
from app.services.content_parser import ParsedContent
from app.services.nlp import nlp


class DirectAnswerCheck(BaseCheck):
    check_id = "direct_answer"
    name = "Direct Answer Detection"

    def run(self, content: ParsedContent) -> CheckResult:
        text = content.first_paragraph
        word_count = len(text.split()) if text else 0
        has_hedge = self._detect_hedge(text=text)
        is_declarative = self._is_declarative(text=text)
        score = self._compute_score(word_count=word_count, has_hedge=has_hedge, is_declarative=is_declarative)

        return CheckResult(
            check_id=self.check_id,
            name=self.name,
            passed=score == MAX_SCORE_PER_CHECK,
            score=score,
            max_score=MAX_SCORE_PER_CHECK,
            details=DirectAnswerDetails(
                word_count=word_count,
                threshold=DIRECT_ANSWER_WORD_LIMIT,
                is_declarative=is_declarative,
                has_hedge_phrase=has_hedge,
            ),
            recommendation=self._recommendation(text=text, word_count=word_count, has_hedge=has_hedge, is_declarative=is_declarative),
        )

    def _detect_hedge(self, text: str) -> bool:
        lower = text.lower()
        return any(phrase in lower for phrase in HEDGE_PHRASES)

    def _is_declarative(self, text: str) -> bool:
        if not text:
            return False

        doc = nlp(text)
        first_sent = next(doc.sents, None)
        if not first_sent:
            return False

        if first_sent.text.strip().endswith("?"):
            return False

        has_subject = any(tok.dep_ in ("nsubj", "nsubjpass") for tok in first_sent)
        has_root_verb = any(
            tok.dep_ == "ROOT" and tok.pos_ in ("VERB", "AUX") for tok in first_sent
        )
        return has_subject and has_root_verb

    def _compute_score(self, word_count: int, has_hedge: bool, is_declarative: bool) -> int:
        if word_count == 0:
            return DIRECT_ANSWER_SCORES["excessive"]
        if word_count > DIRECT_ANSWER_WORD_UPPER:
            return DIRECT_ANSWER_SCORES["excessive"]
        if word_count > DIRECT_ANSWER_WORD_LIMIT:
            return DIRECT_ANSWER_SCORES["over_limit"]
        if is_declarative and not has_hedge:
            return DIRECT_ANSWER_SCORES["perfect"]
        return DIRECT_ANSWER_SCORES["partial"]

    def _recommendation(
        self, text: str, word_count: int, has_hedge: bool, is_declarative: bool
    ) -> str | None:
        if word_count == 0:
            return "No opening paragraph found. Add a direct, declarative answer as the first paragraph."
        if word_count > DIRECT_ANSWER_WORD_UPPER:
            return (
                f"Opening paragraph is {word_count} words. "
                f"Trim to under {DIRECT_ANSWER_WORD_LIMIT} words with a direct, declarative answer."
            )
        if word_count > DIRECT_ANSWER_WORD_LIMIT:
            return (
                f"Opening paragraph is {word_count} words. "
                f"Trim to under {DIRECT_ANSWER_WORD_LIMIT} words for optimal AI extraction."
            )

        parts = []
        if has_hedge:
            found = [p for p in HEDGE_PHRASES if p in text.lower()]
            parts.append(f"Remove hedge phrases like '{found[0]}' for a more definitive answer.")
        if not is_declarative:
            parts.append("Rewrite the opening as a clear declarative statement with a subject and verb.")

        return " ".join(parts) if parts else None

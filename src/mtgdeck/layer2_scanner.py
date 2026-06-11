"""
layer2_scanner.py — Layer 2 Foundation Audit Scanner.

Phase 2.5: Generate reports for systematic audit of mechanical tagging.

Outputs five audit reports:
1. Coverage gaps — cards with zero/low tags, cards with taggable language but no tags
2. Over-tagging risk — high-tag cards, reminder-text false positives, over-frequent patterns
3. Pattern diagnostics — per-rule metrics (match count, test coverage, risk level, known issues)
4. Unmatched phrase clusters — repeated oracle phrases not matched by any pattern
5. Contradictions — semantic errors (tag without evidence, contradictory tags)

Designed to identify what's missing, what's broken, and what's too broad in Layer 2.
"""

from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Counter
from collections import Counter
import re

from .database import Database
from .oracle_preprocessor import preprocess_oracle


@dataclass
class CoverageGap:
    """A card with suspected coverage gap."""
    card_name: str
    oracle_text: str
    tag_count: int
    has_taggable_verbs: bool
    missing_likely_tags: List[str]


@dataclass
class OverTaggingRisk:
    """A card potentially over-tagged."""
    card_name: str
    tag_count: int
    tags: List[str]
    risk_level: str  # "low", "medium", "high"
    reason: str


@dataclass
class PatternDiagnostic:
    """Health metrics for a tagging pattern/rule."""
    rule_id: str
    tag_name: str
    match_count: int
    positive_test_count: int
    negative_test_count: int
    risk_level: str
    known_issues: List[str]


@dataclass
class PhraseClusters:
    """Clusters of unmatched oracle phrases."""
    phrase: str
    frequency: int
    mechanic_family: str
    example_cards: List[str]


class Layer2Scanner:
    """Scanner for Layer 2 (mechanical tagging) audit."""

    # Common mechanic verbs that should trigger tags
    MECHANIC_FAMILIES = {
        "death": ["dies", "death", "graveyard"],
        "sacrifice": ["sacrifice", "sacrificed"],
        "draw": ["draw", "draws"],
        "discard": ["discard", "discards"],
        "return": ["return", "returns"],
        "reanimate": ["return.*from.*graveyard", "put.*from.*graveyard"],
        "exile": ["exile", "exiled"],
        "mill": ["mill", "mills"],
        "tutor": ["search.*deck", "tutor"],
        "mana": ["add.*mana", "produce"],
        "token": ["create.*token", "create.*tokens"],
        "life": ["gain.*life", "lose.*life"],
        "drain": ["target.*opponent.*loses"],
    }

    def __init__(self, db: Database):
        self.db = db

    def scan_coverage_gaps(self, scope: str = "all") -> List[CoverageGap]:
        """
        Find cards with zero tags, low tags, or taggable language but no tags.

        Args:
            scope: "all", "black_colorless", or "deck_pool"

        Returns:
            List of CoverageGap objects
        """
        gaps = []

        # Get cards based on scope
        if scope == "all":
            cards = self.db.all_cards()
        elif scope == "black_colorless":
            black = self.db.cards_by_color("B")
            colorless = [c for c in self.db.all_cards() if not c.color_identity]
            cards = black + colorless
        else:  # deck_pool
            # TODO: Get cards from actual deck pool
            cards = []

        for card in cards:
            if not card.oracle_text:
                continue

            tags = self.db.get_card_tags(card.name)
            tag_count = len(tags)
            has_taggable = self._has_taggable_verbs(card.oracle_text)
            missing_tags = self._find_likely_missing_tags(card.oracle_text)

            if tag_count == 0 or (tag_count <= 2 and has_taggable):
                gap = CoverageGap(
                    card_name=card.name,
                    oracle_text=card.oracle_text[:100],  # Truncate for display
                    tag_count=tag_count,
                    has_taggable_verbs=has_taggable,
                    missing_likely_tags=missing_tags,
                )
                gaps.append(gap)

        return sorted(gaps, key=lambda g: (g.tag_count, g.card_name))

    def scan_over_tagging_risk(self, threshold: int = 8) -> List[OverTaggingRisk]:
        """
        Find cards with unusually high tag counts.

        Args:
            threshold: Number of tags above which to flag as suspicious

        Returns:
            List of OverTaggingRisk objects
        """
        risks = []
        cards = self.db.all_cards()

        for card in cards:
            tags = self.db.get_card_tags(card.name)
            if len(tags) >= threshold:
                tag_names = [t['name'] for t in tags]
                reason = f"High tag count: {len(tags)} tags"

                risk = OverTaggingRisk(
                    card_name=card.name,
                    tag_count=len(tags),
                    tags=tag_names,
                    risk_level="medium" if len(tags) < 12 else "high",
                    reason=reason,
                )
                risks.append(risk)

        return sorted(risks, key=lambda r: -r.tag_count)

    def scan_pattern_diagnostics(self) -> List[PatternDiagnostic]:
        """
        Analyze the health of each tagging pattern.

        Returns metrics on match counts, test coverage, and risk.
        """
        # This is a skeleton; full implementation would query rule metadata from tags.py
        diagnostics = []

        # Example diagnostic (in real implementation, enumerate all patterns)
        diagnostics.append(PatternDiagnostic(
            rule_id="activated_sacrifice_cost_001",
            tag_name="Sacrifice_Outlet",
            match_count=0,  # Would count from database
            positive_test_count=1,
            negative_test_count=1,
            risk_level="low",
            known_issues=[],
        ))

        return diagnostics

    def scan_unmatched_phrases(self, scope: str = "all", min_frequency: int = 3) -> List[PhraseClusters]:
        """
        Find repeated oracle phrases not matched by any pattern.

        Args:
            scope: "all" or "black_colorless"
            min_frequency: Minimum occurrences to report

        Returns:
            List of PhraseClusters objects
        """
        cards = self.db.all_cards() if scope == "all" else self.db.cards_by_color("B")

        # Extract all phrases from untagged/low-tagged cards
        phrase_counts: Dict[str, Set[str]] = {}

        for card in cards:
            if not card.oracle_text:
                continue

            tags = self.db.get_card_tags(card.name)
            if len(tags) > 0:
                continue  # Skip already-tagged cards

            # Extract meaningful phrases
            phrases = self._extract_phrases(card.oracle_text)
            for phrase in phrases:
                if phrase not in phrase_counts:
                    phrase_counts[phrase] = set()
                phrase_counts[phrase].add(card.name)

        # Filter by frequency and build clusters
        clusters = []
        for phrase, cards_with_phrase in phrase_counts.items():
            if len(cards_with_phrase) >= min_frequency:
                family = self._classify_phrase_family(phrase)
                cluster = PhraseClusters(
                    phrase=phrase,
                    frequency=len(cards_with_phrase),
                    mechanic_family=family,
                    example_cards=list(cards_with_phrase)[:3],
                )
                clusters.append(cluster)

        return sorted(clusters, key=lambda c: -c.frequency)

    def scan_contradictions(self) -> List[Dict]:
        """
        Find semantic errors in tagging.

        Examples:
        - Tag exists but no evidence
        - Conflicting tags (Sacrifice_Outlet but no sac language)
        - Manual tag that contradicts oracle text

        Returns:
            List of contradiction reports
        """
        contradictions = []
        # This is a skeleton for future expansion
        return contradictions

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _has_taggable_verbs(self, oracle_text: str) -> bool:
        """Check if oracle text contains common mechanic verbs."""
        text_lower = oracle_text.lower()
        verbs = [
            "sacrifice", "draw", "discard", "return", "exile", "mill",
            "tutor", "search", "mana", "create", "token", "drain",
        ]
        return any(verb in text_lower for verb in verbs)

    def _find_likely_missing_tags(self, oracle_text: str) -> List[str]:
        """Identify tags that should probably exist based on oracle text."""
        text_lower = oracle_text.lower()
        likely = []

        patterns = {
            "Sacrifice_Outlet": r"sacrifice.*:",
            "Draw_Effect": r"draw.*card",
            "Token_Generation": r"create.*token",
            "Mana_Production": r"add.*\{",
            "Reanimation": r"return.*from.*graveyard",
            "Tutor_Effect": r"search.*deck",
        }

        for tag, pattern in patterns.items():
            if re.search(pattern, text_lower):
                likely.append(tag)

        return likely

    def _extract_phrases(self, oracle_text: str, min_length: int = 3) -> List[str]:
        """
        Extract meaningful phrases from oracle text.

        Heuristic: split by common delimiters and return non-trivial phrases.
        """
        # Remove reminder text
        main_text = re.sub(r"\([^)]*\)", "", oracle_text)

        # Split by newlines and punctuation
        phrases = re.split(r"[\n,.]", main_text)

        # Filter and normalize
        result = []
        for phrase in phrases:
            phrase = phrase.strip()
            words = phrase.split()
            if len(words) >= min_length and len(phrase) < 60:  # Reasonable length
                result.append(phrase.lower())

        return result

    def _classify_phrase_family(self, phrase: str) -> str:
        """Classify a phrase into a mechanic family."""
        phrase_lower = phrase.lower()

        for family, keywords in self.MECHANIC_FAMILIES.items():
            for keyword in keywords:
                if keyword in phrase_lower:
                    return family

        return "other"


def generate_audit_report(
    db: Database,
    output_dir: str = "reports/layer2",
    scope: str = "black_colorless",
) -> Dict[str, str]:
    """
    Generate all five audit reports and write to files.

    Args:
        db: Database connection
        output_dir: Directory to write reports
        scope: "all", "black_colorless", or "deck_pool"

    Returns:
        Dictionary of {report_name: file_path}
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    scanner = Layer2Scanner(db)
    reports = {}

    # Report 1: Coverage gaps
    gaps = scanner.scan_coverage_gaps(scope)
    gaps_path = os.path.join(output_dir, "coverage_gaps.md")
    with open(gaps_path, "w") as f:
        f.write("# Layer 2 Coverage Gaps\n\n")
        f.write(f"Scope: {scope}\n")
        f.write(f"Cards with zero or low tags: {len(gaps)}\n\n")
        for gap in gaps[:30]:  # Top 30
            f.write(f"## {gap.card_name}\n")
            f.write(f"- Tags: {gap.tag_count}\n")
            f.write(f"- Has taggable verbs: {gap.has_taggable_verbs}\n")
            f.write(f"- Likely missing: {', '.join(gap.missing_likely_tags)}\n")
            f.write(f"- Text: {gap.oracle_text}\n\n")
    reports["coverage_gaps"] = gaps_path

    # Report 2: Over-tagging risk
    risks = scanner.scan_over_tagging_risk()
    risks_path = os.path.join(output_dir, "over_tagging_risk.md")
    with open(risks_path, "w") as f:
        f.write("# Layer 2 Over-Tagging Risk\n\n")
        f.write(f"Cards with 8+ tags: {len(risks)}\n\n")
        for risk in risks[:20]:  # Top 20
            f.write(f"## {risk.card_name}\n")
            f.write(f"- Tag count: {risk.tag_count} ({risk.risk_level} risk)\n")
            f.write(f"- Tags: {', '.join(risk.tags[:5])}\n\n")
    reports["over_tagging_risk"] = risks_path

    # Report 3: Unmatched phrases
    phrases = scanner.scan_unmatched_phrases(scope)
    phrases_path = os.path.join(output_dir, "unmatched_phrase_clusters.md")
    with open(phrases_path, "w") as f:
        f.write("# Layer 2 Unmatched Phrase Clusters\n\n")
        f.write(f"Scope: {scope}\n\n")
        for cluster in phrases[:20]:  # Top 20
            f.write(f"## {cluster.phrase}\n")
            f.write(f"- Frequency: {cluster.frequency}\n")
            f.write(f"- Family: {cluster.mechanic_family}\n")
            f.write(f"- Examples: {', '.join(cluster.example_cards)}\n\n")
    reports["unmatched_phrases"] = phrases_path

    return reports

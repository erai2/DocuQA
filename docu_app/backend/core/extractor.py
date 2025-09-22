"""Advanced rule extraction utilities for DocuQA."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence
import re

from .parser import DocumentParseResult, ParsedBlock


@dataclass
class RuleCandidate:
    """Represents a rule extracted from a document with provenance metadata."""

    identifier: str
    title: Optional[str]
    content: str
    confidence: float = 0.5
    metadata: Dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "id": self.identifier,
            "title": self.title,
            "content": self.content,
            "confidence": self.confidence,
        }
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload


class RuleExtractor:
    """Extracts rule candidates from parsed documents or raw text."""

    #: captures numbered headings such as "1.", "가.", "제1조".
    HEADING_PATTERN = re.compile(
        r"^(?P<number>(?:제\s*\d+\s*조|제\s*\d+\s*항|[0-9]+\.|[A-Z]\.|[IVX]+\.|[가-힣]\.)\s*)(?P<title>.+)$",
        re.MULTILINE,
    )
    #: fallback for bullet markers
    BULLET_PATTERN = re.compile(r"^(?:[-*•]\s+)(?P<title>[^:：]+)[:：]\s*(?P<body>.+)$", re.MULTILINE)

    def __init__(self, min_length: int = 50) -> None:
        self.min_length = min_length

    # ------------------------------------------------------------------
    def extract(self, source: DocumentParseResult | str) -> List[RuleCandidate]:
        """Extract rule candidates from a parse result or raw text."""
        if isinstance(source, DocumentParseResult):
            return self._extract_from_parse_result(source)
        return self._extract_from_text(source)

    # ------------------------------------------------------------------
    def _extract_from_parse_result(self, result: DocumentParseResult) -> List[RuleCandidate]:
        candidates: List[RuleCandidate] = []
        for block in result.rules:
            candidates.extend(self._expand_block(block, base_confidence=0.95))

        # Recover additional rule-like structures from cases/concepts.
        spillover_blocks = [*result.cases, *result.concepts]
        for block in spillover_blocks:
            inferred = self._expand_block(block, base_confidence=0.5, restrict_by_heading=True)
            if inferred:
                candidates.extend(inferred)
        return self._deduplicate_candidates(candidates)

    def _extract_from_text(self, text: str) -> List[RuleCandidate]:
        pseudo_block = ParsedBlock(
            identifier="raw-text",
            title=None,
            content=text,
            metadata={"source_tag": "규칙"},
        )
        return self._deduplicate_candidates(self._expand_block(pseudo_block, base_confidence=0.4))

    # ------------------------------------------------------------------
    def _expand_block(
        self,
        block: ParsedBlock,
        *,
        base_confidence: float,
        restrict_by_heading: bool = False,
    ) -> List[RuleCandidate]:
        content = block.content.strip()
        if len(content) < self.min_length:
            return []

        matches = list(self.HEADING_PATTERN.finditer(content))
        if matches:
            return self._split_with_heading(block, matches, base_confidence)

        bullet_matches = list(self.BULLET_PATTERN.finditer(content))
        if bullet_matches and not restrict_by_heading:
            return self._split_bullets(block, bullet_matches, base_confidence * 0.9)

        if restrict_by_heading:
            return []

        return [
            RuleCandidate(
                identifier=self._ensure_identifier(block.identifier, block.title),
                title=block.title,
                content=content,
                confidence=base_confidence,
                metadata=dict(block.metadata),
            )
        ]

    def _split_with_heading(
        self,
        block: ParsedBlock,
        matches: Sequence[re.Match[str]],
        base_confidence: float,
    ) -> List[RuleCandidate]:
        candidates: List[RuleCandidate] = []
        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(block.content)
            snippet = block.content[start:end].strip()
            if len(snippet) < self.min_length:
                continue
            number = match.group("number").strip()
            title = match.group("title").strip()
            identifier = self._ensure_identifier(title, block.identifier)
            metadata = dict(block.metadata)
            metadata.update({
                "marker": number,
                "source_tag": metadata.get("source_tag", "규칙"),
            })
            candidates.append(
                RuleCandidate(
                    identifier=identifier,
                    title=title,
                    content=snippet,
                    confidence=min(1.0, base_confidence + 0.03),
                    metadata=metadata,
                )
            )
        return candidates

    def _split_bullets(
        self,
        block: ParsedBlock,
        matches: Sequence[re.Match[str]],
        base_confidence: float,
    ) -> List[RuleCandidate]:
        candidates: List[RuleCandidate] = []
        for match in matches:
            title = match.group("title").strip()
            body = match.group("body").strip()
            snippet = f"{title}: {body}"
            if len(snippet) < self.min_length:
                continue
            identifier = self._ensure_identifier(title, block.identifier)
            metadata = dict(block.metadata)
            metadata.setdefault("source_tag", "규칙")
            metadata["marker"] = "bullet"
            candidates.append(
                RuleCandidate(
                    identifier=identifier,
                    title=title,
                    content=snippet,
                    confidence=base_confidence,
                    metadata=metadata,
                )
            )
        return candidates

    # ------------------------------------------------------------------
    def _ensure_identifier(self, preferred: Optional[str], fallback: Optional[str]) -> str:
        base = (preferred or fallback or "rule").strip().lower()
        base = re.sub(r"[^a-z0-9\-_.]+", "-", base)
        base = re.sub(r"-+", "-", base).strip("-._") or "rule"
        return base

    def _deduplicate_candidates(self, candidates: Iterable[RuleCandidate]) -> List[RuleCandidate]:
        unique: Dict[str, RuleCandidate] = {}
        for candidate in candidates:
            key = candidate.identifier
            existing = unique.get(key)
            if existing is None or candidate.confidence > existing.confidence:
                unique[key] = candidate
        return list(unique.values())

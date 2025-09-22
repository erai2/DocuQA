"""Utilities for parsing semi-structured legal documents used by DocuQA."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import re
import textwrap


_TAG_PATTERN = re.compile(
    r"<(?P<tag>사례|규칙|개념)(?P<attrs>[^>]*)>(?P<body>.*?)</(?P=tag)>",
    re.DOTALL | re.IGNORECASE,
)
_ATTR_PATTERN = re.compile(r"([\w\-:]+)\s*=\s*\"([^\"]*)\"")
_RULE_REFERENCE_PATTERN = re.compile(
    r"(?:\(|\[)?(?:관련\s*)?규칙\s*[:：]\s*(?P<ids>[^)\]\n]+)(?:\)|\])?",
    re.IGNORECASE,
)
_INLINE_RULE_PATTERN = re.compile(
    r"규칙\s*(?P<id>[A-Za-z0-9_\-]+)",
)
_HEADING_PATTERN = re.compile(
    r"^(?P<marker>(?:제\s*\d+\s*조|[0-9]+\.|[IVX]+\.|[A-Z]\.|[가-힣]\.)\s*)(?P<title>.+)$",
    re.MULTILINE,
)
_SECTION_TITLE_PATTERN = re.compile(r"^(?:#|##|###)\s*(사례|규칙|개념)(.*)$", re.MULTILINE)


@dataclass
class ParsedBlock:
    """Structured representation of a tagged block within the source document."""

    identifier: str
    title: Optional[str]
    content: str
    metadata: Dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Optional[str]]:
        """Return a serialisable dictionary representation."""
        data = {
            "id": self.identifier,
            "title": self.title,
            "content": self.content,
        }
        data.update(self.metadata)
        return data


@dataclass
class DocumentParseResult:
    """Container for the parsed structure of a document."""

    cases: List[ParsedBlock] = field(default_factory=list)
    rules: List[ParsedBlock] = field(default_factory=list)
    concepts: List[ParsedBlock] = field(default_factory=list)
    references: Dict[str, List[str]] = field(default_factory=dict)
    diagnostics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        """Export the parse result as a dictionary."""
        return {
            "cases": [case.as_dict() for case in self.cases],
            "rules": [rule.as_dict() for rule in self.rules],
            "concepts": [concept.as_dict() for concept in self.concepts],
            "references": self.references,
            "diagnostics": list(self.diagnostics),
        }


class DocumentParser:
    """Parses DocuQA domain specific documents into structured blocks.

    The parser understands the `<사례>`, `<규칙>` and `<개념>` tags, but it also
    includes a set of heuristics to recover structure from lightly formatted
    text (e.g. Markdown headings). This makes the ingestion step much more
    tolerant to human authored documents that do not strictly follow the
    template.
    """

    def __init__(self, min_block_length: int = 20) -> None:
        self.min_block_length = min_block_length

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def parse_document(self, text: str) -> DocumentParseResult:
        """Parse a raw document string into structured entities.

        Parameters
        ----------
        text:
            The raw document body as a UTF-8 string.
        """
        normalised = self._normalise_text(text)
        result = DocumentParseResult()

        # First, extract explicitly tagged blocks.
        tagged_blocks = list(self._extract_tagged_blocks(normalised))
        consumed_spans: List[Tuple[int, int]] = []

        for tag, attrs, body, span in tagged_blocks:
            identifier = self._resolve_identifier(attrs, prefix=tag)
            title = attrs.get("title") or self._derive_title(body)
            cleaned = self._clean_block(body)
            metadata = {k: v for k, v in attrs.items() if k not in {"id", "title"}}
            metadata["source_tag"] = tag

            block = ParsedBlock(identifier=identifier, title=title, content=cleaned, metadata=metadata)
            if len(cleaned) < self.min_block_length:
                result.diagnostics.append(
                    f"Block '{identifier}' under <{tag}> ignored because content is too short."
                )
                continue

            if tag.lower() == "사례":
                result.cases.append(block)
                references = self._extract_rule_references(cleaned)
                if references:
                    result.references[identifier] = references
            elif tag.lower() == "규칙":
                result.rules.append(block)
            elif tag.lower() == "개념":
                result.concepts.append(block)

            consumed_spans.append(span)

        # Secondly, capture any remaining sections via heuristics.
        remainder = self._extract_remainder(normalised, consumed_spans)
        if remainder.strip():
            heuristic_blocks = self._extract_from_headings(remainder)
            for block in heuristic_blocks:
                if block.metadata["source_tag"] == "규칙":
                    result.diagnostics.append(
                        "Rule candidate recovered heuristically from Markdown heading: "
                        f"{block.identifier}"
                    )
                    result.rules.append(block)
                elif block.metadata["source_tag"] == "사례":
                    result.cases.append(block)
                else:
                    result.concepts.append(block)

        # Deduplicate rule references and normalise ids.
        for case_id, refs in list(result.references.items()):
            seen = set()
            normalised_refs = []
            for ref in refs:
                clean_ref = self._normalise_identifier(ref, fallback_prefix="rule")
                if clean_ref not in seen:
                    seen.add(clean_ref)
                    normalised_refs.append(clean_ref)
            if normalised_refs:
                result.references[case_id] = normalised_refs
            else:
                result.references.pop(case_id, None)

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _normalise_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = textwrap.dedent(text)
        return text.strip()

    def _extract_tagged_blocks(
        self, text: str
    ) -> Iterable[Tuple[str, Dict[str, str], str, Tuple[int, int]]]:
        for match in _TAG_PATTERN.finditer(text):
            tag = match.group("tag")
            attrs = self._parse_attributes(match.group("attrs"))
            body = match.group("body")
            yield tag, attrs, body, match.span()

    def _parse_attributes(self, attr_text: str) -> Dict[str, str]:
        attributes: Dict[str, str] = {}
        for key, value in _ATTR_PATTERN.findall(attr_text or ""):
            attributes[key.lower()] = value.strip()
        return attributes

    def _resolve_identifier(self, attrs: Dict[str, str], prefix: str) -> str:
        identifier = attrs.get("id") or attrs.get("name")
        return self._normalise_identifier(identifier, fallback_prefix=prefix)

    def _normalise_identifier(self, identifier: Optional[str], fallback_prefix: str) -> str:
        if identifier:
            candidate = identifier.strip().lower()
        else:
            candidate = ""
        candidate = re.sub(r"[^a-z0-9\-_.]+", "-", candidate)
        candidate = re.sub(r"-+", "-", candidate).strip("-._")
        if not candidate:
            candidate = f"{fallback_prefix}-{abs(hash(fallback_prefix)) % 10_000}"
        return candidate

    def _derive_title(self, body: str) -> Optional[str]:
        for line in body.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped.split("\u200b")[0][:120]
        return None

    def _clean_block(self, body: str) -> str:
        cleaned = body.strip()
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned

    def _extract_rule_references(self, text: str) -> List[str]:
        references: List[str] = []
        for match in _RULE_REFERENCE_PATTERN.finditer(text):
            raw_ids = match.group("ids")
            if not raw_ids:
                continue
            for ref in re.split(r"[,;\/\s]+", raw_ids):
                ref = ref.strip()
                if not ref:
                    continue
                references.append(ref)
        for match in _INLINE_RULE_PATTERN.finditer(text):
            references.append(match.group("id"))
        return references

    def _extract_remainder(self, text: str, spans: Sequence[Tuple[int, int]]) -> str:
        if not spans:
            return text
        markers = sorted(spans)
        remainder_parts: List[str] = []
        cursor = 0
        for start, end in markers:
            remainder_parts.append(text[cursor:start])
            cursor = end
        remainder_parts.append(text[cursor:])
        return "".join(remainder_parts)

    def _extract_from_headings(self, text: str) -> List[ParsedBlock]:
        blocks: List[ParsedBlock] = []
        if not text:
            return blocks

        sections = []
        last_pos = 0
        for heading in _SECTION_TITLE_PATTERN.finditer(text):
            start = heading.start()
            if last_pos != start:
                sections.append(text[last_pos:start])
            sections.append(text[start:heading.end()])
            last_pos = heading.end()
        if last_pos < len(text):
            sections.append(text[last_pos:])

        current_tag = None
        buffer: List[str] = []
        for line in text.splitlines():
            heading_match = _SECTION_TITLE_PATTERN.match(line)
            if heading_match:
                if buffer and current_tag:
                    content = "\n".join(buffer).strip()
                    if len(content) >= self.min_block_length:
                        identifier = self._normalise_identifier(None, fallback_prefix=current_tag)
                        blocks.append(
                            ParsedBlock(
                                identifier=identifier,
                                title=None,
                                content=content,
                                metadata={"source_tag": current_tag},
                            )
                        )
                current_tag = heading_match.group(1)
                buffer = []
            else:
                buffer.append(line)
        if buffer and current_tag:
            content = "\n".join(buffer).strip()
            if len(content) >= self.min_block_length:
                identifier = self._normalise_identifier(None, fallback_prefix=current_tag)
                blocks.append(
                    ParsedBlock(
                        identifier=identifier,
                        title=None,
                        content=content,
                        metadata={"source_tag": current_tag},
                    )
                )

        # Additionally attempt to split rules based on numbering.
        enriched_blocks: List[ParsedBlock] = []
        for block in blocks:
            if block.metadata.get("source_tag") == "규칙":
                sub_rules = list(self._split_numbered_rules(block))
                if sub_rules:
                    enriched_blocks.extend(sub_rules)
                    continue
            enriched_blocks.append(block)
        return enriched_blocks

    def _split_numbered_rules(self, block: ParsedBlock) -> Iterable[ParsedBlock]:
        positions = list(_HEADING_PATTERN.finditer(block.content))
        if not positions:
            return []
        segments: List[Tuple[int, int, re.Match[str]]] = []
        for idx, match in enumerate(positions):
            start = match.start()
            end = positions[idx + 1].start() if idx + 1 < len(positions) else len(block.content)
            segments.append((start, end, match))

        for start, end, match in segments:
            section = block.content[start:end].strip()
            if len(section) < self.min_block_length:
                continue
            identifier = self._normalise_identifier(match.group("title"), fallback_prefix="rule")
            metadata = dict(block.metadata)
            metadata["marker"] = match.group("marker").strip()
            metadata["source_tag"] = "규칙"
            yield ParsedBlock(
                identifier=identifier,
                title=match.group("title").strip(),
                content=section,
                metadata=metadata,
            )

#!/usr/bin/env python3
"""
import_kb_deck.py — Import a knowledge-base-style deck folder into Spatial Deck.

A purpose-built importer for the two knowledge-base deck formats produced by
AI agents. Different from import_md.py (which expects a flat single-file
markdown convention) in three ways:

  1. KB mode uses `SECTIONS.json` + `slides/NN-*.md` files. Each slide carries
     YAML frontmatter and a `## Speaker Notes` block.
  2. FMX mode uses one numbered `slides.md`; its fully formed SECTIONS.json is
     overlaid with canonical slide order, titles, speakers, and notes.
  3. Both modes fail closed on malformed manifests or missing slide sources.

CLI:
  python3 tools/import_kb_deck.py <deck_dir> --out <out.html>
                                   [--format auto|kb|fmx]
                                   [--title "..."] [--template /path/to/index.html]

Defaults:
  --template = the spatial-deck repo's own index.html (script's grandparent dir).

Outputs:
  A single self-contained HTML file with:
    * SECTIONS array replaced by the imported deck
    * design tokens injected as CSS custom properties on :root
    * window._deckSpeakerNotes / window._deckSpeakers globals for the
      presenter popup
    * tools/_kb_speaker_styling.css inlined for color-coded edge bars

Conventions / defaults (documented for reproducibility):
  * Frontmatter parsed with a regex (no PyYAML required) — only flat scalar
    keys are supported, which is all this format uses.
  * The slide title is the first h1, falling back to the first h2.
  * `lesson.tagline` = first non-heading paragraph in the section's first slide.
  * `lesson.short` = section name uppercased, hyphens → spaces.
  * `lesson.tags` = unique speakers across the section, joined with " · ".
  * `cases` = remaining slides in the section. The case body becomes:
      - subtitle = first paragraph after the title
      - bullets  = up to 6 bulleted/numbered list items (markdown stripped)
      - notes    = content under `## Speaker Notes*` until the next `##`
      - _layout, _speaker = preserved frontmatter fields
  * `accent` for each section cycles through teal/purple/amber/rose/teal...

If the source has fewer/more slides per section than the template demos, that
is fine — Spatial Deck supports arbitrary section/case counts.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
H2_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
SPEAKER_NOTES_RE = re.compile(
    r"^##\s+Speaker\s+Notes[^\n]*\n(.*?)(?=^##\s+|\Z)",
    re.DOTALL | re.MULTILINE | re.IGNORECASE,
)
BULLET_RE = re.compile(r"^[\s]*(?:[-*+]|\d+\.)\s+(.+?)\s*$", re.MULTILINE)
FMX_SLIDE_RE = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$", re.MULTILINE)
FMX_ROLE_RE = re.compile(
    r"^CH\s*(\d+)\s+(Lesson|Case\s+(\d+))(?:\s+[—–-]\s+(.+))?$",
    re.IGNORECASE,
)
FMX_NOTES_RE = re.compile(
    r"^\*\*Speaker\s+notes(?:\s*\(([^)]+)\))?:\*\*\s*(.*)$",
    re.IGNORECASE,
)
FMX_SPEAKER_RE = re.compile(r"^\*\*Speaker:\*\*\s*(.+?)\s*$", re.IGNORECASE)
FMX_FIELD_RE = re.compile(r"^\*\*[^*]+:\*\*")

ACCENT_CYCLE = ["teal", "purple", "amber", "rose"]


class ImportInputError(ValueError):
    """Input is incomplete or malformed and must not be imported."""


# ---------------------------------------------------------------------------
# Frontmatter / markdown parsing
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) — frontmatter is a flat scalar dict."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm_block, body = m.group(1), m.group(2)
    fm: dict[str, str] = {}
    for line in fm_block.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip().strip('"').strip("'")
        fm[key.strip()] = val
    return fm, body


def first_title(body: str) -> str:
    """First h1, fallback to first h2, fallback to ''. Multiple h1s on
    consecutive lines are concatenated with <br> (handles the 2-line title
    convention used in the bold variant)."""
    h1s: list[str] = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("# ") and not s.startswith("## "):
            h1s.append(s[2:].strip())
        elif h1s:
            # Stop collecting once we hit a non-h1 line after seeing h1s
            if s == "":
                continue
            break
    if h1s:
        return "<br>".join(h1s)
    m = H2_RE.search(body)
    return m.group(1).strip() if m else ""


def first_paragraph_after_title(body: str) -> str:
    """First non-heading, non-frontmatter paragraph after the title block.
    Falls back to '' if none."""
    # Strip everything up to and including the title heading lines
    lines = body.splitlines()
    i = 0
    # Skip leading blank lines
    while i < len(lines) and not lines[i].strip():
        i += 1
    # Skip consecutive heading lines (#, ##) at the top
    while i < len(lines) and (lines[i].lstrip().startswith("#") or not lines[i].strip()):
        i += 1
    # Now collect the first paragraph until blank line or heading
    para: list[str] = []
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            if para:
                break
            i += 1
            continue
        if s.startswith("#"):
            if para:
                break
            i += 1
            continue
        if s.startswith("---"):
            break
        # Skip subtitle h2s already eaten? No — collect paragraph text only.
        para.append(s)
        i += 1
    text = " ".join(para).strip()
    # Strip simple markdown emphasis for tagline use
    return _strip_md(text)


def extract_bullets(body: str, limit: int = 6) -> list[str]:
    """Up to N bullet/numbered list items, with markdown stripped."""
    out: list[str] = []
    for m in BULLET_RE.finditer(body):
        item = _strip_md(m.group(1).strip())
        if item:
            out.append(item)
        if len(out) >= limit:
            break
    return out


def extract_speaker_notes(body: str) -> str:
    """Concatenate every `## Speaker Notes*` block (some files have one per
    speaker). Returns plain text with markdown lightly stripped."""
    chunks: list[str] = []
    for m in SPEAKER_NOTES_RE.finditer(body):
        chunks.append(m.group(1).strip())
    notes = "\n\n".join(chunks).strip()
    return _strip_md(notes, keep_newlines=True)


def _strip_md(text: str, keep_newlines: bool = False) -> str:
    if not text:
        return ""
    # Remove inline code backticks but keep content
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Bold/italic
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    # Links [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    if not keep_newlines:
        text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# FMX single-file parsing
# ---------------------------------------------------------------------------

def _fmx_blockquote(lines: list[str]) -> str:
    """Normalize a speaker-note block while preserving paragraph breaks."""
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(">"):
            stripped = stripped[1:].lstrip()
        out.append(stripped)
    return _strip_md("\n".join(out).strip(), keep_newlines=True)


def _fmx_notes_and_speaker(body: str) -> tuple[str, str]:
    """Read labeled speaker notes, or a standalone blockquote as fallback."""
    lines = body.splitlines()
    speaker = ""
    notes: list[str] = []

    for line in lines:
        match = FMX_SPEAKER_RE.match(line.strip())
        if match:
            speaker = match.group(1).strip()
            break

    for index, line in enumerate(lines):
        match = FMX_NOTES_RE.match(line.strip())
        if not match:
            continue
        if match.group(1) and not speaker:
            speaker = match.group(1).strip()
        chunk: list[str] = []
        if match.group(2).strip():
            chunk.append(match.group(2).strip())
        for following in lines[index + 1:]:
            stripped = following.strip()
            if stripped == "---" or FMX_FIELD_RE.match(stripped):
                break
            chunk.append(following)
        value = _fmx_blockquote(chunk)
        if value:
            notes.append(value)

    if notes:
        return "\n\n".join(notes), speaker

    # Some early FMX drafts used an otherwise-unlabeled blockquote for notes.
    # Only accept it when the block has no labeled fields, avoiding confusion
    # with `Big text:` and other quoted display copy.
    if not any(FMX_FIELD_RE.match(line.strip()) for line in lines):
        quoted = [line for line in lines if line.strip().startswith(">")]
        if quoted:
            return _fmx_blockquote(quoted), speaker
    return "", speaker


def _fmx_big_text(body: str) -> str:
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if line.strip().lower() != "**big text:**":
            continue
        quoted: list[str] = []
        for following in lines[index + 1:]:
            if not following.strip().startswith(">"):
                break
            quoted.append(following)
        return "<br>".join(
            line.strip()[1:].lstrip() for line in quoted if line.strip()[1:].strip()
        )
    return ""


def _fmx_subtitle(body: str) -> str:
    match = re.search(r"^\*\*Sub:?\*\*\s*(.+?)\s*$", body, re.MULTILINE)
    return _strip_md(match.group(1)) if match else ""


def parse_fmx_slides(text: str) -> list[dict]:
    """Parse numbered FMX `## N. Title` blocks in declared slide order."""
    matches = list(FMX_SLIDE_RE.finditer(text))
    if not matches:
        raise ImportInputError(
            "slides.md has no numbered slide headings (expected '## N. Title')"
        )

    slides: list[dict] = []
    for index, match in enumerate(matches):
        number = int(match.group(1))
        expected = int(matches[0].group(1)) + index
        if number != expected:
            raise ImportInputError(
                f"slides.md numbering is not contiguous: expected {expected}, got {number}"
            )
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():body_end].strip()
        heading = match.group(2).strip()
        role = FMX_ROLE_RE.match(heading)
        notes, speaker = _fmx_notes_and_speaker(body)
        slides.append({
            "number": number,
            "heading": heading,
            "body": body,
            "chapter": int(role.group(1)) if role else None,
            "kind": role.group(2).lower() if role else "special",
            "case": int(role.group(3)) if role and role.group(3) else None,
            "title": (role.group(4).strip() if role and role.group(4)
                      else _fmx_big_text(body) or heading),
            "subtitle": _fmx_subtitle(body),
            "notes": notes,
            "speaker": speaker,
        })
    return slides


def validate_kb_manifest(manifest: object) -> dict:
    if not isinstance(manifest, dict):
        raise ImportInputError("KB SECTIONS.json must be a JSON object")
    sections = manifest.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ImportInputError("KB SECTIONS.json 'sections' must be a non-empty array")
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ImportInputError(f"KB section {index} must be an object")
        slide_ids = section.get("slides")
        if (not isinstance(slide_ids, list) or not slide_ids
                or not all(isinstance(sid, str) and sid.strip() for sid in slide_ids)):
            raise ImportInputError(
                f"KB section {index} 'slides' must be a non-empty array of slide ids"
            )
    return manifest


def validate_fmx_manifest(manifest: object) -> tuple[list[dict], dict]:
    metadata = manifest if isinstance(manifest, dict) else {}
    sections = manifest.get("sections") if isinstance(manifest, dict) else manifest
    if not isinstance(sections, list) or not sections:
        raise ImportInputError(
            "FMX SECTIONS.json must be a non-empty Spatial Deck array "
            "(or an object containing that array as 'sections')"
        )
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ImportInputError(f"FMX section {index} must be an object")
        lesson = section.get("lesson")
        cases = section.get("cases")
        if not isinstance(lesson, dict) or not isinstance(lesson.get("title"), str):
            raise ImportInputError(
                f"FMX section {index} requires lesson.title"
            )
        if (not isinstance(cases, list)
                or not all(isinstance(case, dict) for case in cases)):
            raise ImportInputError(f"FMX section {index} 'cases' must be an array")
        for case_index, case in enumerate(cases):
            if not isinstance(case.get("title"), str):
                raise ImportInputError(
                    f"FMX section {index} case {case_index} requires title"
                )
    return copy.deepcopy(sections), metadata


def build_fmx_sections(manifest: object, slides_text: str) -> tuple[list, dict, dict, dict]:
    """Overlay an FMX manifest with canonical order/copy from slides.md."""
    sections, _ = validate_fmx_manifest(manifest)
    editorial = parse_fmx_slides(slides_text)
    chapters: dict[int, dict] = {}
    chapter_order: list[int] = []
    for slide in editorial:
        chapter = slide["chapter"]
        if chapter is None:
            continue
        if chapter not in chapters:
            chapters[chapter] = {"lesson": None, "cases": []}
            chapter_order.append(chapter)
        if slide["kind"] == "lesson":
            if chapters[chapter]["lesson"] is not None:
                raise ImportInputError(f"slides.md has duplicate CH{chapter} Lesson")
            chapters[chapter]["lesson"] = slide
        else:
            chapters[chapter]["cases"].append(slide)

    if len(chapter_order) != len(sections):
        raise ImportInputError(
            "FMX slide/manifest mismatch: slides.md has "
            f"{len(chapter_order)} chapters but SECTIONS.json has {len(sections)}"
        )

    sections_by_chapter: dict[int, dict] = {}
    for section in sections:
        year_match = re.fullmatch(r"CH\s*(\d+)", str(section.get("year", "")), re.I)
        if not year_match:
            sections_by_chapter = {}
            break
        chapter = int(year_match.group(1))
        if chapter in sections_by_chapter:
            raise ImportInputError(f"FMX SECTIONS.json has duplicate CH{chapter}")
        sections_by_chapter[chapter] = section
    if sections_by_chapter and set(sections_by_chapter) != set(chapter_order):
        raise ImportInputError(
            "FMX chapter ids differ between slides.md and SECTIONS.json"
        )

    ordered_sections: list[dict] = []
    notes_map: dict[str, str] = {}
    speakers_map: dict[str, str] = {}
    for section_index, chapter in enumerate(chapter_order):
        section = (sections_by_chapter.get(chapter)
                   if sections_by_chapter else sections[section_index])
        group = chapters[chapter]
        lesson_slide = group["lesson"]
        if lesson_slide is None:
            raise ImportInputError(f"slides.md is missing CH{chapter} Lesson")
        case_slides = sorted(group["cases"], key=lambda slide: slide["case"])
        case_numbers = [slide["case"] for slide in case_slides]
        if case_numbers != list(range(1, len(case_slides) + 1)):
            raise ImportInputError(
                f"slides.md CH{chapter} case numbers must be contiguous from 1"
            )
        if len(case_slides) != len(section["cases"]):
            raise ImportInputError(
                f"FMX CH{chapter} has {len(case_slides)} cases in slides.md but "
                f"{len(section['cases'])} in SECTIONS.json"
            )

        lesson = section["lesson"]
        lesson["title"] = lesson_slide["title"]
        if lesson_slide["notes"]:
            lesson["notes"] = lesson_slide["notes"]
        if lesson_slide["speaker"]:
            lesson["_speaker"] = lesson_slide["speaker"]
        lesson_key = f"slide-{lesson_slide['number']}"
        notes_map[lesson_key] = lesson.get("notes", "")
        speakers_map[lesson_key] = lesson_slide["speaker"]

        ordered_cases: list[dict] = []
        for case, slide in zip(section["cases"], case_slides):
            case["title"] = slide["title"]
            if slide["subtitle"]:
                case["subtitle"] = slide["subtitle"]
            if slide["notes"]:
                case["notes"] = slide["notes"]
            if slide["speaker"]:
                case["_speaker"] = slide["speaker"]
            case["_id"] = f"slide-{slide['number']}"
            ordered_cases.append(case)
            key = case["_id"]
            notes_map[key] = case.get("notes", "")
            speakers_map[key] = slide["speaker"]
        section["cases"] = ordered_cases
        ordered_sections.append(section)

    cover = next((slide for slide in editorial if slide["number"] == 0), None)
    cover_info = {
        "title": cover["title"] if cover else "",
        "subtitle": cover["subtitle"] if cover else "",
        "editorial_count": len(editorial),
    }
    return ordered_sections, notes_map, speakers_map, cover_info


# ---------------------------------------------------------------------------
# Template patching
# ---------------------------------------------------------------------------

def find_sections_array(html: str) -> tuple[int, int]:
    """Locate the `const SECTIONS = [ ... ];` block. Returns (start, end)
    indices spanning from `const SECTIONS` through the closing `];`.
    Bracket-aware: handles nested arrays."""
    needle = "const SECTIONS"
    start = html.find(needle)
    if start < 0:
        raise RuntimeError("Could not find 'const SECTIONS' in template.")
    open_bracket = html.find("[", start)
    if open_bracket < 0:
        raise RuntimeError("Could not find opening '[' for SECTIONS.")
    # Walk brackets respecting strings
    depth = 0
    i = open_bracket
    in_str: str | None = None
    escape = False
    while i < len(html):
        ch = html[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == in_str:
                in_str = None
        else:
            if ch in ("'", '"', "`"):
                in_str = ch
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    # Expect a `;` shortly after
                    j = i + 1
                    while j < len(html) and html[j] in " \t\r\n":
                        j += 1
                    if j < len(html) and html[j] == ";":
                        return start, j + 1
                    return start, i + 1
        i += 1
    raise RuntimeError("Unterminated SECTIONS array in template.")


def js_escape(s: str) -> str:
    """Escape for embedding in a JS single-quoted string."""
    if s is None:
        return ""
    return (
        s.replace("\\", "\\\\")
         .replace("'", "\\'")
         .replace("\n", "\\n")
         .replace("\r", "")
    )


def build_design_token_css(tokens: dict) -> str:
    """Map known token names → CSS custom properties on :root.
    Unknown tokens are emitted as --kb-<name> for debugging but not consumed
    by the template."""
    if not tokens:
        return ""
    mapping = {
        "bg_primary":     ["--bg", "--bg-dark"],
        "bg_secondary":   ["--bg-secondary"],
        "bg_card":        ["--bg-card"],
        "text_primary":   ["--text", "--ink"],
        "text_secondary": ["--text-secondary"],
        "text_muted":     ["--dim"],
        "text_dim":       ["--dim"],
        "text_caption":   ["--dim"],
        "accent_magenta": ["--rose"],
        "accent_teal":    ["--teal", "--primary"],
        "accent_purple":  ["--purple", "--secondary"],
        "accent_warm":    ["--rose"],
        "accent_cool":    ["--teal"],
        "accent_signal":  ["--amber"],
        "accent_red":     ["--rose"],
        "accent_url_blue":["--purple"],
        "border":         ["--border"],
    }
    rules: list[str] = []
    fonts_display = tokens.get("font_display") or tokens.get("font_body")
    if fonts_display:
        rules.append(f"  --font: {fonts_display};")
    for tk, val in tokens.items():
        if tk in mapping and isinstance(val, str):
            for css_var in mapping[tk]:
                rules.append(f"  {css_var}: {val};")
    if not rules:
        return ""
    return (
        "<style id=\"kb-design-tokens\">\n"
        ":root {\n" + "\n".join(rules) + "\n}\n"
        "body { background: var(--bg); color: var(--text); }\n"
        "</style>\n"
    )


# ---------------------------------------------------------------------------
# Main import
# ---------------------------------------------------------------------------

def slide_key(slide_id: str) -> str:
    """Normalize a slide id (e.g. '01-title') for keying speaker notes."""
    return slide_id.strip().lower()


def parse_slide(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)
    notes = extract_speaker_notes(body)
    # Strip the speaker notes / visual notes / asset needs / fallback sections
    # from the body before extracting title/subtitle/bullets so they don't
    # leak in.
    body_for_content = re.split(
        r"^##\s+(Speaker\s+Notes|Visual\s+notes|Asset\s+needs|Fallback)\b",
        body, maxsplit=1, flags=re.IGNORECASE | re.MULTILINE,
    )[0]
    title = first_title(body_for_content)
    subtitle = first_paragraph_after_title(body_for_content)
    bullets = extract_bullets(body_for_content, limit=6)
    return {
        "id":       path.stem,
        "title":    title or path.stem,
        "subtitle": subtitle,
        "bullets":  bullets,
        "notes":    notes,
        "_layout":  fm.get("layout", ""),
        "_speaker": fm.get("speaker", ""),
        "_section": fm.get("section", ""),
        "_duration_sec": fm.get("duration_sec", ""),
        "_experiment":   fm.get("experiment", ""),
    }


def build_sections(deck_dir: Path, manifest: dict) -> tuple[list, dict, dict]:
    """Build the SECTIONS list plus speaker_notes/speakers dicts."""
    validate_kb_manifest(manifest)
    slides_dir = deck_dir / "slides"
    # Index every slide file by stem
    slide_files = {p.stem: p for p in sorted(slides_dir.glob("*.md"))}

    sections_out: list[dict] = []
    notes_map: dict[str, str] = {}
    speakers_map: dict[str, str] = {}

    for idx, sec in enumerate(manifest.get("sections", [])):
        section_name = sec.get("section", f"Section {idx+1}")
        slide_ids = sec.get("slides", [])
        slides = []
        for sid in slide_ids:
            p = slide_files.get(sid)
            if not p:
                # Try fuzzy match (e.g. id without leading zero or extension)
                matches = [v for k, v in slide_files.items() if k.startswith(sid)]
                if len(matches) == 1:
                    p = matches[0]
                elif len(matches) > 1:
                    raise ImportInputError(
                        f"KB slide id '{sid}' is ambiguous ({len(matches)} matches)"
                    )
            if not p:
                raise ImportInputError(
                    f"KB section '{section_name}' references missing slide '{sid}'"
                )
            slides.append(parse_slide(p))

        if not slides:
            continue

        # Lesson card from first slide
        first = slides[0]
        speakers_in_sec = []
        seen = set()
        for s in slides:
            sp = s["_speaker"]
            if sp and sp not in seen:
                seen.add(sp)
                speakers_in_sec.append(sp)

        accent = ACCENT_CYCLE[idx % len(ACCENT_CYCLE)]
        # Honor `accent` field if present in manifest
        if isinstance(sec.get("accent"), str):
            accent = sec["accent"]

        lesson = {
            "title":   first["title"],
            "short":   re.sub(r"-", " ", section_name).upper(),
            "tagline": first["subtitle"] or first["title"],
            "tags":    " · ".join(speakers_in_sec) if speakers_in_sec else "",
            "notes":   first["notes"],
            "_speaker": first["_speaker"],
            "_layout": first["_layout"],
            "_id": first["id"],
        }
        cases = []
        for s in slides[1:]:
            cases.append({
                "title":    s["title"],
                "subtitle": s["subtitle"],
                "bullets":  s["bullets"] or [s["subtitle"]] if s["subtitle"] else [],
                "notes":    s["notes"],
                "_speaker": s["_speaker"],
                "_layout":  s["_layout"],
                "_id":      s["id"],
            })
            notes_map[slide_key(s["id"])] = s["notes"]
            speakers_map[slide_key(s["id"])] = s["_speaker"]

        # Also record notes/speakers for the lesson (first) slide
        notes_map[slide_key(first["id"])] = first["notes"]
        speakers_map[slide_key(first["id"])] = first["_speaker"]

        sections_out.append({
            "year":   f"CH {idx+1}",
            "accent": accent,
            "lesson": lesson,
            "cases":  cases,
            "_section_name": section_name,
            "_first_slide_id": first["id"],
            "_first_slide_layout": first["_layout"],
        })

    return sections_out, notes_map, speakers_map


def render_sections_js(sections: list) -> str:
    """Render the SECTIONS array as JS. Uses JSON for safety, then converts
    to JS-style (the template's existing array is JSON-compatible already)."""
    # Strip leading/trailing underscored keys for cleanliness — but the
    # template's renderer ignores unknown keys, and we WANT _layout/_speaker
    # available for color-coding. So we leave them in.
    payload = json.dumps(sections, ensure_ascii=False, indent=2)
    return f"const SECTIONS = {payload};"


def build_speaker_notes_js(notes_map: dict, speakers_map: dict) -> str:
    notes_json    = json.dumps(notes_map, ensure_ascii=False)
    speakers_json = json.dumps(speakers_map, ensure_ascii=False)
    return (
        "<script id=\"kb-speaker-data\">\n"
        f"window._deckSpeakerNotes = {notes_json};\n"
        f"window._deckSpeakers = {speakers_json};\n"
        "</script>\n"
    )


def patch_template(template_html: str, *,
                   title: str,
                   cover_title: str | None,
                   cover_subtitle: str | None,
                   sections_js: str,
                   tokens_css: str,
                   speaker_data_js: str,
                   styling_css: str) -> str:
    html = template_html

    # 1. Replace SECTIONS array
    s, e = find_sections_array(html)
    html = html[:s] + sections_js + html[e:]

    # 2. Update <title>
    html = re.sub(
        r"<title>[^<]*</title>",
        f"<title>{_html_escape(title)}</title>",
        html, count=1,
    )

    # 3. Update cover slide title (cov.innerHTML = `...<h1 class="talk-title">...`)
    if cover_title:
        # Replace the first .talk-title content. We use a multiline regex.
        cover_title_html = "<br>".join(
            _html_escape(part) for part in cover_title.split("<br>")
        )
        html = re.sub(
            r'(<h1 class="talk-title">)[^<]*(?:<br>[^<]*)*(</h1>)',
            lambda m: f'{m.group(1)}{cover_title_html}{m.group(2)}',
            html, count=1,
        )
    if cover_subtitle:
        sub_html = _html_escape(cover_subtitle)
        html = re.sub(
            r'(<p class="talk-subtitle">)[^<]*(</p>)',
            lambda m: f'{m.group(1)}{sub_html}{m.group(2)}',
            html, count=1,
        )

    # 4. Inject design-tokens CSS, speaker-styling CSS, speaker-data JS
    inject = ""
    if tokens_css:
        inject += tokens_css
    if styling_css:
        inject += f"<style id=\"kb-speaker-styling\">\n{styling_css}\n</style>\n"
    if speaker_data_js:
        inject += speaker_data_js
    # Inject right before </head>
    html = html.replace("</head>", inject + "</head>", 1)

    # 5. Add a tiny JS shim that stamps data-speaker on each rendered slide,
    #    mapped from window._deckSpeakers by slide id (matched via title).
    shim = (
        "<script id=\"kb-speaker-shim\">\n"
        "(function(){\n"
        "  function apply(){\n"
        "    var sections = (typeof SECTIONS!=='undefined') ? SECTIONS : [];\n"
        "    var slides = document.querySelectorAll('#deck .slide');\n"
        "    var idx = 0;\n"
        "    // First slide is cover\n"
        "    idx = 1;\n"
        "    sections.forEach(function(sec){\n"
        "      // Lesson slide gets first slide's speaker\n"
        "      var firstCase = sec.cases && sec.cases[0];\n"
        "      var lessonSlide = slides[idx]; idx++;\n"
        "      if (lessonSlide && firstCase && firstCase._speaker){ lessonSlide.setAttribute('data-speaker', firstCase._speaker); }\n"
        "      (sec.cases||[]).forEach(function(c){\n"
        "        var sl = slides[idx]; idx++;\n"
        "        if (sl && c._speaker){ sl.setAttribute('data-speaker', c._speaker); }\n"
        "        if (sl && c._layout){ sl.setAttribute('data-layout', c._layout); }\n"
        "      });\n"
        "    });\n"
        "  }\n"
        "  if (document.readyState === 'loading') {\n"
        "    document.addEventListener('DOMContentLoaded', function(){ setTimeout(apply, 50); });\n"
        "  } else { setTimeout(apply, 50); }\n"
        "})();\n"
        "</script>\n"
    )
    # Replace the LAST </body> — the template's engine script contains
    # `</body>` inside a document.write template literal which would otherwise
    # be matched first.
    last_body = html.rfind("</body>")
    if last_body >= 0:
        html = html[:last_body] + shim + html[last_body:]

    return html


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )


def detect_source_format(deck_dir: Path, requested: str) -> str:
    has_kb = (deck_dir / "slides").is_dir()
    has_fmx = (deck_dir / "slides.md").is_file()
    if requested == "kb":
        if not has_kb:
            raise ImportInputError("KB format requires a slides/ directory")
        return "kb"
    if requested == "fmx":
        if not has_fmx:
            raise ImportInputError("FMX format requires slides.md")
        return "fmx"
    if has_kb and has_fmx:
        raise ImportInputError(
            "both slides/ and slides.md exist; pass --format kb or --format fmx"
        )
    if has_kb:
        return "kb"
    if has_fmx:
        return "fmx"
    raise ImportInputError(
        "could not detect deck format (expected slides/ or slides.md)"
    )


def load_manifest(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ImportInputError(
            f"malformed SECTIONS.json at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("deck_dir", type=Path,
                    help="Deck dir containing SECTIONS.json and slides/ or slides.md")
    ap.add_argument("--out", required=True, type=Path, help="Output HTML path")
    ap.add_argument("--format", choices=("auto", "kb", "fmx"), default="auto",
                    help="Input format (default: auto-detect from slides/ or slides.md)")
    ap.add_argument("--title", default=None, help="Override deck title (defaults to manifest title)")
    ap.add_argument("--template", type=Path, default=None,
                    help="Spatial Deck template index.html (defaults to repo's index.html)")
    args = ap.parse_args()

    deck_dir: Path = args.deck_dir.resolve()
    if not deck_dir.is_dir():
        print(f"error: deck_dir not found: {deck_dir}", file=sys.stderr)
        return 2
    manifest_path = deck_dir / "SECTIONS.json"
    if not manifest_path.is_file():
        print(f"error: missing SECTIONS.json in {deck_dir}", file=sys.stderr)
        return 2
    try:
        source_format = detect_source_format(deck_dir, args.format)
        manifest = load_manifest(manifest_path)
        if source_format == "kb":
            validate_kb_manifest(manifest)
        else:
            validate_fmx_manifest(manifest)
    except (ImportInputError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    template_path: Path
    if args.template:
        template_path = args.template.resolve()
    else:
        template_path = (Path(__file__).resolve().parent.parent / "index.html")
    if not template_path.is_file():
        print(f"error: template not found: {template_path}", file=sys.stderr)
        return 2
    template_html = template_path.read_text(encoding="utf-8")

    metadata = manifest if isinstance(manifest, dict) else {}
    title = args.title or metadata.get("title") or deck_dir.name
    subtitle = metadata.get("subtitle") or ""
    variant = metadata.get("variant") or deck_dir.name

    try:
        if source_format == "kb":
            sections, notes_map, speakers_map = build_sections(deck_dir, manifest)
            cover_title = metadata.get("title") or ""
            editorial_count = sum(1 + len(section["cases"]) for section in sections)
        else:
            slides_path = deck_dir / "slides.md"
            sections, notes_map, speakers_map, cover = build_fmx_sections(
                manifest, slides_path.read_text(encoding="utf-8")
            )
            cover_title = cover["title"]
            subtitle = subtitle or cover["subtitle"]
            title = args.title or cover_title.replace("<br>", " — ") or deck_dir.name
            editorial_count = cover["editorial_count"]
    except (ImportInputError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    sections_js = render_sections_js(sections)
    tokens_css  = build_design_token_css(metadata.get("design_tokens") or {})
    speaker_data_js = build_speaker_notes_js(notes_map, speakers_map)

    # Speaker styling CSS — read from sibling file if present
    styling_css = ""
    styling_path = Path(__file__).resolve().parent / "_kb_speaker_styling.css"
    if styling_path.is_file():
        styling_css = styling_path.read_text(encoding="utf-8")

    # If title is the long form, split on ":" to get the headline + subtitle
    if cover_title and ":" in cover_title:
        head, _, tail = cover_title.partition(":")
        cover_title = head.strip()
        if not subtitle:
            subtitle = tail.strip()

    out_html = patch_template(
        template_html,
        title=title,
        cover_title=cover_title,
        cover_subtitle=subtitle or f"{variant} variant",
        sections_js=sections_js,
        tokens_css=tokens_css,
        speaker_data_js=speaker_data_js,
        styling_css=styling_css,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(out_html, encoding="utf-8")

    total_slides = sum(1 + len(s["cases"]) for s in sections)
    print(
        f"[ok] format={source_format}  variant={variant}  "
        f"sections={len(sections)}  slides={total_slides}  "
        f"editorial={editorial_count}  -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""HTML response formatter — self-contained dark-themed HTML with inline CSS.

Used by the Deal agent to format responses for the UI.
"""

from __future__ import annotations

import html

import markdown


def format_agent_response(
    content: str,
    confidence_level: str | None,
    assumptions: str | None,
    calculations: list[dict] | None,
    citations: list[dict] | None,
    suggested_questions: list[str] | None,
) -> str:
    """Convert structured agent output into fully styled HTML."""
    clean_content = content.replace("\\n", "\n") if "\\n" in content else content
    md_html = markdown.markdown(clean_content, extensions=["tables", "fenced_code"])

    parts: list[str] = [_CSS, '<div class="di-wrapper">']
    parts.append(f'<div class="di-content">{md_html}</div>')

    if citations:
        badges = _citation_badges(citations)
        if badges:
            parts.append(badges)

    if confidence_level:
        parts.append(_confidence_badge(confidence_level))

    buttons: list[str] = []
    if calculations:
        buttons.append(_expandable("Show Calculations", _calc_table(calculations), "calc"))
    if citations:
        buttons.append(_expandable("View Source Text", _source_texts(citations), "source"))
    if assumptions:
        buttons.append(_expandable("Assumptions", f"<p>{html.escape(assumptions)}</p>", "assume"))
    if buttons:
        parts.append(f'<div class="di-buttons">{"".join(buttons)}</div>')

    if suggested_questions:
        chips = "".join(f'<div class="di-chip">{html.escape(q)}</div>' for q in suggested_questions)
        parts.append(f'<div class="di-questions"><div class="di-qlabel">Related questions</div><div class="di-chips">{chips}</div></div>')

    parts.append("</div>")
    return "\n".join(parts)


def _citation_badges(citations: list[dict]) -> str:
    seen: set[str] = set()
    badges: list[str] = []
    for c in citations:
        page = c.get("page_number") or ""
        section = c.get("section_name") or ""
        key = f"{section}:{page}"
        if key in seen:
            continue
        seen.add(key)
        label = f"{section}, p.{page}" if section else f"p.{page}"
        badges.append(f'<span class="di-badge">[{html.escape(str(label))}]</span>')
    return f'<div class="di-badges">{" ".join(badges)}</div>' if badges else ""


def _confidence_badge(level: str) -> str:
    colors = {"high": ("#00c864", "rgba(0,200,100,0.1)"), "medium": ("#ffc800", "rgba(255,200,0,0.1)"), "low": ("#ff5050", "rgba(255,80,80,0.1)")}
    fg, bg = colors.get(level, ("#888", "rgba(136,136,136,0.1)"))
    return f'<div style="display:inline-flex;align-items:center;gap:8px;padding:6px 14px;border-radius:20px;font-size:13px;margin:12px 0;background:{bg};color:{fg}"><strong>{level.capitalize()}</strong> Confidence</div>'


def _expandable(title: str, inner: str, kind: str) -> str:
    bg = {"calc": "#00897b", "source": "#0288d1", "assume": "#7b1fa2"}.get(kind, "#555")
    return f'<details class="di-expand"><summary style="background:{bg};color:#fff;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:13px">{html.escape(title)}</summary><div class="di-expand-body">{inner}</div></details>'


def _calc_table(calculations: list[dict]) -> str:
    rows = ""
    for c in calculations:
        f = html.escape(str(c.get("formula", "")))
        i = html.escape(", ".join(f"{k}={v}" for k, v in c.get("inputs", {}).items()))
        r = c.get("result", "")
        u = c.get("unit", "")
        rows += f"<tr><td>{f}</td><td>{i}</td><td><strong>{r}{u}</strong></td></tr>"
    return f'<table><thead><tr><th>Formula</th><th>Inputs</th><th>Result</th></tr></thead><tbody>{rows}</tbody></table>'


def _source_texts(citations: list[dict]) -> str:
    items: list[str] = []
    for c in citations:
        src = c.get("source_text") or ""
        if not src:
            continue
        sec = c.get("section_name") or "Source"
        pg = c.get("page_number") or ""
        items.append(f'<div class="di-src-item"><strong>{html.escape(str(sec))} (p.{pg})</strong><p style="font-size:12px">{html.escape(str(src)[:200])}</p></div>')
    return "".join(items) if items else "<p>No source text available.</p>"


_CSS = """<style>
.di-wrapper{font-family:'Inter',sans-serif;color:#e0e0e0;background:#1e2028;padding:24px;border-radius:10px;line-height:1.7;max-width:900px}
.di-content h1,.di-content h2{color:#fff;font-size:17px;margin:18px 0 10px;border-bottom:1px solid #333;padding-bottom:6px}
.di-content h3{color:#4dd0e1;font-size:15px;margin:16px 0 8px}
.di-content p{margin:8px 0;color:#c8c8c8;font-size:14px}
.di-content table{width:100%;border-collapse:collapse;margin:12px 0;background:#252830;border-radius:6px}
.di-content th{background:#2d3748;color:#4dd0e1;padding:10px 14px;text-align:left;font-size:13px}
.di-content td{padding:8px 14px;border-top:1px solid #333;color:#d0d0d0;font-size:13px}
.di-badges{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
.di-badge{background:#2d3748;color:#90cdf4;padding:4px 10px;border-radius:4px;font-size:12px}
.di-buttons{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}
.di-expand{display:inline-block}
.di-expand-body{background:#252830;padding:14px;border-radius:6px;margin-top:8px;font-size:13px}
.di-questions{margin:20px 0}
.di-qlabel{color:#888;font-size:13px;margin-bottom:10px}
.di-chips{display:flex;flex-wrap:wrap;gap:8px}
.di-chip{background:#252830;color:#90cdf4;border:1px solid #3d4758;padding:8px 14px;border-radius:20px;font-size:12px;cursor:pointer}
</style>"""

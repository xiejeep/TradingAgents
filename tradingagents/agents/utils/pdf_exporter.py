import os
import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Optional


_UNSAFE_CHAR_MAP = {
    "\u2460": "(1)", "\u2461": "(2)", "\u2462": "(3)", "\u2463": "(4)",
    "\u2464": "(5)", "\u2465": "(6)", "\u2466": "(7)", "\u2467": "(8)",
    "\u2468": "(9)", "\u2469": "(10)",
    "\u25a0": "#", "\u25a1": "[ ]", "\u25b2": "^", "\u25b3": "^",
    "\u25bc": "v", "\u25bd": "v", "\u25c6": "<>", "\u25c7": "<>",
    "\u2605": "*", "\u2606": "*", "\u25cf": "*", "\u25cb": "o",
    "\u2192": "->", "\u2190": "<-", "\u2191": "^", "\u2193": "v",
    "\u2194": "<->", "\u21d2": "=>", "\u21d4": "<=>", "\u21b5": "<-",
    "\u2713": "[v]", "\u2717": "[x]",
    "\u2610": "[ ]", "\u2611": "[x]", "\u2612": "[x]",
    "\u26a0": "!!", "\u26a1": "!!",
    "\u2b06": "^", "\u2b07": "v", "\u27a1": "->",
    "\u2705": "[OK]", "\u274c": "[X]", "\u2b50": "*",
    "\u2500": "-", "\u2502": "|",
    "\ufe0f": "",
    "\u20e3": "",
    "\u200b": "",
    "\u00a0": " ",
    "\u3000": " ",
    "\u2014": "--",
    "\u2018": "'", "\u2019": "'",
    "\u201c": "\"", "\u201d": "\"",
    "\u2026": "...",
    "\u2260": "!=",
    "\u03b2": "beta",
    "\u300a": "<<", "\u300b": ">>",
}

_SAFE_CATEGORIES = {
    "Lu", "Ll", "Lt", "Lm", "Lo",
    "Mn", "Mc", "Me",
    "Nd", "Nl", "No",
    "Pc", "Pd", "Ps", "Pe", "Pi", "Pf", "Po",
    "Zs", "Zl",
}

_EXPLICIT_MAP_PATTERN = re.compile(
    "[" + "".join(re.escape(c) for c in _UNSAFE_CHAR_MAP) + "]"
)


def _sanitize_text(text: str) -> str:
    text = _EXPLICIT_MAP_PATTERN.sub(lambda m: _UNSAFE_CHAR_MAP.get(m.group(), ""), text)

    def _filter_char(c: str) -> str:
        cp = ord(c)
        if cp < 128:
            return c
        if 0x4E00 <= cp <= 0x9FFF:
            return c
        if 0x3400 <= cp <= 0x4DBF:
            return c
        if 0xF900 <= cp <= 0xFAFF:
            return c
        if 0xFF01 <= cp <= 0xFF5E:
            return chr(cp - 0xFEE0)
        if 0xFF5F <= cp <= 0xFFEF:
            return c
        if 0x3000 <= cp <= 0x303F:
            return c
        if 0x3040 <= cp <= 0x30FF:
            return c
        if 0x2000 <= cp <= 0x206F:
            return c
        if 0x0080 <= cp <= 0x024F:
            return c
        if 0x0400 <= cp <= 0x04FF:
            return c
        if 0x010000 <= cp:
            return ""
        cat = unicodedata.category(c)
        if cat in _SAFE_CATEGORIES:
            return c
        return ""

    return "".join(_filter_char(c) for c in text)


_CJK_FONT_SEARCH_PATHS = [
    "/System/Library/Fonts",
    "/System/Library/Fonts/Supplemental",
    "/Library/Fonts",
    os.path.expanduser("~/Library/Fonts"),
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    "C:\\Windows\\Fonts",
]

_CJK_FONT_NAMES = [
    "PingFang.ttc",
    "STHeiti Medium.ttc",
    "STHeiti Light.ttc",
    "Songti.ttc",
    "NotoSansSC-Regular.otf",
    "NotoSansCJKsc-Regular.otf",
    "NotoSansMonoCJKsc-Regular.otf",
    "NotoSansSC-Regular.ttf",
    "NotoSansCJK-Regular.ttc",
    "SourceHanSansSC-Regular.otf",
    "SimSun.ttf",
    "SimHei.ttf",
    "MSYH.ttf",
    "msyh.ttf",
    "msyhbd.ttf",
    "wqy-microhei.ttc",
    "wqy-zenhei.ttc",
    "DroidSansFallback.ttf",
]


def _find_cjk_font() -> Optional[str]:
    for base in _CJK_FONT_SEARCH_PATHS:
        if not os.path.isdir(base):
            continue
        for root, _dirs, files in os.walk(base):
            for name in _CJK_FONT_NAMES:
                if name in files:
                    return os.path.join(root, name)
    return None


def _markdown_to_plain_text(md_content: str) -> str:
    text = md_content
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"!\[.*?\]\([^)]+\)", "", text)
    text = re.sub(r"^\s*[-*+]\s+", "  \u2022 ", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "  ", text, flags=re.MULTILINE)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\|.*\|", "", text)
    text = re.sub(r"---+", "\u2014" * 20, text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def export_report_to_pdf(
    markdown_content: str,
    ticker: str,
    output_path: Optional[str] = None,
) -> str:
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError(
            "fpdf2 is required for PDF export. Install it with: pip install fpdf2"
        )

    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".pdf", prefix=f"report_{ticker}_")
        os.close(fd)

    cjk_font_path = _find_cjk_font()

    pdf = FPDF()
    pdf.set_margins(left=15, top=15, right=15)
    pdf.set_auto_page_break(auto=True, margin=20)

    if cjk_font_path:
        try:
            pdf.add_font("CJK", "", cjk_font_path)
            pdf.add_font("CJK", "B", cjk_font_path)
            font_name = "CJK"
            title_font = "CJK"
            title_style = "B"
        except Exception:
            font_name = "Helvetica"
            title_font = "Helvetica"
            title_style = "B"
    else:
        font_name = "Helvetica"
        title_font = "Helvetica"
        title_style = "B"

    pdf.add_page()

    plain_text = _sanitize_text(_markdown_to_plain_text(markdown_content))
    sections = [s.strip() for s in re.split(r"\n(?=## )", plain_text) if s.strip()]

    for section in sections:
        lines = section.split("\n")
        if not lines:
            continue

        heading_match = re.match(r"^#+\s+(.+)", lines[0])
        body_lines = [l for l in (lines[1:] if heading_match else lines) if l.strip()]

        if heading_match:
            pdf.set_font(title_font, title_style, 14)
            pdf.multi_cell(0, 8, heading_match.group(1))
            pdf.x = pdf.l_margin
            pdf.ln(4)

        pdf.set_font(font_name, "", 10)
        for line in body_lines:
            if line.strip():
                pdf.multi_cell(0, 6, line)
                pdf.x = pdf.l_margin
        pdf.ln(6 if heading_match else 4)

    pdf.output(output_path)
    return output_path


def export_report_file_to_pdf(report_dir: str, output_path: Optional[str] = None) -> str:
    report_path = Path(report_dir) / "complete_report.md"
    if not report_path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    markdown_content = report_path.read_text(encoding="utf-8")
    ticker = Path(report_dir).name.split("_")[0]

    return export_report_to_pdf(
        markdown_content=markdown_content,
        ticker=ticker,
        output_path=output_path,
    )

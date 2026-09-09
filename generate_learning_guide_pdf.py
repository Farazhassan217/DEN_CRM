"""Convert Dental_CRM_Backend_Technical_Learning_Guide.md to a styled PDF."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
MD_PATH = ROOT / "documents" / "Dental_CRM_Backend_Technical_Learning_Guide.md"
OUT_PATH = ROOT / "documents" / "Dental_CRM_Backend_Technical_Learning_Guide.pdf"

PRIMARY = colors.HexColor("#0F172A")
SECONDARY = colors.HexColor("#0284C7")
TEXT_DARK = colors.HexColor("#1E293B")
TEXT_MUTED = colors.HexColor("#475569")
BG_CODE = colors.HexColor("#F1F5F9")
BG_TABLE_HEADER = colors.HexColor("#0F172A")
BG_TABLE_ALT = colors.HexColor("#F8FAFC")
BORDER = colors.HexColor("#CBD5E1")
WHITE = colors.white

WIN_FONTS = Path(r"C:\Windows\Fonts")


def register_fonts() -> dict[str, str]:
    mapping = {
        "body": "Helvetica",
        "body_bold": "Helvetica-Bold",
        "code": "Courier",
        "code_bold": "Courier-Bold",
    }
    candidates = [
        ("body", WIN_FONTS / "segoeui.ttf"),
        ("body_bold", WIN_FONTS / "segoeuib.ttf"),
        ("code", WIN_FONTS / "consola.ttf"),
        ("code_bold", WIN_FONTS / "consolab.ttf"),
    ]
    for key, path in candidates:
        if path.exists():
            name = f"Guide{key.title().replace('_', '')}"
            pdfmetrics.registerFont(TTFont(name, str(path)))
            mapping[key] = name
    return mapping


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        if self._pageNumber > 1:
            self.drawString(36, 756, "Dental CRM — Backend Technical Documentation & Learning Guide")
            self.setStrokeColor(BORDER)
            self.setLineWidth(0.5)
            self.line(36, 750, letter[0] - 36, 750)
        self.setStrokeColor(BORDER)
        self.setLineWidth(0.5)
        self.line(36, 45, letter[0] - 36, 45)
        self.drawString(36, 32, "Confidential — Dental CRM Engineering | Generated: September 2026")
        self.drawRightString(letter[0] - 36, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


BOX_MAP = str.maketrans(
    {
        "┌": "+",
        "┐": "+",
        "└": "+",
        "┘": "+",
        "─": "-",
        "│": "|",
        "┬": "+",
        "┴": "+",
        "┼": "+",
        "├": "+",
        "┤": "+",
        "►": ">",
        "▼": "v",
        "•": "*",
        "–": "-",
        "—": "--",
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "…": "...",
        "·": "-",
    }
)


def sanitize_pre(text: str) -> str:
    return text.translate(BOX_MAP)


def inline_md(text: str) -> str:
    placeholders: list[str] = []

    def _stash_code(match: re.Match) -> str:
        placeholders.append(html.escape(match.group(1)))
        return f"@@CODE{len(placeholders) - 1}@@"

    text = re.sub(r"`([^`]+)`", _stash_code, text)
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    for idx, code in enumerate(placeholders):
        text = text.replace(
            f"@@CODE{idx}@@",
            f'<font face="Courier" size="8" color="#0F172A"><b>{code}</b></font>',
        )
    return text.replace("\n", " ")


def split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def is_table_sep(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells if c)


def build_styles(fonts: dict[str, str]) -> dict:
    styles = getSampleStyleSheet()
    return {
        "cover_kicker": ParagraphStyle(
            "CoverKicker",
            parent=styles["Normal"],
            fontName=fonts["body_bold"],
            fontSize=9,
            textColor=SECONDARY,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=styles["Normal"],
            fontName=fonts["body_bold"],
            fontSize=22,
            leading=28,
            textColor=PRIMARY,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "cover_sub": ParagraphStyle(
            "CoverSub",
            parent=styles["Normal"],
            fontName=fonts["body"],
            fontSize=12,
            leading=16,
            textColor=SECONDARY,
            alignment=TA_CENTER,
            spaceAfter=18,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=styles["Normal"],
            fontName=fonts["body_bold"],
            fontSize=14,
            leading=18,
            textColor=PRIMARY,
            spaceBefore=16,
            spaceAfter=8,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=styles["Normal"],
            fontName=fonts["body_bold"],
            fontSize=11.5,
            leading=15,
            textColor=SECONDARY,
            spaceBefore=12,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=styles["Normal"],
            fontName=fonts["body_bold"],
            fontSize=10.5,
            leading=14,
            textColor=TEXT_DARK,
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName=fonts["body"],
            fontSize=9.5,
            leading=13.5,
            textColor=TEXT_DARK,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=styles["Normal"],
            fontName=fonts["body"],
            fontSize=9.5,
            leading=13,
            textColor=TEXT_MUTED,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=styles["Normal"],
            fontName=fonts["body"],
            fontSize=9.5,
            leading=13,
            textColor=TEXT_DARK,
            leftIndent=14,
            bulletIndent=2,
            spaceAfter=3,
        ),
        "th": ParagraphStyle(
            "TH",
            parent=styles["Normal"],
            fontName=fonts["body_bold"],
            fontSize=8,
            leading=11,
            textColor=WHITE,
        ),
        "td": ParagraphStyle(
            "TD",
            parent=styles["Normal"],
            fontName=fonts["body"],
            fontSize=8,
            leading=11,
            textColor=TEXT_DARK,
        ),
        "code": ParagraphStyle(
            "CodePre",
            parent=styles["Code"],
            fontName=fonts["code"],
            fontSize=6.5,
            leading=8.5,
            textColor=PRIMARY,
            backColor=BG_CODE,
            leftIndent=4,
            rightIndent=4,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=styles["Normal"],
            fontName=fonts["body"],
            fontSize=8,
            textColor=TEXT_MUTED,
            spaceAfter=8,
        ),
    }


def safe_paragraph(text: str, style) -> Paragraph:
    markup = inline_md(text)
    try:
        return Paragraph(markup, style)
    except Exception:
        return Paragraph(html.escape(sanitize_pre(text)), style)


def make_table(rows: list[list[str]], styles: dict, col_width_total: float) -> Table:
    header = [safe_paragraph(c, styles["th"]) for c in rows[0]]
    body = [[safe_paragraph(c, styles["td"]) for c in row] for row in rows[1:]]
    data = [header] + body
    n = len(rows[0])
    col_w = col_width_total / max(n, 1)
    tbl = Table(data, colWidths=[col_w] * n, repeatRows=1)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BG_TABLE_HEADER),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("BACKGROUND", (0, 1), (-1, -1), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, BG_TABLE_ALT]),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tbl


def parse_markdown(md: str, styles: dict, usable_width: float) -> list:
    story: list = []
    lines = md.splitlines()
    i = 0
    first_h1 = True

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width="100%", thickness=0.6, color=BORDER, spaceAfter=8))
            i += 1
            continue

        if stripped.startswith("```"):
            fence = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                fence.append(lines[i])
                i += 1
            i += 1
            code = sanitize_pre("\n".join(fence))
            if not code.strip():
                continue
            block = Preformatted(code, styles["code"])
            wrapped = Table([[block]], colWidths=[usable_width])
            wrapped.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), BG_CODE),
                        ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(wrapped)
            story.append(Spacer(1, 8))
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and is_table_sep(lines[i + 1]):
            header = split_table_row(stripped)
            i += 2
            rows = [header]
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_table_row(lines[i]))
                i += 1
            story.append(make_table(rows, styles, usable_width))
            story.append(Spacer(1, 8))
            continue

        if stripped.startswith("# "):
            title = stripped[2:].strip()
            if first_h1:
                story.append(Spacer(1, 24))
                story.append(Paragraph("DENTAL CRM  ·  den_crm", styles["cover_kicker"]))
                story.append(safe_paragraph(title, styles["cover_title"]))
                first_h1 = False
            else:
                story.append(safe_paragraph(title, styles["h1"]))
            i += 1
            continue

        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            if first_h1 is False and heading.startswith("Technical Documentation"):
                story.append(safe_paragraph(heading, styles["cover_sub"]))
            else:
                story.append(safe_paragraph(heading, styles["h2"]))
            i += 1
            continue

        if stripped.startswith("### "):
            story.append(safe_paragraph(stripped[4:].strip(), styles["h3"]))
            i += 1
            continue

        numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if numbered:
            story.append(safe_paragraph(f"{numbered.group(1)}. {numbered.group(2)}", styles["bullet"]))
            i += 1
            continue

        if stripped.startswith("- "):
            story.append(safe_paragraph(f"• {stripped[2:]}", styles["bullet"]))
            i += 1
            continue

        # Meta lines at top often start with **Audience**
        style_name = "meta" if stripped.startswith("**Audience") or stripped.startswith("**Stack") or stripped.startswith("**API") or stripped.startswith("**Source") else "body"
        story.append(safe_paragraph(stripped, styles[style_name]))
        i += 1

    return story


def build_pdf() -> Path:
    fonts = register_fonts()
    styles = build_styles(fonts)
    md = MD_PATH.read_text(encoding="utf-8")

    doc = SimpleDocTemplate(
        str(OUT_PATH),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=54,
        title="Dental CRM Backend Technical Documentation and Learning Guide",
        author="Dental CRM Engineering",
    )
    usable = letter[0] - 72
    story = parse_markdown(md, styles, usable)
    doc.build(story, canvasmaker=NumberedCanvas)
    return OUT_PATH


if __name__ == "__main__":
    path = build_pdf()
    print(f"Wrote {path} ({path.stat().st_size} bytes)")

"""Generate PDF change report for Dental CRM backend fixes."""

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUTPUT_PATH = Path(__file__).resolve().parent / "CHANGE_REPORT.pdf"


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1a365d"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            parent=styles["Normal"],
            fontSize=11,
            leading=14,
            spaceAfter=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4a5568"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            spaceBefore=14,
            spaceAfter=8,
            textColor=colors.HexColor("#2c5282"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyTextCustom",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            spaceAfter=6,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletCustom",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            leftIndent=14,
            spaceAfter=4,
            bulletIndent=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeBlock",
            parent=styles["Code"],
            fontSize=8.5,
            leading=11,
            backColor=colors.HexColor("#f7fafc"),
            borderColor=colors.HexColor("#e2e8f0"),
            borderWidth=1,
            borderPadding=6,
            spaceAfter=8,
        )
    )
    return styles


def add_section(story, styles, title, paragraphs=None, bullets=None):
    story.append(Paragraph(title, styles["SectionHeading"]))
    if paragraphs:
        for text in paragraphs:
            story.append(Paragraph(text, styles["BodyTextCustom"]))
    if bullets:
        for item in bullets:
            story.append(Paragraph(item, styles["BulletCustom"], bulletText="•"))
    story.append(Spacer(1, 0.15 * cm))


def add_table(story, headers, rows, col_widths=None):
    data = [headers] + rows
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5282")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.25 * cm))


def generate_pdf():
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Dental CRM Backend Change Report",
        author="Cursor Agent",
    )

    story = []
    today = datetime.now().strftime("%B %d, %Y")

    story.append(Paragraph("Dental CRM Backend", styles["ReportTitle"]))
    story.append(Paragraph("Complete Change Report (Roman English)", styles["ReportSubtitle"]))
    story.append(Paragraph(f"Generated on: {today}", styles["ReportSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e0")))
    story.append(Spacer(1, 0.4 * cm))

    add_section(
        story,
        styles,
        "1. Session Ka Maqsad (Purpose)",
        paragraphs=[
            "Pehle poora backend code review kiya gaya tha taake bugs mil sakein. "
            "Us review ke baad 3 main bugs fix kiye gaye, 1 naya file add ki gayi, "
            "debug/temporary code hata diya, aur Uvicorn port issue samjhaya/fix kiya.",
            "Yeh report usi bug review session ki detail hai.",
        ],
    )

    add_table(
        story,
        ["File", "Kya Change Hua", "Kyun"],
        [
            ["backend/app/api/ai.py", "Role bug fix + cleanup", "Super Admin AI endpoints se block ho rahe thay"],
            ["backend/app/database.py", "Env path fix + security fix", "Galat .env path + hardcoded DB password"],
            ["backend/app/core/config.py", "Debug code remove", "Temporary logging hata di"],
            ["backend/app/services/auth.py", "Debug prints remove + simplify login", "Passwords console par print ho rahe thay"],
            ["backend/requirements.txt", "Naya file add", "README ke mutabiq missing thi"],
        ],
        col_widths=[4.2 * cm, 5.2 * cm, 6.8 * cm],
    )

    add_section(
        story,
        styles,
        "2. Bug #1 — AI Role Check (Super Admin Block Ho Raha Tha)",
        paragraphs=[
            "<b>Problem:</b> backend/app/api/ai.py mein management roles list galat thi. "
            "Code mein 'superadmin' likha tha (bina underscore), jabke system mein actual role "
            "'super_admin' hai (underscore ke sath).",
            "Is wajah se Super Admin users AI management endpoints par 403 Forbidden mil raha tha, "
            "chahe wo logged in hon.",
        ],
        bullets=[
            "Pehle: MANAGEMENT_ROLES = ['superadmin', 'org_admin', 'clinic_manager']",
            "Baad mein: MANAGEMENT_ROLES = ['super_admin', 'org_admin', 'clinic_manager']",
            "Naya helper _normalize_role() add kiya taake UserRole enum bhi sahi match ho.",
            "require_role() ab role ko normalize karke compare karta hai.",
        ],
    )

    add_section(
        story,
        styles,
        "3. Bug #2 — Database Config (Security + Wrong .env Path)",
        paragraphs=[
            "<b>Problem A:</b> database.py repo root (den-orm/.env) se env load kar raha tha, "
            "jabke asal .env file backend/.env mein hai. config.py sahi path use karta tha, "
            "lekin database.py alag path use kar raha tha.",
            "<b>Problem B:</b> Agar DATABASE_URL na milta, code ek hardcoded Supabase PostgreSQL URL "
            "use karta tha jisme username/password source code mein likha tha. Yeh serious security bug tha.",
        ],
        bullets=[
            "BASE_DIR ab backend folder point karta hai (parent.parent).",
            "Hardcoded fallback URL hata diya.",
            "Ab DATABASE_URL required hai; missing hone par RuntimeError aata hai.",
            "<b>Important:</b> Purani credentials git history mein ho sakti hain. Supabase par password rotate karna chahiye.",
        ],
    )

    story.append(Paragraph("Fixed database.py logic:", styles["BodyTextCustom"]))
    story.append(
        Paragraph(
            "BASE_DIR = Path(__file__).resolve().parent.parent<br/>"
            "load_dotenv(BASE_DIR / '.env')<br/>"
            "SQLALCHEMY_DATABASE_URL = os.getenv('DATABASE_URL')<br/>"
            "if not SQLALCHEMY_DATABASE_URL: raise RuntimeError(...)",
            styles["CodeBlock"],
        )
    )

    add_section(
        story,
        styles,
        "4. Bug #3 — Missing requirements.txt",
        paragraphs=[
            "backend/README.md kehta tha: pip install -r requirements.txt, lekin file exist nahi karti thi.",
            "Aap ke virtual environment (.venv) se pip freeze karke naya file banaya gaya.",
            "Path: backend/requirements.txt (~73 packages: FastAPI, SQLAlchemy, Supabase, bcrypt, OpenAI/Gemini client, etc.)",
        ],
    )

    add_section(
        story,
        styles,
        "5. Cleanup — Debug Code Hata Diya",
        paragraphs=[
            "Bug hunt ke dauran temporary debug code add hua tha. Verification ke baad sab remove kar diya.",
        ],
        bullets=[
            "auth.py: Login ke waqt plain text password aur hash console par print ho rahe thay — ab clean secure flow hai.",
            "config.py: Temporary JSON debug logging hata di.",
            "ai.py: _agent_log, DEBUG_LOG_PATH, extra imports hata diye.",
        ],
    )

    story.append(Paragraph("Clean authenticate_user() flow:", styles["BodyTextCustom"]))
    story.append(
        Paragraph(
            "clean_email = email.lower().strip()<br/>"
            "user_with_pwd = await UserModel.get_by_email_with_password(clean_email)<br/>"
            "if not user_with_pwd or not user_with_pwd.password: return None<br/>"
            "if not _verify_password(password, user_with_pwd.password): return None<br/>"
            "return await UserModel.get_by_id(str(user_with_pwd.id))",
            styles["CodeBlock"],
        )
    )

    add_section(
        story,
        styles,
        "6. Uvicorn 'Not Running' Issue (Operational Fix)",
        paragraphs=[
            "<b>Error:</b> WinError 10013 — socket access forbidden.",
            "<b>Asal wajah:</b> Port 8000 pehle se occupied tha (purani Uvicorn process). Doosri instance start nahi ho sakti.",
        ],
        bullets=[
            "Port 8001 par server successfully start hua.",
            "Stale process port 8000 par kill kiya.",
            "Health check OK, login bhi 200 OK mil chuka hai.",
            "API docs: http://127.0.0.1:8001/scalar",
        ],
    )

    story.append(Paragraph("Start command:", styles["BodyTextCustom"]))
    story.append(
        Paragraph(
            "cd C:\\workfiles\\den-orm\\backend<br/>"
            "..\\.venv\\Scripts\\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000",
            styles["CodeBlock"],
        )
    )

    add_section(
        story,
        styles,
        "7. AI Endpoints Jo Fix Se Affect Hue",
        bullets=[
            "POST /api/v1/ai/prompts",
            "GET /api/v1/ai/prompts/active/{feature_name}",
            "POST /api/v1/ai/usage",
            "POST /api/v1/ai/automation-rules",
            "GET /api/v1/ai/automation-rules/{organization_id}",
            "POST /api/v1/ai/automation-runs",
            "POST /api/v1/ai/knowledge/documents",
            "POST /api/v1/ai/knowledge/chunks",
        ],
    )

    story.append(PageBreak())

    add_section(
        story,
        styles,
        "8. Jo Bugs Check Kiye Gaye Lekin Fix NAHI Kiye",
    )

    add_table(
        story,
        ["Issue", "Detail", "Status"],
        [
            ["bcrypt vs passlib", "Dono hash/verify sahi kaam kar rahe thay", "No fix needed"],
            ["Missing GEMINI_API_KEY", "Aap ke env mein key maujood thi", "No fix needed"],
            ["Gemini model name", "openai_service.py mein 'gemini-3.5-flash' — verify karo", "Open"],
            ["Frontend DATABASE_URL", "Next.js app bina env ke crash ho sakti hai", "Open"],
            ["Supabase table 'Users'", "Capital U — case-sensitive DB par issue ho sakta hai", "Open"],
            ["Old DB credentials in git", "Purana hardcoded URL history mein ho sakta hai", "Rotate credentials"],
        ],
        col_widths=[3.5 * cm, 8.5 * cm, 4.2 * cm],
    )

    add_section(
        story,
        styles,
        "9. Files Jo Change NAHI Hui",
        bullets=[
            "backend/app/main.py",
            "backend/app/services/openai_service.py",
            "backend/app/core/auth_utils.py",
            "backend/app/models/*",
            "backend/app/schemas/*",
            "Frontend (src/)",
        ],
    )

    add_section(
        story,
        styles,
        "10. Before vs After — Quick Comparison",
    )

    add_table(
        story,
        ["Area", "Pehle (Before)", "Baad (After)"],
        [
            ["Super Admin AI access", "403 Forbidden", "Allowed (valid token ke sath)"],
            ["Database env loading", "Galat path + hardcoded fallback", "backend/.env + required DATABASE_URL"],
            ["Login security", "Password console par print", "No debug output"],
            ["Dependencies file", "Missing", "requirements.txt added"],
            ["Uvicorn on 8000", "Port conflict", "Stale process killed; 8001 working"],
        ],
        col_widths=[4.5 * cm, 5.5 * cm, 6.2 * cm],
    )

    add_section(
        story,
        styles,
        "11. Recommended Next Steps",
        bullets=[
            "Supabase par database password rotate karo (purana hardcoded URL expose ho chuka tha).",
            "Super Admin se login karke AI endpoint test karo: GET /api/v1/ai/prompts/active/lead_summary",
            "Gemini model name verify karo: gemini-3.5-flash sahi hai ya nahi.",
            "Frontend ke liye .env.example add karo taake setup easy ho.",
        ],
    )

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e0")))
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        Paragraph(
            "End of Report — Dental CRM Backend Change Summary",
            styles["ReportSubtitle"],
        )
    )

    doc.build(story)
    return OUTPUT_PATH


if __name__ == "__main__":
    path = generate_pdf()
    print(f"PDF generated: {path}")

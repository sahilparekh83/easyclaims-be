import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

from fpdf import FPDF

MOCK_PDF = "/tmp/mock_policy.pdf"
PASS = "✓"
FAIL = "✗"

def create_mock_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in [
        "HEALTH INSURANCE POLICY",
        "Policy Number   : HLT-2024-098765",
        "Insured Name    : Rahul Sharma",
        "Insurer         : Star Health Insurance Co. Ltd.",
        "Sum Insured     : Rs. 5,00,000",
        "Policy Start    : 01-April-2025",
        "Policy End      : 31-March-2026",
    ]:
        pdf.cell(0, 10, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(MOCK_PDF)

def header(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def result(label, value):
    print(f"  {label:<22}: {value}")

# ─── Setup ────────────────────────────────────────────
create_mock_pdf()
print("\nMock PDF created. Starting agent tests...\n")

errors = []

# ─── Agent 1: Document Extractor ──────────────────────
header("1. DocumentExtractorAgent")
try:
    from app.agents.document_extractor import DocumentExtractorAgent
    extracted = DocumentExtractorAgent().extract(MOCK_PDF, policy_id="test-001")
    result("Policy Number", extracted.policy_number)
    result("Insured Name", extracted.insured_name)
    result("Insurer", extracted.insurer_name)
    result("Sum Insured", extracted.sum_insured)
    result("Start Date", extracted.start_date)
    result("End Date", extracted.end_date)
    result("Confidence", extracted.confidence)
    print(f"\n  {PASS} PASSED")
except Exception as e:
    print(f"  {FAIL} FAILED: {e}")
    errors.append("DocumentExtractorAgent")
    extracted = type("E", (), {
        "policy_number": "HLT-2024-098765", "insured_name": "Rahul Sharma",
        "insurer_name": "Star Health", "sum_insured": 500000.0,
        "start_date": "2025-04-01", "end_date": "2026-03-31", "confidence": 1.0
    })()

# ─── Agent 2: Doc Validator ───────────────────────────
header("2. DocValidatorAgent")
try:
    from app.agents.doc_validator import DocValidatorAgent
    validation = DocValidatorAgent().validate(
        extracted={
            "policy_number": extracted.policy_number,
            "insured_name": extracted.insured_name,
            "insurer_name": extracted.insurer_name,
            "sum_insured": extracted.sum_insured,
            "end_date": extracted.end_date,
            "confidence": extracted.confidence,
        },
        member_name="Rahul Sharma",
        policy_id="test-001",
    )
    result("Status", validation.status)
    result("Name Match", validation.name_match)
    result("Doc Type Valid", validation.document_type_valid)
    result("Not Expired", validation.not_expired)
    result("Reason", validation.reason)
    print(f"\n  {PASS} PASSED")
except Exception as e:
    print(f"  {FAIL} FAILED: {e}")
    errors.append("DocValidatorAgent")

# ─── Agent 3: Policy Q&A ──────────────────────────────
header("3. PolicyQAAgent")
try:
    from app.agents.policy_qa import PolicyQAAgent
    qa = PolicyQAAgent().answer(
        question="What is my sum insured and when does my policy expire?",
        policy_data={
            "policy_number": "HLT-2024-098765",
            "insurer": "Star Health Insurance",
            "sum_insured": 500000,
            "end_date": "2026-03-31",
        },
        membership_status="Active",
        membership_end="2026-06-30",
        language="English",
        member_id="member-001",
    )
    result("Answer", qa.answer[:100] + "..." if len(qa.answer) > 100 else qa.answer)
    result("Language", qa.language)
    print(f"\n  {PASS} PASSED")
except Exception as e:
    print(f"  {FAIL} FAILED: {e}")
    errors.append("PolicyQAAgent")

# ─── Agent 4: Claim Assistant ─────────────────────────
header("4. ClaimAssistantAgent")
try:
    from app.agents.claim_assistant import ClaimAssistantAgent
    claim = ClaimAssistantAgent().assist(
        claim_type="Health",
        incident_details="I was hospitalized on 10th June 2026 for dengue fever. Admitted for 3 days.",
        policy_data={"insurer": "Star Health", "sum_insured": 500000, "policy_number": "HLT-2024-098765"},
        language="English",
        member_id="member-001",
    )
    result("Incident Summary", claim.incident_summary[:80] + "...")
    result("Documents needed", len(claim.required_documents))
    for i, doc in enumerate(claim.required_documents, 1):
        print(f"    {i}. {doc}")
    result("Next Steps", claim.next_steps[:80] + "...")
    print(f"\n  {PASS} PASSED")
except Exception as e:
    print(f"  {FAIL} FAILED: {e}")
    errors.append("ClaimAssistantAgent")

# ─── Agent 5: Outbound Caller ─────────────────────────
header("5. OutboundCallerAgent")
try:
    from app.agents.outbound_caller import OutboundCallerAgent
    script = OutboundCallerAgent().generate_script(
        call_type="Welcome Call",
        member_name="Rahul Sharma",
        plan_name="EasyClaims Secure Plan",
        end_date="2027-06-30",
        language="Hindi",
        member_id="member-001",
    )
    result("Greeting", script.greeting[:80] + "...")
    result("Body", script.body[:80] + "...")
    result("Closing", script.closing[:80] + "...")
    result("Language", script.language)
    print(f"\n  {PASS} PASSED")
except Exception as e:
    print(f"  {FAIL} FAILED: {e}")
    errors.append("OutboundCallerAgent")

# ─── Agent 6: Dashboard Insights ─────────────────────
header("6. DashboardInsightsAgent")
try:
    from app.agents.dashboard_insights import DashboardInsightsAgent
    insights = DashboardInsightsAgent().generate(
        partner_name="Jain Insurance Brokers",
        period="June 2026",
        total_members=240,
        active_members=198,
        expiring_soon=34,
        renewals_done=12,
        float_balance=8500.0,
        claims_count=7,
        open_tickets=5,
        partner_id="partner-001",
    )
    result("Total Insights", len(insights.insights))
    for i, ins in enumerate(insights.insights, 1):
        alert = " [ALERT]" if ins.is_alert else ""
        print(f"    {i}. {ins.message[:80]}{alert}")
    print(f"\n  {PASS} PASSED")
except Exception as e:
    print(f"  {FAIL} FAILED: {e}")
    errors.append("DashboardInsightsAgent")

# ─── Agent 7: Multilingual ───────────────────────────
header("7. MultilingualAgent")
try:
    from app.agents.multilingual import MultilingualAgent
    translation = MultilingualAgent().translate(
        text="Your health insurance policy has been successfully activated. Your coverage starts from 1st April 2025.",
        target_language="Hindi",
    )
    result("Original", "Your health insurance policy has been...")
    result("Translated", translation.translated_text[:100] + "...")
    result("Language", translation.language)
    print(f"\n  {PASS} PASSED")
except Exception as e:
    print(f"  {FAIL} FAILED: {e}")
    errors.append("MultilingualAgent")

# ─── Agent 8: Ticket Manager ─────────────────────────
header("8. TicketManagerAgent")
try:
    from app.agents.ticket_manager import TicketManagerAgent
    ticket = TicketManagerAgent().classify(
        message="Hello, my father met with an accident yesterday. I need to file a motor insurance claim urgently. Policy number: MOT-2025-112233",
        channel="WhatsApp",
        member_name="Rahul Sharma",
        member_id="member-001",
    )
    result("Category", ticket.category)
    result("Priority", ticket.priority)
    result("Summary", ticket.summary)
    result("Is Duplicate", ticket.is_duplicate)
    print(f"\n  {PASS} PASSED")
except Exception as e:
    print(f"  {FAIL} FAILED: {e}")
    errors.append("TicketManagerAgent")

# ─── Final Summary ────────────────────────────────────
print(f"\n{'='*50}")
print(f"  RESULTS: {8 - len(errors)}/8 agents passed")
if errors:
    print(f"  Failed: {', '.join(errors)}")
print(f"{'='*50}\n")

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

# --- Create a mock insurance policy PDF for testing ---
from fpdf import FPDF

def create_mock_policy_pdf(path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    lines = [
        "HEALTH INSURANCE POLICY",
        "",
        "Policy Number   : HLT-2024-098765",
        "Insured Name    : Rahul Sharma",
        "Insurer         : Star Health Insurance Co. Ltd.",
        "Sum Insured     : Rs. 5,00,000",
        "Policy Start    : 01-April-2025",
        "Policy End      : 31-March-2026",
        "Plan Type       : Individual Health Cover",
        "",
        "This is a valid health insurance policy document.",
    ]
    for line in lines:
        pdf.cell(0, 10, line, ln=True)
    pdf.output(path)

mock_pdf = "/tmp/mock_policy.pdf"

try:
    create_mock_policy_pdf(mock_pdf)
    print("Mock PDF created.")
except ImportError:
    print("fpdf2 not installed — using existing PDF")
    mock_pdf = "uploads/policies/c0b50711-22bf-4ea6-a7d7-f932591705fb/e9a6e084-db6d-43d4-a85f-1fd6a23b0d11.pdf"

# --- Run the agent ---
from app.agents.document_extractor import DocumentExtractorAgent

agent = DocumentExtractorAgent()
result = agent.extract(pdf_path=mock_pdf, policy_id="test-001")

print("\n=== EXTRACTED POLICY DATA ===")
print(f"Policy Number : {result.policy_number}")
print(f"Insured Name  : {result.insured_name}")
print(f"Insurer Name  : {result.insurer_name}")
print(f"Sum Insured   : {result.sum_insured}")
print(f"Start Date    : {result.start_date}")
print(f"End Date      : {result.end_date}")
print(f"Confidence    : {result.confidence}")
print("=============================\n")

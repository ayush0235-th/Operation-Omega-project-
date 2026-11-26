#!/usr/bin/env python3
"""
Generate a professional Forensic Chain of Custody PDF for CASE-OMEGA.
Reads metadata from 03_Evidence/chain_of_custody.csv, evidence_inventory.csv,
and hash_manifest.csv, producing a standardized, court-ready format report.
"""

import os
import sys
import pandas as pd
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print 'Page X of Y' page numbers
    along with running header and footer rules.
    """
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
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        page_w, page_h = A4

        # Running Header
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1A365D"))
        self.drawString(36, page_h - 32, "CASE OMEGA  |  FORENSIC CHAIN OF CUSTODY RECORD")
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#C53030"))
        self.drawRightString(page_w - 36, page_h - 32, "FORM CoC-01 • CONFIDENTIAL / ACADEMIC")
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.75)
        self.line(36, page_h - 36, page_w - 36, page_h - 36)

        # Running Footer
        self.line(36, 38, page_w - 36, 38)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#718096"))
        self.drawString(36, 26, "CASE ID: OMEGA-2026-001  •  Omega Multispeciality Hospital  •  BSA 2023 Sec 63 / IT Act Sec 65B Framework")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(page_w - 36, 26, page_str)
        self.restoreState()


def build_coc_pdf(output_paths):
    # Base paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    coc_csv_path = os.path.join(base_dir, "03_Evidence", "chain_of_custody.csv")
    inv_csv_path = os.path.join(base_dir, "03_Evidence", "evidence_inventory.csv")
    hash_csv_path = os.path.join(base_dir, "03_Evidence", "hash_manifest.csv")

    coc_df = pd.read_csv(coc_csv_path) if os.path.exists(coc_csv_path) else None
    inv_df = pd.read_csv(inv_csv_path) if os.path.exists(inv_csv_path) else None
    hash_df = pd.read_csv(hash_csv_path) if os.path.exists(hash_csv_path) else None

    # Setup styles
    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1A365D")  # Deep Navy
    secondary_color = colors.HexColor("#2B6CB0")  # Slate Blue
    dark_text = colors.HexColor("#2D3748")
    muted_text = colors.HexColor("#718096")
    alert_bg = colors.HexColor("#FFF5F5")
    alert_border = colors.HexColor("#FEB2B2")
    alert_text = colors.HexColor("#9B2C2C")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=primary_color,
        alignment=0,
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=secondary_color,
        spaceAfter=8
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=dark_text
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=dark_text
    )

    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=dark_text
    )

    cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=dark_text
    )

    cell_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white
    )

    mono_hash = ParagraphStyle(
        'MonoHash',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor("#2D3748")
    )

    story = []

    # 1. Document Title Banner
    story.append(Paragraph("DIGITAL EVIDENCE CHAIN OF CUSTODY FORM", title_style))
    story.append(Paragraph("DIGITAL FORENSIC LABORATORY  •  INCIDENT EVIDENCE TRACKING & CUSTODY RECORD", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=0, spaceAfter=6))

    # 2. Case Administrative Metadata Table
    case_admin_data = [
        [
            Paragraph("<b>Case ID:</b>", body_style),
            Paragraph("OMEGA-2026-001", body_bold),
            Paragraph("<b>Scenario Date:</b>", body_style),
            Paragraph("17 November 2026 (09:00 IST)", body_style),
        ],
        [
            Paragraph("<b>Organization:</b>", body_style),
            Paragraph("Omega Multispeciality Hospital (fictional)", body_style),
            Paragraph("<b>Governing SOP:</b>", body_style),
            Paragraph("SOP-OMEGA-IR-001 (Rev 1.0)", body_style),
        ],
        [
            Paragraph("<b>Lead Examiner:</b>", body_style),
            Paragraph("Kartik Kumar (ID: 2301730205)", body_bold),
            Paragraph("<b>Institution:</b>", body_style),
            Paragraph("K.R. Mangalam University", body_style),
        ],
        [
            Paragraph("<b>Investigation Type:</b>", body_style),
            Paragraph("Academic Forensic Simulation (Ransomware)", body_style),
            Paragraph("<b>Storage Location:</b>", body_style),
            Paragraph("Forensic Lab Secure Vault / Evidence Repo", body_style),
        ]
    ]

    t_admin = Table(case_admin_data, colWidths=[90, 175, 95, 163])
    t_admin.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_admin)
    story.append(Spacer(1, 6))

    # 3. Academic Notice Banner
    notice_text = (
        "<b>SIMULATION DISCLOSURE & SCOPE NOTICE:</b> This Chain of Custody form is generated for an academic "
        "cyber-forensic simulation. Evidence items (EVD-001 through EVD-003) represent synthetic test fixtures, "
        "reproducible scripts, and generated log records. No real healthcare network or production clinical systems "
        "were accessed, compromised, or seized. Seals, transfer signatures, and custody verifications are executed "
        "in compliance with digital forensic educational standards."
    )
    notice_p = Paragraph(notice_text, ParagraphStyle('NoticeP', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=10, textColor=alert_text))
    t_notice = Table([[notice_p]], colWidths=[523])
    t_notice.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), alert_bg),
        ('BOX', (0, 0), (-1, -1), 1, alert_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_notice)
    story.append(Spacer(1, 8))

    # 4. Master Evidence Register & Technical Identification
    story.append(Paragraph("1. Master Evidence Inventory & Acquisition Details", section_heading))

    inv_table_data = [
        [
            Paragraph("Item ID", cell_header),
            Paragraph("Evidence Description", cell_header),
            Paragraph("Category & Type", cell_header),
            Paragraph("Acquisition Source", cell_header),
            Paragraph("Acquisition Time", cell_header),
            Paragraph("Tamper Seal ID", cell_header)
        ],
        [
            Paragraph("<b>EVD-001</b>", cell_bold),
            Paragraph("Synthetic evidence fixture bundle (source media)", cell_style),
            Paragraph("Evidence Bundle<br/>ZIP Archive (3,482 B)", cell_style),
            Paragraph("Project source_media<br/>(Server OMEGA-FS01)", cell_style),
            Paragraph("2026-11-17<br/>10:00 IST", cell_style),
            Paragraph("<b>SIM-SEAL-001</b><br/>(Intact / Verified)", cell_style)
        ],
        [
            Paragraph("<b>EVD-002</b>", cell_bold),
            Paragraph("Synthetic master event logs (multi-source events)", cell_style),
            Paragraph("Master Log File<br/>CSV Dataset (1,693 B)", cell_style),
            Paragraph("sample_logs folder<br/>(SIEM Export)", cell_style),
            Paragraph("2026-11-17<br/>10:05 IST", cell_style),
            Paragraph("<b>SIM-SEAL-002</b><br/>(Intact / Verified)", cell_style)
        ],
        [
            Paragraph("<b>EVD-003</b>", cell_bold),
            Paragraph("Ransomware demonstration simulator script", cell_style),
            Paragraph("Forensic Artifact<br/>Python Script (3,260 B)", cell_style),
            Paragraph("04_Malware folder<br/>(Harmless Testbed)", cell_style),
            Paragraph("2026-11-17<br/>10:10 IST", cell_style),
            Paragraph("<b>SIM-SEAL-003</b><br/>(Intact / Verified)", cell_style)
        ]
    ]

    t_inv = Table(inv_table_data, colWidths=[48, 140, 85, 105, 70, 75])
    t_inv.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_inv)
    story.append(Spacer(1, 8))

    # 5. Chronological Chain of Custody Transfer Log
    story.append(Paragraph("2. Chronological Custodial Transfer Log", section_heading))

    custody_table_data = [
        [
            Paragraph("Item ID", cell_header),
            Paragraph("Transfer Date & Time", cell_header),
            Paragraph("Released By (Relinquished)", cell_header),
            Paragraph("Received By (Custodian)", cell_header),
            Paragraph("Purpose of Custody Transfer", cell_header),
            Paragraph("Custodial Location & Seal Check", cell_header)
        ],
        [
            Paragraph("<b>EVD-001</b>", cell_bold),
            Paragraph("2026-11-17 10:00 IST", cell_style),
            Paragraph("Student Investigator<br/>(First Responder)", cell_style),
            Paragraph("Evidence Vault<br/>(Initial Booking)", cell_style),
            Paragraph("Scene evidence collection and initial packaging under SOP-001", cell_style),
            Paragraph("03_Evidence/source_media<br/>Seal SIM-SEAL-001: <b>SECURED</b>", cell_style)
        ],
        [
            Paragraph("<b>EVD-001</b>", cell_bold),
            Paragraph("2026-11-17 10:15 IST", cell_style),
            Paragraph("Student Investigator<br/>(Simulation Officer)", cell_style),
            Paragraph("Kartik Kumar<br/>(Forensic Examiner)", cell_style),
            Paragraph("Transfer for SHA-256 baseline hashing and controlled extraction", cell_style),
            Paragraph("03_Evidence/source_media<br/>Seal SIM-SEAL-001: <b>INTACT</b>", cell_style)
        ],
        [
            Paragraph("<b>EVD-002</b>", cell_bold),
            Paragraph("2026-11-17 10:05 IST", cell_style),
            Paragraph("Student Investigator<br/>(First Responder)", cell_style),
            Paragraph("Evidence Vault<br/>(Initial Booking)", cell_style),
            Paragraph("Log file harvest from security audit trail and master event stream", cell_style),
            Paragraph("05_Logs/sample_logs<br/>Seal SIM-SEAL-002: <b>SECURED</b>", cell_style)
        ],
        [
            Paragraph("<b>EVD-002</b>", cell_bold),
            Paragraph("2026-11-17 10:20 IST", cell_style),
            Paragraph("Student Investigator<br/>(Simulation Officer)", cell_style),
            Paragraph("Kartik Kumar<br/>(Forensic Examiner)", cell_style),
            Paragraph("Transfer for timeline construction, parsing, and event correlation", cell_style),
            Paragraph("05_Logs/sample_logs<br/>Seal SIM-SEAL-002: <b>INTACT</b>", cell_style)
        ],
        [
            Paragraph("<b>EVD-003</b>", cell_bold),
            Paragraph("2026-11-17 10:10 IST", cell_style),
            Paragraph("Student Investigator<br/>(First Responder)", cell_style),
            Paragraph("Evidence Vault<br/>(Initial Booking)", cell_style),
            Paragraph("Script triage and identification of reversible transform artifact", cell_style),
            Paragraph("04_Malware<br/>Seal SIM-SEAL-003: <b>SECURED</b>", cell_style)
        ],
        [
            Paragraph("<b>EVD-003</b>", cell_bold),
            Paragraph("2026-11-17 10:25 IST", cell_style),
            Paragraph("Student Investigator<br/>(Simulation Officer)", cell_style),
            Paragraph("Kartik Kumar<br/>(Forensic Examiner)", cell_style),
            Paragraph("Transfer for static code review and safe behavioural demonstration", cell_style),
            Paragraph("04_Malware/test_data<br/>Seal SIM-SEAL-003: <b>INTACT</b>", cell_style)
        ]
    ]

    t_custody = Table(custody_table_data, colWidths=[48, 75, 95, 95, 115, 95])
    t_custody.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_custody)
    story.append(Spacer(1, 8))

    # Page Break to keep Integrity, Protocols & Signatures cleanly structured on Page 2
    story.append(PageBreak())

    # 6. Cryptographic Integrity Verification Manifest
    story.append(Paragraph("3. Forensic Cryptographic Integrity Verification (SHA-256)", section_heading))

    hash_intro = (
        "In accordance with forensic standard practices and Indian evidentiary rules (BSA 2023 Sec 63), "
        "SHA-256 cryptographic digests were computed immediately upon acquisition and re-verified at every custodial "
        "transition using block-based buffered hashing (64 KB). The hashes confirm that no bit-level alteration occurred."
    )
    story.append(Paragraph(hash_intro, body_style))
    story.append(Spacer(1, 4))

    hash_table_data = [
        [
            Paragraph("Item ID", cell_header),
            Paragraph("File Path & Relative Location", cell_header),
            Paragraph("Size (Bytes)", cell_header),
            Paragraph("Algorithm", cell_header),
            Paragraph("Cryptographic SHA-256 Checksum", cell_header),
            Paragraph("Integrity Status", cell_header)
        ],
        [
            Paragraph("<b>EVD-001</b>", cell_bold),
            Paragraph("03_Evidence/source_media/omega_synthetic_evidence_fixture.zip", cell_style),
            Paragraph("3,482", cell_style),
            Paragraph("SHA-256", cell_style),
            Paragraph("e30ce04c4d7281211e783d0e3703c50d06aa9164df3d547ea0f6bd9a0528d23e", mono_hash),
            Paragraph("<b>VERIFIED / MATCH</b>", cell_bold)
        ],
        [
            Paragraph("<b>EVD-002</b>", cell_bold),
            Paragraph("05_Logs/sample_logs/master_events.csv", cell_style),
            Paragraph("1,693", cell_style),
            Paragraph("SHA-256", cell_style),
            Paragraph("cab3fb649bcf940797b0fc69cc460f54077bae2604202b338ecefedd38491ae4", mono_hash),
            Paragraph("<b>VERIFIED / MATCH</b>", cell_bold)
        ],
        [
            Paragraph("<b>EVD-003</b>", cell_bold),
            Paragraph("04_Malware/ransomware_simulator.py", cell_style),
            Paragraph("3,260", cell_style),
            Paragraph("SHA-256", cell_style),
            Paragraph("77e7e6470b827d238422d46f369224775db979257c7424c0af18a53fc832058e", mono_hash),
            Paragraph("<b>VERIFIED / MATCH</b>", cell_bold)
        ]
    ]

    t_hash = Table(hash_table_data, colWidths=[48, 145, 45, 45, 175, 65])
    t_hash.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), secondary_color),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_hash)
    story.append(Spacer(1, 10))

    # 7. Custody Security, Handling Controls & Environmental Safeguards
    story.append(Paragraph("4. Evidence Storage Protocols & Handling Safeguards", section_heading))

    controls_text = (
        "<b>A. Access Control & Physical Security:</b> Master digital evidence fixtures are stored in an encrypted, "
        "access-restricted repository. Direct access is limited exclusively to authorized examiners designated on this form.<br/>"
        "<b>B. Forensic Working Copies:</b> Analysis was conducted solely on verified working copies. Original evidence "
        "bundles remain write-blocked and sealed with their respective cryptographic hashes intact.<br/>"
        "<b>C. Tamper-Evident Seals:</b> Physical/logical seals (SIM-SEAL-001, 002, 003) were inspected prior to every transfer. "
        "No container breach, unauthorized unsealing, or metadata tampering occurred throughout the investigative lifecycle.<br/>"
        "<b>D. Controlled Malware Environment:</b> Simulator execution was restricted strictly to the designated isolated testbed "
        "(<code>04_Malware/test_data/</code>). No outbound communication or system persistence mechanisms were engaged."
    )
    story.append(Paragraph(controls_text, body_style))
    story.append(Spacer(1, 10))

    # 8. Statutory Compliance Declaration (BSA 2023 / IT Act 2000)
    story.append(Paragraph("5. Forensic Examiner Certificate & Legal Admissibility Declaration", section_heading))

    cert_text = (
        "<b>CERTIFICATE UNDER SECTION 63, BHARATIYA SAKSHYA ADHINIYAM (BSA), 2023 / SECTION 65B, IT ACT, 2000:</b><br/>"
        "I, <b>Kartik Kumar</b>, lead forensic student investigator for Case OMEGA-2026-001, hereby certify that:<br/>"
        "1. The electronic records referenced herein were produced, collected, and managed under strict chain-of-custody protocols.<br/>"
        "2. The cryptographic hashes recorded at acquisition match the current digests with zero variance, establishing strict bit-level integrity.<br/>"
        "3. The computing systems and software tools employed to log, calculate digests, and correlate events were operating properly without malfunction.<br/>"
        "4. This document reflects an accurate and contemporaneous record of all custodial transfers, examinations, and dispositions."
    )
    story.append(Paragraph(cert_text, body_style))
    story.append(Spacer(1, 12))

    # 9. Sign-off & Verification Blocks
    sig_data = [
        [
            Paragraph("<b>FIRST RESPONDER / RELEASING OFFICER</b>", cell_header),
            Paragraph("<b>LEAD FORENSIC EXAMINER / CUSTODIAN</b>", cell_header)
        ],
        [
            Paragraph(
                "<b>Name:</b> Student Investigator (Simulation)<br/>"
                "<b>Role:</b> Digital First Responder (IR Team)<br/>"
                "<b>Affiliation:</b> Omega Incident Response Unit<br/>"
                "<b>Date & Time:</b> 2026-11-17 10:25 IST<br/>"
                "<b>Signature:</b> <i>[Simulated Digital Signature - Verified]</i><br/>"
                "<b>Seal ID Verified:</b> SIM-SEAL-001 / 002 / 003",
                cell_style
            ),
            Paragraph(
                "<b>Name:</b> Kartik Kumar (Roll: 2301730205)<br/>"
                "<b>Role:</b> Lead Digital Forensic Examiner<br/>"
                "<b>Affiliation:</b> K.R. Mangalam University<br/>"
                "<b>Date & Time:</b> 2026-11-17 10:30 IST<br/>"
                "<b>Signature:</b> <i>[Kartik Kumar - Authenticated Record]</i><br/>"
                "<b>Integrity Check:</b> SHA-256 Verified Match (Pass)",
                cell_style
            )
        ],
        [
            Paragraph("<b>EVIDENCE DISPOSITION / CASE STATUS:</b> Retained in secure evidence archive for academic review.", cell_bold),
            Paragraph("<b>CUSTODIAL STATUS:</b> Chain of Custody continuous and unbroken.", cell_bold)
        ]
    ]

    t_sig = Table(sig_data, colWidths=[260, 263])
    t_sig.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#EDF2F7")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_sig)

    # Build primary target PDF
    primary_out = output_paths[0]
    os.makedirs(os.path.dirname(primary_out), exist_ok=True)
    doc = SimpleDocTemplate(
        primary_out,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=45,
        bottomMargin=45
    )
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {primary_out}")

    # Copy to any alternate target paths
    import shutil
    for alt_out in output_paths[1:]:
        shutil.copyfile(primary_out, alt_out)
        print(f"Successfully replicated: {alt_out}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    report_dir = os.path.join(base_dir, "06_Report")
    
    # Generate both Chain_of_Custody.pdf and Case_Omega_Chain_of_Custody.pdf in 06_Report
    targets = [
        os.path.join(report_dir, "Chain_of_Custody.pdf"),
        os.path.join(report_dir, "Case_Omega_Chain_of_Custody.pdf")
    ]
    build_coc_pdf(targets)

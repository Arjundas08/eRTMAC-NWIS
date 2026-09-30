"""
Generates authentic, industry-standard Daily Drilling Reports (DDR) and Well Completion Report (WCR)
PDF documents modeled directly on Equinor Volve Field (Block 15/9) and NOPIMS public petroleum records.
Includes:
- Native clean PDFs with standard IADC / Equinor DDR tables and operations summaries
- Scanned-style rasterized PDF pages for OCR pipeline testing
- Clean routine drilling reports with zero incidents (negative cases)
- Multi-page reports with complex tables and ambiguous depths for review queue testing
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "documents" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def build_pdf_ddr_f14_loss(output_path: Path):
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0f2b48'), alignment=1
    )
    section_style = ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor('#005c8a')
    )
    body_style = ParagraphStyle(
        'DocBody', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#222222')
    )
    bold_body = ParagraphStyle(
        'BoldBody', parent=body_style, fontName='Helvetica-Bold'
    )
    alert_style = ParagraphStyle(
        'AlertBody', parent=body_style, textColor=colors.HexColor('#990000'), fontName='Helvetica-Bold'
    )

    story = []

    # Header block
    story.append(Paragraph("STATOILHYDRO ASA / VOLVE FIELD OPERATIONS", title_style))
    story.append(Paragraph("DAILY DRILLING REPORT (DDR) — REPORT NO. 44", ParagraphStyle('Sub', parent=title_style, fontSize=11, leading=14)))
    story.append(Spacer(1, 10))

    # Well Header Table
    well_info_data = [
        [Paragraph("<b>Wellbore Name:</b> 15/9-F-14", body_style), Paragraph("<b>NPD Wellbore ID:</b> 5885", body_style), Paragraph("<b>Field / Block:</b> Volve / PL 046", body_style)],
        [Paragraph("<b>Rig Name:</b> Mærsk Inspirer", body_style), Paragraph("<b>RKB Elevation:</b> 43.5 m", body_style), Paragraph("<b>Water Depth:</b> 82.0 m", body_style)],
        [Paragraph("<b>Report Date:</b> 2008-09-14", body_style), Paragraph("<b>Midnight Depth (MD):</b> 2965.0 m", body_style), Paragraph("<b>Midnight Depth (TVD):</b> 2911.5 m (2868.0m TVDSS)", body_style)],
        [Paragraph("<b>Current Formation:</b> Hugin FM", body_style), Paragraph("<b>Hole Size:</b> 8.5 in", body_style), Paragraph("<b>Current Mud Weight:</b> 1.31 SG", body_style)]
    ]
    t1 = Table(well_info_data, colWidths=[175, 175, 175])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f4f8')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#005c8a')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t1)
    story.append(Spacer(1, 12))

    # Operations 24-hr Summary Table
    story.append(Paragraph("1. 24-HOUR OPERATIONAL SUMMARY & TIME BREAKDOWN", section_style))
    ops_data = [
        ["From", "To", "Hours", "Phase", "Activity", "Operational Summary Description"],
        ["00:00", "04:30", "4.5", "DRILL", "Drilling Ahead", "Rotary drilling 8.5 inch hole from 2930m to 2965m MD with 1.31 SG mud, 550 GPM, 18 kft-lbs torque."],
        ["04:30", "12:00", "7.5", "NPT", "Lost Circulation", "At 2965m MD (2868m TVDSS), penetrated top porous sandstone of Hugin FM. Observed immediate pit volume drop. Mud loss rate measured at 42 bbl/hr. Dynamic ECD 1.31 SG."],
        ["12:00", "18:00", "6.0", "NPT", "LCM Treatment", "Mixed and pumped 35 bbl medium-coarse CaCO3 and nut-plug LCM pill. Reduced flow rate to 420 GPM and mud density to 1.25 SG. Monitored pit level for 2 hours."],
        ["18:00", "24:00", "6.0", "DRILL", "Drilling Ahead", "Wellbore stabilized. Zero static losses. Resumed controlled rotary drilling at 2965m with reduced ROP and 1.25 SG MW."]
    ]
    t2 = Table(ops_data, colWidths=[40, 40, 35, 45, 80, 285])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#005c8a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
        ('BACKGROUND', (0,2), (-1,3), colors.HexColor('#fee2e2')), # Highlight NPT rows
    ]))
    story.append(t2)
    story.append(Spacer(1, 12))

    # Page 2: Detailed Incident and Mud Properties
    story.append(PageBreak())
    story.append(Paragraph("2. MUD PROPERTIES & DETAILED INCIDENT NARRATIVE", section_style))
    story.append(Spacer(1, 6))

    mud_data = [
        ["Time", "Depth (m MD)", "Mud Type", "Density (SG)", "PV (cP)", "YP (lb/100ft²)", "Gel 10s/10m", "Fluid Loss (ml)", "pH"],
        ["04:00", "2960.0", "Versatec OBM", "1.31", "24", "18", "7 / 14", "3.2", "9.5"],
        ["08:00", "2965.0", "Versatec OBM", "1.25", "22", "15", "6 / 12", "3.6", "9.4"],
        ["16:00", "2965.0", "Versatec OBM", "1.25", "23", "16", "6 / 13", "3.4", "9.4"],
    ]
    t3 = Table(mud_data, colWidths=[45, 65, 85, 65, 55, 75, 65, 70, 40])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t3)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>INCIDENT REPORT DETAILS (PAGE 2 SUPPORTING PASSAGE):</b>", bold_body))
    narrative_p = (
        "Observed pit volume drop at 2965m while penetrating upper Hugin sand. Loss rate measured at 42 bbl/hr. "
        "Dynamic ECD was 1.31 SG with 550 GPM pump rate. Standpipe pressure dropped from 3200 psi to 2850 psi. "
        "Pushed 35 bbl medium-coarse CaCO3 and nut-plug LCM pill. Reduced flow rate to 420 GPM and mud density to 1.25 SG. "
        "Wellbore stabilized after 13.5 hours total NPT."
    )
    story.append(Paragraph(narrative_p, alert_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>SUPERINTENDENT REMARKS & APPROVAL:</b>", bold_body))
    story.append(Paragraph("DDR reviewed and approved by Drilling Superintendent J. Hansen. Verified against Mærsk Inspirer mud logging unit sensor records.", body_style))

    doc.build(story)

def build_pdf_ddr_f14_stuck_pipe(output_path: Path):
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0f2b48'), alignment=1)
    section_style = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor('#005c8a'))
    body_style = ParagraphStyle('DocBody', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#222222'))
    bold_body = ParagraphStyle('BoldBody', parent=body_style, fontName='Helvetica-Bold')
    alert_style = ParagraphStyle('AlertBody', parent=body_style, textColor=colors.HexColor('#990000'), fontName='Helvetica-Bold')

    story = [
        Paragraph("STATOILHYDRO ASA / VOLVE FIELD OPERATIONS", title_style),
        Paragraph("DAILY DRILLING REPORT (DDR) — REPORT NO. 52", ParagraphStyle('Sub', parent=title_style, fontSize=11, leading=14)),
        Spacer(1, 10)
    ]

    well_info_data = [
        [Paragraph("<b>Wellbore Name:</b> 15/9-F-14", body_style), Paragraph("<b>NPD Wellbore ID:</b> 5885", body_style), Paragraph("<b>Field / Block:</b> Volve / PL 046", body_style)],
        [Paragraph("<b>Report Date:</b> 2008-09-22", body_style), Paragraph("<b>Midnight Depth (MD):</b> 3012.0 m", body_style), Paragraph("<b>Midnight Depth (TVD):</b> 2941.5 m (2898.0m TVDSS)", body_style)],
        [Paragraph("<b>Current Formation:</b> Hugin FM", body_style), Paragraph("<b>Hole Size:</b> 8.5 in", body_style), Paragraph("<b>Mud Weight:</b> 1.25 SG", body_style)]
    ]
    t1 = Table(well_info_data, colWidths=[175, 175, 175])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f4f8')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#005c8a')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t1)
    story.append(Spacer(1, 12))

    story.append(Paragraph("1. 24-HOUR OPERATIONAL SUMMARY", section_style))
    ops_data = [
        ["From", "To", "Hours", "Phase", "Activity", "Operational Summary Description"],
        ["00:00", "14:15", "14.25", "DRILL", "Drilling Sand", "Rotary drilling 8.5 inch hole from 2980m to 3012m MD. Maintained 1.25 SG Versatec OBM."],
        ["14:15", "24:00", "9.75", "NPT", "Stuck Pipe", "Drillstring became stuck while standing static for 8 minutes to service top-drive connection across depleted Hugin sandstone at 3012m MD (2898m TVDSS). Unable to rotate or reciprocate with 80 klbs overpull."]
    ]
    t2 = Table(ops_data, colWidths=[40, 40, 35, 45, 80, 285])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#005c8a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#fee2e2')),
    ]))
    story.append(t2)
    story.append(Spacer(1, 12))

    story.append(PageBreak())
    story.append(Paragraph("3. JAR & SOAKING OPERATIONS (PAGE 3 SUPPORTING PASSAGE)", section_style))
    passage_text = (
        "Drillstring became stuck while standing static for 8 minutes to service top-drive connection across depleted Hugin sandstone. "
        "Unable to rotate or reciprocate with 80 klbs overpull. Spotted 40 bbl low-toxicity oil-based soaking pill around BHA. "
        "Allowed 4 hours soak time while working torque up to 18 kft-lbs. Pipe freed on third jar impact after 36.0 hours total NPT."
    )
    story.append(Paragraph(passage_text, alert_style))
    doc.build(story)

def build_pdf_ddr_f15s_packoff(output_path: Path):
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0f2b48'), alignment=1)
    section_style = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor('#005c8a'))
    body_style = ParagraphStyle('DocBody', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#222222'))
    alert_style = ParagraphStyle('AlertBody', parent=body_style, textColor=colors.HexColor('#990000'), fontName='Helvetica-Bold')

    story = [
        Paragraph("STATOILHYDRO ASA / VOLVE FIELD OPERATIONS", title_style),
        Paragraph("DAILY DRILLING REPORT (DDR) — WELL 15/9-F-15 S", ParagraphStyle('Sub', parent=title_style, fontSize=11, leading=14)),
        Spacer(1, 10)
    ]

    well_info_data = [
        [Paragraph("<b>Wellbore Name:</b> 15/9-F-15 S", body_style), Paragraph("<b>NPD Wellbore ID:</b> 6023", body_style), Paragraph("<b>Field / Block:</b> Volve / PL 046", body_style)],
        [Paragraph("<b>Report Date:</b> 2009-02-18", body_style), Paragraph("<b>Midnight Depth (MD):</b> 3220.0 m", body_style), Paragraph("<b>Midnight Depth (TVD):</b> 3118.5 m (3075.0m TVDSS)", body_style)],
        [Paragraph("<b>Current Formation:</b> Skagerrak FM", body_style), Paragraph("<b>Hole Size:</b> 8.5 in", body_style), Paragraph("<b>Mud Weight:</b> 1.28 SG", body_style)]
    ]
    t1 = Table(well_info_data, colWidths=[175, 175, 175])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f4f8')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#005c8a')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t1)
    story.append(Spacer(1, 12))

    story.append(PageBreak())
    story.append(Paragraph("2. INCIDENT & HOLE CLEANING NARRATIVE (PAGE 2 SUPPORTING PASSAGE)", section_style))
    passage_text = (
        "High torque spikes and string stall encountered entering Skagerrak abrasive interval at 3220m MD (3075m TVDSS). "
        "Shaker screens showed poor cutting returns and large cavings. Annular velocity insufficient to carry heavy abrasive sands. "
        "Pumped high-viscosity tandem sweeps (30 bbl weighted pill followed by 30 bbl low-vis pill). "
        "Reamed interval twice before resuming drilling. 14.5 hours NPT logged."
    )
    story.append(Paragraph(passage_text, alert_style))
    doc.build(story)

def build_pdf_clean_routine_drilling(output_path: Path):
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0f2b48'), alignment=1)
    section_style = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor('#005c8a'))
    body_style = ParagraphStyle('DocBody', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#222222'))

    story = [
        Paragraph("STATOILHYDRO ASA / VOLVE FIELD OPERATIONS", title_style),
        Paragraph("DAILY DRILLING REPORT — ROUTINE OPERATIONS (NEGATIVE TEST CASE)", ParagraphStyle('Sub', parent=title_style, fontSize=11, leading=14)),
        Spacer(1, 10)
    ]

    well_info_data = [
        [Paragraph("<b>Wellbore Name:</b> 15/9-F-12", body_style), Paragraph("<b>NPD Wellbore ID:</b> 5667", body_style), Paragraph("<b>Field / Block:</b> Volve / PL 046", body_style)],
        [Paragraph("<b>Report Date:</b> 2008-04-25", body_style), Paragraph("<b>Midnight Depth (MD):</b> 1850.0 m", body_style), Paragraph("<b>Midnight Depth (TVD):</b> 1806.5 m (1763.0m TVDSS)", body_style)],
        [Paragraph("<b>Current Formation:</b> Nordland GP", body_style), Paragraph("<b>Hole Size:</b> 12.25 in", body_style), Paragraph("<b>Mud Weight:</b> 1.18 SG", body_style)]
    ]
    t1 = Table(well_info_data, colWidths=[175, 175, 175])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f4f8')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#005c8a')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t1)
    story.append(Spacer(1, 12))

    story.append(Paragraph("1. 24-HOUR OPERATIONAL SUMMARY", section_style))
    ops_data = [
        ["From", "To", "Hours", "Phase", "Activity", "Operational Summary Description"],
        ["00:00", "24:00", "24.0", "DRILL", "Routine Drilling", "Drilling ahead 12.25 inch hole from 1420m to 1850m MD. Steady ROP of 18 m/hr. Shakers running clean with fine sandstone cuttings. Zero NPT. Zero mud losses or torque drag anomalies."]
    ]
    t2 = Table(ops_data, colWidths=[40, 40, 35, 45, 80, 285])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#005c8a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
    ]))
    story.append(t2)
    doc.build(story)

def build_pdf_scanned_simulation(output_path: Path):
    """
    Creates a genuinely scanned-style PDF: renders text onto a PIL raster image,
    adds slight scan tilt and noise, and embeds as a pure image PDF (zero native text layer).
    This exercises the OCR and scanned document detection pipeline.
    """
    # Create PIL image
    img = Image.new('RGB', (1600, 2200), color=(248, 247, 243))
    draw = ImageDraw.Draw(img)
    
    # Draw simulated typewriter / scanned text header
    draw.rectangle([60, 60, 1540, 180], outline=(40, 40, 40), width=3)
    draw.text((100, 80), "STATOIL VOLVE FIELD - SCANNED DRILLING OPERATIONS ARCHIVE", fill=(20, 20, 20))
    draw.text((100, 120), "WELL: NO 15/9-F-4 | DATE: 2007-10-12 | HOLE: 8.5 INCH", fill=(40, 40, 40))
    
    # Draw table outline
    draw.rectangle([60, 220, 1540, 700], outline=(80, 80, 80), width=2)
    draw.line([60, 280, 1540, 280], fill=(80, 80, 80), width=2)
    draw.text((80, 240), "TIME / DEPTH", fill=(30, 30, 30))
    draw.text((350, 240), "FORMATION / EVENT", fill=(30, 30, 30))
    draw.text((750, 240), "OPERATIONAL NARRATIVE & MITIGATION", fill=(30, 30, 30))
    
    draw.text((80, 320), "07:15 / 2760m MD", fill=(50, 50, 50))
    draw.text((350, 320), "HEATHER FM / TIGHT HOLE", fill=(160, 20, 20))
    draw.text((750, 320), "Encountered 45 klbs overpull on 8.5 inch BHA during wiper trip at", fill=(40, 40, 40))
    draw.text((750, 360), "Heather shale transition zone. Reamed tight hole section back to bottom", fill=(40, 40, 40))
    draw.text((750, 400), "with 90 RPM and circulating 480 GPM. Controlled tripping speed < 15 m/min.", fill=(40, 40, 40))
    draw.text((750, 440), "NPT logged: 5.5 hours. Depth TVDSS: 2715.0m.", fill=(40, 40, 40))
    
    # Save temporary image and build image-only PDF
    temp_img_path = output_path.with_suffix('.png')
    img.save(temp_img_path)
    
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.drawImage(str(temp_img_path), 0, 0, width=A4[0], height=A4[1])
    c.save()
    
    if temp_img_path.exists():
        temp_img_path.unlink()

def main():
    print("Generating authentic petroleum documents...")
    build_pdf_ddr_f14_loss(OUTPUT_DIR / "VOLVE_DDR_20080914_F14.pdf")
    build_pdf_ddr_f14_stuck_pipe(OUTPUT_DIR / "VOLVE_DDR_20080922_F14.pdf")
    build_pdf_ddr_f15s_packoff(OUTPUT_DIR / "VOLVE_DDR_20090218_F15S.pdf")
    build_pdf_clean_routine_drilling(OUTPUT_DIR / "VOLVE_DDR_ROUTINE_DRILLING_CLEAN.pdf")
    build_pdf_scanned_simulation(OUTPUT_DIR / "VOLVE_DDR_SCANNED_MUD_REPORT.pdf")
    print(f"Generated 5 authentic petroleum PDFs in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()

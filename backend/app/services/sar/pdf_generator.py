"""
SAR PDF Generator - Render SAR data into PDF following FinCEN SAR template layout.

This module provides the SARPDFGenerator class that generates compliant PDF documents
following the official FinCEN SAR template specifications using ReportLab.
"""

from io import BytesIO
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.schemas.sar import SARData, SubjectInfo, ActivityInfo, FilingInstitution
from app.services.sar.formatter import SARReportFormatter
from app.services.sar.security import sanitize_text_input
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SARPDFGenerator:
    """Generates SAR PDF documents following FinCEN template layout."""

    def __init__(self):
        """Initialize PDF generator with layout constants."""
        self.page_width, self.page_height = letter
        self.margin_left = 0.75 * inch
        self.margin_right = 0.75 * inch
        self.margin_top = 0.5 * inch
        self.margin_bottom = 0.5 * inch
        self.line_height = 14
        self.section_spacing = 20
        self.formatter = SARReportFormatter()
    
    def _sanitize(self, text: str) -> str:
        """
        Sanitize text before rendering in PDF.
        
        Args:
            text: Input text
            
        Returns:
            Sanitized text safe for PDF rendering
            
        Validates: Requirements 8.6
        """
        if not text:
            return ""
        return sanitize_text_input(str(text))

    def create_sar_pdf(self, sar_data: SARData) -> bytes:
        """
        Generate SAR PDF document following FinCEN template.

        Args:
            sar_data: Complete SAR data structure

        Returns:
            PDF bytes that can be saved to file or served to client

        Validates: Requirements 3.1, 3.7
        """
        logger.info(f"Generating SAR PDF for report {sar_data.report_id}")

        # Create PDF buffer
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        # Start rendering from top of page
        y_position = self.page_height - self.margin_top

        # Render standardized section format.
        y_position = self.render_header_section(c, sar_data, y_position)
        self.render_standardized_layout(c, sar_data, y_position)

        # Finalize PDF
        c.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"Successfully generated SAR PDF ({len(pdf_bytes)} bytes)")
        return pdf_bytes

    def render_standardized_layout(
        self, c: canvas.Canvas, sar_data: SARData, y_position: float
    ) -> None:
        """Render the unified SAR section layout in canonical order."""
        text = self.formatter.render_text(sar_data.report_layout)
        self._render_wrapped_multiline(c, text, y_position)

    def _render_wrapped_multiline(self, c: canvas.Canvas, text: str, y_position: float) -> None:
        """Render long multi-line text with wrapping and pagination."""
        c.setFont("Helvetica", 10)
        available_width = self.page_width - self.margin_left - self.margin_right
        page_number = 1

        for raw_line in text.splitlines():
            # Preserve narrative whitespace/paragraph boundaries.
            line = raw_line.rstrip()
            if not line:
                y_position -= self.line_height
                continue

            chunks = self._wrap_line(c, line, available_width)
            for chunk in chunks:
                if y_position < self.margin_bottom + 30:
                    c.setFont("Helvetica", 9)
                    c.drawString(self.page_width / 2 - 20, self.margin_bottom, f"Page {page_number}")
                    c.showPage()
                    page_number += 1
                    y_position = self.page_height - self.margin_top
                    c.setFont("Helvetica", 10)
                c.drawString(self.margin_left, y_position, self._sanitize(chunk))
                y_position -= self.line_height

        c.setFont("Helvetica", 9)
        c.drawString(self.page_width / 2 - 20, self.margin_bottom, f"Page {page_number}")

    def _wrap_line(self, c: canvas.Canvas, line: str, available_width: float) -> list[str]:
        """Wrap line by word for current font settings."""
        words = line.split(" ")
        if not words:
            return [""]
        out: list[str] = []
        current: list[str] = []
        for word in words:
            trial = " ".join(current + [word]).strip()
            if not current or c.stringWidth(trial, "Helvetica", 10) <= available_width:
                current.append(word)
                continue
            out.append(" ".join(current))
            current = [word]
        if current:
            out.append(" ".join(current))
        return out

    def render_header_section(
        self, c: canvas.Canvas, sar_data: SARData, y_position: float
    ) -> float:
        """
        Render form header with filing institution information.

        Args:
            c: ReportLab canvas object
            sar_data: Complete SAR data structure
            y_position: Current vertical position on page

        Returns:
            Updated y_position after rendering

        Validates: Requirements 3.2
        """
        logger.debug("Rendering header section")

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(self.margin_left, y_position, "FinCEN Suspicious Activity Report (SAR)")
        y_position -= 25

        # Form identifier
        c.setFont("Helvetica", 10)
        c.drawString(self.margin_left, y_position, "FinCEN Form 111 (Revised 04/2013)")
        y_position -= 20

        # Filing institution section
        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.margin_left, y_position, "Filing Institution Information")
        y_position -= 18

        # Institution details
        c.setFont("Helvetica", 10)
        institution = sar_data.filing_institution
        
        c.drawString(self.margin_left, y_position, f"Name: {self._sanitize(institution.name)}")
        y_position -= self.line_height
        
        c.drawString(self.margin_left, y_position, f"TIN: {self._sanitize(institution.tin)}")
        y_position -= self.line_height
        
        c.drawString(
            self.margin_left, y_position,
            f"Address: {self._sanitize(institution.address)}, {self._sanitize(institution.city)}, {self._sanitize(institution.state)} {self._sanitize(institution.zip_code)}"
        )
        y_position -= self.line_height
        
        c.drawString(self.margin_left, y_position, f"Contact: {self._sanitize(institution.contact_name)}")
        y_position -= self.line_height
        
        c.drawString(
            self.margin_left, y_position,
            f"Phone: {self._sanitize(institution.contact_phone)} | Email: {self._sanitize(institution.contact_email)}"
        )
        y_position -= self.line_height

        # Report metadata
        y_position -= 10
        c.setFont("Helvetica", 9)
        c.drawString(
            self.margin_left, y_position,
            f"Generated: {sar_data.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        y_position -= self.line_height
        
        c.drawString(self.margin_left, y_position, f"Report ID: {self._sanitize(sar_data.report_id)}")
        y_position -= self.line_height
        
        c.drawString(self.margin_left, y_position, f"Case ID: {self._sanitize(sar_data.case_id)}")
        y_position -= self.section_spacing

        return y_position

    def render_subject_information(
        self, c: canvas.Canvas, subject: SubjectInfo, y_position: float
    ) -> float:
        """
        Render Part I - Subject Information section.

        Args:
            c: ReportLab canvas object
            subject: Subject information data
            y_position: Current vertical position on page

        Returns:
            Updated y_position after rendering

        Validates: Requirements 3.3
        """
        logger.debug("Rendering subject information section")

        # Section header
        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.margin_left, y_position, "Part I - Subject Information")
        y_position -= 18

        # Subject details
        c.setFont("Helvetica", 10)
        
        c.drawString(self.margin_left, y_position, f"Subject Type: {self._sanitize(subject.subject_type)}")
        y_position -= self.line_height
        
        c.drawString(self.margin_left, y_position, f"Name: {self._sanitize(subject.name)}")
        y_position -= self.line_height
        
        if subject.address:
            c.drawString(self.margin_left, y_position, f"Address: {self._sanitize(subject.address)}")
            y_position -= self.line_height
        
        c.drawString(self.margin_left, y_position, f"Identification: {self._sanitize(subject.identification)}")
        y_position -= self.line_height
        
        if subject.account_number:
            c.drawString(self.margin_left, y_position, f"Account Number: {self._sanitize(subject.account_number)}")
            y_position -= self.line_height
        
        c.drawString(
            self.margin_left, y_position,
            f"Relationship to Institution: {self._sanitize(subject.relationship_to_institution)}"
        )
        y_position -= self.section_spacing

        return y_position

    def render_suspicious_activity(
        self, c: canvas.Canvas, activity: ActivityInfo, y_position: float
    ) -> float:
        """
        Render Part II - Suspicious Activity Information.

        Args:
            c: ReportLab canvas object
            activity: Activity information data
            y_position: Current vertical position on page

        Returns:
            Updated y_position after rendering

        Validates: Requirements 3.4
        """
        logger.debug("Rendering suspicious activity section")

        # Section header
        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.margin_left, y_position, "Part II - Suspicious Activity Information")
        y_position -= 18

        # Activity details
        c.setFont("Helvetica", 10)
        
        c.drawString(
            self.margin_left, y_position,
            f"Activity Date From: {activity.activity_date_from.strftime('%Y-%m-%d')}"
        )
        y_position -= self.line_height
        
        c.drawString(
            self.margin_left, y_position,
            f"Activity Date To: {activity.activity_date_to.strftime('%Y-%m-%d')}"
        )
        y_position -= self.line_height
        
        c.drawString(
            self.margin_left, y_position,
            f"Total Amount: ${activity.total_amount:,.2f}"
        )
        y_position -= self.line_height
        
        # Activity types
        c.drawString(self.margin_left, y_position, "Activity Type(s):")
        y_position -= self.line_height
        
        for activity_type in activity.activity_type:
            c.drawString(self.margin_left + 20, y_position, f"• {self._sanitize(activity_type)}")
            y_position -= self.line_height
        
        # Product types
        c.drawString(self.margin_left, y_position, "Product Type(s):")
        y_position -= self.line_height
        
        for product_type in activity.product_type:
            c.drawString(self.margin_left + 20, y_position, f"• {self._sanitize(product_type)}")
            y_position -= self.line_height
        
        # Instrument types
        c.drawString(self.margin_left, y_position, "Instrument Type(s):")
        y_position -= self.line_height
        
        for instrument_type in activity.instrument_type:
            c.drawString(self.margin_left + 20, y_position, f"• {self._sanitize(instrument_type)}")
            y_position -= self.line_height
        
        y_position -= self.section_spacing

        return y_position

    def render_narrative(
        self, c: canvas.Canvas, narrative: str, y_position: float
    ) -> None:
        """
        Render Part V - Narrative section with pagination support.

        Args:
            c: ReportLab canvas object
            narrative: Narrative text describing suspicious activity
            y_position: Current vertical position on page

        Validates: Requirements 3.5, 3.6, 8.6
        """
        logger.debug(f"Rendering narrative section ({len(narrative)} characters)")
        
        # Sanitize narrative text before rendering
        narrative = self._sanitize(narrative)

        # Section header
        c.setFont("Helvetica-Bold", 12)
        c.drawString(self.margin_left, y_position, "Part V - Suspicious Activity Information Narrative")
        y_position -= 18

        # Set font for narrative text
        c.setFont("Helvetica", 10)

        # Calculate available width for text
        available_width = self.page_width - self.margin_left - self.margin_right

        # Split narrative into words for wrapping
        words = narrative.split()
        lines = []
        current_line = []
        
        for word in words:
            # Test if adding this word exceeds line width
            test_line = " ".join(current_line + [word])
            text_width = c.stringWidth(test_line, "Helvetica", 10)
            
            if text_width <= available_width:
                current_line.append(word)
            else:
                # Line is full, save it and start new line
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        # Add the last line
        if current_line:
            lines.append(" ".join(current_line))

        # Render lines with pagination
        page_number = 1
        
        for line in lines:
            # Check if we need a new page
            if y_position < self.margin_bottom + 30:
                # Add page number at bottom
                c.setFont("Helvetica", 9)
                c.drawString(
                    self.page_width / 2 - 20, self.margin_bottom,
                    f"Page {page_number}"
                )
                
                # Start new page
                c.showPage()
                page_number += 1
                y_position = self.page_height - self.margin_top
                
                # Re-render section header on new page
                c.setFont("Helvetica-Bold", 12)
                c.drawString(
                    self.margin_left, y_position,
                    "Part V - Suspicious Activity Information Narrative (continued)"
                )
                y_position -= 18
                c.setFont("Helvetica", 10)
            
            # Draw the line
            c.drawString(self.margin_left, y_position, line)
            y_position -= self.line_height

        # Add final page number
        c.setFont("Helvetica", 9)
        c.drawString(
            self.page_width / 2 - 20, self.margin_bottom,
            f"Page {page_number}"
        )

        logger.debug(f"Narrative rendered across {page_number} page(s)")

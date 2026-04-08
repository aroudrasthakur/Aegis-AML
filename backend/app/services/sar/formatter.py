"""Standard SAR layout formatting utilities."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Iterable

from app.schemas.sar import SARReportLayout


class SARReportFormatter:
    """Formats SAR layouts into standardized human-readable text."""

    SECTION_ORDER: list[tuple[str, str]] = [
        ("subject_information", "Subject Information"),
        ("reporting_institution", "Reporting Institution Details"),
        ("suspicious_activity", "Suspicious Activity Details"),
        ("narrative", "Narrative"),
        ("transaction_information", "Transaction Information"),
        ("supporting_documentation", "Supporting Documentation"),
        ("internal_review_actions", "Internal Review and Actions Taken"),
        ("law_enforcement_notification", "Law Enforcement Notification"),
    ]

    def render_text(self, layout: SARReportLayout) -> str:
        """Render standardized SAR text in required section order."""
        out: list[str] = []
        for field_name, heading in self.SECTION_ORDER:
            section = getattr(layout, field_name)
            out.append(f"{heading}")
            out.append("-" * len(heading))
            out.extend(self._render_section(field_name, section))
            out.append("")
        return "\n".join(out).rstrip() + "\n"

    def _render_section(self, section_name: str, section: object) -> list[str]:
        lines: list[str] = []

        if section_name == "subject_information":
            lines.extend(
                [
                    f"Full Name: {section.full_name}",
                    f"Address: {section.address or 'N/A'}",
                    f"Date of Birth: {self._fmt_date(section.date_of_birth)}",
                    f"Identification Number: {section.identification_number}",
                    f"Occupation or Business Type: {section.occupation_or_business_type or 'N/A'}",
                ]
            )
            return lines

        if section_name == "reporting_institution":
            lines.extend(
                [
                    f"Institution Name: {section.institution_name}",
                    f"Branch Location: {section.branch_location}",
                    f"Contact Person: {section.contact_person}",
                    f"Contact Information: {section.contact_information}",
                    f"Institution ID: {section.institution_id}",
                ]
            )
            return lines

        if section_name == "suspicious_activity":
            lines.extend(
                [
                    f"Activity Dates: {self._fmt_list(section.activity_dates, self._fmt_date)}",
                    f"Activity Types: {self._fmt_list(section.activity_types)}",
                    f"Total Amount: {self._fmt_amount(section.total_amount)}",
                    f"Affected Accounts: {self._fmt_list(section.affected_accounts)}",
                ]
            )
            return lines

        if section_name == "narrative":
            lines.append("Summary Text:")
            # Preserve paragraph spacing exactly as authored.
            lines.extend(section.summary_text.splitlines() or [""])
            return lines

        if section_name == "transaction_information":
            lines.extend(
                [
                    f"Transaction Dates: {self._fmt_list(section.transaction_dates, self._fmt_date)}",
                    f"Amounts: {self._fmt_list(section.amounts, self._fmt_amount)}",
                    f"Methods: {self._fmt_list(section.methods)}",
                    f"Origin Accounts: {self._fmt_list(section.origin_accounts)}",
                    f"Destination Accounts: {self._fmt_list(section.destination_accounts)}",
                    f"Countries Involved: {self._fmt_list(section.countries_involved)}",
                ]
            )
            return lines

        if section_name == "supporting_documentation":
            lines.extend(
                [
                    f"Attachment Refs: {self._fmt_list(section.attachment_refs)}",
                    f"Notes: {section.notes or 'N/A'}",
                ]
            )
            return lines

        if section_name == "internal_review_actions":
            lines.extend(
                [
                    f"Actions Taken: {self._fmt_list(section.actions_taken)}",
                    f"Investigation Opened: {'Yes' if section.investigation_opened else 'No'}",
                    f"Account Restricted: {'Yes' if section.account_restricted else 'No'}",
                    f"Filing Date: {self._fmt_date(section.filing_date)}",
                    f"Compliance Approver: {section.compliance_approver or 'N/A'}",
                ]
            )
            return lines

        if section_name == "law_enforcement_notification":
            lines.extend(
                [
                    f"Agency Name: {section.agency_name or 'N/A'}",
                    f"Notification Date: {self._fmt_date(section.notification_date)}",
                    f"Case Reference Number: {section.case_reference_number or 'N/A'}",
                ]
            )
            return lines

        return lines

    @staticmethod
    def _fmt_list(items: Iterable[object], formatter=None) -> str:
        values = list(items or [])
        if not values:
            return "None"
        if formatter:
            return ", ".join(formatter(v) for v in values)
        return ", ".join(str(v) for v in values)

    @staticmethod
    def _fmt_date(value: date | None) -> str:
        if value is None:
            return "N/A"
        return value.isoformat()

    @staticmethod
    def _fmt_amount(value: Decimal | float | int | str) -> str:
        try:
            amount = Decimal(str(value))
        except Exception:
            return str(value)
        return f"${amount:,.2f}"

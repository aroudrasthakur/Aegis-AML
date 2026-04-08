"""
SAR Data Mapper - Transform internal data structures to FinCEN SAR template format.

This module provides the SARDataMapper class that maps internal report and case data
to the official FinCEN SAR template structure for PDF generation.
"""

from datetime import date, datetime, timezone
from typing import Optional

from app.schemas.sar import (
    SARData,
    FilingInstitution,
    SubjectInfo,
    ActivityInfo,
    SARReportLayout,
    SubjectInformationSection,
    ReportingInstitutionSection,
    SuspiciousActivitySection,
    NarrativeSection,
    TransactionInformationSection,
    SupportingDocumentationSection,
    InternalReviewActionsSection,
    LawEnforcementNotificationSection,
)
from app.services.sar.config import get_filing_institution_config
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Mapping from internal typology to FinCEN SAR activity types
TYPOLOGY_TO_SAR_ACTIVITY_TYPES = {
    "peel chain": ["Structuring", "Money Laundering"],
    "fan-out": ["Structuring", "Money Laundering"],
    "many-to-one collection": ["Structuring", "Money Laundering"],
    "cross-chain bridge hop": ["Money Laundering", "Terrorist Financing"],
    "circular loop / round-tripping": ["Money Laundering"],
    "reconsolidation": ["Money Laundering", "Structuring"],
    "offramp exits": ["Money Laundering", "Structuring"],
    "layering": ["Money Laundering", "Structuring"],
}


class SARDataMapper:
    """Maps internal report/case data to FinCEN SAR template structure."""

    def map_to_sar_format(self, report: dict, case: dict) -> SARData:
        """
        Map internal data to SAR template structure.

        Args:
            report: Report dictionary from database
            case: Network case dictionary from database

        Returns:
            SARData object with all required fields populated

        Validates: Requirements 2.1, 2.7
        """
        logger.info(f"Mapping SAR data for report {report.get('id')} and case {case.get('id')}")

        # Get filing institution from configuration
        filing_institution = self._get_filing_institution_config()

        # Map subject information (primary wallet)
        subject = self.map_subject_information(case)

        # Map activity information
        activity = self.map_suspicious_activity(case)

        # Generate narrative from explanation
        narrative = self.map_narrative(report, case)
        report_layout = self.map_report_layout(
            report=report,
            case=case,
            filing_institution=filing_institution,
            subject=subject,
            activity=activity,
            narrative=narrative,
        )

        sar_data = SARData(
            filing_institution=filing_institution,
            subject=subject,
            activity=activity,
            narrative=narrative,
            case_id=case.get("id", ""),
            report_id=report.get("id", ""),
            generated_at=datetime.now(timezone.utc),
            report_layout=report_layout,
        )

        logger.info(f"Successfully mapped SAR data for report {report.get('id')}")
        return sar_data

    def map_subject_information(self, case: dict) -> SubjectInfo:
        """
        Extract and format subject (wallet) information.

        Args:
            case: Network case dictionary containing wallet addresses

        Returns:
            SubjectInfo object with wallet identification

        Validates: Requirements 2.2
        """
        wallet_addresses = case.get("wallet_addresses", [])

        # Use primary wallet (first in list) or "Unknown" if empty
        primary_wallet = wallet_addresses[0] if wallet_addresses else "Unknown"

        # Create a readable name from wallet address
        wallet_name = f"Wallet {primary_wallet[:8]}..." if primary_wallet != "Unknown" else "Unknown Wallet"

        subject = SubjectInfo(
            subject_type="Entity",
            name=wallet_name,
            address=None,  # Blockchain wallets don't have physical addresses
            identification=primary_wallet,
            account_number=None,
            relationship_to_institution="Customer",
        )

        logger.debug(f"Mapped subject information for wallet {primary_wallet[:8]}...")
        return subject

    def map_suspicious_activity(self, case: dict) -> ActivityInfo:
        """
        Extract and format suspicious activity details.

        Args:
            case: Network case dictionary containing activity data

        Returns:
            ActivityInfo object with dates, amounts, and activity types

        Validates: Requirements 2.3, 2.4
        """
        # Parse dates with fallback to current time if missing
        start_time = case.get("start_time")
        end_time = case.get("end_time")

        activity_date_from = self._parse_datetime(start_time) if start_time else datetime.now(timezone.utc)
        activity_date_to = self._parse_datetime(end_time) if end_time else datetime.now(timezone.utc)

        # Extract total amount with fallback to 0
        total_amount = float(case.get("total_amount", 0))

        # Map typology to SAR activity types
        typology = case.get("typology", "").lower()
        activity_types = self._map_typology_to_sar_types(typology)

        activity = ActivityInfo(
            activity_date_from=activity_date_from,
            activity_date_to=activity_date_to,
            total_amount=total_amount,
            activity_type=activity_types,
            product_type=["Digital Currency"],
            instrument_type=["Blockchain Transaction"],
        )

        logger.debug(f"Mapped activity information: {typology} -> {activity_types}")
        return activity

    def map_narrative(self, report: dict, case: dict) -> str:
        """
        Generate narrative description from explanation data.

        Args:
            report: Report dictionary containing explanation
            case: Network case dictionary containing case details

        Returns:
            Narrative string describing the suspicious activity

        Validates: Requirements 2.5
        """
        # Extract key information
        case_id = case.get("id", "Unknown")
        typology = case.get("typology", "Unknown")
        risk_score = case.get("risk_score", 0)
        total_amount = case.get("total_amount", 0)
        wallet_addresses = case.get("wallet_addresses", [])
        explanation = report.get("explanation", "")

        # Build narrative sections
        narrative_parts = []

        # Introduction
        narrative_parts.append(
            f"This Suspicious Activity Report concerns Case ID {case_id}, "
            f"which involves suspicious blockchain activity classified as {typology}."
        )

        # Subject information
        if wallet_addresses:
            narrative_parts.append(
                f"\n\nThe primary subject is a blockchain wallet with address {wallet_addresses[0]}. "
                f"A total of {len(wallet_addresses)} wallet address(es) are associated with this case."
            )

        # Activity summary
        narrative_parts.append(
            f"\n\nThe suspicious activity involves digital currency transactions totaling "
            f"${total_amount:,.2f}. The case has been assigned a risk score of {risk_score:.2f}, "
            f"indicating {'high' if risk_score >= 0.75 else 'medium' if risk_score >= 0.5 else 'low'} risk."
        )

        # Explanation details
        if explanation:
            narrative_parts.append(f"\n\nDetailed Analysis:\n{explanation}")
        else:
            narrative_parts.append(
                "\n\nThe activity was flagged by our automated monitoring system based on "
                "pattern analysis and risk scoring algorithms."
            )

        # Conclusion
        narrative_parts.append(
            "\n\nBased on the analysis of transaction patterns, risk indicators, and behavioral "
            "characteristics, this activity warrants further investigation and reporting to FinCEN."
        )

        narrative = "".join(narrative_parts)

        # Truncate if exceeds maximum length (10,000 characters)
        if len(narrative) > 10000:
            logger.warning(f"Narrative exceeds 10,000 characters ({len(narrative)}), truncating")
            narrative = narrative[:9997] + "..."

        logger.debug(f"Generated narrative of {len(narrative)} characters")
        return narrative

    def map_report_layout(
        self,
        *,
        report: dict,
        case: dict,
        filing_institution: FilingInstitution,
        subject: SubjectInfo,
        activity: ActivityInfo,
        narrative: str,
    ) -> SARReportLayout:
        """Build standardized SAR section layout for rendering/serialization."""
        tx_dates: list[date] = []
        tx_amounts: list[float] = []
        tx_methods: list[str] = []
        origin_accounts: list[str] = []
        destination_accounts: list[str] = []
        countries_involved: list[str] = []

        suspicious_rows = case.get("suspicious_transactions") or []
        for row in suspicious_rows:
            ts = row.get("timestamp")
            if ts:
                tx_dates.append(self._parse_datetime(ts).date())
            amt = row.get("amount")
            if amt is not None:
                tx_amounts.append(float(amt))
            if row.get("asset_type"):
                tx_methods.append(str(row.get("asset_type")))
            sender = row.get("sender_wallet")
            receiver = row.get("receiver_wallet")
            if sender:
                origin_accounts.append(str(sender))
            if receiver:
                destination_accounts.append(str(receiver))
            chain = row.get("chain_id")
            if chain:
                countries_involved.append(str(chain))

        activity_dates = [
            activity.activity_date_from.date(),
            activity.activity_date_to.date(),
        ]
        filing_date = (
            self._parse_datetime(case.get("end_time")).date()
            if case.get("end_time")
            else None
        )

        layout = SARReportLayout(
            subject_information=SubjectInformationSection(
                full_name=subject.name,
                address=subject.address,
                identification_number=subject.identification,
                occupation_or_business_type=subject.subject_type,
            ),
            reporting_institution=ReportingInstitutionSection(
                institution_name=filing_institution.name,
                branch_location=", ".join(
                    [
                        filing_institution.address,
                        filing_institution.city,
                        filing_institution.state,
                        filing_institution.zip_code,
                    ]
                ),
                contact_person=filing_institution.contact_name,
                contact_information=f"{filing_institution.contact_phone} | {filing_institution.contact_email}",
                institution_id=filing_institution.tin,
            ),
            suspicious_activity=SuspiciousActivitySection(
                activity_dates=activity_dates,
                activity_types=activity.activity_type,
                total_amount=activity.total_amount,
                affected_accounts=case.get("wallet_addresses") or [],
            ),
            narrative=NarrativeSection(summary_text=narrative),
            transaction_information=TransactionInformationSection(
                transaction_dates=tx_dates,
                amounts=tx_amounts,
                methods=sorted(set(tx_methods)),
                origin_accounts=sorted(set(origin_accounts)),
                destination_accounts=sorted(set(destination_accounts)),
                countries_involved=sorted(set(countries_involved)),
            ),
            supporting_documentation=SupportingDocumentationSection(
                attachment_refs=[],
                notes=report.get("explanation") or None,
            ),
            internal_review_actions=InternalReviewActionsSection(
                actions_taken=["SAR drafted for compliance review"],
                investigation_opened=True,
                account_restricted=False,
                filing_date=filing_date,
                compliance_approver=None,
            ),
            law_enforcement_notification=LawEnforcementNotificationSection(),
        )
        return layout

    def _get_filing_institution_config(self) -> FilingInstitution:
        """
        Get filing institution information from configuration.

        Returns:
            FilingInstitution object with institution details

        Validates: Requirements 2.1
        """
        return get_filing_institution_config()

    def _map_typology_to_sar_types(self, typology: str) -> list[str]:
        """
        Convert internal typology classification to FinCEN SAR activity type codes.

        Args:
            typology: Internal typology string

        Returns:
            List of SAR activity type strings

        Validates: Requirements 2.4
        """
        typology_lower = typology.lower().strip()

        # Look up in mapping table
        activity_types = TYPOLOGY_TO_SAR_ACTIVITY_TYPES.get(typology_lower)

        if activity_types:
            return activity_types.copy()

        # Default fallback if typology not recognized
        logger.warning(f"Unknown typology '{typology}', using default activity types")
        return ["Money Laundering"]

    def _parse_datetime(self, dt_value) -> datetime:
        """
        Parse datetime value from various formats.

        Args:
            dt_value: Datetime value (string, datetime, or timestamp)

        Returns:
            datetime object

        Validates: Requirements 2.6
        """
        if isinstance(dt_value, datetime):
            # Ensure timezone aware
            if dt_value.tzinfo is None:
                return dt_value.replace(tzinfo=timezone.utc)
            return dt_value

        if isinstance(dt_value, str):
            try:
                # Try ISO format
                parsed = datetime.fromisoformat(dt_value.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed
            except ValueError:
                logger.warning(f"Failed to parse datetime string: {dt_value}")
                return datetime.now(timezone.utc)

        # Fallback to current time
        logger.warning(f"Unexpected datetime type: {type(dt_value)}")
        return datetime.now(timezone.utc)

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class StrictModel(BaseModel):
    """Base model that rejects unknown fields across SAR sections."""

    model_config = ConfigDict(extra="forbid")


class FilingInstitution(StrictModel):
    """Filing institution information for SAR header."""

    name: str
    tin: str  # Tax Identification Number (EIN format: XX-XXXXXXX)
    address: str
    city: str
    state: str
    zip_code: str
    contact_name: str
    contact_phone: str
    contact_email: str


class SubjectInfo(StrictModel):
    """Legacy subject information structure used by existing mapper/generator flow."""

    subject_type: str  # "Individual" or "Entity"
    name: str
    address: Optional[str] = None
    identification: str  # Wallet address
    account_number: Optional[str] = None
    relationship_to_institution: str


class ActivityInfo(StrictModel):
    """Legacy suspicious activity structure used by existing mapper/generator flow."""

    activity_date_from: datetime
    activity_date_to: datetime
    total_amount: float
    activity_type: list[str] = Field(default_factory=list)
    product_type: list[str] = Field(default_factory=list)
    instrument_type: list[str] = Field(default_factory=list)


class SubjectInformationSection(StrictModel):
    full_name: str
    address: Optional[str] = None
    date_of_birth: Optional[date] = None
    identification_number: str
    occupation_or_business_type: Optional[str] = None

    @field_validator("full_name", "identification_number")
    @classmethod
    def _non_empty_required_text(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("value must not be empty")
        return value.strip()


class ReportingInstitutionSection(StrictModel):
    institution_name: str
    branch_location: str
    contact_person: str
    contact_information: str
    institution_id: str


class SuspiciousActivitySection(StrictModel):
    activity_dates: list[date] = Field(default_factory=list)
    activity_types: list[str] = Field(default_factory=list)
    total_amount: Decimal
    affected_accounts: list[str] = Field(default_factory=list)

    @field_validator("total_amount", mode="before")
    @classmethod
    def _coerce_decimal(cls, value: Any) -> Decimal:
        try:
            return Decimal(str(value))
        except Exception as exc:
            raise ValueError("total_amount must be numeric") from exc


class NarrativeSection(StrictModel):
    summary_text: str

    @field_validator("summary_text")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        if value is None:
            raise ValueError("summary_text is required")
        if not isinstance(value, str):
            raise ValueError("summary_text must be a string")
        if not value.strip():
            raise ValueError("summary_text must not be empty")
        return value


class TransactionInformationSection(StrictModel):
    transaction_dates: list[date] = Field(default_factory=list)
    amounts: list[Decimal] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    origin_accounts: list[str] = Field(default_factory=list)
    destination_accounts: list[str] = Field(default_factory=list)
    countries_involved: list[str] = Field(default_factory=list)

    @field_validator("amounts", mode="before")
    @classmethod
    def _coerce_amounts(cls, value: Any) -> list[Decimal]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("amounts must be a list")
        out: list[Decimal] = []
        for item in value:
            try:
                out.append(Decimal(str(item)))
            except Exception as exc:
                raise ValueError("amounts must contain only numeric values") from exc
        return out


class SupportingDocumentationSection(StrictModel):
    attachment_refs: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class InternalReviewActionsSection(StrictModel):
    actions_taken: list[str] = Field(default_factory=list)
    investigation_opened: bool = False
    account_restricted: bool = False
    filing_date: Optional[date] = None
    compliance_approver: Optional[str] = None


class LawEnforcementNotificationSection(StrictModel):
    agency_name: Optional[str] = None
    notification_date: Optional[date] = None
    case_reference_number: Optional[str] = None


class SARReportLayout(StrictModel):
    subject_information: SubjectInformationSection
    reporting_institution: ReportingInstitutionSection
    suspicious_activity: SuspiciousActivitySection
    narrative: NarrativeSection
    transaction_information: TransactionInformationSection
    supporting_documentation: SupportingDocumentationSection
    internal_review_actions: InternalReviewActionsSection
    law_enforcement_notification: LawEnforcementNotificationSection


class SARData(StrictModel):
    """Complete SAR data structure for generation + rendering."""

    filing_institution: FilingInstitution
    subject: SubjectInfo
    activity: ActivityInfo
    narrative: str
    case_id: str
    report_id: str
    generated_at: datetime
    report_layout: SARReportLayout


class SARRecord(BaseModel):
    """SAR database record model."""

    id: str
    report_id: str
    case_id: str
    sar_path: str
    filing_date: datetime
    status: str  # "draft", "filed", "rejected"
    bsa_id: Optional[str] = None  # BSA Identifier assigned by FinCEN
    generated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed_statuses = {"draft", "filed", "rejected"}
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v

    @field_validator("bsa_id")
    @classmethod
    def validate_bsa_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        pattern = r"^\d{8}-\d{3}-\d{5}$"
        if not re.match(pattern, v):
            raise ValueError("BSA ID must follow format: XXXXXXXX-XXX-XXXXX")
        return v


class SARGenerationResponse(BaseModel):
    sar_id: str
    report_id: str
    case_id: str
    download_url: str
    status: str
    generated_at: datetime


def validate_sar_layout(payload: dict) -> tuple[Optional[SARReportLayout], list[dict[str, Any]]]:
    """Validate a SAR layout payload and return structured validation errors."""

    try:
        return SARReportLayout.model_validate(payload), []
    except ValidationError as exc:
        return None, exc.errors()

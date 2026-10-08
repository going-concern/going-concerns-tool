from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ControlStatus(str):
    DRAFT = "DRAFT"
    READY_FOR_TESTING = "READY_FOR_TESTING"
    TESTING_IN_PROGRESS = "TESTING_IN_PROGRESS"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    REVIEW_NOTES = "REVIEW_NOTES"
    CLEARED = "CLEARED"
    FINAL = "FINAL"


class ControlType(str):
    MANUAL = "MANUAL"
    AUTOMATED = "AUTOMATED"
    IT_DEPENDENT = "IT_DEPENDENT"


class ControlClassification(str):
    PREVENTIVE = "PREVENTIVE"
    DETECTIVE = "DETECTIVE"


class Frequency(str):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    ANNUAL = "ANNUAL"
    EVENT_DRIVEN = "EVENT_DRIVEN"


class SamplingMethodology(str):
    RANDOM = "RANDOM"
    SYSTEMATIC = "SYSTEMATIC"
    HAPHAZARD = "HAPHAZARD"
    USER_SELECTED = "USER_SELECTED"


class SampleResultStatus(str):
    PASS = "PASS"
    EXCEPTION = "EXCEPTION"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNABLE_TO_TEST = "UNABLE_TO_TEST"
    PENDING = "PENDING"


class SupportingDocument(BaseModel):
    name: str = ""
    type: str = ""
    reference: str = ""


class SampleResult(BaseModel):
    sample_id: str = ""
    population_record_id: str = ""
    sample_number: int | None = None
    test_result: str = SampleResultStatus.PENDING
    exception_indicator: bool = False
    exception_type: str = ""
    exception_description: str = ""
    evidence_ids: List[str] = Field(default_factory=list)
    tester: str = ""
    testing_date: Optional[str] = None
    notes: str = ""
    status: str = SampleResultStatus.PENDING

    @field_validator("test_result")
    @classmethod
    def validate_test_result(cls, value: str) -> str:
        valid = {item.value for item in SampleResultStatus}
        normalized = str(value).strip().upper()
        if normalized not in valid:
            raise ValueError(f"Invalid sample result: {value}. Allowed values: {sorted(valid)}")
        return normalized


class ControlVersion(BaseModel):
    version_id: str = ""
    control_id: str = ""
    version_number: int = 1
    testing_period: str = ""
    population_definition: str = ""
    population_period: str = ""
    expected_deviation_rate: Optional[float] = None
    tolerable_deviation_rate: Optional[float] = None
    sample_size: int = 1
    sampling_methodology: str = SamplingMethodology.RANDOM
    evidence_requirements: str = ""
    exception_definition: str = ""
    testing_procedure: str = ""
    di_conclusion: str = ""
    di_rationale: str = ""
    is_locked: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("sample_size")
    @classmethod
    def validate_sample_size(cls, value: int) -> int:
        if value < 1:
            raise ValueError("sample_size must be at least 1")
        return value

    @field_validator("tolerable_deviation_rate")
    @classmethod
    def validate_tolerable_rate(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and (value < 0 or value > 100):
            raise ValueError("tolerable_deviation_rate must be between 0 and 100")
        return value


class ControlTestRequest(BaseModel):
    control_id: str = ""
    control_name: str = ""
    control_description: str = ""
    objective: str = ""
    relevant_risk: str = ""
    relevant_assertions: str = ""
    financial_statement_area: str = ""
    process: str = ""
    control_owner: str = ""
    frequency: str = Frequency.MONTHLY
    control_type: str = ControlType.MANUAL
    control_classification: str = ControlClassification.PREVENTIVE
    key_control_indicator: str = ""
    di_conclusion: str = ""
    di_rationale: str = ""
    testing_period: str = ""
    population_definition: str = ""
    population_period: str = ""
    expected_deviation_rate: Optional[float] = None
    tolerable_deviation_rate: Optional[float] = None
    sample_size: int = 1
    sampling_methodology: str = SamplingMethodology.RANDOM
    evidence_requirements: str = ""
    exception_definition: str = ""
    testing_procedure: str = ""
    auditor: str = ""
    reviewer: str = ""
    status: str = ControlStatus.DRAFT
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    supporting_documents: List[SupportingDocument] = Field(default_factory=list)
    sample_results: List[SampleResult] = Field(default_factory=list)
    reviewer_notes: str = ""

    @model_validator(mode="after")
    def validate_required_fields(self):
        required = [
            "control_id",
            "control_name",
            "objective",
            "testing_period",
            "population_definition",
            "sample_size",
        ]
        for field in required:
            value = getattr(self, field)
            if value is None or str(value).strip() == "":
                raise ValueError(f"{field} is required and cannot be blank")
        if self.sample_size < 1:
            raise ValueError("sample_size must be at least 1")
        if self.tolerable_deviation_rate is not None and (self.tolerable_deviation_rate < 0 or self.tolerable_deviation_rate > 100):
            raise ValueError("tolerable_deviation_rate must be between 0 and 100")
        if self.expected_deviation_rate is not None and (self.expected_deviation_rate < 0 or self.expected_deviation_rate > 100):
            raise ValueError("expected_deviation_rate must be between 0 and 100")
        return self

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        valid = {item.value for item in ControlStatus}
        normalized = str(value).strip().upper()
        if normalized not in valid:
            raise ValueError(f"Invalid status: {value}. Allowed values: {sorted(valid)}")
        return normalized


class ControlEvaluation(BaseModel):
    total_samples: int = 0
    pass_count: int = 0
    fail_count: int = 0
    inconclusive_count: int = 0
    observed_deviation_rate: Optional[float] = None
    tolerable_deviation_rate: Optional[float] = None
    summary: str = ""
    auditor_evaluation_required: bool = False
    calculation_note: str = ""

    @property
    def has_exception_flag(self) -> bool:
        return self.fail_count > 0 or self.auditor_evaluation_required


def load_control_request(path: str | Path) -> ControlTestRequest:
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return parse_control_input(payload)


def parse_control_input(payload: Dict[str, Any]) -> ControlTestRequest:
    return ControlTestRequest.model_validate(payload)


def evaluate_control(control: ControlTestRequest) -> ControlEvaluation:
    total_samples = len(control.sample_results) if control.sample_results else control.sample_size
    pass_count = 0
    fail_count = 0
    inconclusive_count = 0

    for sample in control.sample_results:
        result = str(sample.test_result).strip().upper() if hasattr(sample, "test_result") else str(sample.result).strip().upper()
        if result == SampleResultStatus.PASS:
            pass_count += 1
        elif result == SampleResultStatus.EXCEPTION:
            fail_count += 1
        elif result in {SampleResultStatus.NOT_APPLICABLE, SampleResultStatus.UNABLE_TO_TEST, SampleResultStatus.PENDING}:
            inconclusive_count += 1

    observed_deviation_rate = None
    if total_samples > 0:
        observed_deviation_rate = round((fail_count / total_samples) * 100, 2)

    tolerable_deviation_rate = control.tolerable_deviation_rate
    auditor_evaluation_required = bool(
        fail_count > 0 or (tolerable_deviation_rate is not None and observed_deviation_rate is not None and observed_deviation_rate > tolerable_deviation_rate)
    )

    if observed_deviation_rate is not None:
        summary = (
            f"{fail_count} exceptions identified in {total_samples} samples. "
            f"Observed deviation rate: {observed_deviation_rate}%. "
            f"Configured tolerable deviation rate: {tolerable_deviation_rate if tolerable_deviation_rate is not None else 'Not configured'}. "
            "Auditor evaluation required."
        )
    else:
        summary = "No sample results recorded. Auditor evaluation required."

    return ControlEvaluation(
        total_samples=total_samples,
        pass_count=pass_count,
        fail_count=fail_count,
        inconclusive_count=inconclusive_count,
        observed_deviation_rate=observed_deviation_rate,
        tolerable_deviation_rate=tolerable_deviation_rate,
        summary=summary,
        auditor_evaluation_required=auditor_evaluation_required,
        calculation_note="Automated calculation only; final audit conclusion remains a professional auditor judgment.",
    )


VALID_STATUS_TRANSITIONS = {
    ControlStatus.DRAFT: {ControlStatus.READY_FOR_TESTING},
    ControlStatus.READY_FOR_TESTING: {ControlStatus.TESTING_IN_PROGRESS},
    ControlStatus.TESTING_IN_PROGRESS: {ControlStatus.READY_FOR_REVIEW, ControlStatus.REVIEW_NOTES},
    ControlStatus.READY_FOR_REVIEW: {ControlStatus.REVIEW_NOTES, ControlStatus.CLEARED},
    ControlStatus.REVIEW_NOTES: {ControlStatus.READY_FOR_REVIEW, ControlStatus.CLEARED},
    ControlStatus.CLEARED: {ControlStatus.FINAL},
    ControlStatus.FINAL: set(),
}


def is_valid_status_transition(current: str | ControlStatus, next_status: str | ControlStatus) -> bool:
    current_value = ControlStatus(str(current).upper()) if not isinstance(current, ControlStatus) else current
    next_value = ControlStatus(str(next_status).upper()) if not isinstance(next_status, ControlStatus) else next_status
    allowed = VALID_STATUS_TRANSITIONS.get(current_value, set())
    return next_value in allowed


DEFAULT_EXCEPTION_TYPES = [
    "CONTROL_NOT_PERFORMED",
    "CONTROL_PERFORMED_LATE",
    "MISSING_APPROVAL",
    "MISSING_REVIEW",
    "UNAUTHORIZED_PERFORMER",
    "INSUFFICIENT_EVIDENCE",
    "INCORRECT_INFORMATION",
    "POPULATION_ISSUE",
    "OTHER",
]


__all__ = [
    "ControlStatus",
    "ControlType",
    "ControlClassification",
    "Frequency",
    "SamplingMethodology",
    "SampleResultStatus",
    "SupportingDocument",
    "SampleResult",
    "ControlVersion",
    "ControlTestRequest",
    "ControlEvaluation",
    "load_control_request",
    "parse_control_input",
    "evaluate_control",
    "is_valid_status_transition",
    "DEFAULT_EXCEPTION_TYPES",
]

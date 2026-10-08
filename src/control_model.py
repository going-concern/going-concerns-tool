from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, Field, field_validator


class SupportingDocument(BaseModel):
    name: str = ""
    type: str = ""
    reference: str = ""


class SampleResult(BaseModel):
    sample_id: str = ""
    description: str = ""
    result: str = "pass"
    critical: bool = False
    notes: str = ""
    evidence_reference: str = ""

    @field_validator("result")
    @classmethod
    def normalize_result(cls, value: str) -> str:
        return value.strip().lower()


class ControlTestRequest(BaseModel):
    control_id: str = "CTRL-001"
    control_name: str = "Manual Control"
    objective: str = ""
    design_criterion: str = ""
    implementation_criterion: str = ""
    sample_size: int = 0
    testing_period: str = ""
    acceptable_failures: int = 0
    supporting_documents: List[SupportingDocument] = Field(default_factory=list)
    sample_results: List[SampleResult] = Field(default_factory=list)
    reviewer_notes: str = ""
    conclusion: str = ""


class ControlEvaluation(BaseModel):
    total_samples: int
    pass_count: int
    fail_count: int
    inconclusive_count: int
    conclusion: str
    rationale: str
    threshold_exceeded: bool


def load_control_request(path: str | Path) -> ControlTestRequest:
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return ControlTestRequest.model_validate(payload)


def parse_control_input(payload: Dict[str, Any]) -> ControlTestRequest:
    return ControlTestRequest.model_validate(payload)


def evaluate_control(control: ControlTestRequest) -> ControlEvaluation:
    total_samples = len(control.sample_results) if control.sample_results else control.sample_size
    pass_count = 0
    fail_count = 0
    inconclusive_count = 0

    for sample in control.sample_results:
        normalized = sample.result.strip().lower()
        if normalized == "pass":
            pass_count += 1
        elif normalized == "fail":
            fail_count += 1
        else:
            inconclusive_count += 1

    threshold_exceeded = fail_count > control.acceptable_failures
    critical_failure = any(item.result.lower() == "fail" and item.critical for item in control.sample_results)

    if critical_failure or threshold_exceeded:
        conclusion = "Not operating effectively"
        rationale = (
            "The sample results include a critical failure or exceed the allowable failure threshold. "
            "This indicates the control is not operating effectively for the tested population."
        )
    elif inconclusive_count > 0:
        conclusion = "Inconclusive"
        rationale = "At least one sample result is inconclusive and must be reviewed before a final conclusion can be reached."
    else:
        conclusion = "Operating effectively"
        rationale = "The tested sample met the required criteria and did not exceed the allowable failure threshold."

    return ControlEvaluation(
        total_samples=total_samples,
        pass_count=pass_count,
        fail_count=fail_count,
        inconclusive_count=inconclusive_count,
        conclusion=conclusion,
        rationale=rationale,
        threshold_exceeded=threshold_exceeded,
    )

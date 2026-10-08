from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SupportingDocument:
    name: str
    type: str
    reference: str


@dataclass
class SampleResult:
    sample_id: str
    description: str
    result: str
    critical: bool = False
    notes: str = ""
    evidence_reference: str = ""


@dataclass
class ControlTestRequest:
    control_id: str
    control_name: str
    objective: str
    design_criterion: str
    implementation_criterion: str
    sample_size: int
    testing_period: str
    acceptable_failures: int = 0
    supporting_documents: List[SupportingDocument] = field(default_factory=list)
    sample_results: List[SampleResult] = field(default_factory=list)
    reviewer_notes: str = ""
    conclusion: str = ""


@dataclass
class ControlEvaluation:
    total_samples: int
    pass_count: int
    fail_count: int
    inconclusive_count: int
    conclusion: str
    rationale: str
    threshold_exceeded: bool


def parse_control_input(payload: Dict[str, Any]) -> ControlTestRequest:
    documents = [
        SupportingDocument(
            name=item.get("name", "Document"),
            type=item.get("type", "Unknown"),
            reference=item.get("reference", ""),
        )
        for item in payload.get("supporting_documents", [])
    ]

    sample_results = [
        SampleResult(
            sample_id=item.get("sample_id", ""),
            description=item.get("description", ""),
            result=item.get("result", "pass"),
            critical=item.get("critical", False),
            notes=item.get("notes", ""),
            evidence_reference=item.get("evidence_reference", ""),
        )
        for item in payload.get("sample_results", [])
    ]

    return ControlTestRequest(
        control_id=payload.get("control_id", "CTRL-001"),
        control_name=payload.get("control_name", "Manual Control"),
        objective=payload.get("objective", ""),
        design_criterion=payload.get("design_criterion", ""),
        implementation_criterion=payload.get("implementation_criterion", ""),
        sample_size=int(payload.get("sample_size", len(sample_results) or 0)),
        testing_period=payload.get("testing_period", ""),
        acceptable_failures=int(payload.get("acceptable_failures", 0)),
        supporting_documents=documents,
        sample_results=sample_results,
        reviewer_notes=payload.get("reviewer_notes", ""),
        conclusion=payload.get("conclusion", ""),
    )


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
    critical_failure = any(item.result.strip().lower() == "fail" and item.critical for item in control.sample_results)

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

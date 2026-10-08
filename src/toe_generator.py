from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.control_model import (
    ControlStatus,
    ControlTestRequest,
    ControlVersion,
    DEFAULT_EXCEPTION_TYPES,
    is_valid_status_transition,
    parse_control_input,
)
from src.database import connect, initialize_database, utc_now


class ControlService:
    def __init__(self, db_path: str | Path = "data/going_concerns.db"):
        self.db_path = str(db_path)
        initialize_database(self.db_path)

    def create_control(self, payload: Dict[str, Any], created_by: str = "system") -> ControlTestRequest:
        control = parse_control_input(payload)
        control_id = control.control_id.strip()
        now = utc_now()
        if not control_id:
            raise ValueError("control_id is required")

        with connect(self.db_path) as conn:
            existing = conn.execute("SELECT 1 FROM controls WHERE control_id = ?", (control_id,)).fetchone()
            if existing is not None:
                raise ValueError(f"A control with control_id '{control_id}' already exists")

            version_id = str(uuid.uuid4())
            control_record = {
                "id": str(uuid.uuid4()),
                "control_id": control_id,
                "control_name": control.control_name,
                "control_description": control.control_description,
                "objective": control.objective,
                "relevant_risk": control.relevant_risk,
                "relevant_assertions": control.relevant_assertions,
                "financial_statement_area": control.financial_statement_area,
                "process": control.process,
                "control_owner": control.control_owner,
                "frequency": control.frequency,
                "control_type": control.control_type,
                "control_classification": control.control_classification,
                "key_control_indicator": control.key_control_indicator,
                "di_conclusion": control.di_conclusion,
                "di_rationale": control.di_rationale,
                "testing_period": control.testing_period,
                "population_definition": control.population_definition,
                "population_period": control.population_period,
                "expected_deviation_rate": control.expected_deviation_rate,
                "tolerable_deviation_rate": control.tolerable_deviation_rate,
                "sample_size": control.sample_size,
                "sampling_methodology": control.sampling_methodology,
                "evidence_requirements": control.evidence_requirements,
                "exception_definition": control.exception_definition,
                "testing_procedure": control.testing_procedure,
                "auditor": control.auditor,
                "reviewer": control.reviewer,
                "status": control.status,
                "current_version_id": version_id,
                "created_at": now,
                "updated_at": now,
            }
            conn.execute(
                """
                INSERT INTO controls (
                    id, control_id, control_name, control_description, objective, relevant_risk,
                    relevant_assertions, financial_statement_area, process, control_owner, frequency,
                    control_type, control_classification, key_control_indicator, di_conclusion,
                    di_rationale, testing_period, population_definition, population_period,
                    expected_deviation_rate, tolerable_deviation_rate, sample_size,
                    sampling_methodology, evidence_requirements, exception_definition,
                    testing_procedure, auditor, reviewer, status, current_version_id,
                    created_at, updated_at
                ) VALUES (
                    :id, :control_id, :control_name, :control_description, :objective, :relevant_risk,
                    :relevant_assertions, :financial_statement_area, :process, :control_owner, :frequency,
                    :control_type, :control_classification, :key_control_indicator, :di_conclusion,
                    :di_rationale, :testing_period, :population_definition, :population_period,
                    :expected_deviation_rate, :tolerable_deviation_rate, :sample_size,
                    :sampling_methodology, :evidence_requirements, :exception_definition,
                    :testing_procedure, :auditor, :reviewer, :status, :current_version_id,
                    :created_at, :updated_at
                )
                """,
                control_record,
            )

            version_payload = {
                "id": version_id,
                "control_id": control_id,
                "version_number": 1,
                "testing_period": control.testing_period,
                "population_definition": control.population_definition,
                "population_period": control.population_period,
                "expected_deviation_rate": control.expected_deviation_rate,
                "tolerable_deviation_rate": control.tolerable_deviation_rate,
                "sample_size": control.sample_size,
                "sampling_methodology": control.sampling_methodology,
                "evidence_requirements": control.evidence_requirements,
                "exception_definition": control.exception_definition,
                "testing_procedure": control.testing_procedure,
                "di_conclusion": control.di_conclusion,
                "di_rationale": control.di_rationale,
                "is_locked": 0,
                "created_at": now,
                "updated_at": now,
            }
            conn.execute(
                """
                INSERT INTO control_versions (
                    id, control_id, version_number, testing_period, population_definition,
                    population_period, expected_deviation_rate, tolerable_deviation_rate,
                    sample_size, sampling_methodology, evidence_requirements,
                    exception_definition, testing_procedure, di_conclusion, di_rationale,
                    is_locked, created_at, updated_at
                ) VALUES (
                    :id, :control_id, :version_number, :testing_period, :population_definition,
                    :population_period, :expected_deviation_rate, :tolerable_deviation_rate,
                    :sample_size, :sampling_methodology, :evidence_requirements,
                    :exception_definition, :testing_procedure, :di_conclusion, :di_rationale,
                    :is_locked, :created_at, :updated_at
                )
                """,
                version_payload,
            )

            self._write_audit_log(
                conn,
                user_name=created_by,
                action="CONTROL_CREATED",
                object_type="control",
                object_id=control_id,
                new_value=control_id,
                description="Control created and initial parameter version created.",
            )

            conn.commit()

        return control

    def create_version(self, control_id: str, payload: Dict[str, Any], created_by: str = "system") -> ControlVersion:
        with connect(self.db_path) as conn:
            current = conn.execute(
                "SELECT * FROM controls WHERE control_id = ?",
                (control_id,),
            ).fetchone()
            if current is None:
                raise ValueError(f"No control exists for control_id '{control_id}'")

            row = conn.execute(
                "SELECT * FROM control_versions WHERE control_id = ? ORDER BY version_number DESC LIMIT 1",
                (control_id,),
            ).fetchone()
            version_number = 1 if row is None else int(row["version_number"]) + 1

            version = ControlVersion(
                version_id=str(uuid.uuid4()),
                control_id=control_id,
                version_number=version_number,
                testing_period=str(payload.get("testing_period", "")),
                population_definition=str(payload.get("population_definition", "")),
                population_period=str(payload.get("population_period", "")),
                expected_deviation_rate=payload.get("expected_deviation_rate"),
                tolerable_deviation_rate=payload.get("tolerable_deviation_rate"),
                sample_size=int(payload.get("sample_size", 1)),
                sampling_methodology=str(payload.get("sampling_methodology", "RANDOM")),
                evidence_requirements=str(payload.get("evidence_requirements", "")),
                exception_definition=str(payload.get("exception_definition", "")),
                testing_procedure=str(payload.get("testing_procedure", "")),
                di_conclusion=str(payload.get("di_conclusion", "")),
                di_rationale=str(payload.get("di_rationale", "")),
                is_locked=False,
                created_at=__import__("datetime").datetime.utcnow(),
                updated_at=__import__("datetime").datetime.utcnow(),
            )

            conn.execute(
                """
                INSERT INTO control_versions (
                    id, control_id, version_number, testing_period, population_definition,
                    population_period, expected_deviation_rate, tolerable_deviation_rate,
                    sample_size, sampling_methodology, evidence_requirements,
                    exception_definition, testing_procedure, di_conclusion, di_rationale,
                    is_locked, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    version.version_id,
                    version.control_id,
                    version.version_number,
                    version.testing_period,
                    version.population_definition,
                    version.population_period,
                    version.expected_deviation_rate,
                    version.tolerable_deviation_rate,
                    version.sample_size,
                    version.sampling_methodology,
                    version.evidence_requirements,
                    version.exception_definition,
                    version.testing_procedure,
                    version.di_conclusion,
                    version.di_rationale,
                    utc_now(),
                    utc_now(),
                ),
            )

            conn.execute(
                "UPDATE controls SET current_version_id = ?, updated_at = ? WHERE control_id = ?",
                (version.version_id, utc_now(), control_id),
            )

            self._write_audit_log(
                conn,
                user_name=created_by,
                action="CONTROL_VERSION_CREATED",
                object_type="control_version",
                object_id=version.version_id,
                new_value=str(version.version_number),
                description="A new control parameter version was created.",
            )
            conn.commit()

            return version

    def transition_status(self, control_id: str, new_status: str, changed_by: str = "system") -> str:
        with connect(self.db_path) as conn:
            row = conn.execute("SELECT status FROM controls WHERE control_id = ?", (control_id,)).fetchone()
            if row is None:
                raise ValueError(f"No control exists for control_id '{control_id}'")

            current_status = row["status"]
            if not is_valid_status_transition(current_status, new_status):
                raise ValueError(f"Invalid status transition from {current_status} to {new_status}")

            conn.execute(
                "UPDATE controls SET status = ?, updated_at = ? WHERE control_id = ?",
                (new_status, utc_now(), control_id),
            )
            self._write_audit_log(
                conn,
                user_name=changed_by,
                action="STATUS_CHANGED",
                object_type="control",
                object_id=control_id,
                old_value=current_status,
                new_value=new_status,
                description=f"Status changed from {current_status} to {new_status}.",
            )
            conn.commit()
            return new_status

    def get_control(self, control_id: str) -> Optional[ControlTestRequest]:
        with connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM controls WHERE control_id = ?", (control_id,)).fetchone()
            if row is None:
                return None
            payload = dict(row)
            return parse_control_input(payload)

    def list_exception_types(self) -> List[str]:
        with connect(self.db_path) as conn:
            rows = conn.execute("SELECT code FROM exception_types WHERE is_active = 1 ORDER BY code").fetchall()
            return [row["code"] for row in rows]

    @staticmethod
    def _write_audit_log(conn: sqlite3.Connection, *, user_name: str, action: str, object_type: str, object_id: str, old_value: str | None = None, new_value: str | None = None, description: str | None = None) -> None:
        conn.execute(
            "INSERT INTO audit_log (id, timestamp, user_name, action, object_type, object_id, old_value, new_value, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()),
                utc_now(),
                user_name,
                action,
                object_type,
                object_id,
                old_value,
                new_value,
                description,
            ),
        )


__all__ = ["ControlService"]

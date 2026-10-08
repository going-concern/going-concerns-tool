from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS controls (
    id TEXT PRIMARY KEY,
    control_id TEXT NOT NULL UNIQUE,
    control_name TEXT NOT NULL,
    control_description TEXT,
    objective TEXT,
    relevant_risk TEXT,
    relevant_assertions TEXT,
    financial_statement_area TEXT,
    process TEXT,
    control_owner TEXT,
    frequency TEXT,
    control_type TEXT,
    control_classification TEXT,
    key_control_indicator TEXT,
    di_conclusion TEXT,
    di_rationale TEXT,
    testing_period TEXT,
    population_definition TEXT,
    population_period TEXT,
    expected_deviation_rate REAL,
    tolerable_deviation_rate REAL,
    sample_size INTEGER,
    sampling_methodology TEXT,
    evidence_requirements TEXT,
    exception_definition TEXT,
    testing_procedure TEXT,
    auditor TEXT,
    reviewer TEXT,
    status TEXT NOT NULL DEFAULT 'DRAFT',
    current_version_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS control_versions (
    id TEXT PRIMARY KEY,
    control_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    testing_period TEXT NOT NULL,
    population_definition TEXT,
    population_period TEXT,
    expected_deviation_rate REAL,
    tolerable_deviation_rate REAL,
    sample_size INTEGER NOT NULL,
    sampling_methodology TEXT,
    evidence_requirements TEXT,
    exception_definition TEXT,
    testing_procedure TEXT,
    di_conclusion TEXT,
    di_rationale TEXT,
    is_locked INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(control_id, version_number)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    user_name TEXT NOT NULL,
    action TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS exception_types (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    created_by TEXT
);

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

DEFAULT_EXCEPTION_TYPES = [
    ("EXC-001", "CONTROL_NOT_PERFORMED", "Control not performed"),
    ("EXC-002", "CONTROL_PERFORMED_LATE", "Control performed late"),
    ("EXC-003", "MISSING_APPROVAL", "Missing approval"),
    ("EXC-004", "MISSING_REVIEW", "Missing review"),
    ("EXC-005", "UNAUTHORIZED_PERFORMER", "Unauthorized performer/reviewer"),
    ("EXC-006", "INSUFFICIENT_EVIDENCE", "Insufficient evidence"),
    ("EXC-007", "INCORRECT_INFORMATION", "Incorrect information"),
    ("EXC-008", "POPULATION_ISSUE", "Population issue"),
    ("EXC-009", "OTHER", "Other"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def initialize_database(db_path: str | Path = "data/going_concerns.db") -> str:
    resolved = Path(db_path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(resolved))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)

    current_version = conn.execute("SELECT value FROM schema_meta WHERE key = 'schema_version'").fetchone()
    if current_version is None:
        conn.execute(
            "INSERT INTO schema_meta (key, value, updated_at) VALUES (?, ?, ?)",
            ("schema_version", "1", utc_now()),
        )

    for exc_code, code, description in DEFAULT_EXCEPTION_TYPES:
        row = conn.execute("SELECT 1 FROM exception_types WHERE code = ?", (code,)).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO exception_types (id, code, description, is_active, created_at, created_by) VALUES (?, ?, ?, 1, ?, 'system')",
                (exc_code, code, description, utc_now()),
            )

    conn.commit()
    conn.close()
    return str(resolved)


def connect(db_path: str | Path = "data/going_concerns.db") -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


__all__ = [
    "initialize_database",
    "connect",
    "DEFAULT_EXCEPTION_TYPES",
    "SCHEMA_SQL",
    "utc_now",
]

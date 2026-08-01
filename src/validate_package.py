#!/usr/bin/env python3
"""Validate the synthetic lab, recorded results, tests, and package manifest."""

from __future__ import annotations

import hashlib
import ast
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from generate_lab import build_database  # noqa: E402

TABLES = (
    "staging_identity",
    "customer_core",
    "contact_details",
    "financial_profile",
    "case_notes",
    "auth_users",
    "defended_identifiers",
)

MANIFEST_PATHS = (
    ".github/workflows/ci.yml",
    ".gitattributes",
    ".gitignore",
    "CITATION.cff",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "README.md",
    "README_EN.md",
    "ETHICS.md",
    "LICENSE",
    "SECURITY.md",
    "Makefile",
    "requirements-notebook.txt",
    "notebooks/Fulcrum_DNI_PoC_Mac.ipynb",
    "notebooks/GUIA_MAC_JUPYTER.md",
    "research/article_draft.md",
    "research/claims_matrix.md",
    "research/dossier.md",
    "research/portada_linkedin_cien_millones_entropia.jpg",
    "research/sources.md",
    "results/benchmark.json",
    "results/reconstruction.json",
    "results/validation.json",
    "results/README.md",
    "src/benchmark.py",
    "src/dni_sha256_enum.c",
    "src/generate_lab.py",
    "src/run_reconstruction.py",
    "src/validate_package.py",
    "tests/test_lab.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(connection: sqlite3.Connection, table: str) -> list[tuple[object, ...]]:
    return connection.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()


def validate_database(database: Path) -> dict[str, object]:
    connection = sqlite3.connect(database)
    metadata = dict(connection.execute("SELECT key, value FROM metadata"))
    counts = {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in TABLES
    }
    names = [
        row[0]
        for row in connection.execute(
            "SELECT synthetic_name FROM staging_identity ORDER BY rowid"
        )
    ]
    emails = [
        row[0]
        for row in connection.execute(
            "SELECT email FROM contact_details ORDER BY rowid"
        )
    ]
    hash_mismatches = connection.execute(
        """
        SELECT COUNT(*)
        FROM staging_identity AS s
        JOIN customer_core AS c USING (link_key)
        WHERE length(c.nif_sha256) != 64
        """
    ).fetchone()[0]
    password_controls = [
        row[0]
        for row in connection.execute(
            "SELECT password_kdf_record FROM auth_users ORDER BY rowid"
        )
    ]
    connection.close()

    checks = {
        "dataset_marked_synthetic": metadata.get("dataset") == "ENTIRELY_SYNTHETIC",
        "all_tables_have_12_rows": all(count == 12 for count in counts.values()),
        "all_names_are_synthetic": all(
            re.fullmatch(r"PERSONA_SINTETICA_\d{3}", name) for name in names
        ),
        "all_emails_use_invalid_tld": all(
            email.endswith("@example.invalid") for email in emails
        ),
        "all_identifier_hashes_are_sha256_length": hash_mismatches == 0,
        "all_password_controls_use_scrypt": all(
            value.startswith("scrypt$n=16384,r=8,p=1$")
            for value in password_controls
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"database validation failed: {checks}")
    return {"sha256": sha256_file(database), "counts": counts, "checks": checks}


def validate_reproducibility(database: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="dni-package-validation-") as directory:
        regenerated = Path(directory) / "synthetic_identity.db"
        build_database(regenerated)
        original = sqlite3.connect(database)
        duplicate = sqlite3.connect(regenerated)
        identical_tables = {
            table: rows(original, table) == rows(duplicate, table)
            for table in ("metadata", *TABLES)
        }
        original.close()
        duplicate.close()
        if not all(identical_tables.values()):
            raise RuntimeError(
                f"deterministic regeneration failed: {identical_tables}"
            )
        return {
            "semantic_tables_identical": True,
            "byte_identical_in_this_environment": (
                sha256_file(database) == sha256_file(regenerated)
            ),
        }


def validate_recorded_results() -> dict[str, object]:
    benchmark = json.loads((ROOT / "results/benchmark.json").read_text())
    reconstruction = json.loads(
        (ROOT / "results/reconstruction.json").read_text()
    )

    full = benchmark["full_run"]
    salted = benchmark["known_global_salt_full_run"]
    benchmark_checks = {
        "full_domain_measured": full["candidate_limit"] == 100_000_000,
        "unsalted_target_found": full["found_count"] == 1,
        "known_salt_full_domain_measured": (
            salted["candidate_limit"] == 100_000_000
        ),
        "known_salt_target_found": salted["found_count"] == 1,
    }
    reconstruction_checks = {
        "twelve_targets": reconstruction["target_hashes"] == 12,
        "twelve_hashes_recovered": reconstruction["recovered_hashes"] == 12,
        "twelve_profiles_reconstructed": (
            len(reconstruction["identity_packages"]) == 12
        ),
        "no_consistency_failures": reconstruction["consistency_failures"] == [],
        "three_attack_paths_recorded": len(reconstruction["attack_paths"]) == 3,
    }
    if not all((*benchmark_checks.values(), *reconstruction_checks.values())):
        raise RuntimeError(
            "recorded-result validation failed: "
            f"{benchmark_checks} {reconstruction_checks}"
        )
    return {
        "benchmark_checks": benchmark_checks,
        "reconstruction_checks": reconstruction_checks,
        "measured": {
            "unsalted_full_seconds": full["elapsed_seconds"],
            "unsalted_hashes_per_second": full["hashes_per_second"],
            "known_global_salt_full_seconds": salted["elapsed_seconds"],
            "reconstruction_full_seconds": reconstruction["cracking"][
                "elapsed_seconds"
            ],
            "recovered_profiles": len(reconstruction["identity_packages"]),
        },
    }


def run_tests() -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    combined = completed.stdout + completed.stderr
    if completed.returncode != 0:
        raise RuntimeError(f"test suite failed:\n{combined}")
    match = re.search(r"Ran (\d+) tests? in ([0-9.]+)s", combined)
    return {
        "status": "passed",
        "tests_run": int(match.group(1)) if match else None,
        "reported_seconds": float(match.group(2)) if match else None,
    }


def validate_notebook() -> dict[str, object]:
    path = ROOT / "notebooks/Fulcrum_DNI_PoC_Mac.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    if notebook.get("nbformat") != 4:
        raise RuntimeError("notebook must use nbformat 4")

    code_cells = [
        cell for cell in notebook["cells"] if cell.get("cell_type") == "code"
    ]
    markdown_cells = [
        cell for cell in notebook["cells"] if cell.get("cell_type") == "markdown"
    ]
    for index, cell in enumerate(code_cells, start=1):
        ast.parse(cell["source"], filename=f"notebook-code-cell-{index}")
        if cell.get("outputs") != [] or cell.get("execution_count") is not None:
            raise RuntimeError(
                "distributed notebook must not contain execution outputs"
            )

    joined_markdown = "\n".join(cell["source"] for cell in markdown_cells)
    required_markers = (
        "datos sintéticos",
        "100.000.000",
        "Capturas que sí aportan",
        "Uso ético",
    )
    missing = [
        marker for marker in required_markers if marker not in joined_markdown
    ]
    if missing:
        raise RuntimeError(f"notebook markers missing: {missing}")
    return {
        "status": "passed",
        "cells": len(notebook["cells"]),
        "code_cells": len(code_cells),
        "markdown_cells": len(markdown_cells),
        "outputs_embedded": 0,
    }


def write_manifest() -> dict[str, object]:
    missing = [relative for relative in MANIFEST_PATHS if not (ROOT / relative).is_file()]
    if missing:
        raise FileNotFoundError(f"manifest inputs missing: {missing}")
    records = [
        f"{sha256_file(ROOT / relative)}  {relative}" for relative in MANIFEST_PATHS
    ]
    output = ROOT / "results/manifest.sha256"
    output.write_text("\n".join(records) + "\n", encoding="utf-8")
    return {"path": str(output.relative_to(ROOT)), "entries": len(records)}


def main() -> None:
    database = ROOT / "lab/synthetic_identity.db"
    if not database.exists():
        build_database(database)
    report = {
        "title": "Fulcrum/DNI research package validation",
        "scope": "entirely synthetic laboratory",
        "database": validate_database(database),
        "reproducibility": validate_reproducibility(database),
        "recorded_results": validate_recorded_results(),
        "notebook": validate_notebook(),
        "tests": run_tests(),
    }
    validation_path = ROOT / "results/validation.json"
    validation_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report["manifest"] = write_manifest()
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

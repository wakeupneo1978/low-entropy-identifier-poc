#!/usr/bin/env python3
"""Recover synthetic DNI hashes and reconstruct cross-table identity packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sqlite3
import subprocess
import sys
import time
from pathlib import Path


def reverse_caesar_hex(value: str, shift: int = 8) -> str:
    encoded = bytes.fromhex(value)
    return bytes((byte - shift) % 256 for byte in encoded).decode("ascii")


def export_targets(connection: sqlite3.Connection, path: Path) -> list[str]:
    hashes = [
        row[0]
        for row in connection.execute(
            "SELECT nif_sha256 FROM customer_core ORDER BY customer_id"
        )
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(hashes) + "\n", encoding="ascii")
    return hashes


def invoke_cracker(
    cracker: Path,
    targets: Path,
    limit: int,
    threads: int | None = None,
) -> dict[str, object]:
    command = [str(cracker), "--targets", str(targets), "--limit", str(limit)]
    if threads is not None:
        if threads < 1:
            raise ValueError("threads must be at least 1")
        command += ["--threads", str(threads)]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def reconstruct(
    database: Path,
    cracker: Path,
    output: Path,
    limit: int,
    threads: int | None = None,
) -> dict[str, object]:
    started = time.perf_counter()
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row

    targets_path = output.parent / "targets.txt"
    target_hashes = export_targets(connection, targets_path)
    cracking = invoke_cracker(cracker, targets_path, limit, threads=threads)
    recovered = {item["sha256"]: item["dni"] for item in cracking["matches"]}

    rows = connection.execute(
        """
        SELECT
            c.customer_id,
            c.link_key,
            c.nif_sha256,
            s.synthetic_name,
            s.birth_year,
            s.postcode,
            d.email,
            d.phone,
            d.policy_number,
            f.iban_surrogate,
            f.income_band,
            f.risk_score,
            n.nif_caesar_hex,
            n.synthetic_note,
            a.password_kdf_record
        FROM customer_core c
        JOIN staging_identity s USING (link_key)
        JOIN contact_details d USING (link_key)
        JOIN financial_profile f USING (link_key)
        JOIN case_notes n USING (link_key)
        JOIN auth_users a USING (link_key)
        ORDER BY c.customer_id
        """
    ).fetchall()

    packages = []
    consistency_failures = []
    for row in rows:
        recovered_nif = recovered.get(row["nif_sha256"])
        decoded_nif = reverse_caesar_hex(row["nif_caesar_hex"])
        package = {
            "customer_id": row["customer_id"],
            "link_key": row["link_key"],
            "recovered_nif": recovered_nif,
            "decoded_weak_obfuscation": decoded_nif,
            "synthetic_name": row["synthetic_name"],
            "birth_year": row["birth_year"],
            "postcode": row["postcode"],
            "email": row["email"],
            "phone": row["phone"],
            "policy_number": row["policy_number"],
            "iban_surrogate": row["iban_surrogate"],
            "income_band": row["income_band"],
            "risk_score": row["risk_score"],
            "synthetic_note": row["synthetic_note"],
            "credential_control": row["password_kdf_record"].split("$", 1)[0],
        }
        if recovered_nif is not None and (
            hashlib.sha256(recovered_nif.encode("ascii")).hexdigest()
            != row["nif_sha256"]
            or recovered_nif != decoded_nif
        ):
            consistency_failures.append(row["customer_id"])
        packages.append(package)

    connection.close()
    report = {
        "title": "Synthetic identity reconstruction",
        "scope": "entirely_synthetic_lab_data",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "database_sha256": hashlib.sha256(database.read_bytes()).hexdigest(),
        "target_hashes": len(target_hashes),
        "recovered_hashes": len(recovered),
        "cracking": cracking,
        "join_key": "link_key",
        "attack_paths": {
            "hash_enumeration": {
                "source": "customer_core.nif_sha256",
                "result": "recovered_nif",
                "requires_staging_plaintext": False,
            },
            "plaintext_staging_linkage": {
                "source": "staging_identity.nif_plain",
                "link": "link_key",
                "requires_hash_recovery": False,
            },
            "weak_obfuscation": {
                "source": "case_notes.nif_caesar_hex",
                "result": "decoded_weak_obfuscation",
                "requires_hash_recovery": False,
            },
        },
        "tables_joined": [
            "customer_core",
            "staging_identity",
            "contact_details",
            "financial_profile",
            "case_notes",
            "auth_users",
        ],
        "consistency_failures": consistency_failures,
        "elapsed_total_seconds": time.perf_counter() - started,
        "identity_packages": packages,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--cracker", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/reconstruction.json"),
    )
    parser.add_argument("--limit", type=int, default=100_000_000)
    parser.add_argument(
        "--threads",
        type=int,
        help="Number of enumerator threads; defaults to detected logical CPUs",
    )
    args = parser.parse_args()
    report = reconstruct(
        args.database,
        args.cracker,
        args.output,
        args.limit,
        threads=args.threads,
    )
    summary = {
        "output": str(args.output),
        "target_hashes": report["target_hashes"],
        "recovered_hashes": report["recovered_hashes"],
        "hashes_per_second": report["cracking"]["hashes_per_second"],
        "elapsed_seconds": report["cracking"]["elapsed_seconds"],
        "consistency_failures": report["consistency_failures"],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

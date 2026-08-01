#!/usr/bin/env python3
"""Run a documented short and optional full-domain SHA-256 benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import tempfile
import time
from pathlib import Path

CONTROL_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"


def make_dni(number: int) -> str:
    return f"{number:08d}{CONTROL_LETTERS[number % 23]}"


def run(
    cracker: Path,
    target_file: Path,
    limit: int,
    salt: str = "",
    threads: int | None = None,
) -> dict:
    command = [
        str(cracker),
        "--targets",
        str(target_file),
        "--limit",
        str(limit),
    ]
    if salt:
        command += ["--salt", salt]
    if threads is not None:
        if threads < 1:
            raise ValueError("threads must be at least 1")
        command += ["--threads", str(threads)]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cracker", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("results/benchmark.json")
    )
    parser.add_argument("--quick", action="store_true")
    parser.add_argument(
        "--threads",
        type=int,
        help="Number of enumerator threads; defaults to detected logical CPUs",
    )
    args = parser.parse_args()

    short_limit = 1_000_000
    full_limit = 100_000_000
    target_number = 999_999 if args.quick else 98_765_432
    dni = make_dni(target_number)
    target = hashlib.sha256(dni.encode("ascii")).hexdigest()
    known_salt = "PUBLIC_LAB_SALT_2026"
    salted_target = hashlib.sha256((known_salt + dni).encode("ascii")).hexdigest()

    with tempfile.TemporaryDirectory(prefix="dni-poc-") as directory:
        target_file = Path(directory) / "target.txt"
        target_file.write_text(target + "\n", encoding="ascii")
        short = run(
            args.cracker,
            target_file,
            short_limit,
            threads=args.threads,
        )

        full = None
        known_salt_result = None
        if not args.quick:
            full = run(
                args.cracker,
                target_file,
                full_limit,
                threads=args.threads,
            )
            salted_file = Path(directory) / "salted_target.txt"
            salted_file.write_text(salted_target + "\n", encoding="ascii")
            known_salt_result = run(
                args.cracker,
                salted_file,
                full_limit,
                salt=known_salt,
                threads=args.threads,
            )

    reference_rate = (
        full["hashes_per_second"] if full is not None else short["hashes_per_second"]
    )
    raw_binary_table_bytes = 100_000_000 * (32 + 4)
    csv_hex_table_bytes = 100_000_000 * (64 + 1 + 9 + 1)
    report = {
        "title": "DNI SHA-256 exhaustive enumeration benchmark",
        "scope": "synthetic candidate space; no personal data",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "logical_cpus": os.cpu_count(),
        },
        "method": {
            "candidate_space": 100_000_000,
            "candidate_format": "eight zero-padded digits plus deterministic mod-23 letter",
            "hash": "SHA-256",
            "target_count": 1,
            "compiler_note": "See Makefile; built with -O3 unless CFLAGS is overridden",
        },
        "short_run": short,
        "full_run": full,
        "known_global_salt_full_run": known_salt_result,
        "derived": {
            "dni_domain_entropy_bits": 26.575424759098897,
            "nie_30m_domain_entropy_bits": 24.838459164932694,
            "estimated_full_pass_seconds_at_reference_rate": (
                100_000_000 / reference_rate
            ),
            "raw_binary_table_bytes_digest_plus_u32": raw_binary_table_bytes,
            "raw_binary_table_gib": raw_binary_table_bytes / (1024**3),
            "csv_hex_table_bytes_estimate": csv_hex_table_bytes,
            "csv_hex_table_gib_estimate": csv_hex_table_bytes / (1024**3),
            "per_record_salt_cost_for_1000_targets_full_passes_seconds": (
                1000 * 100_000_000 / reference_rate
            ),
        },
        "interpretation": [
            "The SHA-256 digest width does not increase source-domain entropy.",
            "One unsalted or globally salted pass can match every target sharing the same transform.",
            "A disclosed per-record salt prevents amortising one pass across all rows but does not stop a targeted pass.",
            "HMAC requires a high-entropy key stored outside the exfiltrated data; this benchmark does not attempt key recovery.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "derived": report["derived"]}, indent=2))


if __name__ == "__main__":
    main()

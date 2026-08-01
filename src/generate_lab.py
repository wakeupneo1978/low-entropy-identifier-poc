#!/usr/bin/env python3
"""Generate a deterministic, entirely synthetic identity-linkage laboratory."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sqlite3
from pathlib import Path

CONTROL_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
SYNTHETIC_NUMBERS = [
    1234,
    120_045,
    987_654,
    7_654_321,
    12_345_678,
    23_456_789,
    34_567_890,
    45_678_901,
    56_789_012,
    67_890_123,
    78_901_234,
    98_765_432,
]


def dni_from_number(number: int) -> str:
    if not 0 <= number <= 99_999_999:
        raise ValueError("DNI number must fit in eight decimal digits")
    return f"{number:08d}{CONTROL_LETTERS[number % 23]}"


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def caesar_bytes(text: str, shift: int = 8) -> str:
    """Printable hexadecimal representation of an intentionally weak transform."""
    return bytes((byte + shift) % 256 for byte in text.encode("ascii")).hex()


def synthetic_password_hash(index: int) -> str:
    """Scrypt PHC-like record; no actual password or credential is used."""
    password = f"LAB_ONLY_PASSWORD_{index:03d}".encode()
    salt = hashlib.sha256(f"LAB_SALT_{index:03d}".encode()).digest()[:16]
    derived = hashlib.scrypt(password, salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt$n=16384,r=8,p=1${salt.hex()}${derived.hex()}"


def build_database(output: Path) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    connection = sqlite3.connect(output)
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE staging_identity (
            link_key TEXT PRIMARY KEY,
            nif_plain TEXT NOT NULL,
            synthetic_name TEXT NOT NULL,
            birth_year INTEGER NOT NULL,
            postcode TEXT NOT NULL
        );

        CREATE TABLE customer_core (
            customer_id INTEGER PRIMARY KEY,
            link_key TEXT NOT NULL,
            nif_sha256 TEXT NOT NULL,
            FOREIGN KEY (link_key) REFERENCES staging_identity(link_key)
        );

        CREATE TABLE contact_details (
            link_key TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            policy_number TEXT NOT NULL,
            FOREIGN KEY (link_key) REFERENCES staging_identity(link_key)
        );

        CREATE TABLE financial_profile (
            link_key TEXT NOT NULL,
            iban_surrogate TEXT NOT NULL,
            income_band TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            FOREIGN KEY (link_key) REFERENCES staging_identity(link_key)
        );

        CREATE TABLE case_notes (
            link_key TEXT NOT NULL,
            nif_caesar_hex TEXT NOT NULL,
            synthetic_note TEXT NOT NULL,
            FOREIGN KEY (link_key) REFERENCES staging_identity(link_key)
        );

        CREATE TABLE auth_users (
            link_key TEXT NOT NULL,
            password_kdf_record TEXT NOT NULL,
            FOREIGN KEY (link_key) REFERENCES staging_identity(link_key)
        );

        CREATE TABLE defended_identifiers (
            link_key TEXT NOT NULL,
            public_row_salt TEXT NOT NULL,
            salted_sha256 TEXT NOT NULL,
            hmac_sha256 TEXT NOT NULL,
            random_token TEXT NOT NULL,
            FOREIGN KEY (link_key) REFERENCES staging_identity(link_key)
        );

        CREATE INDEX idx_customer_hash ON customer_core(nif_sha256);
        CREATE INDEX idx_customer_link ON customer_core(link_key);
        CREATE INDEX idx_contact_link ON contact_details(link_key);
        CREATE INDEX idx_financial_link ON financial_profile(link_key);
        CREATE INDEX idx_notes_link ON case_notes(link_key);
        """
    )

    lab_hmac_key = hashlib.sha256(
        b"DEMONSTRATION_KEY_STORED_OUTSIDE_EXFILTRATED_DATABASE"
    ).digest()
    metadata = {
        "dataset": "ENTIRELY_SYNTHETIC",
        "candidate_format": "eight_digits_plus_mod23_letter",
        "identifier_hash": "SHA-256(nif_ascii_uppercase)",
        "weak_obfuscation": "bytewise_caesar_plus_8_then_hex",
        "password_kdf": "scrypt(n=16384,r=8,p=1)",
        "hmac_key_location": "external_to_database_for_lab",
        "record_count": str(len(SYNTHETIC_NUMBERS)),
    }
    connection.executemany(
        "INSERT INTO metadata(key, value) VALUES (?, ?)", metadata.items()
    )

    for index, number in enumerate(SYNTHETIC_NUMBERS, start=1):
        nif = dni_from_number(number)
        link_key = hashlib.sha256(f"LINK-{index:03d}".encode()).hexdigest()[:24]
        row_salt = hashlib.sha256(f"ROW-SALT-{index:03d}".encode()).hexdigest()[:32]
        token = hashlib.sha256(f"RANDOM-LAB-TOKEN-{index:03d}".encode()).hexdigest()[:32]

        connection.execute(
            """
            INSERT INTO staging_identity
                (link_key, nif_plain, synthetic_name, birth_year, postcode)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                link_key,
                nif,
                f"PERSONA_SINTETICA_{index:03d}",
                1965 + (index * 3) % 35,
                f"{28_000 + index:05d}",
            ),
        )
        connection.execute(
            """
            INSERT INTO customer_core(customer_id, link_key, nif_sha256)
            VALUES (?, ?, ?)
            """,
            (index, link_key, sha256_hex(nif)),
        )
        connection.execute(
            """
            INSERT INTO contact_details(link_key, email, phone, policy_number)
            VALUES (?, ?, ?, ?)
            """,
            (
                link_key,
                f"persona{index:03d}@example.invalid",
                f"+3491000{index:04d}",
                f"POL-LAB-{index:08d}",
            ),
        )
        connection.execute(
            """
            INSERT INTO financial_profile
                (link_key, iban_surrogate, income_band, risk_score)
            VALUES (?, ?, ?, ?)
            """,
            (
                link_key,
                f"ES00-LAB-{index:016d}",
                ["LOW", "MEDIUM", "HIGH"][index % 3],
                400 + (index * 37) % 450,
            ),
        )
        connection.execute(
            """
            INSERT INTO case_notes(link_key, nif_caesar_hex, synthetic_note)
            VALUES (?, ?, ?)
            """,
            (
                link_key,
                caesar_bytes(nif),
                f"NOTA_SINTETICA_SIN_DATOS_PERSONALES_{index:03d}",
            ),
        )
        connection.execute(
            """
            INSERT INTO auth_users(link_key, password_kdf_record)
            VALUES (?, ?)
            """,
            (link_key, synthetic_password_hash(index)),
        )
        connection.execute(
            """
            INSERT INTO defended_identifiers
                (link_key, public_row_salt, salted_sha256, hmac_sha256, random_token)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                link_key,
                row_salt,
                sha256_hex(row_salt + nif),
                hmac.new(lab_hmac_key, nif.encode("ascii"), hashlib.sha256).hexdigest(),
                token,
            ),
        )

    connection.commit()
    counts = {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in (
            "staging_identity",
            "customer_core",
            "contact_details",
            "financial_profile",
            "case_notes",
            "auth_users",
            "defended_identifiers",
        )
    }
    connection.close()
    return {
        "database": str(output),
        "synthetic": True,
        "counts": counts,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("lab/synthetic_identity.db"),
    )
    args = parser.parse_args()
    print(json.dumps(build_database(args.output), indent=2))


if __name__ == "__main__":
    main()

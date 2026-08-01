from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from generate_lab import CONTROL_LETTERS, build_database, dni_from_number  # noqa: E402
from run_reconstruction import reconstruct, reverse_caesar_hex  # noqa: E402


class TestDniFormat(unittest.TestCase):
    def test_known_check_letter_example(self) -> None:
        self.assertEqual(dni_from_number(12_345_678), "12345678Z")

    def test_domain_edges(self) -> None:
        self.assertEqual(dni_from_number(0), "00000000T")
        self.assertEqual(
            dni_from_number(99_999_999),
            f"99999999{CONTROL_LETTERS[99_999_999 % 23]}",
        )

    def test_invalid_numbers(self) -> None:
        with self.assertRaises(ValueError):
            dni_from_number(-1)
        with self.assertRaises(ValueError):
            dni_from_number(100_000_000)

    def test_weak_obfuscation_reverse(self) -> None:
        original = "12345678Z"
        encoded = bytes((byte + 8) % 256 for byte in original.encode()).hex()
        self.assertEqual(reverse_caesar_hex(encoded), original)


class TestEndToEnd(unittest.TestCase):
    def test_short_domain_reconstruction(self) -> None:
        cracker = ROOT / "build" / "dni_sha256_enum"
        if not cracker.exists():
            self.skipTest("Native cracker has not been built")

        with tempfile.TemporaryDirectory(prefix="dni-lab-test-") as directory:
            base = Path(directory)
            database = base / "lab.db"
            output = base / "report.json"
            build_database(database)

            connection = sqlite3.connect(database)
            connection.execute(
                "DELETE FROM customer_core WHERE customer_id > 3"
            )
            for table in (
                "staging_identity",
                "contact_details",
                "financial_profile",
                "case_notes",
                "auth_users",
                "defended_identifiers",
            ):
                connection.execute(
                    f"""
                    DELETE FROM {table}
                    WHERE link_key NOT IN (SELECT link_key FROM customer_core)
                    """
                )
            connection.commit()
            connection.close()

            report = reconstruct(
                database,
                cracker,
                output,
                limit=1_000_000,
                threads=1,
            )
            self.assertEqual(report["target_hashes"], 3)
            self.assertEqual(report["recovered_hashes"], 3)
            self.assertEqual(report["cracking"]["threads"], 1)
            self.assertEqual(report["consistency_failures"], [])
            self.assertEqual(len(report["identity_packages"]), 3)
            self.assertTrue(output.exists())

            saved = json.loads(output.read_text())
            matches = {
                item["dni"]: item["sha256"] for item in saved["cracking"]["matches"]
            }
            for package in saved["identity_packages"]:
                nif = package["recovered_nif"]
                self.assertEqual(
                    hashlib.sha256(nif.encode()).hexdigest(),
                    matches[nif],
                )


if __name__ == "__main__":
    unittest.main()

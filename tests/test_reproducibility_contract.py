import hashlib
import os
import tempfile
import unittest

from reality_audit.data_analysis.reproducibility_contract import (
    artifact_name, build_reproducibility_contract, normalize_mode, sha256_file,
)


class ReproducibilityContractTests(unittest.TestCase):
    def test_confirmatory_alias_is_normalized(self):
        self.assertEqual(normalize_mode("preregistered_confirmatory"), "confirmatory")

    def test_artifact_name_is_machine_detectable(self):
        self.assertEqual(
            artifact_name(16, "confirmatory", "fermi", "run42", "manifest"),
            "16_confirmatory_fermi_run42_manifest.json",
        )

    def test_artifact_name_rejects_path_injection(self):
        with self.assertRaises(ValueError):
            artifact_name(16, "confirmatory", "fermi", "../run", "manifest")

    def test_contract_records_input_digest_and_controls(self):
        with tempfile.NamedTemporaryFile(delete=False) as handle:
            handle.write(b"audit-input")
            path = handle.name
        try:
            contract = build_reproducibility_contract(
                stage=14, run_mode="preregistered_confirmatory", catalog="multi",
                run_id="gate", input_files=[path], seed=42,
                null_model={"fermi": "exposure_corrected"}, axis_count=192,
                trial_correction_method="holm", preregistration_locked=True,
            )
            self.assertEqual(contract["run_mode"], "confirmatory")
            self.assertEqual(contract["inputs"][0]["sha256"],
                             hashlib.sha256(b"audit-input").hexdigest())
            self.assertEqual(contract["trial_correction_method"], "holm")
            self.assertTrue(contract["preregistration_locked"])
        finally:
            os.unlink(path)

    def test_missing_input_is_explicit(self):
        self.assertIsNone(sha256_file("does-not-exist.json"))


if __name__ == "__main__":
    unittest.main()


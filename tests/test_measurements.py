import unittest
from reality_audit.measurement import MeasurementSuite

class MeasurementSuiteTests(unittest.TestCase):
    def setUp(self):
        self.path = [
            {"time": 0.0, "measured_position": (0.0, 0.0), "measured_velocity": (0.0, 0.0), "heading": 0.0, "hidden_state": {"position": (0.0, 0.0)}},
            {"time": 0.1, "measured_position": (0.5, 0.1), "measured_velocity": (1.0, 0.2), "heading": 0.05, "hidden_state": {"position": (0.5, 0.1)}},
            {"time": 0.2, "measured_position": (1.0, 0.2), "measured_velocity": (1.0, 0.1), "heading": 0.1, "hidden_state": {"position": (1.0, 0.2)}},
        ]

    def test_position_error(self):
        error = MeasurementSuite.position_error(self.path, (1.0, 0.0))
        self.assertGreater(error, 0.0)

    def test_convergence_time(self):
        time = MeasurementSuite.convergence_time(self.path, (1.0, 0.2), tolerance=0.05)
        self.assertEqual(time, 0.2)

    def test_quantization_artifact_score(self):
        score = MeasurementSuite.quantization_artifact_score(self.path)
        self.assertIsInstance(score, float)

if __name__ == "__main__":
    unittest.main()

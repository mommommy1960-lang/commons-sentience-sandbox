import unittest

from commons_sentience_sim.core.memory import EpisodicMemory


class MemoryProvenanceTests(unittest.TestCase):
    def test_memory_has_nonempty_source(self):
        memory = EpisodicMemory(summary="observed event")
        self.assertTrue(memory.source)

    def test_memory_source_survives_serialization(self):
        memory = EpisodicMemory(summary="system event", source="system")
        self.assertEqual(memory.to_dict()["source"], "system")


if __name__ == "__main__":
    unittest.main()

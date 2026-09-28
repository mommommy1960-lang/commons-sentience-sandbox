import unittest
import xml.etree.ElementTree as ET

from chromaskin.demo import render_theme


PANELS = [
    {"name": "wall-left", "x": 0, "y": 0, "width": 320, "height": 240},
    {"name": "wall-right", "x": 320, "y": 0, "width": 320, "height": 240},
]


class ChromaSkinDemoTests(unittest.TestCase):
    def test_two_panels_share_one_scene_without_resetting_at_seam(self):
        root = ET.fromstring(render_theme(PANELS))
        ns = {"s": "http://www.w3.org/2000/svg"}
        self.assertEqual(root.attrib["viewBox"], "0 0 640 240")
        groups = root.findall("s:g", ns)
        self.assertEqual(len(groups), 2)
        self.assertTrue(all(group.find("s:rect", ns).attrib["width"] == "640" for group in groups))
        self.assertEqual(render_theme(PANELS), render_theme(PANELS))

    def test_fireplace_and_escaped_panel_name_are_valid_svg(self):
        panels = [{**PANELS[0], "name": 'wall"<&'}]
        root = ET.fromstring(render_theme(panels, "fireplace"))
        self.assertEqual(root.find("{http://www.w3.org/2000/svg}g").attrib["data-panel"], 'wall"<&')

    def test_invalid_geometry_fails_closed(self):
        invalid = [
            [{**PANELS[0], "width": 0}],
            [{**PANELS[0], "x": float("nan")}],
            [PANELS[0], {**PANELS[1], "x": 319}],
            [{**PANELS[0], "width": 10001}],
        ]
        for panels in invalid:
            with self.subTest(panels=panels), self.assertRaises(ValueError):
                render_theme(panels)


if __name__ == "__main__":
    unittest.main()

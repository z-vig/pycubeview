"""Unit tests for pycubeview.util_classes module."""

import unittest

from pycubeview.util_classes import PixelValue


class TestPixelValue(unittest.TestCase):
    """Test cases for PixelValue class."""

    def setUp(self) -> None:
        self.single_pixel_val = PixelValue(v=1.1, pixel_type="single")
        self.rgb_pixel_val = PixelValue(r=0.4, g=0.5, b=0.1, pixel_type="rgb")
        self.null_pixel_val = PixelValue.null()

    def test_single(self):
        self.assertEqual(
            self.single_pixel_val.v, 1.1, "Single Pixel Value is wrong"
        )

    def test_rgb(self):
        self.assertEqual(
            self.rgb_pixel_val.r, 0.4, "RGB value is wrong in the R channel."
        )
        self.assertEqual(
            self.rgb_pixel_val.g, 0.5, "RGB value is wrong in the G channel."
        )
        self.assertEqual(
            self.rgb_pixel_val.b, 0.1, "RGB value is wrong in the B channel."
        )

    def test_null(self):
        self.assertEqual(self.null_pixel_val.v, -999.0, "Null Value is wrong.")
        self.assertEqual(self.null_pixel_val.r, -999.0, "Null R is wrong.")
        self.assertEqual(self.null_pixel_val.g, -999.0, "Null G is wrong.")
        self.assertEqual(self.null_pixel_val.b, -999.0, "Null B is wrong.")

    def test_defaults(self):
        """Default construction yields zeros and 'single' pixel_type."""
        default = PixelValue()
        self.assertEqual(default.v, 0.0)
        self.assertEqual(default.r, 0.0)
        self.assertEqual(default.g, 0.0)
        self.assertEqual(default.b, 0.0)
        self.assertEqual(default.pixel_type, "single")

    def test_equality_and_repr(self):
        """Dataclass equality works and repr contains class name."""
        a = PixelValue(v=1.0, r=2.0, g=3.0, b=4.0, pixel_type="rgb")
        b = PixelValue(v=1.0, r=2.0, g=3.0, b=4.0, pixel_type="rgb")
        self.assertEqual(a, b)
        self.assertIn("PixelValue", repr(a))

    def test_mixed_values_and_types(self):
        """
        Mixed initialization stores values and keeps numeric types as float.
        """
        mixed = PixelValue(v=5, r=10.5, pixel_type="single")
        # ints are accepted at runtime but stored according to annotation.
        self.assertAlmostEqual(mixed.v, 5)
        self.assertAlmostEqual(mixed.r, 10.5)
        self.assertEqual(mixed.pixel_type, "single")

    def test_null_returns_floats(self):
        """Ensure null sentinel values are floats (not ints)."""
        self.assertIsInstance(self.null_pixel_val.v, float)
        self.assertIsInstance(self.null_pixel_val.r, float)
        self.assertIsInstance(self.null_pixel_val.g, float)
        self.assertIsInstance(self.null_pixel_val.b, float)


if __name__ == "__main__":
    unittest.main()

"""Tests for GRIM the desktop reaper. Run: python3 -m unittest -v test_reaper"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image

import make_sprites as ms
from questions import BANK

HERE = os.path.dirname(os.path.abspath(__file__))


class SpriteAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.right = os.path.join(HERE, "assets", "reaper.png")
        cls.left = os.path.join(HERE, "assets", "reaper_flip.png")
        if not (os.path.exists(cls.right) and os.path.exists(cls.left)):
            raise unittest.SkipTest("sprites not built yet (make_sprites.py)")

    def test_assets_are_transparent_pngs(self):
        im = Image.open(self.right)
        self.assertEqual(im.mode, "RGBA")
        self.assertLess(im.getchannel("A").getextrema()[0], 250)  # real alpha
        hist = im.getchannel("A").histogram()
        coverage = sum(hist[41:]) / (im.width * im.height)
        self.assertGreater(coverage, 0.10)  # something is drawn
        self.assertLess(coverage, 0.80)     # but it's not a solid block

    def test_flip_is_mirror(self):
        a = Image.open(self.right)
        b = Image.open(self.left)
        self.assertEqual(a.size, b.size)
        self.assertEqual(a.transpose(Image.FLIP_LEFT_RIGHT).tobytes(),
                         b.tobytes())


class KnockoutTests(unittest.TestCase):
    def make_image(self, w, h, box):
        """White canvas with a solid black rectangle (the 'figure')."""
        im = Image.new("RGBA", (w, h), (255, 255, 255, 255))
        for y in range(box[1], box[3]):
            for x in range(box[0], box[2]):
                im.putpixel((x, y), (10, 10, 10, 255))
        return im

    def test_backgroundish_classification(self):
        colors = [(255, 255, 255), (204, 204, 204), (10, 10, 10),
                  (200, 60, 60), (180, 200, 190)]
        im = Image.new("RGBA", (len(colors), 1))
        px = im.load()
        for i, c in enumerate(colors):
            px[i, 0] = c
        got = [ms.backgroundish(px, i, 0) for i in range(len(colors))]
        self.assertEqual(got, [True, True, False, False, False])

    def test_knockout_removes_only_connected_background(self):
        # wide margins so the closing kernel can't eat the ring
        im = self.make_image(60, 50, (15, 10, 45, 40))
        alpha = ms.knock_out_background(im)
        self.assertEqual(alpha.getpixel((0, 0)), 0)          # corner removed
        self.assertEqual(alpha.getpixel((30, 8)), 0)         # above the box
        self.assertEqual(alpha.getpixel((30, 25)), 255)      # inside figure
        self.assertEqual(alpha.getpixel((15, 10)), 255)      # figure edge

    def test_enclosed_pale_hollow_cleared(self):
        # black figure with a pure-white hollow inside, connected to the
        # outside by a thin pale anti-alias channel (the chest-hole case)
        im = self.make_image(80, 60, (20, 15, 60, 45))
        for y in range(25, 35):
            for x in range(30, 50):
                im.putpixel((x, y), (255, 255, 255, 255))    # pale hollow
        for x in range(59, 80):
            im.putpixel((x, 30), (250, 250, 250, 255))       # leak channel
        alpha = ms.knock_out_background(im)
        self.assertEqual(alpha.getpixel((40, 30)), 0)        # hollow cleared
        self.assertEqual(alpha.getpixel((2, 2)), 0)          # outer bg removed
        self.assertEqual(alpha.getpixel((21, 16)), 255)      # figure edge kept

    def test_shaded_enclosed_region_stays_solid(self):
        # skull-like content: light but with real shading (dark pixels),
        # so it must NOT be knocked out even though it is enclosed
        im = self.make_image(80, 60, (20, 15, 60, 45))
        for y in range(25, 35):
            for x in range(30, 50):
                shade = 255 if (x + y) % 2 else 190          # shaded bone
                im.putpixel((x, y), (shade, shade, shade, 255))
        alpha = ms.knock_out_background(im)
        self.assertEqual(alpha.getpixel((40, 30)), 255)      # shading kept


class BankHasReaperFood(unittest.TestCase):
    def test_enough_questions_per_subject(self):
        for subj in ("ML", "DSA", "LA"):
            n = sum(1 for q in BANK if q.subject == subj)
            self.assertGreaterEqual(n, 20, subj)


if __name__ == "__main__":
    unittest.main()

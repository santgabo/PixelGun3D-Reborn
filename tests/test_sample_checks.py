import io
import struct
import unittest
import wave

from tools.sample_checks import inspect_obj, inspect_wav

OBJ = """mtllib bench.mtl
v 0 0 0
v 1 0 0
v 0 1 0
vt 0 0
vt 1 0
vt 0 1
vn 0 0 1
usemtl atlas
f 1/1/1 2/2/1 3/3/1
"""


def wav(values, rate=32000):
    result = io.BytesIO()
    with wave.open(result, "wb") as audio:
        audio.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        audio.writeframes(struct.pack("<" + "h" * len(values), *values))
    return result.getvalue()


class SampleChecksTests(unittest.TestCase):
    def test_obj_geometry_and_material(self):
        obj = inspect_obj(OBJ)
        self.assertEqual(len(obj["vertices"]), 3)
        self.assertEqual(obj["libraries"], ["bench.mtl"])
        self.assertEqual(obj["materials"], ["atlas"])

    def test_obj_rejects_missing_uv_bad_indices_and_nan(self):
        for text in [OBJ.replace("3/3/1", "4/3/1"), OBJ.replace("vt 0 1\n", ""),
                     OBJ.replace("v 1 0 0", "v nan 0 0"), "v 0 0 0\n"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                inspect_obj(text)

    def test_wav_signal_statistics(self):
        info = inspect_wav(wav([0, 1000, -1000, 32767]))
        self.assertEqual(info["frames"], 4)
        self.assertEqual(info["sample_rate"], 32000)
        self.assertEqual(info["clipped_sample_fraction"], 0.25)
        self.assertGreater(info["rms_normalized"], 0)

    def test_wav_rejects_silence_empty_and_truncated(self):
        for data in [wav([0] * 4), wav([]), wav([1000] * 4)[:-2]]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                inspect_wav(data)


if __name__ == "__main__":
    unittest.main()

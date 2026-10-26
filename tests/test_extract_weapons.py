import unittest

from tools.extract_weapons import choose_primary, disambiguate, is_arm, slugify


class WeaponClassificationTests(unittest.TestCase):
    def test_slug_keeps_the_readable_name(self):
        self.assertEqual(slugify("AK-48"), "ak-48")
        self.assertEqual(slugify("Pixel Gun"), "pixel-gun")
        self.assertEqual(slugify("Acid Cannon (tier 1)"), "acid-cannon-tier-1")

    def test_arms_are_not_the_weapon_mesh(self):
        self.assertTrue(is_arm("Arms_Mesh"))
        self.assertTrue(is_arm("FPS_PLAYER_Arm_left"))
        self.assertTrue(is_arm("player001"))
        self.assertFalse(is_arm("SparklyBlaster_Mesh"))
        self.assertFalse(is_arm("Scythe_Mesh"))
        self.assertFalse(is_arm("Dater_Arms"))

    def test_primary_is_the_gun_not_the_hands(self):
        gun = {"object_name": "SparklyBlaster_Mesh", "role": "weapon", "vertices": 600, "source_glb": "gun.glb"}
        arms = {"object_name": "Arms_Mesh", "role": "arm", "vertices": 800, "source_glb": "arms.glb"}
        chosen = choose_primary([arms, gun])
        self.assertIs(chosen, gun)

    def test_fist_falls_back_to_the_viewmodel(self):
        arms = {"object_name": "Arms_Mesh", "role": "arm", "vertices": 40, "source_glb": "arms.glb"}
        chosen = choose_primary([arms])
        self.assertEqual(chosen["role"], "viewmodel")

    def test_shared_name_uses_tier_when_the_mesh_is_the_same(self):
        weapons = [
            {"name": "Acid Cannon", "tier": 1, "number": 438, "id": "weapon438", "aliases": [],
             "primary": {"object_name": "AcidCannon_Mesh", "mesh_name": "AcidCannon_Mesh"}},
            {"name": "Acid Cannon", "tier": 3, "number": 439, "id": "weapon439", "aliases": [],
             "primary": {"object_name": "AcidCannon_Mesh", "mesh_name": "AcidCannon_Mesh"}},
        ]
        disambiguate(weapons)
        self.assertEqual([item["name"] for item in weapons], ["Acid Cannon (tier 1)", "Acid Cannon (tier 3)"])


if __name__ == "__main__":
    unittest.main()

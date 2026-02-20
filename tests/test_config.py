"""Tests for config seal definitions."""

import config


class TestSealConfig:
    def test_twelve_seals(self):
        assert len(config.SEAL_NAMES) == 12

    def test_all_seals_have_display_names(self):
        for seal in config.SEAL_NAMES:
            assert seal in config.SEAL_DISPLAY, f"Missing display name for {seal}"

    def test_seal_images_exist(self):
        for seal in config.SEAL_NAMES:
            path = config.seal_image_path(seal)
            assert path.exists(), f"Missing image for {seal}: {path}"

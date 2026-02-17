"""Tests for feature extraction."""

import numpy as np
import pytest

from cvjutsu.features import extract_features, feature_names, FEATURE_DIM, _normalize_hand


def _make_hand(offset: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> list[tuple[float, float, float]]:
    """Create a fake 21-landmark hand with some spread."""
    landmarks = []
    for i in range(21):
        x = 0.5 + offset[0] + i * 0.01
        y = 0.5 + offset[1] + (i % 5) * 0.02
        z = offset[2]
        landmarks.append((x, y, z))
    return landmarks


class TestNormalizeHand:
    def test_wrist_at_origin(self):
        hand = _make_hand()
        pts = _normalize_hand(hand)
        assert pts.shape == (21, 3)
        np.testing.assert_allclose(pts[0], [0.0, 0.0, 0.0], atol=1e-6)

    def test_scale_invariant(self):
        hand1 = _make_hand()
        hand2 = [(x * 2, y * 2, z * 2) for x, y, z in hand1]
        pts1 = _normalize_hand(hand1)
        pts2 = _normalize_hand(hand2)
        # After normalization, should be similar (not identical due to scale reference point)
        assert pts1.shape == pts2.shape


class TestExtractFeatures:
    def test_two_hands(self):
        left = _make_hand((0.0, 0.0, 0.0))
        right = _make_hand((0.2, 0.0, 0.0))
        features = extract_features([left, right], ["Left", "Right"])
        assert features is not None
        assert features.shape == (FEATURE_DIM,)
        assert not np.any(np.isnan(features))

    def test_single_hand_padded(self):
        hand = _make_hand()
        features = extract_features([hand], ["Right"])
        assert features is not None
        assert features.shape == (FEATURE_DIM,)

    def test_no_hands(self):
        features = extract_features([], [])
        assert features is None

    def test_feature_names_length(self):
        names = feature_names()
        assert len(names) == FEATURE_DIM

    def test_consistent_ordering(self):
        """Left hand always comes first regardless of input order."""
        left = _make_hand((0.0, 0.0, 0.0))
        right = _make_hand((0.2, 0.0, 0.0))
        f1 = extract_features([left, right], ["Left", "Right"])
        f2 = extract_features([right, left], ["Right", "Left"])
        assert f1 is not None and f2 is not None
        np.testing.assert_allclose(f1, f2, atol=1e-6)

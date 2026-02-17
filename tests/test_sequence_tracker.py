"""Tests for sequence tracker."""

import time
from unittest.mock import patch

import pytest

from cvjutsu.sequence_tracker import SequenceTracker


class TestSequenceTracker:
    def setup_method(self):
        self.tracker = SequenceTracker()

    def _feed_seal(self, seal: str, confidence: float = 0.9, frames: int = 6):
        """Feed a seal for enough frames to get it confirmed."""
        state = None
        for _ in range(frames):
            state = self.tracker.update(seal, confidence)
        return state

    def test_none_predictions_no_confirm(self):
        """None predictions should not confirm any seal."""
        for _ in range(10):
            state = self.tracker.update(None, 0.0)
        assert len(state.confirmed_sequence) == 0
        assert state.current_seal is None

    def test_seal_confirmed_after_hold(self):
        state = self._feed_seal("tora")
        # Should be confirmed at some point
        assert "tora" in state.confirmed_sequence

    def test_sequence_builds(self):
        self._feed_seal("mi")
        # Need to break the streak to allow next seal
        self.tracker.update(None, 0.0)
        self.tracker.update(None, 0.0)
        self.tracker.update(None, 0.0)
        state = self._feed_seal("hitsuji")
        assert state.confirmed_sequence == ["mi", "hitsuji"]

    def test_fireball_jutsu_match(self):
        """Mi → Hitsuji → Tora should match Fireball."""
        for seal in ["mi", "hitsuji", "tora"]:
            self._feed_seal(seal)
            # Clear window between seals
            for _ in range(3):
                self.tracker.update(None, 0.0)

        # The last feed should have matched
        state = self._feed_seal("tora")
        # Check that the fireball was matched at some point
        assert state.matched_jutsu is not None
        assert "Fireball" in state.matched_jutsu.display or state.matched_jutsu.name == "katon_goukakyu"

    def test_chidori_match(self):
        """Ushi → Tori → Hitsuji should match Chidori."""
        for seal in ["ushi", "tori", "hitsuji"]:
            self._feed_seal(seal)
            for _ in range(3):
                self.tracker.update(None, 0.0)

        state = self._feed_seal("hitsuji")
        assert state.matched_jutsu is not None
        assert state.matched_jutsu.name == "chidori"

    def test_low_confidence_ignored(self):
        """Predictions below threshold should not confirm."""
        state = self._feed_seal("tora", confidence=0.3)
        assert len(state.confirmed_sequence) == 0

    def test_reset_clears_state(self):
        self._feed_seal("tora")
        self.tracker.reset()
        state = self.tracker.update(None, 0.0)
        assert len(state.confirmed_sequence) == 0
        assert state.matched_jutsu is None

    def test_single_seal_delay(self):
        """Shadow Clone (single hitsuji) should have a delay before triggering."""
        state = self._feed_seal("hitsuji")
        # Should NOT immediately match (delay required)
        assert not state.jutsu_just_matched

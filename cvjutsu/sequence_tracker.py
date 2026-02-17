"""State machine: noisy predictions → stable seals → jutsu match.

Uses prediction smoothing (rolling window majority vote), then tracks
confirmed seals into a sequence. Matches sequences to jutsu using
suffix matching (longest-match-first). Single-seal jutsu have a delay
to avoid false triggers when longer sequences end with the same seal.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field

import config
from cvjutsu.jutsu_db import JUTSU_LIST, Jutsu


@dataclass
class TrackerState:
    """Current state of the sequence tracker."""
    current_seal: str | None = None
    current_confidence: float = 0.0
    confirmed_sequence: list[str] = field(default_factory=list)
    matched_jutsu: Jutsu | None = None
    seal_just_confirmed: bool = False
    jutsu_just_matched: bool = False


class SequenceTracker:
    """Converts noisy per-frame predictions into stable seal confirmations
    and matches them to known jutsu."""

    def __init__(self) -> None:
        self._window: deque[str | None] = deque(maxlen=config.SEAL_HOLD_FRAMES)
        self._last_confirmed: str | None = None
        self._sequence: list[str] = []
        self._last_seal_time: float = 0.0
        self._pending_single_jutsu: Jutsu | None = None
        self._pending_single_time: float = 0.0
        self._matched_jutsu: Jutsu | None = None

    def update(self, seal: str | None, confidence: float) -> TrackerState:
        """Process one frame's prediction and return the current state.

        Args:
            seal: Predicted seal label, or None if below threshold.
            confidence: Prediction confidence [0, 1].

        Returns:
            TrackerState with current status.
        """
        now = time.time()
        state = TrackerState()

        # Check for sequence timeout
        if self._sequence and (now - self._last_seal_time) > config.SEQUENCE_TIMEOUT_SEC:
            self._sequence.clear()
            self._last_confirmed = None
            self._pending_single_jutsu = None

        # Apply confidence threshold
        if seal is not None and confidence < config.CONFIDENCE_THRESHOLD:
            seal = None

        # Add to rolling window
        self._window.append(seal)

        # Majority vote over window
        stable_seal = self._majority_vote()
        state.current_seal = stable_seal
        state.current_confidence = confidence if stable_seal == seal else 0.0

        # Check if this is a newly confirmed seal (different from last)
        if stable_seal is not None and stable_seal != self._last_confirmed:
            self._last_confirmed = stable_seal
            self._sequence.append(stable_seal)
            self._last_seal_time = now
            state.seal_just_confirmed = True

            # Clear any pending single-seal jutsu
            self._pending_single_jutsu = None

            # Try to match a jutsu (longest match first)
            matched = self._match_jutsu()
            if matched is not None:
                if len(matched.seals) == 1:
                    # Delay single-seal jutsu
                    self._pending_single_jutsu = matched
                    self._pending_single_time = now
                else:
                    self._matched_jutsu = matched
                    state.jutsu_just_matched = True
                    state.matched_jutsu = matched
        elif stable_seal is None:
            self._last_confirmed = None

        # Check pending single-seal jutsu delay
        if (
            self._pending_single_jutsu is not None
            and (now - self._pending_single_time) >= config.SINGLE_SEAL_DELAY_SEC
        ):
            self._matched_jutsu = self._pending_single_jutsu
            state.jutsu_just_matched = True
            state.matched_jutsu = self._pending_single_jutsu
            self._pending_single_jutsu = None

        state.confirmed_sequence = list(self._sequence)
        if state.matched_jutsu is None:
            state.matched_jutsu = self._matched_jutsu

        return state

    def _majority_vote(self) -> str | None:
        """Return the most common non-None seal in the window, if it's the majority."""
        counts: dict[str, int] = {}
        for s in self._window:
            if s is not None:
                counts[s] = counts.get(s, 0) + 1

        if not counts:
            return None

        best = max(counts, key=counts.get)  # type: ignore[arg-type]
        # Require majority (more than half the window)
        if counts[best] > len(self._window) // 2:
            return best
        return None

    def _match_jutsu(self) -> Jutsu | None:
        """Check if the current sequence suffix matches any jutsu.
        Longest match wins."""
        best: Jutsu | None = None
        for jutsu in JUTSU_LIST:
            seq_len = len(jutsu.seals)
            if seq_len <= len(self._sequence):
                if self._sequence[-seq_len:] == jutsu.seals:
                    if best is None or len(jutsu.seals) > len(best.seals):
                        best = jutsu
        return best

    def reset(self) -> None:
        """Clear all tracking state."""
        self._window.clear()
        self._last_confirmed = None
        self._sequence.clear()
        self._pending_single_jutsu = None
        self._matched_jutsu = None

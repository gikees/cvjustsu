"""Visual effect overlays for jutsu matches.

Loads transparent PNG sprites and alpha-blends them onto camera frames
with fade-in/fade-out animation.
"""

from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

import config


class EffectOverlay:
    """Manages loading and rendering effect sprites on frames."""

    EFFECT_DURATION = 3.0   # seconds
    FADE_DURATION = 0.5     # seconds for fade in/out

    def __init__(self) -> None:
        self._sprites: dict[str, np.ndarray] = {}
        self._active_effect: str | None = None
        self._effect_start: float = 0.0
        self._load_sprites()

    def _load_sprites(self) -> None:
        """Load all BGRA PNG sprites from assets/effects/."""
        effects_dir = config.EFFECTS_DIR
        if not effects_dir.exists():
            return
        for path in effects_dir.glob("*.png"):
            img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            if img is not None:
                # Ensure BGRA
                if img.shape[2] == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
                self._sprites[path.stem] = img

    def trigger(self, effect_name: str) -> None:
        """Start playing an effect."""
        # Strip .png extension if present
        name = Path(effect_name).stem
        self._active_effect = name
        self._effect_start = time.time()

    def render(self, frame: np.ndarray) -> np.ndarray:
        """Composite active effect onto the frame. Returns the modified frame."""
        if self._active_effect is None:
            return frame

        elapsed = time.time() - self._effect_start
        if elapsed > self.EFFECT_DURATION:
            self._active_effect = None
            return frame

        sprite = self._sprites.get(self._active_effect)
        if sprite is None:
            # No sprite loaded — draw text overlay instead
            return self._render_text_effect(frame, elapsed)

        # Calculate opacity for fade in/out
        opacity = self._calc_opacity(elapsed)

        # Resize sprite to fit frame (centered, 40% of frame size)
        fh, fw = frame.shape[:2]
        target_w = int(fw * 0.4)
        target_h = int(target_w * sprite.shape[0] / sprite.shape[1])
        resized = cv2.resize(sprite, (target_w, target_h))

        # Center position
        x = (fw - target_w) // 2
        y = (fh - target_h) // 2

        # Alpha blend
        frame = self._alpha_blend(frame, resized, x, y, opacity)
        return frame

    def _render_text_effect(self, frame: np.ndarray, elapsed: float) -> np.ndarray:
        """Fallback: render effect name as text overlay."""
        opacity = self._calc_opacity(elapsed)
        if self._active_effect is None:
            return frame

        display_name = self._active_effect.replace("_", " ").upper()
        fh, fw = frame.shape[:2]

        # Semi-transparent background bar
        overlay = frame.copy()
        bar_h = 80
        bar_y = fh // 2 - bar_h // 2
        cv2.rectangle(overlay, (0, bar_y), (fw, bar_y + bar_h), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6 * opacity, frame, 1 - 0.6 * opacity, 0)

        # Text
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 1.5
        thickness = 3
        text_size = cv2.getTextSize(display_name, font, scale, thickness)[0]
        tx = (fw - text_size[0]) // 2
        ty = fh // 2 + text_size[1] // 2

        color = (255, 255, 255)
        alpha_color = tuple(int(c * opacity) for c in color)
        cv2.putText(frame, display_name, (tx, ty), font, scale, alpha_color, thickness)

        return frame

    def _calc_opacity(self, elapsed: float) -> float:
        """Calculate opacity based on fade in/out timing."""
        if elapsed < self.FADE_DURATION:
            return elapsed / self.FADE_DURATION
        elif elapsed > self.EFFECT_DURATION - self.FADE_DURATION:
            return (self.EFFECT_DURATION - elapsed) / self.FADE_DURATION
        return 1.0

    @staticmethod
    def _alpha_blend(
        frame: np.ndarray,
        sprite: np.ndarray,
        x: int,
        y: int,
        opacity: float,
    ) -> np.ndarray:
        """Alpha-blend a BGRA sprite onto a BGR frame at position (x, y)."""
        fh, fw = frame.shape[:2]
        sh, sw = sprite.shape[:2]

        # Clip to frame bounds
        x1, y1 = max(x, 0), max(y, 0)
        x2, y2 = min(x + sw, fw), min(y + sh, fh)
        sx1, sy1 = x1 - x, y1 - y
        sx2, sy2 = sx1 + (x2 - x1), sy1 + (y2 - y1)

        if x2 <= x1 or y2 <= y1:
            return frame

        roi = frame[y1:y2, x1:x2]
        sprite_roi = sprite[sy1:sy2, sx1:sx2]

        alpha = (sprite_roi[:, :, 3:4] / 255.0) * opacity
        blended = roi * (1 - alpha) + sprite_roi[:, :, :3] * alpha
        frame[y1:y2, x1:x2] = blended.astype(np.uint8)

        return frame

    @property
    def is_active(self) -> bool:
        return self._active_effect is not None

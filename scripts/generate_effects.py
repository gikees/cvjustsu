"""
Generate placeholder effect images (BGRA with transparency) using OpenCV and numpy.
  - fireball.png:     orange/red radial gradient circle
  - chidori.png:      blue lightning-like pattern
  - shadow_clone.png: white humanoid silhouette
"""

import cv2
import numpy as np
import os

OUT_DIR = "/Users/gies/dev/nyu/cvjustsu/assets/effects"
SIZE = 300
CENTER = SIZE // 2


def make_fireball():
    """Orange-red circle with a radial gradient on a transparent background."""
    img = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)

    Y, X = np.ogrid[:SIZE, :SIZE]
    dist = np.sqrt((X - CENTER) ** 2 + (Y - CENTER) ** 2).astype(np.float64)
    radius = 120
    mask = dist <= radius
    norm = np.clip(1.0 - dist / radius, 0, 1)

    b = np.zeros((SIZE, SIZE), dtype=np.uint8)
    g = (norm ** 1.5 * 180).astype(np.uint8)
    r = (np.clip(norm * 1.2, 0, 1) * 255).astype(np.uint8)
    a = (norm ** 0.6 * 255).astype(np.uint8)

    img[:, :, 0] = b
    img[:, :, 1] = g
    img[:, :, 2] = r
    img[:, :, 3] = a

    outside = ~mask
    img[outside] = 0

    # Bright hot-spots
    rng = np.random.RandomState(7)
    for _ in range(12):
        angle = rng.uniform(0, 2 * np.pi)
        r_off = rng.uniform(0, radius * 0.6)
        cx = int(CENTER + r_off * np.cos(angle))
        cy = int(CENTER + r_off * np.sin(angle))
        rad = rng.randint(8, 25)
        cv2.circle(img, (cx, cy), rad, (30, 220, 255, 200), -1)

    img = cv2.GaussianBlur(img, (15, 15), 0)
    return img


def make_chidori():
    """Blue lightning-like pattern on a transparent background."""
    img = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)

    rng = np.random.RandomState(42)
    num_bolts = 8
    for i in range(num_bolts):
        angle = 2 * np.pi * i / num_bolts + rng.uniform(-0.2, 0.2)
        pts = [(CENTER, CENTER)]
        segments = 10
        for s in range(1, segments + 1):
            frac = s / segments
            length = frac * 130
            jitter_angle = angle + rng.uniform(-0.5, 0.5)
            x = int(CENTER + length * np.cos(jitter_angle) + rng.randint(-8, 8))
            y = int(CENTER + length * np.sin(jitter_angle) + rng.randint(-8, 8))
            x = int(np.clip(x, 0, SIZE - 1))
            y = int(np.clip(y, 0, SIZE - 1))
            pts.append((x, y))

        for j in range(len(pts) - 1):
            cv2.line(img, pts[j], pts[j + 1], (255, 200, 50, 255), 3)
        for j in range(len(pts) - 1):
            cv2.line(img, pts[j], pts[j + 1], (255, 255, 220, 255), 1)

    cv2.circle(img, (CENTER, CENTER), 25, (255, 220, 100, 255), -1)
    cv2.circle(img, (CENTER, CENTER), 12, (255, 255, 255, 255), -1)

    glow = cv2.GaussianBlur(img.copy(), (31, 31), 0)
    img = np.maximum(img, glow)
    return img


def make_shadow_clone():
    """White humanoid silhouette on a transparent background."""
    img = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
    white = (255, 255, 255, 220)

    cv2.circle(img, (CENTER, 70), 30, white, -1)
    cv2.rectangle(img, (CENTER - 8, 100), (CENTER + 8, 115), white, -1)

    torso = np.array([[CENTER-40,115],[CENTER+40,115],[CENTER+30,200],[CENTER-30,200]])
    cv2.fillPoly(img, [torso], white)

    left_arm = np.array([[CENTER-40,115],[CENTER-45,120],[CENTER-85,175],[CENTER-75,180]])
    cv2.fillPoly(img, [left_arm], white)

    right_arm = np.array([[CENTER+40,115],[CENTER+45,120],[CENTER+85,175],[CENTER+75,180]])
    cv2.fillPoly(img, [right_arm], white)

    left_leg = np.array([[CENTER-30,200],[CENTER-10,200],[CENTER-20,280],[CENTER-35,280]])
    cv2.fillPoly(img, [left_leg], white)

    right_leg = np.array([[CENTER+30,200],[CENTER+10,200],[CENTER+20,280],[CENTER+35,280]])
    cv2.fillPoly(img, [right_leg], white)

    img = cv2.GaussianBlur(img, (5, 5), 0)

    glow = cv2.GaussianBlur(img.copy(), (41, 41), 0)
    glow[:, :, 3] = (glow[:, :, 3].astype(np.float32) * 0.4).astype(np.uint8)
    img = np.maximum(img, glow)
    return img


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    effects = {
        "fireball.png": make_fireball(),
        "chidori.png": make_chidori(),
        "shadow_clone.png": make_shadow_clone(),
    }

    for name, image in effects.items():
        path = os.path.join(OUT_DIR, name)
        cv2.imwrite(path, image)
        print(f"Saved {path}  (shape={image.shape}, dtype={image.dtype})")


if __name__ == "__main__":
    main()

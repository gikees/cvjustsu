"""Global configuration constants."""

from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent
ASSETS_DIR = PROJECT_ROOT / "assets"
EFFECTS_DIR = ASSETS_DIR / "effects"
SEALS_DIR = ASSETS_DIR / "seals"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
MODELS_DIR = DATA_DIR / "models"
MODEL_PATH = MODELS_DIR / "seal_classifier.pkl"

# Camera
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# MediaPipe Hands
MP_MAX_HANDS = 2
MP_MIN_DETECTION_CONFIDENCE = 0.7
MP_MIN_TRACKING_CONFIDENCE = 0.5

# Classifier
RF_N_ESTIMATORS = 100
CONFIDENCE_THRESHOLD = 0.6

# Sequence tracker
SEAL_HOLD_FRAMES = 5        # Frames a seal must be stable to confirm
SEQUENCE_TIMEOUT_SEC = 5.0  # Reset sequence after this idle time
SINGLE_SEAL_DELAY_SEC = 1.5 # Delay before triggering single-seal jutsu

# Hand seals (traditional zodiac order)
SEAL_NAMES = [
    "ne", "ushi", "tora", "u", "tatsu", "mi",
    "uma", "hitsuji", "saru", "tori", "inu", "i",
]
SEAL_DISPLAY = {
    "ne": "Rat",
    "ushi": "Ox",
    "tora": "Tiger",
    "u": "Hare",
    "tatsu": "Dragon",
    "mi": "Snake",
    "uma": "Horse",
    "hitsuji": "Ram",
    "saru": "Monkey",
    "tori": "Bird",
    "inu": "Dog",
    "i": "Boar",
}


def seal_image_path(seal_id: str) -> Path:
    """Return the best available image path for a seal (new JPEG, then old PNG)."""
    english = SEAL_DISPLAY.get(seal_id, seal_id).lower()
    jpeg = SEALS_DIR / f"{english}_{seal_id}.jpeg"
    if jpeg.exists():
        return jpeg
    return SEALS_DIR / f"{seal_id}.png"

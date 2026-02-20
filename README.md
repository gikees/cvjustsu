# CVJutsu — Naruto Hand Seal Recognition

Real-time desktop app that uses a webcam to detect Naruto hand seals via MediaPipe hand landmarks, classifies them with a trained model, tracks seal sequences, matches them to known jutsu, and overlays visual effects on the camera feed.

## Supported Seals

All 12 zodiac seals from the Naruto universe:

| Seal | Japanese | Seal | Japanese |
|------|----------|------|----------|
| Rat | Ne | Horse | Uma |
| Ox | Ushi | Ram | Hitsuji |
| Tiger | Tora | Monkey | Saru |
| Hare | U | Bird | Tori |
| Dragon | Tatsu | Dog | Inu |
| Snake | Mi | Boar | I |

## Supported Jutsu

| Jutsu | Sequence | Element |
|-------|----------|---------|
| Katon: Goukakyu (Fireball) | Snake → Ram → Tiger | Fire |
| Katon: Housenka (Phoenix Flower) | Snake → Tiger | Fire |
| Chidori | Ox → Bird → Ram | Lightning |
| Suiton: Suiryudan (Water Dragon) | Ox → Snake → Dragon → Hare → Bird | Water |
| Doton: Doryuheki (Earth Wall) | Snake → Tiger → Dog → Ox | Earth |
| Kuchiyose (Summoning) | Boar → Dog → Bird → Monkey → Ram | — |
| Kage Bunshin (Shadow Clone) | Ram | — |

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Download the MediaPipe hand landmarker model:

```bash
curl -L -o assets/hand_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
```

## Usage

### Run the app

```bash
python main.py
```

### Collect training data

1. Switch to **Collect Data** mode using the toolbar button
2. Select a seal from the dropdown
3. Perform the hand seal in front of the camera
4. Press **Space** to capture a sample
5. Collect 100+ samples per seal for best results

### Train the model

Either click **Train Model** in the collection panel, or run:

```bash
python scripts/train_model.py
```

### Recognize seals

1. Switch to **Recognize** mode
2. Select a jutsu from the toolbar dropdown to see its required seal sequence
3. Perform the seals — the strip highlights your progress
4. Complete a sequence to trigger the jutsu effect

### Keyboard shortcuts

- **Space** — Capture sample (in collect mode)
- **R** — Reset current sequence

## Evaluate model

```bash
python scripts/evaluate_model.py
```

## Run tests

```bash
pytest tests/
```

## Tech Stack

- Python 3.10+
- PyQt6 (GUI)
- OpenCV (camera/image processing)
- MediaPipe HandLandmarker (21-landmark hand detection)
- scikit-learn RandomForestClassifier (seal classification)
- NumPy / Pandas (feature engineering)

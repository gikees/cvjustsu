"""Save landmark features + labels to CSV files for training."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import config
from cvjutsu.features import extract_features, feature_names, FEATURE_DIM


class DataCollector:
    """Collects labeled feature vectors and saves to per-seal CSV files."""

    def __init__(self, output_dir: Path | None = None) -> None:
        self._output_dir = output_dir or config.RAW_DATA_DIR
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def save_sample(
        self,
        seal_label: str,
        landmarks_list: list[list[tuple[float, float, float]]],
        handedness_list: list[str],
    ) -> bool:
        """Extract features and append to the seal's CSV file.

        Returns True if sample was saved successfully.
        """
        features = extract_features(landmarks_list, handedness_list)
        if features is None:
            return False

        if len(features) != FEATURE_DIM:
            return False

        csv_path = self._output_dir / f"{seal_label}.csv"
        names = feature_names()

        row = pd.DataFrame([features], columns=names)
        row["label"] = seal_label

        if csv_path.exists():
            row.to_csv(csv_path, mode="a", header=False, index=False)
        else:
            row.to_csv(csv_path, index=False)

        return True

    def get_counts(self) -> dict[str, int]:
        """Return sample counts per seal label."""
        counts = {}
        for seal_id in config.SEAL_NAMES:
            csv_path = self._output_dir / f"{seal_id}.csv"
            if csv_path.exists():
                # Count lines minus header
                df = pd.read_csv(csv_path)
                counts[seal_id] = len(df)
            else:
                counts[seal_id] = 0
        return counts

    def load_all(self) -> pd.DataFrame | None:
        """Load all CSV files into a single DataFrame."""
        frames = []
        for seal_id in config.SEAL_NAMES:
            csv_path = self._output_dir / f"{seal_id}.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                frames.append(df)
        if not frames:
            return None
        return pd.concat(frames, ignore_index=True)

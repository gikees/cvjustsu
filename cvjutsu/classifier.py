"""RandomForest classifier for hand seal recognition."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

import config


class SealClassifier:
    """Train, save, load, and predict hand seals with RandomForest."""

    def __init__(self) -> None:
        self._model: RandomForestClassifier | None = None
        self._classes: list[str] = []

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def classes(self) -> list[str]:
        return self._classes

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        n_estimators: int = config.RF_N_ESTIMATORS,
        augment: bool = False,
    ) -> float:
        """Train the classifier and return training accuracy.

        Args:
            X: Feature matrix (n_samples, n_features).
            y: Label array (n_samples,).
            n_estimators: Number of trees.
            augment: If True, add Gaussian noise copies (3x) for data augmentation.

        Returns:
            Training accuracy score.
        """
        if augment:
            rng = np.random.default_rng(42)
            aug_copies = []
            aug_labels = []
            for _ in range(3):
                noise = rng.normal(0.0, 0.05, size=X.shape).astype(X.dtype)
                aug_copies.append(X + noise)
                aug_labels.append(y)
            X = np.concatenate([X] + aug_copies)
            y = np.concatenate([y] + aug_labels)

        self._model = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=42,
            n_jobs=-1,
        )
        self._model.fit(X, y)
        self._classes = list(self._model.classes_)
        return self._model.score(X, y)

    def predict(self, features: np.ndarray) -> tuple[str, float]:
        """Predict seal label and confidence for a single feature vector.

        Returns:
            (predicted_label, confidence) tuple.
        """
        if self._model is None:
            raise RuntimeError("Model not loaded")

        features_2d = features.reshape(1, -1)
        proba = self._model.predict_proba(features_2d)[0]
        best_idx = np.argmax(proba)
        return self._classes[best_idx], float(proba[best_idx])

    def save(self, path: Path | None = None) -> Path:
        """Save model to disk."""
        if self._model is None:
            raise RuntimeError("No model to save")
        path = path or config.MODEL_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self._model, "classes": self._classes}, path)
        return path

    def load(self, path: Path | None = None) -> bool:
        """Load model from disk. Returns True if successful."""
        path = path or config.MODEL_PATH
        if not path.exists():
            return False
        data = joblib.load(path)
        self._model = data["model"]
        self._classes = data["classes"]
        return True

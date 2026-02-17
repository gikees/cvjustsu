"""Tests for the seal classifier."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from cvjutsu.classifier import SealClassifier


class TestSealClassifier:
    def _make_training_data(self, n_per_class: int = 50):
        """Generate synthetic training data for 5 classes."""
        classes = ["tora", "mi", "hitsuji", "tori", "ushi"]
        n_features = 147
        X_parts, y_parts = [], []
        for i, cls in enumerate(classes):
            # Each class centered at different point
            center = np.zeros(n_features)
            center[i * 20:(i + 1) * 20] = 1.0
            samples = center + np.random.randn(n_per_class, n_features) * 0.1
            X_parts.append(samples)
            y_parts.append(np.array([cls] * n_per_class))
        X = np.vstack(X_parts).astype(np.float32)
        y = np.concatenate(y_parts)
        return X, y

    def test_train_and_predict(self):
        X, y = self._make_training_data()
        clf = SealClassifier()
        acc = clf.train(X, y)
        assert acc > 0.8
        assert clf.is_loaded
        assert len(clf.classes) == 5

        # Predict a sample
        label, confidence = clf.predict(X[0])
        assert label == y[0]
        assert 0.0 <= confidence <= 1.0

    def test_save_and_load(self):
        X, y = self._make_training_data()
        clf = SealClassifier()
        clf.train(X, y)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_model.pkl"
            clf.save(path)
            assert path.exists()

            clf2 = SealClassifier()
            assert clf2.load(path)
            assert clf2.is_loaded
            assert clf2.classes == clf.classes

            # Same predictions
            label1, _ = clf.predict(X[0])
            label2, _ = clf2.predict(X[0])
            assert label1 == label2

    def test_load_nonexistent(self):
        clf = SealClassifier()
        assert not clf.load(Path("/tmp/nonexistent_model.pkl"))
        assert not clf.is_loaded

    def test_predict_without_model_raises(self):
        clf = SealClassifier()
        with pytest.raises(RuntimeError):
            clf.predict(np.zeros(147))

"""Standalone training script for the seal classifier."""

import sys
from pathlib import Path

import numpy as np
from sklearn.model_selection import cross_val_score

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from cvjutsu.classifier import SealClassifier
from cvjutsu.data_collector import DataCollector


def main() -> None:
    collector = DataCollector()
    df = collector.load_all()

    if df is None or len(df) == 0:
        print("No training data found. Collect data first using the GUI.")
        sys.exit(1)

    print(f"Loaded {len(df)} samples")
    print(f"Class distribution:\n{df['label'].value_counts().to_string()}\n")

    feature_cols = [c for c in df.columns if c != "label"]
    X = df[feature_cols].values.astype(np.float32)
    y = df["label"].values

    classifier = SealClassifier()

    # Cross-validation
    print("Running 5-fold cross-validation...")
    from sklearn.ensemble import RandomForestClassifier
    rf = RandomForestClassifier(n_estimators=config.RF_N_ESTIMATORS, random_state=42, n_jobs=-1)
    scores = cross_val_score(rf, X, y, cv=min(5, len(np.unique(y))), scoring="accuracy")
    print(f"CV accuracy: {scores.mean():.3f} (+/- {scores.std():.3f})")

    # Train on full data
    print("\nTraining on full dataset...")
    train_acc = classifier.train(X, y, augment=True)
    print(f"Training accuracy: {train_acc:.3f}")

    # Save
    path = classifier.save()
    print(f"\nModel saved to {path}")


if __name__ == "__main__":
    main()

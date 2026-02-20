"""Evaluate trained model with confusion matrix and classification report."""

import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import cross_val_predict

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from cvjutsu.classifier import SealClassifier
from cvjutsu.data_collector import DataCollector
from cvjutsu.features import feature_names


def main() -> None:
    collector = DataCollector()
    df = collector.load_all()

    if df is None or len(df) == 0:
        print("No data found.")
        sys.exit(1)

    feature_cols = [c for c in df.columns if c != "label"]
    X = df[feature_cols].values.astype(np.float32)
    y = df["label"].values

    print(f"Total samples: {len(df)}")
    print(f"Classes: {sorted(np.unique(y))}\n")

    # Cross-validated predictions for unbiased evaluation
    from sklearn.ensemble import RandomForestClassifier
    rf = RandomForestClassifier(n_estimators=config.RF_N_ESTIMATORS, random_state=42, n_jobs=-1)
    n_folds = min(5, min(np.bincount(np.unique(y, return_inverse=True)[1])))
    if n_folds < 2:
        print("Not enough samples per class for cross-validation.")
        sys.exit(1)

    y_pred = cross_val_predict(rf, X, y, cv=n_folds)

    print("Classification Report (cross-validated):")
    print(classification_report(y, y_pred, target_names=sorted(np.unique(y))))

    print("Confusion Matrix:")
    labels = sorted(np.unique(y))
    cm = confusion_matrix(y, y_pred, labels=labels)
    # Print with labels
    header = "        " + " ".join(f"{l:>8}" for l in labels)
    print(header)
    for i, label in enumerate(labels):
        row = " ".join(f"{cm[i, j]:>8}" for j in range(len(labels)))
        print(f"{label:>8} {row}")

    # Feature importance
    print("\nFeature Importance (top 20):")
    rf.fit(X, y)
    names = feature_names()
    importances = rf.feature_importances_
    indices = np.argsort(importances)[::-1][:20]
    for rank, idx in enumerate(indices, 1):
        name = names[idx] if idx < len(names) else f"feature_{idx}"
        print(f"  {rank:>2}. {name:<35} {importances[idx]:.4f}")


if __name__ == "__main__":
    main()

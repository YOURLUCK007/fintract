"""CLI to (re)train and persist ML models.

Usage:
    python -m app.ml.train
"""
from __future__ import annotations

from sklearn.model_selection import cross_val_score

from .categorizer import train_model
from .dataset import TRAINING_DATA


def main() -> None:
    print(f"Training categorizer on {len(TRAINING_DATA)} labeled samples...")
    pipe = train_model(save=True)

    texts = [t for t, _ in TRAINING_DATA]
    labels = [c for _, c in TRAINING_DATA]
    scores = cross_val_score(pipe, texts, labels, cv=3)
    print(f"Categorizer 3-fold CV accuracy: {scores.mean():.3f} (+/- {scores.std():.3f})")
    print("Saved model artifacts. Done.")


if __name__ == "__main__":
    main()

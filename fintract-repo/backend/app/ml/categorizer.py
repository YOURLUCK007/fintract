"""Expense auto-categorization using a TF-IDF + Naive Bayes text classifier.

Trained on an in-repo labeled corpus (``dataset.TRAINING_DATA``). The model is
persisted with joblib and loaded lazily. If the model file is missing it is
trained on first use, so the API works out of the box with no separate step.
"""
from __future__ import annotations

import os
import re
import threading

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from .dataset import TRAINING_DATA

MODEL_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_PATH = os.path.join(MODEL_DIR, "categorizer.joblib")

_CATEGORIES = [
    "Food", "Travel", "Shopping", "Bills", "Healthcare",
    "Entertainment", "Education", "Investments", "Others",
]

# Regex fallback used when the model is very unsure (low confidence).
_KEYWORDS: list[tuple[str, str]] = [
    (r"swiggy|zomato|restaurant|dinner|lunch|grocery|bigbasket|blinkit|food|cafe|pizza|coffee|bakery", "Food"),
    (r"uber|ola|petrol|diesel|fuel|flight|train|metro|cab|taxi|travel|airport|toll|parking|rapido", "Travel"),
    (r"amazon|myntra|flipkart|ajio|apparel|shoe|shopping|mall|zara|nike|ikea|furniture", "Shopping"),
    (r"electricity|bill|recharge|water|gas|broadband|rent|wifi|dth|insurance|maintenance", "Bills"),
    (r"pharmacy|apollo|hospital|doctor|medic|health|dental|clinic|lab test|vaccin", "Healthcare"),
    (r"netflix|spotify|prime|hotstar|movie|game|concert|entertain|bookmyshow|youtube", "Entertainment"),
    (r"course|udemy|coursera|book|tuition|school|college|education|exam|coaching|certification", "Education"),
    (r"sip|stock|mutual|index|invest|etf|gold bond|fixed deposit|ppf|crypto|nps|zerodha", "Investments"),
]

_model: Pipeline | None = None
_lock = threading.Lock()


def train_model(save: bool = True) -> Pipeline:
    """Train and (optionally) persist the categorization pipeline."""
    texts = [t for t, _ in TRAINING_DATA]
    labels = [c for _, c in TRAINING_DATA]
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("clf", MultinomialNB(alpha=0.15)),
    ])
    pipe.fit(texts, labels)
    if save:
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(pipe, MODEL_PATH)
    return pipe


def _get_model() -> Pipeline:
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                if os.path.exists(MODEL_PATH):
                    _model = joblib.load(MODEL_PATH)
                else:
                    _model = train_model(save=True)
    return _model


def _regex_category(description: str) -> str:
    d = description.lower()
    for pattern, cat in _KEYWORDS:
        if re.search(pattern, d):
            return cat
    return "Others"


def categorize(description: str) -> tuple[str, float]:
    """Return (category, confidence in 0..1) for a free-text description."""
    text = (description or "").strip()
    if not text:
        return "Others", 0.0

    model = _get_model()
    probs = model.predict_proba([text])[0]
    classes = list(model.named_steps["clf"].classes_)
    best_idx = int(probs.argmax())
    category = classes[best_idx]
    confidence = float(probs[best_idx])

    # If the model is unsure, blend with the deterministic keyword rules,
    # and fall back to "Others" when nothing matches confidently.
    if confidence < 0.35:
        rule = _regex_category(text)
        if rule != "Others":
            return rule, max(confidence, 0.55)
        if confidence < 0.2:
            return "Others", round(confidence, 3)
    return str(category), round(confidence, 3)

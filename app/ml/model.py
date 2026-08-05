import os
from dataclasses import dataclass
from typing import Any, Tuple
import pandas as pd
import joblib
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier

from app.ml.feature_engineering import FEATURE_COLUMNS, create_features


@dataclass
class PredictionResult:
    direction: str
    confidence: float
    up_probability: float
    down_probability: float
    model_accuracy: float


def walk_forward_fit(data: pd.DataFrame) -> Tuple[XGBClassifier, float]:
    """Train model with walk-forward validation"""
    split_idx = int(len(data) * 0.8)
    train_df = data.iloc[:split_idx]
    test_df = data.iloc[split_idx:]
    
    model = XGBClassifier(
        n_estimators=250,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        use_label_encoder=False
    )
    
    model.fit(train_df[FEATURE_COLUMNS], train_df["target"])
    preds = model.predict(test_df[FEATURE_COLUMNS])
    acc = accuracy_score(test_df["target"], preds)
    
    return model, float(acc)


def load_or_train_model(df_raw: pd.DataFrame, model_path: str) -> Tuple[XGBClassifier, float]:
    """Load existing model or train new one"""
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    if os.path.exists(model_path):
        payload = joblib.load(model_path)
        return payload["model"], payload.get("accuracy", 0.0)
    
    features_df = create_features(df_raw)
    model, acc = walk_forward_fit(features_df)
    joblib.dump({"model": model, "accuracy": acc}, model_path)
    
    return model, acc


def predict_direction(model: XGBClassifier, features_df: pd.DataFrame, model_accuracy: float) -> PredictionResult:
    """Make prediction using trained model"""
    latest = features_df.iloc[-1:][FEATURE_COLUMNS]
    proba_up = float(model.predict_proba(latest)[0][1])
    proba_down = 1.0 - proba_up
    direction = "UP" if proba_up >= 0.5 else "DOWN"
    confidence = max(proba_up, proba_down) * 100
    
    return PredictionResult(
        direction=direction,
        confidence=round(confidence, 2),
        up_probability=round(proba_up * 100, 2),
        down_probability=round(proba_down * 100, 2),
        model_accuracy=round(model_accuracy * 100, 2),
    )
import logging
import pickle
import numpy as np
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "saved_models" / "success_predictor.pkl"


class SuccessPredictor:
    def __init__(self):
        self._model = None
        self._scaler = None
        self._loaded = False

    def _load_model(self):
        if self._loaded:
            return
        try:
            if MODEL_PATH.exists():
                with open(MODEL_PATH, "rb") as f:
                    saved = pickle.load(f)
                    self._model = saved.get("model")
                    self._scaler = saved.get("scaler")
                    logger.info("Success predictor model loaded")
            self._loaded = True
        except Exception as e:
            logger.warning(f"Could not load success predictor: {e}")
            self._loaded = True

    def predict(self, ats_score: float, skill_match: float, mock_scores: Optional[list] = None) -> float:
        self._load_model()
        avg_mock_score = float(np.mean(mock_scores)) * 10 if mock_scores else 50.0

        if self._model and self._scaler:
            try:
                features = np.array([[ats_score, skill_match, avg_mock_score, self._compute_consistency(mock_scores) if mock_scores else 50.0]])
                features_scaled = self._scaler.transform(features)
                return round(float(self._model.predict_proba(features_scaled)[0][1]), 3)
            except Exception as e:
                logger.warning(f"XGBoost prediction failed: {e}")

        return self._heuristic_predict(ats_score, skill_match, avg_mock_score)

    def _heuristic_predict(self, ats_score: float, skill_match: float, mock_score: float) -> float:
        composite = (ats_score * 0.35 + skill_match * 0.35 + mock_score * 0.30) / 100
        adjusted = 1 / (1 + np.exp(-8 * (composite - 0.55)))
        return round(float(adjusted), 3)

    def _compute_consistency(self, scores: list) -> float:
        if not scores or len(scores) < 2:
            return 50.0
        std = np.std(scores)
        return max(0, 10 - std) / 10 * 100

    def train(self, ats_scores: list, skill_matches: list, mock_scores_list: list, outcomes: list) -> dict:
        try:
            import xgboost as xgb
            from sklearn.preprocessing import StandardScaler
            from sklearn.model_selection import cross_val_score
        except ImportError:
            return {"error": "xgboost not installed"}

        if len(ats_scores) < 20:
            return {"error": "Need at least 20 samples to train"}

        X = []
        for i in range(len(ats_scores)):
            mock_avg = float(np.mean(mock_scores_list[i])) * 10 if mock_scores_list[i] else 50.0
            consistency = self._compute_consistency(mock_scores_list[i]) if mock_scores_list[i] else 50.0
            X.append([ats_scores[i], skill_matches[i], mock_avg, consistency])

        X = np.array(X)
        y = np.array(outcomes)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = xgb.XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, eval_metric="logloss", random_state=42)
        cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring="roc_auc")
        model.fit(X_scaled, y)

        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump({"model": model, "scaler": scaler}, f)

        self._model = model
        self._scaler = scaler
        self._loaded = True

        return {"cv_roc_auc_mean": round(float(cv_scores.mean()), 3), "cv_roc_auc_std": round(float(cv_scores.std()), 3)}


success_predictor = SuccessPredictor()

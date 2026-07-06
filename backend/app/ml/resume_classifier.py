import logging
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "saved_models" / "resume_classifier.pkl"

CATEGORY_KEYWORDS = {
    "Data Scientist": ["machine learning", "deep learning", "data science", "statistics", "jupyter", "kaggle", "pandas", "numpy", "scikit", "regression", "classification", "neural network", "data analysis", "matplotlib", "seaborn", "tableau"],
    "ML Engineer": ["mlops", "model deployment", "serving", "pytorch", "tensorflow", "inference", "feature engineering", "pipeline", "model training", "a/b testing", "kubeflow", "mlflow", "gpu", "cuda", "hugging face"],
    "NLP Engineer": ["nlp", "natural language processing", "transformers", "bert", "gpt", "llm", "text classification", "named entity", "sentiment analysis", "language model", "tokenization", "embeddings", "langchain", "spacy", "nltk"],
    "Frontend Developer": ["react", "vue", "angular", "html", "css", "javascript", "typescript", "ui", "ux", "responsive", "web design", "figma", "tailwind", "bootstrap", "next.js", "webpack", "redux", "component", "accessibility"],
    "Backend Developer": ["api", "rest", "microservices", "backend", "server", "database", "sql", "postgresql", "django", "flask", "fastapi", "spring", "express", "node", "authentication", "middleware", "orm", "cache", "queue"],
    "DevOps Engineer": ["devops", "docker", "kubernetes", "ci/cd", "terraform", "ansible", "jenkins", "github actions", "aws", "gcp", "azure", "infrastructure", "monitoring", "prometheus", "grafana", "linux", "deployment", "cloud"],
    "Data Engineer": ["data engineering", "etl", "pipeline", "spark", "hadoop", "airflow", "kafka", "data warehouse", "bigquery", "snowflake", "redshift", "dbt", "data lake", "databricks", "hive"],
    "Full Stack Developer": ["full stack", "fullstack", "frontend", "backend", "react", "node", "django", "both frontend and backend", "end-to-end", "web application"],
    "Product Manager": ["product manager", "product owner", "roadmap", "stakeholder", "user story", "agile", "scrum", "product strategy", "metrics", "kpi", "user research"],
}


class ResumeClassifier:
    def __init__(self):
        self._model = None
        self._vectorizer = None
        self._loaded = False

    def _load_model(self):
        if self._loaded:
            return
        try:
            if MODEL_PATH.exists():
                with open(MODEL_PATH, "rb") as f:
                    saved = pickle.load(f)
                    self._model = saved.get("model")
                    self._vectorizer = saved.get("vectorizer")
                    logger.info("Resume classifier model loaded from disk")
            self._loaded = True
        except Exception as e:
            logger.warning(f"Could not load resume classifier: {e}")
            self._loaded = True

    def predict(self, resume_text: str) -> str:
        if not resume_text:
            return "Software Engineer"

        self._load_model()
        if self._model and self._vectorizer:
            try:
                features = self._vectorizer.transform([resume_text.lower()])
                return self._model.predict(features)[0]
            except Exception as e:
                logger.warning(f"ML model prediction failed: {e}")

        return self._keyword_classify(resume_text)

    def _keyword_classify(self, text: str) -> str:
        scores = self._get_keyword_scores(text)
        if not scores:
            return "Software Engineer"
        return max(scores, key=scores.get)

    def _get_keyword_scores(self, text: str) -> dict:
        text_lower = text.lower()
        scores = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[category] = score
        if not scores and any(kw in text_lower for kw in ["software", "engineer", "developer", "programmer", "code", "coding"]):
            scores["Software Engineer"] = 1
        return scores

    def train(self, texts: list, labels: list) -> dict:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import classification_report
        from sklearn.model_selection import train_test_split

        if len(texts) < 10:
            return {"error": "Need at least 10 samples to train"}

        X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42, stratify=labels)
        vectorizer = TfidfVectorizer(max_features=15000, ngram_range=(1, 2), min_df=2, stop_words="english", sublinear_tf=True)
        X_train_tf = vectorizer.fit_transform([t.lower() for t in X_train])
        X_test_tf = vectorizer.transform([t.lower() for t in X_test])

        model = LogisticRegression(max_iter=1000, C=5.0, solver="lbfgs", class_weight="balanced")
        model.fit(X_train_tf, y_train)
        y_pred = model.predict(X_test_tf)
        report = classification_report(y_test, y_pred, output_dict=True)

        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump({"model": model, "vectorizer": vectorizer}, f)

        self._model = model
        self._vectorizer = vectorizer
        self._loaded = True
        logger.info(f"Resume classifier trained. Accuracy: {report.get('accuracy', 'N/A')}")
        return report


resume_classifier = ResumeClassifier()

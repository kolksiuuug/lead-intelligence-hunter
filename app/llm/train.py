from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
import joblib
from app.llm.dataset import get_dataset
import logging
logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s: %(message)s",force=True)
logger = logging.getLogger(__name__)
def train_model():
    train_x,train_y,test_x,test_y,train_x_profile,test_x_profile,train_y_profile,test_y_profile = get_dataset()
    model = Pipeline([
    ("tfidf", TfidfVectorizer(
        max_features=20000,
        min_df=2,
        max_df=0.95,
        ngram_range=(1, 2),
        sublinear_tf=True
    )),("ridge", Ridge(alpha=1.0))])
    model.fit(train_x, train_y)
    predictions = model.predict(test_x)
    error = mean_absolute_error(test_y, predictions)
    logger.info(f"MAE: {error:.4f}")

    model_profile = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=20000,
            min_df=1,
            max_df=0.95,
            ngram_range=(1, 2),
            sublinear_tf=True
        )),("ridge", Ridge(alpha=1.0))])
    model_profile.fit(train_x_profile, train_y_profile)
    predictions_profile = model_profile.predict(test_x_profile)
    error_profile = mean_absolute_error(test_y_profile, predictions_profile)
    logger.info(f"MAE: {error_profile:.4f}")
    joblib.dump(model, "issue_score_model.joblib")
    joblib.dump(model_profile, "issue_matcher_model.joblib")

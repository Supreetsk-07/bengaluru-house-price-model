from pathlib import Path
import json

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PROJECT = Path(__file__).resolve().parent
DATA = PROJECT / "data" / "processed" / "bengaluru_house_cleaned.csv"
OUTPUT = PROJECT / "models"
OUTPUT.mkdir(parents=True, exist_ok=True)

data = pd.read_csv(DATA)

feature_columns = [
    "location_grouped",
    "area_type",
    "bhk",
    "bath",
    "balcony",
    "total_sqft_numeric",
]
target_column = "price"

X = data[feature_columns].copy()
y = data[target_column].copy()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)

categorical_columns = ["location_grouped", "area_type"]
numeric_columns = ["bhk", "bath", "balcony", "total_sqft_numeric"]

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore")),
            ]),
            categorical_columns,
        ),
        (
            "numeric",
            Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
            ]),
            numeric_columns,
        ),
    ],
)

models = {
    "Ridge Regression": Ridge(alpha=1.0),
    "Random Forest": RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
    ),
    "Gradient Boosting": GradientBoostingRegressor(random_state=42),
}

results = []
fitted_pipelines = {}

for name, model in models.items():
    pipeline = Pipeline([
        ("preprocessing", preprocessor),
        ("model", model),
    ])
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    mse = mean_squared_error(y_test, predictions)
    rmse = mse ** 0.5
    r2 = r2_score(y_test, predictions)

    results.append({
        "model": name,
        "mae_lakh": round(mae, 4),
        "mse": round(mse, 4),
        "rmse_lakh": round(rmse, 4),
        "r2": round(r2, 4),
    })
    fitted_pipelines[name] = pipeline

comparison = pd.DataFrame(results).sort_values("rmse_lakh")
comparison.to_csv(OUTPUT / "model_comparison.csv", index=False)

rf_grid = GridSearchCV(
    estimator=Pipeline([
        ("preprocessing", preprocessor),
        (
            "model",
            RandomForestRegressor(random_state=42, n_jobs=-1),
        ),
    ]),
    param_grid={
        "model__n_estimators": [200, 400],
        "model__max_depth": [None, 20],
        "model__min_samples_leaf": [1, 3],
    },
    scoring="neg_root_mean_squared_error",
    cv=3,
    n_jobs=-1,
)
rf_grid.fit(X_train, y_train)
tuned_predictions = rf_grid.predict(X_test)

tuning = {
    "best_parameters": rf_grid.best_params_,
    "best_cross_validated_rmse_lakh": round(-rf_grid.best_score_, 4),
    "test_mae_lakh": round(mean_absolute_error(y_test, tuned_predictions), 4),
    "test_rmse_lakh": round(
        mean_squared_error(y_test, tuned_predictions) ** 0.5, 4
    ),
    "test_r2": round(r2_score(y_test, tuned_predictions), 4),
}
(OUTPUT / "random_forest_tuning.json").write_text(
    json.dumps(tuning, indent=2),
    encoding="utf-8",
)

joblib.dump(rf_grid.best_estimator_, OUTPUT / "bengaluru_house_price_model.joblib")

rf_model = rf_grid.best_estimator_.named_steps["model"]
encoded_features = rf_grid.best_estimator_.named_steps["preprocessing"].get_feature_names_out()
feature_importance = pd.DataFrame({
    "feature": encoded_features,
    "importance": rf_model.feature_importances_,
}).sort_values("importance", ascending=False)
feature_importance.to_csv(OUTPUT / "feature_importance.csv", index=False)

print(comparison.to_string(index=False))
print("\nRandom Forest tuning:")
print(json.dumps(tuning, indent=2))

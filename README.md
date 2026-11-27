# Bengaluru House Price Model

A student project exploring Bengaluru residential listing data and building regression models to estimate listed property prices from property attributes.

> **Use limitation:** This is an educational prototype, not a professional property valuation. Predictions are estimates from historical listing data and may not reflect current market prices.

## Project question

Can we estimate a Bengaluru property's listed price using its locality, area type, bedroom count, bathrooms, balconies, and area in square feet?

- **Target:** `price`, recorded in lakh rupees.
- **Unit of prediction:** one property listing.
- **Source data:** 13,320 rows in the original CSV.
- **Analysis data:** 11,947 rows after the documented Phase 1 cleaning steps.

## Dataset and attribution

The project uses `Bengaluru_House_Data.csv`, downloaded from the Kaggle dataset page:

<https://www.kaggle.com/datasets/pulakdroy/final-dataset>

The Kaggle page lists the dataset under the Apache-2.0 license. Check the source page for current terms before redistribution or reuse. The CSV is included here for reproducibility and remains unchanged in `data/raw/`. The source dataset is not authored by this project.

## Repository layout

```text
data/
  raw/                 Original source CSV (unchanged)
  processed/           Cleaned data and Phase 1 reports
notebooks/             Phase 1 EDA and Phase 2 modeling notebooks
models/                Model comparison, tuning results, feature importance, saved pipeline
reports/charts/        Phase 1 EDA and model charts
phase1_analysis.py     Reproducible profiling, cleaning, EDA and statistics
phase2_modeling.py     Train/test split, model comparison and Random Forest tuning
create_phase2_presentation.py
                       Regenerate the Phase 2 review presentation
```

## Setup

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
```

Activate it:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```
## Run tests

```bash
python -m pytest -v
```

## Reproduce Phase 1

From the repository root:

```bash
python phase1_analysis.py
```

This reads the raw CSV without modifying it and regenerates:

- Cleaned analysis dataset: `data/processed/bengaluru_house_cleaned.csv`
- Data dictionary, quality summary and cleaning decision log
- Descriptive statistics and Kruskal-Wallis test result
- Eight EDA charts under `reports/charts/`

Key transformations include extracting numeric BHK, interpreting square-foot ranges by their midpoint, converting supported area units to square feet, removing exact duplicates, checking domain outliers, and grouping locations with fewer than ten listings. See `data/processed/cleaning_decision_log.csv` for decisions and reasons.

## Reproduce Phase 2

Run Phase 1 first if the processed dataset is missing, then run:

```bash
python phase2_modeling.py
```

The model uses these features:

- `location_grouped`
- `area_type`
- `bhk`
- `bath`
- `balcony`
- `total_sqft_numeric`

The target is `price`. The target-derived `price_per_sqft` feature is intentionally excluded to prevent target leakage. A fixed 80/20 train/test split (random state 42) is used. Missing-value handling and categorical one-hot encoding are fitted inside a scikit-learn pipeline on training data.

The script compares Ridge Regression, Random Forest and Gradient Boosting, tunes Random Forest with 3-fold cross-validation, and saves:

- `models/model_comparison.csv`
- `models/random_forest_tuning.json`
- `models/feature_importance.csv`
- `models/bengaluru_house_price_model.joblib`

### Current model results

On the current holdout split, Gradient Boosting has the lowest RMSE (103.91 lakh) and the highest R² (0.591). The tuned Random Forest has MAE 36.03 lakh, RMSE 109.09 lakh and R² 0.549. The saved model file currently contains the tuned Random Forest, not the lowest-RMSE model; final model selection is still an open decision. Metrics are not guarantees for individual predictions.

## Notebooks and presentation

Open the notebooks in `notebooks/` with Jupyter or the VS Code Jupyter extension. Select the project's Python environment as the kernel, then run cells from top to bottom.

- `Bengaluru_House_Price_Phase1_EDA.ipynb`
- `Bengaluru_House_Price_Phase2_Modeling.ipynb`

The Phase 2 slide deck is `Bengaluru_House_Price_Phase2_Review.pptx`. Regenerate it after running Phase 1 and Phase 2:

```bash
python create_phase2_presentation.py
```

## Current scope and limitations

Implemented: Phase 1 data preparation, exploratory analysis and statistics; Phase 2 regression baselines, model comparison, Random Forest tuning, and a serialized prediction pipeline.

Not implemented yet: neural-network/DL experiment, GenAI assistant, FastAPI service, Streamlit application, Docker packaging, or cloud deployment.

The data is cross-sectional listing data and does not provide a reliable date feature for time-based validation. Price values are right-skewed and contain high-end properties, so RMSE is sensitive to large errors. Feature importance indicates how the fitted Random Forest used features; it does not establish causation.

## Team contributions

See [CONTRIBUTING.md](CONTRIBUTING.md) for suggested, independently verifiable work. Contributors should use their own GitHub accounts and describe only the work they actually completed.

from pathlib import Path
from src.cleaning import convert_total_sqft, extract_bhk

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy.stats import kruskal


PROJECT = Path(__file__).resolve().parent
RAW = PROJECT / "data" / "raw" / "Bengaluru_House_Data.csv"
PROCESSED = PROJECT / "data" / "processed"
CHARTS = PROJECT / "reports" / "charts"
PROCESSED.mkdir(parents=True, exist_ok=True)
CHARTS.mkdir(parents=True, exist_ok=True)
sns.set_theme(style="whitegrid")


def convert_total_sqft(value):
    if pd.isna(value):
        return None
    text = str(value).strip().lower()
    range_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", text)
    if range_match:
        return (float(range_match.group(1)) + float(range_match.group(2))) / 2

    number_match = re.match(r"(\d+(?:\.\d+)?)", text)
    if not number_match:
        return None
    number = float(number_match.group(1))
    if "sq. meter" in text or "sqm" in text:
        return number * 10.7639
    if "sq. yard" in text or "sq yard" in text:
        return number * 9.0
    if "acre" in text:
        return number * 43560.0
    if "cent" in text:
        return number * 435.6
    if "guntha" in text:
        return number * 1089.0
    if "ground" in text:
        return number * 2400.0
    if "perch" in text:
        return number * 272.25
    return number


raw = pd.read_csv(RAW)
raw_rows = len(raw)

quality = pd.DataFrame({
    "column": raw.columns,
    "missing_count": [int(raw[c].isna().sum()) for c in raw.columns],
    "missing_percent": [round(raw[c].isna().mean() * 100, 2) for c in raw.columns],
    "data_type": [str(raw[c].dtype) for c in raw.columns],
    "unique_values": [int(raw[c].nunique(dropna=True)) for c in raw.columns],
})
quality.to_csv(PROCESSED / "data_quality_summary.csv", index=False)

data_dictionary = pd.DataFrame([
    ("area_type", "Area measurement/listing category", "Categorical"),
    ("availability", "Listing availability or date-like status", "Categorical/date-like"),
    ("location", "Bengaluru locality", "Categorical"),
    ("size", "Original bedroom-size text", "Text"),
    ("society", "Society/project name", "Categorical"),
    ("total_sqft", "Original area value, possibly range or unit", "Text"),
    ("bath", "Number of bathrooms", "Numeric"),
    ("balcony", "Number of balconies", "Numeric"),
    ("price", "Property price in lakh rupees", "Numeric target"),
    ("bhk", "Numeric bedroom count derived from size", "Engineered numeric"),
    ("total_sqft_numeric", "Standardized area in square feet", "Engineered numeric"),
    ("price_per_sqft", "Price in rupees per square foot", "Engineered numeric"),
    ("sqft_per_bhk", "Area divided by bedroom count", "Engineered numeric"),
])
data_dictionary.columns = ["column", "meaning", "data_type_or_note"]
data_dictionary.to_csv(PROCESSED / "data_dictionary.csv", index=False)

clean = raw.copy()
clean["location"] = clean["location"].astype("string").str.strip()
clean["area_type"] = clean["area_type"].astype("string").str.strip()
clean["size"] = clean["size"].astype("string").str.strip()
clean["society"] = clean["society"].astype("string").str.strip()
clean["bhk"] = clean["size"].str.extract(r"(\d+)", expand=False).astype("Float64")
clean["total_sqft_numeric"] = clean["total_sqft"].apply(convert_total_sqft)
clean["price_per_sqft"] = clean["price"] * 100000 / clean["total_sqft_numeric"]
clean["sqft_per_bhk"] = clean["total_sqft_numeric"] / clean["bhk"]

exact_duplicates = int(clean.duplicated().sum())
clean = clean.drop_duplicates().copy()

clean["location"] = clean["location"].replace("", pd.NA)
clean = clean.dropna(subset=["location", "bhk", "total_sqft_numeric", "bath"])
clean = clean[(clean["bhk"] >= 1) & (clean["bhk"] <= 10)]
clean["bhk"] = clean["bhk"].astype("int64")
clean = clean[clean["total_sqft_numeric"] >= 100]
clean = clean[clean["sqft_per_bhk"] >= 300]
clean = clean[clean["bath"] <= clean["bhk"] + 2]
clean = clean[clean["price_per_sqft"].between(500, 100000)]

location_counts = clean["location"].value_counts()
rare_locations = location_counts[location_counts < 10].index
clean["location_grouped"] = clean["location"].replace(list(rare_locations), "other")

clean.to_csv(PROCESSED / "bengaluru_house_cleaned.csv", index=False)

decisions = pd.DataFrame([
    ("Missing location", "1 raw row", "Drop in analysis copy", "Location is required for location analysis and prediction"),
    ("Missing size", "16 raw rows", "No value invented; derive BHK only where size exists", "Avoid fabricating bedroom counts"),
    ("Missing society", "5502 raw rows", "Keep missing; use the column only for traceability, not this Phase 2 baseline", "Too much missingness to impute reliably"),
    ("Missing bath", "73 raw rows", "Drop rows because bath is needed for domain checks", "Arbitrary bathroom imputation would distort price patterns"),
    ("Missing balcony", "609 raw rows", "Keep missing; do not impute in cleaned EDA copy", "Balcony was not needed for core cleaning decisions"),
    ("Exact duplicates", f"{exact_duplicates} exact duplicates", "Remove one duplicate occurrence", "Repeated listings are not independent observations"),
    ("total_sqft ranges", "Range values present", "Use midpoint of range", "A midpoint is transparent and reproducible"),
    ("total_sqft units", "Meter, yard, acre, cent, guntha, ground and perch forms", "Convert to square feet", "Enable comparable area measurements"),
    ("Unconverted total_sqft", "Any remaining non-numeric value", "Set as missing and remove if cleaning is blocked", "Do not silently guess units"),
    ("Outlier: area per BHK", "Rows below 300 sqft per BHK", "Remove", "Likely data errors or implausible listings"),
    ("Outlier: bath count", "Bath count greater than BHK + 2", "Remove", "Implausible for this dataset"),
    ("Outlier: price_per_sqft", "Outside 500-100000 rupees/sqft", "Remove", "Domain limits exclude implausible extreme values"),
    ("Rare locations", "Location count below 10", "Group as 'other'", "Prevent high-dimensional sparse location categories"),
])
decisions.columns = ["problem", "evidence", "proposed_decision", "reason"]
decisions.to_csv(PROCESSED / "cleaning_decision_log.csv", index=False)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
sns.histplot(clean["price"], bins=50, ax=axes[0])
axes[0].set_title("Distribution of Property Prices")
sns.histplot(clean["price_per_sqft"], bins=50, ax=axes[1])
axes[1].set_title("Distribution of Price per Sqft")
plt.tight_layout()
plt.savefig(CHARTS / "01_price_distributions.png", dpi=160)
plt.close()

plt.figure(figsize=(10, 5))
clean["area_type"].value_counts().plot(kind="bar")
plt.title("Listing Count by Area Type")
plt.ylabel("Count")
plt.tight_layout()
plt.savefig(CHARTS / "02_area_type_counts.png", dpi=160)
plt.close()

plt.figure(figsize=(10, 6))
sns.scatterplot(data=clean.sample(min(len(clean), 3000), random_state=42),
                x="total_sqft_numeric", y="price", alpha=0.35)
plt.title("Area vs Price")
plt.tight_layout()
plt.savefig(CHARTS / "03_area_vs_price.png", dpi=160)
plt.close()

plt.figure(figsize=(10, 6))
order = sorted(clean["bhk"].dropna().unique())
sns.boxplot(data=clean, x="bhk", y="price", order=order)
plt.title("Price Distribution by BHK")
plt.tight_layout()
plt.savefig(CHARTS / "04_bhk_vs_price.png", dpi=160)
plt.close()

top_locations = clean["location"].value_counts().head(15).index
location_subset = clean[clean["location"].isin(top_locations)]
plt.figure(figsize=(12, 7))
sns.boxplot(data=location_subset, x="location", y="price")
plt.xticks(rotation=55, ha="right")
plt.title("Price Distribution in Top 15 Locations")
plt.tight_layout()
plt.savefig(CHARTS / "05_location_vs_price.png", dpi=160)
plt.close()

plt.figure(figsize=(10, 6))
sns.scatterplot(data=clean.sample(min(len(clean), 3000), random_state=42),
                x="price_per_sqft", y="price", hue="bhk", palette="viridis", alpha=0.5)
plt.title("Price per Sqft vs Price")
plt.tight_layout()
plt.savefig(CHARTS / "06_price_per_sqft_vs_price.png", dpi=160)
plt.close()

numeric = clean[["price", "bhk", "bath", "balcony", "total_sqft_numeric",
                 "price_per_sqft", "sqft_per_bhk"]].corr(numeric_only=True)
plt.figure(figsize=(10, 8))
sns.heatmap(numeric, annot=True, fmt=".2f", cmap="coolwarm", center=0)
plt.title("Correlation Heatmap")
plt.tight_layout()
plt.savefig(CHARTS / "07_correlation_heatmap.png", dpi=160)
plt.close()

plt.figure(figsize=(11, 6))
clean["location_grouped"].value_counts().head(15).plot(kind="bar")
plt.title("Top Location Groups")
plt.ylabel("Listing Count")
plt.tight_layout()
plt.savefig(CHARTS / "08_location_counts.png", dpi=160)
plt.close()

area_groups = [group["price_per_sqft"].dropna() for _, group in clean.groupby("area_type")]
statistic, p_value = kruskal(*area_groups)

stats = numeric["price"].sort_values(ascending=False)
summary = pd.DataFrame([
    ("raw_rows", raw_rows),
    ("cleaned_rows", len(clean)),
    ("rows_removed", raw_rows - len(clean)),
    ("exact_duplicate_rows_removed", exact_duplicates),
    ("mean_price_lakh", clean["price"].mean()),
    ("median_price_lakh", clean["price"].median()),
    ("price_std_lakh", clean["price"].std()),
    ("mean_price_per_sqft", clean["price_per_sqft"].mean()),
    ("median_price_per_sqft", clean["price_per_sqft"].median()),
    ("kruskal_wallis_statistic", statistic),
    ("kruskal_wallis_p_value", p_value),
])
summary.columns = ["metric", "value"]
summary.to_csv(PROCESSED / "statistics_summary.csv", index=False)

print(f"Raw rows: {raw_rows}")
print(f"Cleaned rows: {len(clean)}")
print(f"Rows removed: {raw_rows - len(clean)}")
print(f"Kruskal-Wallis p-value: {p_value:.6g}")

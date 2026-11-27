from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
CHARTS = ROOT / "reports" / "charts"
OUTPUT = ROOT / "Bengaluru_House_Price_Phase2_Review.pptx"

NAVY = RGBColor(17, 28, 48)
PANEL = RGBColor(29, 44, 68)
TEAL = RGBColor(37, 205, 178)
WHITE = RGBColor(246, 248, 252)
MUTED = RGBColor(174, 189, 207)
GOLD = RGBColor(255, 195, 91)
RED = RGBColor(250, 116, 116)
GREEN = RGBColor(87, 215, 164)

comparison = pd.read_csv(MODELS / "model_comparison.csv")
importance = pd.read_csv(MODELS / "feature_importance.csv").head(8).copy()
importance["feature"] = importance["feature"].str.replace(
    r"^(numeric__|categorical__)", "", regex=True
)

metric_chart = CHARTS / "phase2_model_metrics.png"
fig, ax = plt.subplots(figsize=(8, 3.8))
colors = ["#25cdb2" if name == "Random Forest" else "#6c7f9b"
          for name in comparison["model"]]
ax.bar(comparison["model"], comparison["rmse_lakh"], color=colors)
ax.set_title("Test-set RMSE (lower is better)", fontsize=14, weight="bold")
ax.set_ylabel("RMSE (lakh rupees)")
ax.spines[["top", "right", "left"]].set_visible(False)
ax.grid(axis="y", alpha=0.2)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig(metric_chart, dpi=180, transparent=False, facecolor="white")
plt.close(fig)

importance_chart = CHARTS / "phase2_random_forest_feature_importance.png"
importance = importance.sort_values("importance")
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.barh(importance["feature"], importance["importance"] * 100, color="#25cdb2")
ax.set_title("Random Forest feature importance", fontsize=14, weight="bold")
ax.set_xlabel("Importance (%)")
ax.spines[["top", "right", "left"]].set_visible(False)
ax.grid(axis="x", alpha=0.2)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig(importance_chart, dpi=180, transparent=False, facecolor="white")
plt.close(fig)
importance = importance.sort_values("importance", ascending=False)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]


def add_background(slide):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = NAVY


def add_text(slide, text, x, y, w, h, size=18, color=WHITE,
             bold=False, align=PP_ALIGN.LEFT, font="Aptos"):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(0.02)
    tf.margin_right = Inches(0.02)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]
    p.alignment = align
    p.space_after = Pt(0)
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def add_rich_lines(slide, lines, x, y, w, h, size=17, gap=12):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(0.02)
    tf.margin_right = Inches(0.02)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    for i, (label, detail) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        p.level = 0
        lead = p.add_run()
        lead.text = f"•  {label}"
        lead.font.name = "Aptos"
        lead.font.size = Pt(size)
        lead.font.bold = True
        lead.font.color.rgb = TEAL
        body = p.add_run()
        body.text = f"  {detail}"
        body.font.name = "Aptos"
        body.font.size = Pt(size)
        body.font.color.rgb = WHITE
    return box


def add_card(slide, x, y, w, h, title, body, accent=TEAL):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = PANEL
    shape.line.fill.background()
    add_text(slide, title, x + 0.22, y + 0.18, w - 0.44, 0.42,
             16, accent, True)
    add_text(slide, body, x + 0.22, y + 0.7, w - 0.44, h - 0.82,
             15, WHITE)
    return shape


def add_slide(title, eyebrow="PHASE 2 | MODEL DEVELOPMENT"):
    slide = prs.slides.add_slide(blank)
    add_background(slide)
    add_text(slide, eyebrow, 0.65, 0.34, 8, 0.25, 10, TEAL, True)
    add_text(slide, title, 0.65, 0.73, 12, 0.65, 28, WHITE, True)
    add_text(slide, "BENGALURU HOUSE PRICE PREDICTION", 0.65, 7.12, 7, 0.18,
             9, MUTED, True)
    add_text(slide, f"{len(prs.slides):02d}", 12.22, 7.08, 0.45, 0.22,
             10, MUTED, False, PP_ALIGN.RIGHT)
    return slide


def add_image_contain(slide, path, x, y, w, h):
    from PIL import Image
    with Image.open(path) as image:
        image_w, image_h = image.size
    scale = min(w / image_w, h / image_h)
    width = image_w * scale
    height = image_h * scale
    slide.shapes.add_picture(
        str(path),
        Inches(x + (w - width) / 2),
        Inches(y + (h - height) / 2),
        width=Inches(width),
        height=Inches(height),
    )


# 1. Title
slide = prs.slides.add_slide(blank)
add_background(slide)
shape = slide.shapes.add_shape(
    MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.16), Inches(7.5)
)
shape.fill.solid()
shape.fill.fore_color.rgb = TEAL
shape.line.fill.background()
add_text(slide, "PROJECT REVIEW | PHASE 2", 0.85, 0.82, 6, 0.32, 13, TEAL, True)
add_text(slide, "Bengaluru House Price\nPrediction", 0.85, 1.6, 9.5, 1.65,
         38, WHITE, True)
add_text(slide, "Regression models • Random Forest tuning • Evaluation",
         0.88, 3.63, 9.8, 0.55, 20, MUTED)
add_text(slide, "From cleaned property listings to a tested price-estimation model",
         0.88, 4.42, 9.8, 0.52, 16, WHITE)
add_text(slide, "Online review presentation", 0.88, 6.5, 5, 0.3, 12, MUTED)
add_text(slide, "01", 12.22, 7.08, 0.45, 0.22, 10, MUTED, False, PP_ALIGN.RIGHT)

# 2. Problem and goal
slide = add_slide("What Phase 2 is solving")
add_text(slide, "Business question", 0.75, 1.62, 3.2, 0.35, 16, TEAL, True)
add_text(slide, "Given a property's details, what sale price should we expect?",
         0.75, 2.05, 5.2, 1.3, 27, WHITE, True)
add_rich_lines(slide, [
    ("Input", "location, area type, BHK, bathrooms, balconies, square feet"),
    ("Output", "estimated property price, in lakh rupees"),
    ("Purpose", "learn patterns from historical listings; support—not replace—valuation"),
], 6.35, 1.75, 6.1, 3.6, 17, 20)
add_card(slide, 0.75, 5.45, 11.85, 0.95, "Phase 1 handoff",
         "The modeling data comes from the cleaned dataset; the original CSV remains unchanged.",
         TEAL)

# 3. Data and leakage
slide = add_slide("Data used by the models")
add_card(slide, 0.75, 1.68, 3.75, 2.15, "Training data",
         "80% of the cleaned rows. The models learn relationships from these examples.")
add_card(slide, 4.78, 1.68, 3.75, 2.15, "Test data",
         "20% held aside. Used once for an unseen-data performance estimate.", GOLD)
add_card(slide, 8.82, 1.68, 3.75, 2.15, "Prediction target",
         "price (lakh rupees). Features: location, area type, BHK, bath, balcony, area.")
add_text(slide, "Leakage safeguard", 0.85, 4.45, 3.0, 0.35, 17, TEAL, True)
add_text(slide,
         "price_per_sqft is not an input feature because it is calculated using the target price. "
         "Using it would let the model indirectly see the answer.",
         0.85, 4.92, 11.5, 0.95, 19, WHITE)
add_text(slide,
         "Categorical encoding and missing-value handling are inside the scikit-learn pipeline, "
         "fitted using training data.",
         0.85, 6.0, 11.5, 0.62, 15, MUTED)

# 4. Models
slide = add_slide("Three regression approaches")
add_card(slide, 0.75, 1.72, 3.75, 2.45, "Ridge Regression",
         "Linear baseline. A regularized linear model sets a simple point of comparison.")
add_card(slide, 4.78, 1.72, 3.75, 2.45, "Random Forest",
         "Many decision trees vote together. Learns nonlinear patterns and feature interactions.",
         TEAL)
add_card(slide, 8.82, 1.72, 3.75, 2.45, "Gradient Boosting",
         "Builds trees sequentially, with later trees correcting earlier errors.")
add_text(slide,
         "All models use the same train/test split and the same input features. "
         "Random Forest was additionally tuned with cross-validation.",
         0.85, 4.85, 11.5, 0.95, 18, WHITE)
add_text(slide,
         "Why Random Forest? It can represent nonlinear price patterns without requiring a linear relationship.",
         0.85, 6.0, 11.5, 0.5, 15, MUTED)

# 5. Metrics
slide = add_slide("How model quality is measured")
add_rich_lines(slide, [
    ("MAE", "average absolute error; easier to interpret in lakh rupees"),
    ("RMSE", "penalizes large misses more strongly; lower is better"),
    ("R²", "fraction of test price variation explained; closer to 1 is better"),
], 0.85, 1.75, 5.1, 3.7, 17, 22)
add_card(slide, 6.25, 1.78, 5.95, 1.25, "Example interpretation",
         "MAE ≈ 34 lakh means the average absolute test error is about ₹34 lakh.")
add_text(slide,
         "These are estimates on the held-out test set—not a guarantee for every property.",
         6.48, 3.45, 5.45, 1.0, 16, MUTED)

# 6. Results
slide = add_slide("Test-set results: no single metric tells the whole story")
add_image_contain(slide, metric_chart, 0.65, 1.58, 6.0, 3.85)
table_shape = slide.shapes.add_table(
    4, 4, Inches(6.75), Inches(1.72), Inches(5.85), Inches(2.55)
)
table = table_shape.table
table.columns[0].width = Inches(2.0)
for col in range(1, 4):
    table.columns[col].width = Inches(1.28)
headers = ["Model", "MAE", "RMSE", "R²"]
for col, value in enumerate(headers):
    cell = table.cell(0, col)
    cell.text = value
for row, name in enumerate(["Ridge Regression", "Random Forest", "Gradient Boosting"], 1):
    record = comparison.loc[comparison["model"] == name].iloc[0]
    values = [
        name,
        f"{record['mae_lakh']:.2f}",
        f"{record['rmse_lakh']:.2f}",
        f"{record['r2']:.3f}",
    ]
    for col, value in enumerate(values):
        table.cell(row, col).text = value
for row in range(4):
    for col in range(4):
        cell = table.cell(row, col)
        cell.fill.solid()
        cell.fill.fore_color.rgb = TEAL if row == 0 else PANEL
        cell.margin_left = Inches(0.08)
        cell.margin_right = Inches(0.04)
        cell.margin_top = Inches(0.04)
        cell.margin_bottom = Inches(0.02)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        for paragraph in cell.text_frame.paragraphs:
            paragraph.alignment = PP_ALIGN.LEFT
            for run in paragraph.runs:
                run.font.name = "Aptos"
                run.font.size = Pt(11)
                run.font.bold = row == 0
                run.font.color.rgb = NAVY if row == 0 else WHITE
add_card(slide, 0.85, 5.45, 11.8, 0.95, "Readout",
         "Gradient Boosting has the lowest RMSE and highest R². Random Forest has the lowest MAE among the three untuned comparisons.",
         GOLD)

# 7. Tuning
slide = add_slide("Random Forest: tuning and validation")
add_text(slide, "Selected hyperparameters", 0.85, 1.7, 5.2, 0.42, 17, TEAL, True)
add_rich_lines(slide, [
    ("Trees", "200 estimators"),
    ("Depth", "maximum depth 20"),
    ("Leaf size", "minimum 3 samples"),
    ("Validation", "3-fold cross-validation on training data"),
], 0.85, 2.25, 5.45, 3.3, 17, 15)
add_card(slide, 6.55, 1.85, 5.55, 1.35, "Cross-validation RMSE",
         "88.90 lakh (average across folds)", TEAL)
add_card(slide, 6.55, 3.45, 5.55, 1.35, "Held-out test RMSE",
         "109.09 lakh after tuning", GOLD)
add_text(slide,
         "Cross-validation and test scores are calculated on different data partitions; "
         "the test score is the estimate of performance on unseen listings.",
         6.6, 5.2, 5.35, 0.95, 15, MUTED)

# 8. Interpretation
slide = add_slide("What the Random Forest learned")
add_image_contain(slide, importance_chart, 0.7, 1.5, 7.2, 4.75)
add_card(slide, 8.25, 1.85, 4.15, 1.35, "Total square feet",
         "About 76.2% of this model's feature importance.", TEAL)
add_card(slide, 8.25, 3.45, 4.15, 1.35, "Next strongest",
         "BHK 5.4% • bath 5.2% • balcony 3.3%", GOLD)
add_text(slide,
         "Importance shows how the fitted forest used features; it does not prove causation.",
         8.32, 5.2, 3.95, 0.9, 14, MUTED)

# 9. Honest decision / status
slide = add_slide("Result, current artifact, and next decision")
add_card(slide, 0.8, 1.65, 3.75, 2.2, "What we can claim",
         "The models learn useful relationships. Gradient Boosting gives the best RMSE/R² in the current comparison.", GREEN)
add_card(slide, 4.78, 1.65, 3.75, 2.2, "Random Forest status",
         "It was tuned and evaluated as requested. The saved model file currently contains the tuned Random Forest pipeline.", TEAL)
add_card(slide, 8.75, 1.65, 3.75, 2.2, "Before deployment",
         "Choose the final model using an agreed business metric; consider tuning Gradient Boosting and comparing again.", GOLD)
add_text(slide, "Current model files", 0.9, 4.55, 3.0, 0.35, 16, TEAL, True)
add_text(slide,
         "models/model_comparison.csv  •  models/random_forest_tuning.json  •  "
         "models/feature_importance.csv  •  models/bengaluru_house_price_model.joblib",
         0.9, 5.0, 11.6, 0.8, 15, WHITE)
add_text(slide,
         "This is Phase 2 only. Neural-network experiments, GenAI, API, interface, Docker, and deployment are future phases.",
         0.9, 6.15, 11.4, 0.48, 13, MUTED)

prs.save(OUTPUT)
print(f"Saved presentation: {OUTPUT}")

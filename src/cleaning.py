import re

import pandas as pd


def extract_bhk(value):
    """Return the bedroom count from labels such as '2 BHK' or '4 Bedroom'."""
    if pd.isna(value):
        return None

    match = re.search(r"(\d+)", str(value).strip())
    return int(match.group(1)) if match else None


def convert_total_sqft(value):
    """Convert supported area values and ranges to square feet."""
    if pd.isna(value):
        return None

    text = str(value).strip().lower()

    range_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", text)
    if range_match:
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        return (low + high) / 2

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

import pytest

from src.cleaning import convert_total_sqft, extract_bhk


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1056", 1056),
        ("1115 - 1130", 1122.5),
        ("100 sq. meter", 1076.39),
        ("10 sq yard", 90),
    ],
)
def test_convert_total_sqft(value, expected):
    assert convert_total_sqft(value) == pytest.approx(expected)


@pytest.mark.parametrize("value", [None, "", "not available"])
def test_unusable_area_returns_none(value):
    assert convert_total_sqft(value) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2 BHK", 2),
        ("4 Bedroom", 4),
        ("1 RK", 1),
    ],
)
def test_extract_bhk(value, expected):
    assert extract_bhk(value) == expected


@pytest.mark.parametrize("value", [None, "", "unknown"])
def test_missing_bhk_returns_none(value):
    assert extract_bhk(value) is None

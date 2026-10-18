"""
analysis.py
-----------
All data cleaning and calculations live here, so app.py only has to
display results. Each function does one small job.

Expected CSV formats
--------------------
Air pollution CSV      -> columns: date, aqi, pm25, pm10
Hospital admissions CSV -> columns: date, age_group, admissions
(Extra columns are ignored. Column names are not case-sensitive.)
"""

import numpy as np
import pandas as pd
from scipy import stats

AIR_COLUMNS = ["date", "aqi", "pm25", "pm10"]
HOSPITAL_COLUMNS = ["date", "age_group", "admissions"]


class DataError(Exception):
    """Raised when a CSV file cannot be used. The message is shown to the user."""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Make column names lower-case and swap spaces for underscores ('Date ' -> 'date')."""
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


def _check_columns(df: pd.DataFrame, required: list, file_name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise DataError(
            f"The {file_name} file is missing column(s): {', '.join(missing)}. "
            f"Required columns are: {', '.join(required)}."
        )


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------
def clean_air_data(df: pd.DataFrame):
    """Clean the air pollution table and return (monthly_table, notes).

    Steps: check columns -> convert dates and numbers -> remove invalid values
    -> fill gaps by interpolation -> average per month.
    """
    notes = []
    df = _standardise_columns(df)
    _check_columns(df, AIR_COLUMNS, "air pollution")
    df = df[AIR_COLUMNS].copy()

    # 1. Dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    bad_dates = int(df["date"].isna().sum())
    if bad_dates:
        notes.append(f"Air data: removed {bad_dates} row(s) with an invalid date.")
        df = df.dropna(subset=["date"])

    # 2. Numbers (text like 'N/A' becomes NaN; negative readings are impossible)
    pollutants = ["aqi", "pm25", "pm10"]
    for col in pollutants:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] < 0, col] = np.nan

    if df.empty:
        raise DataError("The air pollution file has no usable rows after cleaning.")
    for col in pollutants:
        if df[col].isna().all():
            raise DataError(f"The '{col}' column has no valid numbers.")

    # 3. Missing values -> linear interpolation (fills a gap using its neighbours)
    df = df.sort_values("date").reset_index(drop=True)
    missing = int(df[pollutants].isna().sum().sum())
    if missing:
        df[pollutants] = df[pollutants].interpolate(limit_direction="both")
        notes.append(f"Air data: filled {missing} missing/invalid value(s) by interpolation.")

    # 4. One row per month (average of the readings in that month)
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    monthly = df.groupby("month", as_index=False)[pollutants].mean()
    return monthly, notes


def clean_hospital_data(df: pd.DataFrame):
    """Clean the hospital admissions table and return (monthly_table, notes).

    The result has one row per month per age group (admissions are summed).
    """
    notes = []
    df = _standardise_columns(df)
    _check_columns(df, HOSPITAL_COLUMNS, "hospital admissions")
    df = df[HOSPITAL_COLUMNS].copy()

    # 1. Dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    bad_dates = int(df["date"].isna().sum())
    if bad_dates:
        notes.append(f"Hospital data: removed {bad_dates} row(s) with an invalid date.")
        df = df.dropna(subset=["date"])

    # 2. Age group labels
    df["age_group"] = df["age_group"].astype("string").str.strip()
    blank_groups = int(df["age_group"].isna().sum() + (df["age_group"] == "").sum())
    if blank_groups:
        notes.append(f"Hospital data: removed {blank_groups} row(s) with no age group.")
        df = df[df["age_group"].notna() & (df["age_group"] != "")]

    # 3. Admission counts
    df["admissions"] = pd.to_numeric(df["admissions"], errors="coerce")
    df.loc[df["admissions"] < 0, "admissions"] = np.nan

    if df.empty:
        raise DataError("The hospital admissions file has no usable rows after cleaning.")
    if df["admissions"].isna().all():
        raise DataError("The 'admissions' column has no valid numbers.")

    # 4. Missing counts -> median of the same age group
    missing = int(df["admissions"].isna().sum())
    if missing:
        group_median = df.groupby("age_group")["admissions"].transform("median")
        df["admissions"] = df["admissions"].fillna(group_median)
        df["admissions"] = df["admissions"].fillna(df["admissions"].median())
        notes.append(
            f"Hospital data: filled {missing} missing/invalid count(s) "
            "with the median of the same age group."
        )

    # 5. One row per month per age group
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    monthly = df.groupby(["month", "age_group"], as_index=False)["admissions"].sum()
    return monthly, notes


def merge_monthly(air_monthly: pd.DataFrame, hospital_monthly: pd.DataFrame) -> pd.DataFrame:
    """Join air pollution and TOTAL admissions on the month column."""
    total = hospital_monthly.groupby("month", as_index=False)["admissions"].sum()
    merged = air_monthly.merge(total, on="month", how="inner")
    if len(merged) < 3:
        raise DataError(
            "Fewer than 3 months overlap between the two files, so a correlation "
            "cannot be calculated. Please check that the dates cover the same period."
        )
    return merged


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------
def pearson(x: pd.Series, y: pd.Series):
    """Return (r, p_value). Returns (nan, nan) if it cannot be calculated."""
    if len(x) < 3 or x.nunique() < 2 or y.nunique() < 2:
        return np.nan, np.nan
    r, p = stats.pearsonr(x, y)
    return float(r), float(p)


def describe_strength(r: float) -> str:
    """Turn r into plain words, e.g. 0.72 -> 'Strong positive'."""
    if np.isnan(r):
        return "Not enough data"
    size = abs(r)
    if size < 0.2:
        label = "Very weak"
    elif size < 0.4:
        label = "Weak"
    elif size < 0.6:
        label = "Moderate"
    elif size < 0.8:
        label = "Strong"
    else:
        label = "Very strong"
    direction = "positive" if r > 0 else "negative"
    return f"{label} {direction}" if size >= 0.2 else label


def correlation_table(merged: pd.DataFrame) -> pd.DataFrame:
    """Pearson correlation of each pollutant with monthly total admissions."""
    rows = []
    for column, label in [("aqi", "AQI"), ("pm25", "PM2.5"), ("pm10", "PM10")]:
        r, p = pearson(merged[column], merged["admissions"])
        rows.append(
            {
                "Pollutant": label,
                "Pearson r": r,
                "p-value": p,
                "Strength": describe_strength(r),
            }
        )
    return pd.DataFrame(rows)


def age_group_summary(hospital_monthly: pd.DataFrame) -> pd.DataFrame:
    """Total admissions per age group, with each group's share of the total."""
    summary = hospital_monthly.groupby("age_group", as_index=False)["admissions"].sum()
    summary["share_percent"] = (summary["admissions"] / summary["admissions"].sum() * 100).round(1)
    return summary.sort_values("admissions", ascending=False).reset_index(drop=True)


def age_group_correlation(air_monthly: pd.DataFrame, hospital_monthly: pd.DataFrame) -> pd.DataFrame:
    """Pearson correlation between PM2.5 and admissions for each age group."""
    rows = []
    for group, part in hospital_monthly.groupby("age_group"):
        joined = air_monthly.merge(part[["month", "admissions"]], on="month", how="inner")
        r, p = pearson(joined["pm25"], joined["admissions"])
        rows.append({"Age group": group, "Pearson r (PM2.5)": r, "p-value": p})
    return pd.DataFrame(rows)


def format_p(p: float) -> str:
    """Friendly p-value text."""
    if np.isnan(p):
        return "n/a"
    return "< 0.0001" if p < 0.0001 else f"{p:.4f}"
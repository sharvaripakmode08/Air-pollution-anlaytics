"""
generate_sample_data.py
-----------------------
Creates the two SAMPLE CSV files in the data/ folder.

IMPORTANT: The numbers produced here are SYNTHETIC (computer-generated).
They are NOT real air-quality readings and NOT real hospital records.
They exist only so the dashboard can be demonstrated without real data.

Run it (optional - the CSV files are already included):
    python generate_sample_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

rng = np.random.default_rng(42)  # fixed seed -> same files every time

# 5 years of monthly data: Jan 2021 - Dec 2025 (60 months)
months = pd.date_range("2021-01-01", "2025-12-01", freq="MS")
month_number = months.month.to_numpy()

# ---------------------------------------------------------------------------
# 1) Air pollution (SAMPLE)
#    Pattern: higher in winter, lower in monsoon, plus random noise.
# ---------------------------------------------------------------------------
seasonal = np.cos(2 * np.pi * (month_number - 1) / 12)  # peak in Jan, low in Jul
trend = np.linspace(4, -4, len(months))                 # slight improvement over time

pm25 = np.clip(55 + 28 * seasonal + trend + rng.normal(0, 6, len(months)), 15, None)
pm10 = 1.9 * pm25 + rng.normal(0, 10, len(months))
aqi = 1.7 * pm25 + 20 + rng.normal(0, 8, len(months))

air = pd.DataFrame(
    {
        "date": months.strftime("%Y-%m-%d"),
        "aqi": aqi.round(1),
        "pm25": pm25.round(1),
        "pm10": pm10.round(1),
        "data_label": "SAMPLE (synthetic, not real data)",
    }
)

# Leave a few cells empty on purpose, to show how missing values are handled
for col in ["aqi", "pm25", "pm10"]:
    air.loc[rng.choice(len(air), 2, replace=False), col] = np.nan

# ---------------------------------------------------------------------------
# 2) Hospital admissions for respiratory diseases (SAMPLE)
#    Three age groups per month; admissions loosely follow PM2.5 plus noise.
# ---------------------------------------------------------------------------
age_groups = {
    # name: (baseline admissions per month, sensitivity to PM2.5)
    "Children (0-14)": (110, 0.008),
    "Adults (15-59)": (140, 0.005),
    "Elderly (60+)": (125, 0.010),
}

rows = []
for i, month in enumerate(months):
    for group, (base, sensitivity) in age_groups.items():
        value = base * (1 + sensitivity * (pm25[i] - 55)) + rng.normal(0, 8)
        rows.append(
            {
                "date": month.strftime("%Y-%m-%d"),
                "age_group": group,
                "admissions": int(max(10, round(value))),
                "data_label": "SAMPLE (synthetic, not real data)",
            }
        )

hospital = pd.DataFrame(rows)
hospital["admissions"] = hospital["admissions"].astype("Int64")
hospital.loc[rng.choice(len(hospital), 4, replace=False), "admissions"] = pd.NA

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
air.to_csv(DATA_DIR / "sample_air_pollution.csv", index=False)
hospital.to_csv(DATA_DIR / "sample_hospital_admissions.csv", index=False)
print("Sample files written to:", DATA_DI
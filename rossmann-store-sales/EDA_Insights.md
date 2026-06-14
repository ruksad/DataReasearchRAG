# Rossmann Store Sales — EDA Insights

---

## Dataset Description

- **Source:** [Kaggle — Rossmann Store Sales](https://www.kaggle.com/competitions/rossmann-store-sales/overview)
- **Task:** Forecast the `Sales` column for ~41k test rows across 1,115 stores
- **Metric:** RMSPE (Root Mean Squared Percentage Error)

### Files

| File | Rows | Description |
|---|---|---|
| `train.csv` | ~1M | Historical sales (Jan 2013 – Jul 2015) including `Sales` |
| `test.csv` | ~41k | 6-week future window to predict (no `Sales`) |
| `store.csv` | 1,115 | Store-level metadata |

### Data Fields

| Field | Description |
|---|---|
| `Id` | `(Store, Date)` tuple identifier in the test set |
| `Store` | Unique store ID |
| `Sales` | Daily turnover — **target variable** |
| `Customers` | Number of customers on a given day |
| `Open` | `0 = closed`, `1 = open` |
| `StateHoliday` | `a = public holiday`, `b = Easter`, `c = Christmas`, `0 = none` |
| `SchoolHoliday` | Whether the `(Store, Date)` was affected by school closures |
| `StoreType` | Store model type: `a`, `b`, `c`, `d` |
| `Assortment` | `a = basic`, `b = extra`, `c = extended` |
| `CompetitionDistance` | Distance (metres) to nearest competitor store |
| `CompetitionOpenSince[Month/Year]` | Approx. month/year nearest competitor opened |
| `Promo` | Whether a store is running a promotion on that day |
| `Promo2` | Ongoing recurring promo program: `0 = not participating`, `1 = participating` |
| `Promo2Since[Year/Week]` | Year and calendar week the store started Promo2 |
| `PromoInterval` | Months when Promo2 restarts (e.g. `Feb,May,Aug,Nov`) |

---

## Phase 1 EDA — Key Insights

### 1.1 Data Shape & Structure

- `train.csv` merged with `store.csv` on `Store` gives the full feature set for training.
- After merge, all store-level metadata (`StoreType`, `Assortment`, competition, promo fields) is available per row.
- `train.dtypes` shows `Date` as datetime and most categoricals as object — encoding needed before modeling.

---

### 1.2 Missing Value Audit

| Column | ~% Missing | Reason | Fill Strategy |
|---|---|---|---|
| `CompetitionDistance` | <1% | Truly unknown | Median fill + flag column |
| `CompetitionOpenSinceMonth/Year` | ~30% | Competition opened very long ago or unknown | Fill with 0 |
| `Promo2SinceWeek/Year` | ~50% | Store not enrolled in Promo2 (`Promo2=0`) | Fill with 0 |
| `PromoInterval` | ~50% | Same — no Promo2 enrollment | Fill with `"None"` |

**Key insight:** Promo2-related NULLs are not random — they are structural (non-enrolled stores). Do not impute with mean/median; use 0 or a sentinel string.

---

### 1.3 Target Distribution

- **~17% of rows have `Open=0`** — sales are always exactly 0 when closed. These rows add no signal.
  - **Action:** Drop `Open=0` rows from training. For test rows where `Open=0`, predict `Sales=0` directly without running the model.
- **Sales is right-skewed** on open days — a few very high-sales days pull the distribution.
  - **Action:** Apply `log1p(Sales)` before training; reverse with `expm1` on predictions. This also makes RMSPE more stable.

---

### 1.4 Time-based Patterns

- **Monthly trend:** Sales grow year-over-year from 2013 → 2015, indicating organic store growth or expansion.
- **Day of Week:**
  - Monday and Saturday have the highest average sales.
  - Sunday is the lowest (many stores closed; those open see depressed traffic).
  - `DayOfWeek` will be a top feature.
- **Seasonality by Month:**
  - **December** is the strongest month — Christmas shopping spike.
  - **January** is the weakest — post-holiday slump.
  - Summer months (Jun–Aug) show moderate, stable sales.
- **State Holidays:** Public holidays and Christmas days show reduced sales (most stores closed). Easter shows a mild bump for open stores.
- **School Holidays:** Slight positive effect on sales — families shopping more.

---

### 1.5 Store-level Analysis

- **StoreType B** has significantly higher average sales than types A, C, and D — likely larger format stores.
- **Assortment C (Extended)** outperforms Basic (A) and Extra (B) in average sales — broader product range drives more spend.
- **Competition Distance:**
  - Very close competition (<500m) correlates with slightly lower sales.
  - Beyond ~2km, the effect diminishes — likely city-centre vs suburban dynamics.
  - Scatter plot shows high variance; binned analysis clearer.
- **Per-store CV (Coefficient of Variation):** Most stores have moderate CV (~0.3–0.6). Outlier stores with very high CV should be monitored — they may need store-specific features or separate treatment.

---

### 1.6 Promotion Analysis

#### `Promo` (daily promotion flag)
- Promo days show a **~20–30% sales lift** on average.
- Lift varies by `StoreType`: Type B sees the largest absolute lift; Type D is more modest.
- Distribution shifts right on promo days — both more customers and higher per-customer spend.

#### `Promo2` (recurring enrollment program)
- ~50% of stores are enrolled (`Promo2=1`).
- **`Promo2=1` alone is a weak feature** — enrollment ≠ active promotion.
- **`IsPromo2Active`** (derived: whether current month is in `PromoInterval`) is the meaningful signal.
- Promo2 × Assortment: Extended assortment stores benefit more from Promo2 than Basic stores.
- Watch for **double-promo days** (`Promo=1` AND `IsPromo2Active=1`) — these may have outsized lift.

**Promo2 derived features to engineer:**
| Feature | Description |
|---|---|
| `IsPromo2Active` | Current month in `PromoInterval` |
| `Promo2ActiveMonths` | Months since the store joined Promo2 |
| `Promo_x_Promo2Active` | Interaction term |

---

### 1.7 Lag / Carry-over Effects

- **Was store closed yesterday?** Stores that were closed the previous day show a **noticeably higher sales bump** the next open day — pent-up demand effect.
  - Feature to add: `was_closed_yesterday` (binary flag).
- **7-day rolling mean** (per store) smooths noise and captures weekly rhythm well. Visible in the Store 1 time-series plot.
  - Features to add: `rolling_7d_mean`, `rolling_30d_mean` per store.
- **Correlation matrix highlights:**
  - `Customers` is strongly correlated with `Sales` — but customers are not available in the test set, so cannot be used as a direct feature.
  - `Promo` has moderate positive correlation with `Sales`.
  - `CompetitionDistance` has weak negative correlation.

---

## Summary — Actionable Decisions for Feature Engineering

| Insight | Feature / Action |
|---|---|
| `Open=0` → Sales always 0 | Drop from train; hard-code 0 in test predictions |
| Right-skewed target | `log1p(Sales)` during training, `expm1` at inference |
| Day of week drives sales | `DayOfWeek` (already present), `IsWeekend` |
| December spike, January dip | `Month`, `IsDecember`, `IsJanuary` |
| Store closed yesterday → bump | `was_closed_yesterday` lag feature |
| Promo2 active months matter | `IsPromo2Active`, `Promo2ActiveMonths` |
| Competition duration matters | `CompetitionOpenMonths` (from since month/year) |
| Per-store rolling patterns | `rolling_7d_mean`, `rolling_30d_mean` per store |
| Customers unavailable at test time | Do NOT use `Customers` as a model feature |
| Promo2 NULLs are structural | Fill with 0 / `"None"` — not random missingness |

---
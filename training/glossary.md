# Rossmann Business Glossary

## Key rules
- ALWAYS bracket `[Open]` and `[Date]` in SQL — they are reserved keywords in T-SQL.
- Filter `[Open] = 1` on any Sales aggregation to exclude closed-day zeros.
- Use `dbo.Train` for time-series sales data; use `dbo.Store` for store metadata. Join on `Store`.

## Term definitions

**open day** — a row in dbo.Train where `[Open] = 1`. Always filter these when computing Sales metrics.

**revenue / total sales** — `SUM(Sales)` on open days: `SUM(Sales) WHERE [Open] = 1`

**average sales** — `AVG(Sales)` on open days: `AVG(Sales) WHERE [Open] = 1`

**promo day** — a row where `Promo = 1` (daily promotion running that day).

**non-promo day** — a row where `Promo = 0`.

**promo lift** — difference in average Sales between promo days and non-promo days.

**active Promo2** — a store enrolled in Promo2 (`Promo2 = 1`) and the current month appears in its `PromoInterval` column. PromoInterval is a comma-separated string like `'Feb,May,Aug,Nov'`.

**store type B** — `StoreType = 'b'`. Largest format stores; historically highest average sales.

**extended assortment** — `Assortment = 'c'`. Broadest product range; highest average sales vs basic ('a') and extra ('b').

**peak day of week** — the `DayOfWeek` value with the highest `AVG(Sales)` on open days. DayOfWeek 1=Monday … 7=Sunday.

**weekend** — `DayOfWeek IN (6, 7)` (Saturday and Sunday).

**Christmas period** — `StateHoliday = 'c'`.

**public holiday** — `StateHoliday = 'a'`.

**school holiday** — `SchoolHoliday = 1`.

**competition open months** — derived as `(YEAR([Date]) - CompetitionOpenSinceYear) * 12 + (MONTH([Date]) - CompetitionOpenSinceMonth)`. Measures how long a competitor has been open relative to each sales row.

**close competitor** — `CompetitionDistance < 500` (less than 500 metres away).

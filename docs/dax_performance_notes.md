# DAX Performance Notes

## Overview

DAX Studio and VertiPaq Analyzer were used to evaluate the
performance and storage characteristics of the `AWS Billing Analysis` Power BI semantic
model.

The review focused on:

- VertiPaq table and column storage
- Column cardinality
- Column compression
- High-cardinality columns
- DAX query execution time
- Formula Engine (FE) performance
- Storage Engine (SE) performance

The model contained approximately 850,619 rows in the `FactsCost`
fact table which served as the basis for review.

---

# 1. VertiPaq Analyzer Review

VertiPaq Analyzer was used to identify columns with relatively high
cardinality and large storage requirements.

The initial analysis identified the following major storage
consumers in `FactsCost`:

| Column | Rows | Cardinality | Column Size | % Table | Data Type |
|---|---:|---:|---:|---:|---|
| `usage_quantity` | 850,619 | 76,532 | 5,642,356 B | 25.91% | Double |
| `amortized_cost` | 850,619 | 76,307 | 5,638,808 B | 25.90% | Double |
| `unblended_cost` | 850,619 | 76,304 | 5,639,056 B | 25.90% | Double |
| `unit_rate` | 850,619 | 43,629 | 2,939,424 B | 13.50% | Double |

The primary reason for the high storage consumption was their high cardinality as many
rows contained distinct decimal values because of high decimal places.

---

# 2. Optimisation Applied: Numeric Rounding

The observed numeric measurement columns were rounded off to 2d.p to
reduce unnecessary decimal precision. This consequently reduced the
number of distinct values stored by VertiPaq and improved compression

The observed columns are:

- `usage_quantity`
- `unblended_cost`
- `amortized_cost`
- `unit_rate`

For example, values with high decimal precision were
modified to a minimal level of precision precisely 2 decimal places:

    Before:
    42.3849271837
    42.3849271838
    42.3849271839

    After:
    42.38
    42.38
    42.38

---

# 3. Before vs After VertiPaq Results

The impact of the rounding optimisation was measured using
VertiPaq Analyzer after refreshing the model.

| Column | Before Cardinality | After Cardinality | Cardinality Reduction | Before Column Size | After Column Size | Size Reduction |
|---|---:|---:|---:|---:|---:|---:|
| `usage_quantity` | 76,532 | 50,924 | 33.46% | 5,642,356 B | 4,621,184 B | 18.10% |
| `unblended_cost` | 76,304 | 9,756 | 87.21% | 5,639,056 B | 1,994,804 B | 64.63% |
| `amortized_cost` | 76,307 | 9,704 | 87.28% | 5,638,808 B | 1,993,984 B | 64.64% |
| `unit_rate` | 43,629 | 42 | 99.90% | 2,939,424 B | 166,072 B | 94.35% |

## Observed improvement

The optimisation produced a significant reduction in cardinality
across all the observed four columns.

The largest improvements were observed in:

### `unit_rate`

Cardinality decreased from:

    43,629 → 42

representing a **99.90% reduction**.

Column size decreased from:

    2,939,424 B → 166,072 B

representing a **94.35% reduction**.

### `unblended_cost`

Cardinality decreased from:

    76,304 → 9,756

representing an **87.21% reduction**.

Column size decreased from:

    5,639,056 B → 1,994,804 B

representing a **64.63% reduction**.

### `amortized_cost`

Cardinality decreased from:

    76,307 → 9,704

representing an **87.28% reduction**.

Column size decreased from:

    5,638,808 B → 1,993,984 B

representing a **64.64% reduction**.

### `usage_quantity`

Cardinality decreased from:

    76,532 → 50,924

representing a **33.46% reduction**.

Column size decreased from:

    5,642,356 B → 4,621,184 B

representing an **18.10% reduction**.

---

# 4. Other VertiPaq Findings

## Resource ID

`DimResource[resource_id]` was identified as a high-cardinality
column:

- Rows: 1,368
- Cardinality: 1,368
- Column Size: 54,133 B
- Data Type: String

**Action**: Although the column has 100% cardinality; its total storage
requirement is small. Therefore, no optimisation was applied and the reason being that 
the column is required to identify AWS resources and it's best to remain as it is for accurate reporting and analysis.

---

## Resource Surrogate Key

`DimResource[resource_key]`:

- Rows: 1,368
- Cardinality: 1,368
- Column Size: 51,792 B
- Data Type: Int64

`FactsCost[Dim_Resource.resource_key]`:

- Rows: 850,619
- Cardinality: 1,368
- Data Type: Int64

**Action**: No optimisation was required.

---

## Date Key

`FactsCost[Dim_Date.date_key]`:

- Rows: 850,619
- Cardinality: 730
- Column Size: 1,153,864 B
- Data Type: Int64

The low cardinality of the date key only means that the same
values are repeated throughout the `FactsCost` table.

**Action**: No change was required.

---

## Date Dimension

`DimDate[date]`:

- Rows: 730
- Cardinality: 730
- Column Size: 29,572 B
- Data Type: DateTime

The date dimension is small and is not expected to pose any storage bottlenecks

**Action**: No change was required.

---

# 5. DAX Studio Server Timings

DAX Studio was used to analyze three observed
visuals from the report. The queries were then copied from Power BI Desktop Performance Analyzer and executed in DAX Studio with Server Timings enabled.

---

## 5.1 Monthly Cost Trend

The analysed visual (`Monthly Cost trend`) grouped `Total Cost` by month.

| Metric | Result |
|---|---:|
| Total Duration | 7 ms |
| Formula Engine | 7 ms |
| Storage Engine Queries | 1 |
| VertiPaq Cache Matches | 1 |
| Result Rows | 12 |

The query completed in approximately **7 ms**.

**Action**: No DAX optimisation was required.

---

## 5.2 Committed Spend Ratio

The `Committed Spend Ratio` measure was profiled using DAX Studio.

The query performed two Storage Engine operations:

1. Calculate cost for Reserved Instances and Savings Plans.
2. Calculate total cost.

| Metric | Result |
|---|---:|
| Total Duration | 4 ms |
| Formula Engine | 4 ms |
| Storage Engine Queries | 2 |
| VertiPaq Cache Matches | 2 |
| Result Rows | 1 |

The query completed in approximately **4 ms**.


**Finding**: The measure did not represent a performance bottleneck.


**Action**: No DAX optimisation was applied.

---

# 6. Service × Region Matrix

This visual is a relatively more complex matric visual which grouped `Total Cost` by:

- `DimService[service_name]`
- `DimRegion[region]`

| Metric | Result |
|---|---:|
| Total Duration | 10 ms |
| Formula Engine | 7 ms |
| Storage Engine | 3 ms |
| Storage Engine Queries | 3 |
| VertiPaq Cache Matches | 2 |
| Result Rows | 99 |
| Approximate Peak Memory | 1,061 KB |

Despite the multiple dimensions involved, relationships, date
filtering, grouping and totals associated in the visual, the query completed in approximately
**10 ms**.

**Finding**: No meaningful performance bottleneck was identified.

**Action**: No DAX optimisation was applied.

---

# 7. Server Timings Summary

| Visual | Total Duration | Formula Engine | Storage Engine | SE Queries |
|---|---:|---:|---:|---:|
| Monthly Cost Trend | 7 ms | 7 ms | ~0 ms | 1 |
| Committed Spend Ratio | 4 ms | 4 ms | ~0 ms | 2 |
| Service × Region Matrix | 10 ms | 7 ms | 3 ms | 3 |

**Finding**: All three tested queries completed within approximately 10 ms.

**Action**: No significant Formula Engine or Storage Engine bottleneck was identified.

---

# 8. Performance Optimisation Summary

Numeric rounding is the only notable action applied to help improve the performarnce of the model. This approach greatly helped to reduce cardinality and VertiPaq column storage.

The largest improvement was observed in `unit_rate`, where cardinality decreased by 99.90% and column size decreased by 94.35%.

---

# 9. Conclusion

- VertiPaq Analyzer and DAX Studio together gave both storage-level and query-level insight into the semantic model.
- VertiPaq Analyzer identified the primary storage consumers and flagged high-cardinality numeric columns as the main targets for optimisation.
- Rounding off the numeric columns produced measurable cardinality reductions which are presented below:
  - `usage_quantity` — 33.46% reduction
  - `unblended_cost` — 87.21% reduction
  - `amortized_cost` — 87.28% reduction
  - `unit_rate` — 99.90% reduction
- Column storage size also decreased substantially, with the largest reduction on `unit_rate` at 94.35%.
- DAX Studio Server Timings showed all three tested report queries completing within 4–10 ms, with no significant Formula Engine or Storage Engine bottleneck identified.
- All the approaches leveraged in this analysis were evidence-based. The high-cardinality numeric columns were optimised as necessary and only when required, while other columns and DAX expressions already performing efficiently were left unchanged.
# Security Matrix — RLS & OLS

**Model:** AWS Business Analysis

---

## Row-Level Security (RLS)

Applied on `DimAccount[business_unit]`. Each role restricts the account rows a user can see; all other tables inherit the filter through the star schema relationships.

| Role | DAX filter (on Dim_Account) | Rows visible |
|---|---|---|
| Engineering | `[business_unit] = "Engineering"` | Only Engineering business unit accounts |
| DataPlatform | `[business_unit] = "DataPlatform"` | Only Data Platform business unit accounts |
| Marketing | `[business_unit] = "Marketing"` | Only Marketing business unit accounts |
| Finance | `[business_unit] = "Finance"` | Only Finance business unit accounts |
| SharedServices | `[business_unit] = "SharedServices"` | Only sharedservices accounts |
| Executive | No filter | All business units |

---

## Object-Level Security (OLS)

Applied at the column level in Tabular Editor. Restricted columns return blank for any role not explicitly granted **Read** access.

| Column | Table | Roles with access | Roles restricted | Reason |
|---|---|---|---|---|
| amortized_cost | FactsCost | Finance, Executive | Engineering, DataPlatform, Marketing, SharedServices | Sensitive pricing detail |
| linked_account_id | DimAccount | Finance, Executive | Engineering, DataPlatform, Marketing, SharedServices | This is raw AWS account numberand is an internal identifier with no analytical value outside Finance/Executive |

Restricted roles can still see aggregated cost through the right measures (e.g. `amortized_cost`) and where the report is designed to expose them. The sole purpose of OLS here is to restrict direct access to the *raw columns* and not the measures built on top of them.

---

## Combined access summary

| Role | Row scope | Can see raw armotized cost columns | Can see raw account IDs |
|---|---|---|---|
| Engineering | Engineering accounts only | No | No |
| DataPlatform | Data Platform accounts only | No | No |
| Marketing | Marketing accounts only | No | No |
| SharedServices | Shared infrastructure accounts only | No | No |
| Finance | All accounts | Yes | Yes |
| Executive | All accounts | Yes | Yes |

Note: Finance is listed here with full row access rather than BU-restricted because Finance needs a complete view of spending across the organisation for things like chargebacks, cost allocation, financial analysis, and negotiating cloud pricing/deals.
# Best Practice Analyzer

**Model:** AWS Billing Analysis

**Ruleset:** Tabular Editor 3 (TE3) built-in Best Practice Analyzer file

---

## BPA Rules by Category

### Governance

| Rule | Affected Objects | Applied fix and Why |
|---|---|---|
| Power BI models should use latest compatibility level | Semantic model | Updated the model to the latest compatibility level supported by the Power BI environment. This ensures access to the latest semantic-model features and functionality.

### Performance

| Rule | Affected Objects | Applied fix and Why |
|---|---|---|
| Set `IsAvailableInMdx` to false on non-attribute columns | resource_id, and any other high-cardinality column not used for slicing | Set IsAvailableInMdx to false for columns that do not need to be exposed as attribute hierarchies. This approach helps to reduce processing times and memory use. |
| Do not summarize numeric columns that aren't meant to be summed | Surrogate key columns (region_key, resource_key, date_key) | KSet Summarize By to None for surrogate key columns. This prevents accidental aggregation of key values, which could produce misleading totals. |


### Maintenance

| Rule | Affected Objects | Applied fix and Why |
|---|---|---|
| Visible measures with no description | All visible measures in the _Measures table | Added clear descriptions to all measures explaining their purpose and calculation logic. This improves discoverability and helps anyone with adequate permissions understand how each measure should be used without having to inspect the DAX code.
| Visible tables with no description | All visible tables loaded onto the power dashboard | Added clear descriptions to each visible table explaining its purpose and role within the semantic model.


### Formatting

| Rule | Affected Objects | Applied fix and Why |
|---|---|---|
| Hide foreign key columns | Any key column left visible in facts tables that exists only to support relationships | All foreign keys should be hidden as they can clutter the field list and should not be user-facing |
| Do not summarize numeric columns that aren't meant to be aggregated | Latitude, Longitude | Set `Summarize By = None` because geographical coordinates are descriptive attributes. This prevents report users from accidentally aggregating coordinates. |
| Provide format string for visible numeric measures | Cost measures (Total Cost, MTD Cost, YTD Cost, etc.) and ratio measures (MoM %, Committed Spend Ratio, Effective Savings Rate) | Without clear currency/percentage format strings, visuals might display raw unformatted numbers |
| Provide format string for visible numeric columns| Numeric columns exposed to report authors, such as usage_quantity, unblended_cost and amortized_cost | Applied appropriate format strings based on the business meaning of each column. Cost columns use a currency format and percentages use a percentage format |


# AWS Billing Analysis

A Power BI project built around a synthetic AWS Cost and Usage Report (CUR). The project covers data modelling, DAX, security, performance tuning, and GitHub Actions CI/CD.

The aim was to build something similar to the reporting and semantic model used for cloud cost analysis, while also applying some of the development and governance practices used in a production BI environment.

---

## 1. Project Overview

AWS Billing Analysis uses a synthetic AWS CUR-style dataset to analyse cloud costs across accounts, services, regions, teams and business units.

The project includes:

- A Power BI star schema
- Power Query transformations
- DAX measures for cost and FinOps reporting
- Row-Level Security (RLS)
- Object-Level Security (OLS)
- VertiPaq Analyzer and DAX Studio performance analysis
- Tabular Editor 3 for model development and Best Practice Analyzer checks
- Git and GitHub for version control
- GitHub Actions for CI/CD

The dataset is completely synthetic and follows the structure of an AWS CUR export but does not contain real AWS billing information.

**Owner:** Opeyemi Aniwura — AWS Solutions Architect Associate, OCI Cloud Solutions Architect Associate, Data Analyst

---

## 2. Technical Requirements

| Layer | Tool |
|---|---|
| Data generation | Artificially generated |
| ETL | Power Query |
| Semantic model | Power BI Desktop, PBIP/TMDL |
| DAX authoring & governance | Tabular Editor 3 |
| Performance analysis | DAX Studio, VertiPaq Analyzer |
| Security | Row-Level Security (RLS), Object-Level Security (OLS) |
| Version control | Git / GitHub |
| CI/CD | GitHub Actions, Tabular Editor CLI, Best Practice Analyzer |

---

## 3. Repository Structure

```
AWS Billing Analysis/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── data/
│   └── aws_cloudcost_cur_dataset.csv
├── model/
│   ├── AWS_Billing_Analysis.pbip
│   ├── AWS_Billing_Analysis.Report/
│   └── AWS_Billing_Analysis.SemanticModel/
├── docs/
│   ├── erd.drawio
│   ├── erd.png
│   ├── architecture.png
│   ├── vertipaq_analyzer_(after).png
│   ├── server_timings1.json
│   ├── server_timings2.json
│   ├── server_timings3.json
│   ├── bpa-findings.md
│   ├── dax_performance_notes.md
│   ├── project_plan.md
│   ├── data-dictionary.md
│   ├── security-matrix.md
│   └── model-metadata.json                                 #auto-generated after running ci.yml
├── scripts/
│   └── BPARules.json
└── README.md
```

---

## 4. Data Model

A star schema built from the synthetic CUR dataset, using surrogate integer keys throughout.

The main fact table is:

- **FactsCost** — contains the cost and usage records, including `usage_quantity`, `unit_rate`, `unblended_cost`, and `amortized_cost`

The dimension tables are:

- **DimDate**
- **DimAccount**
- **DimService**
- **DimRegion**
- **DimResource**
- **DimPricingModel**
- **DimUsage**
- **DimTeam**
- **DimProject**
- **DimEnvironment**

Surrogate integer keys were generated to facilitate the relationships between the fact and dimension tables.

Full ERD: [`docs/erd.png`](docs/erd.png). Full column-by-column and measure-by-measure documentation: [`docs/data_dictionary.md`](docs/data_dictionary.md).

---

## 5. DAX Measures

The measures are stored in a `_Measures` table and organised into display folders.

### Core

- Total Cost
- Total Amortized Cost
- Total Usage
- Cost per Unit
- Distinct Resources

### Time Intelligence

- MTD Cost
- QTD Cost
- YTD Cost
- MoM Cost Change %
- YoY Cost Change %
- Rolling 3-Month Avg Cost
- Rolling 7-Day Avg Cost

### Variance

- Cost Variance vs Prior Month
- Cost Variance %
- Daily Cost StdDev

### FinOps KPIs

- On-Demand Cost
- Committed Cost
- Committed Spend Ratio
- Effective Savings Rate
- Cost Contribution %

Full descriptions: [`docs/data_dictionary.md`](docs/data_dictionary.md).

---

## 6. Report Pages

| Page | Status |
|---|---|
| Executive Summary | Built |
| Cost by Service & Region | Built |
| Business Unit Deep Dive (RLS) | Built |
| Pricing Model Mix | Built |

---

## 7. Security

### Row-Level Security

Six roles were created to control access by business unit:

- Engineering
- DataPlatform
- Marketing
- SharedServices
- Finance
- Executive

Finance is intentionally unrestricted at the row level, since chargeback/cost-allocation reporting requires cross-BU visibility. (See rationale in the security matrix). All roles were created and tested via "View As Role."

### Object-Level Security

Object-Level Security was configured in Tabular Editor and the following columns are restricted to Finance and Executive:

- `amortized_cost`
- `linked_account_id`

The OLS configuration was tested to confirm that users outside those roles cannot access the restricted columns.

Full role-by-role and column-by-column detail: [`docs/security-matrix.md`](docs/security-matrix.md).

---

## 8. Best Practice Analyzer

A full BPA pass was run in Tabular Editor 3 using the built-in Best Practice Analyzer, covering:

- Governance
- Performance
- Maintenance
- Formatting

Some of the changes made included:

- Updating the compatibility level
- Disabling `IsAvailableInMdx` on high-cardinality columns that are not used for slicing
- Disabling summarization on surrogate keys and geographic coordinates
- Adding descriptions to visible tables and measures
- Hiding foreign keys
- Applying format strings to cost and ratio measures

Full findings and fixes: [`docs/bpa-findings.md`](docs/bpa-findings.md).

The same ruleset (`scripts/BPARules.json`) also runs automatically in CI on every pull request via the Tabular Editor CLI, disallowing any future regression against these same standards.

---

## 9. Performance Tuning

DAX Studio and VertiPaq Analyzer were used to audit the model (~850,619 rows in FactsCost). High-cardinality numeric columns were rounded to 2 decimal places, producing measurable improvements:

| Column | Cardinality Reduction | Storage Size Reduction |
|---|---:|---:|
| `unit_rate` | 99.90% | 94.35% |
| `amortized_cost` | 87.28% | 64.64% |
| `unblended_cost` | 87.21% | 64.63% |
| `usage_quantity` | 33.46% | 18.10% |

The rounding was only applied to the columns where it produced a useful reduction without affecting the required reporting precision.

DAX Studio Server Timings was also used to check several report queries including:

- Monthly Cost Trend
- Committed Spend Ratio
- Service × Region Matrix

The tested queries completed in approximately 4–10 ms, and the Server Timings results did not show a significant Formula Engine or Storage Engine bottleneck.

Full detail: [`docs/dax_performance_notes.md`](docs/dax_performance_notes.md).

---

## 10. CI/CD Pipeline

The project uses GitHub Actions for automated checks.

### CI

`ci.yml` runs when a pull request is opened or updated.

The workflow:

1. Checks out the repository
2. Downloads the Tabular Editor CLI
3. Runs Best Practice Analyzer against `scripts/BPARules.json`
4. Fails the check if an Error-severity BPA rule is triggered

This provides a basic check before changes are merged into `main`.

### CD

`cd.yml` runs after changes are merged into `main`.

The workflow uses the Tabular Editor CLI to export model metadata, including:

- Tables
- Columns
- Measures
- Relationships

The exported metadata is saved as:

```
docs/model-metadata.json
```

The project was built without access to a Power BI Pro/PPU workspace, so the CD workflow currently focuses on generating and versioning model documentation rather than deploying the model to a Power BI workspace.

---

## 11. Known Limitations

- The project does not currently deploy to a Power BI workspace because Power BI Pro/PPU workspace access was not available during development.
- The CD pipeline therefore generates model metadata rather than performing a live Power BI deployment.
- The dataset is synthetic and does not represent actual AWS billing data.
- Relationship keys use surrogate integers.

---

## 12. Documentation

Additional project documentation can be found in the `docs` folder:

- `data-dictionary.md` — model columns and measures
- `security-matrix.md` — RLS and OLS configuration
- `bpa-findings.md` — Best Practice Analyzer findings and fixes
- `dax_performance_notes.md` — DAX Studio and Server Timings analysis
- `performance-tuning.md` — VertiPaq optimisation work
- `project_plan.md` — project planning
- `model-metadata.json` — exported model metadata

---

## 13. Author

**Opeyemi Aniwura**

AWS Solutions Architect Associate  
OCI Cloud Solutions Architect Associate  
Data Analyst
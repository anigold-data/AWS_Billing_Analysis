# AWS Billing Analysis — Project Plan
**Power BI specific project: RLS/OLS, Tabular Editor, DAX Studio, GitHub CI/CD**

### Owner: Opeyemi Aniwura
### Estimated duration: 6–7 weeks at a few hours/week
---

## Goal

**Goal:** Deliver one repo, one working Power BI solution which starts from analyzing synthetically generated raw data to finally delivering a version-controlled, CI/CD-deployed semantic model.

---

## Phase 1 — Environment setup (Week 1, ~2-3 hrs)

| Task | Detail |
|---|---|
| Install Power BI Desktop | Latest version |
| Install Tabular Editor | Tabular Editor 2 |
| Install DAX Studio |Connects to Power BI Desktop's local model while it's open |
| Set up GitHub repo | Public repo, e.g. `AWS Billing Analysis` |
| Enable Power BI Project format (.pbip) | This approach is what makes the model git-diffable (i.e. stored in a text-based format where Git can clearly see and compare changes line-by-line) and can be done by: File > Options > Preview features > "Power BI Project (.pbip) save option" —  |

**Deliverable :** An empty repo with folder structure illustrated below.

```
AWS Billing Analysis/
├── .github/
│   └── workflows/
│       ├── ci.yml    
│       └── cd.yml 
├── data/
│   └── aws_cloudcost_cur_dataset.csv           Synthetic CUR(Cost and Usage Report) CSV file
├── model/                                      (PBIP + TMDL semantic model)
│   ├── AWS_Billing_Analysis.pbip
│   ├── AWS_Billing_Analysis.Report/
│   └── AWS_Billing_Analysis.SemanticModel/
├── docs/
│   ├── erd.drawio                              ERD rendered in draw.io
│   ├── erd.png                                 Shows how each table relate to each other
│   ├── architecture.png                        Screenshot of model view in PowerBI
│   ├── vertipaq_analyzer_(after).png
│   ├── server_timings1.json
│   ├── server_timings2.json
│   ├── server_timings3.json
│   ├── bpa-findings.md
│   ├── dax_performance_notes.md           
│   ├── project_plan.md      
│   ├── data-dictionary.md                      Explains the data 
│   └── security-matrix.md                      Illustrates the restrictions imposed (view related)
├── scripts/
│   └── BPARules.json                           Tabular Editor's Best Practice Analyzer (BPA)
└── README.md
```

---

## Phase 2 — Synthetic dataset generation (Week 1-2, ~3-4 hrs)

It should be emphasized that the dataset used in this portfolio project was sythentically generated. While it may bear resemblance to real world data, it has no reference to any real world AWS data and should be regarded as fictitious. The data basically simulates AWS billing data by mirroring real Cost and Usage Report (CUR) fields such as:

- `usage_date`, `linked_account_id`, `account_name`, `business_unit`
- `service` (EC2, S3, RDS, Lambda, CloudFront, VPC, ElastiCache, etc.)
- `usage_type`, `operation`, `region`, `availability_zone`
- `resource_id`, `instance_type`, `pricing_model` (On-Demand/Reserved/Spot/Savings Plan)
- `unblended_cost`, `amortized_cost`, `usage_quantity`, `tags` (cost-allocation tags: `environment`, `team`, `project`)

**Deliverable:** `data/aws_cloudcost_cur_dataset.csv`.

---

## Phase 3 — Data modelling (star schema) and Power Query ETL (Week 2, ~3-4 hrs)

Build in Power Query first, then relationships are confirmed in the model view.

**Fact table**
- `FactsCost` 

**Dimension tables**
- `DimDate` 
- `DimEnvironment`
- `DimService` 
- `DimAccount`
- `DimRegion`
- `DimResource`
- `DimPricingModel`
- `DimProject`
- `DimTeam`
- `DimUsage`
- `DimTag` 

**Power Query ETL**
- Import the raw synthetic file (`aws_cloudcost_cur_dataset`), then apply data types and perform error handling.
- Parameterise the data source source paths using Power Query parameters
- Build dimension tables by referencing the cleaned raw synthetic file (staging query)

```
aws_cloudcost_cur_dataset
        │
        ├── Reference → FactCosts
        │
        ├── Reference → DimAccount
        │
        ├── Reference → DimService
.........
```
- Apply Power BI naming conventions (prefix `Dim`/`Facts`, PascalCase)
- Set the raw/staging query to: `Enable Load = OFF`

Document the ERD (draw.io) into `/docs/erd.png`.

**Deliverable:** Dim and Fact tables built, a defined working star schema in Power BI Desktop, all relationships validated (1-to-many and preferably single direction), screenshot of model view (for `../docs/architecture.png`)

---

## Phase 4 — DAX measures (Week 2-3, ~4-5 hrs)

The goal is to build a measure library organised in display folders:
- **Core**: Total Cost, Total Usage, Cost per Unit, Total Armotised Cost, Distinct Resources
- **Time Intelligence**: MTD, QTD, YTD, MoM Cost Change %, YoY Cost Change %, Rolling 3-Month Avg Cost, Rolling 7-Day Avg Cost
- **Variance**: Cost Variance vs Prior Month, Cost Variance %, Daily Cost StdDev
- **FinOps KPIs**: On-Demand Cost, Committed Cost, Committed Spend Ratio, Effective Savings Rate, 
Cost Contribution %.

**Deliverable:** measures built and organized into a display folder (`_Measures`) in the model.

---

## Phase 5 — Tabular Editor (Week 3, ~3-4 hrs)

- Connect Tabular Editor to the local model via the External Tools ribbon
- Run the **Best Practice Analyzer (BPA)**. Install the standard community BPA rule file or use the built-in BPA rules, fix at least flagged issues with severity of 3. 
- Save the model as **TMDL** (Tabular Model Definition Language) so it's readable in git diffs.

**Deliverable:** `.tmdl` files committed to `/model`, a short `docs/bpa-findings.md` noting what BPA flagged and what was changed.

---

## Phase 6 — RLS and OLS (Week 4, ~3-4 hrs)

**RLS (Row-Level Security):**
- Create roles in Power BI Desktop (simpler UI for this than TE): `BU_Marketing`, `BU_Engineering`, `BU_Finance`, `BU_DataPlatform`, `BU_SharedServices`, `Executive`
- Test with "View As Role" for each. Screenshot each result for the security matrix doc

**OLS (Object-Level Security):**
- OLS isn't available in Power BI Desktop's UI so this was executed in **Tabular Editor**
- Restrict `amortized_cost` columns from non-finance/non-executive roles (e.g., only Finance and Excecutive sees raw negotiated cost; other roles see usage/quantity only). In Tabular Editor: select `amortized_cost` column → Object Level Security → set to "None" (no read access) for non-finance/non-executive roles, "Read" for a `Finance`or `Executive` role
- Hide `DimAccount[linked_account_id]` raw AWS account numbers from non-Finance roles

**Deliverable:** `docs/security-matrix.md`

---

## Phase 7 — DAX Studio performance pass (Week 4-5, ~2-3 hrs)

- Connect DAX Studio to the local Power BI Desktop model
- Run VertiPaq Analyzer to audit table/column size, cardinality, compression
- Identify and fix high-cardinality columns affecting compression
- Capture query plans (Server Timings) for the 3 heaviest visuals; document before/after query duration

**Deliverable:** `docs/dax_performance_notes.md` with before/after screenshots of the VertiPaq Analyzer.

---

## Phase 8 — GitHub Actions CI/CD (Week 5-6, ~4-6 hrs)

**CI (triggered on every pull request):**
1. Checkout the repo
2. Install Tabular Editor CLI, downloads and extracts the portable executable onto the runner.
3. Run Tabular Editor  CLI headless against the `.tmdl` model with `-A`, pointing to the BPA rules file in `scripts/`. Any critical rule violation fails the build.
4. Run a DAX smoke test. Tabular Editor CLI executes a sample query such as (`Total Cost`) against the model to catch broken measure references before merge happens.

**CD (triggered on merge to `main`):**
- During the process of building the model, no Power BI Pro/PPU workspace was available, so XMLA-based deployment (`-D`) isn't executable in this environment.
- The pipeline substitutes model documentation export as its CD artifact: Tabular Editor CLI runs `-M` to export metadata (tables, columns, measures) to `docs/model-metadata.json`, committed back to the repo automatically on every merge.
- This constraint is documented in the README file.

**Deliverable:** working `ci.yml` and `cd.yml` under `.github/workflows/`, with a green-checkmark PR history as evidence of an enforced, automated pipeline.

---

## Phase 9 — Documentation (Week 6-7, ~4-5 hrs)

- `README.md` 
- `docs/data_dictionary.md`
- `docs/architecture.png` 
- `docs/security_matrix.md` 
- `docs/lessons-learned.md`

**Deliverable:** repo that can be cloned and understood easily from the README.



# AWS Billing Insights — Data Dictionary

## Dim_Date
| Column | Description |
|---|---|
| date_key | system-generated surrogate key for each record in the table |
| date | The calendar date, one row per day |
| year | Calendar year |
| quarter | Calendar quarter (Q1–Q4) |
| month_number | Month number (1–12) |
| month_name | Month name (January, February, etc.) |
| weekday_number | Week number within the year |
| weekday | Day name (Monday, Tuesday, etc.) |
| month_year_sort | In the order Month, Year (202508) |


## Dim_Account
| Column | Description |
|---|---|
| account_key | unique identifier for each record in the table |
| account_name | name of the AWS account (e.g. acct-eng-prod) |
| linked_account_id | The AWS account ID this data belongs to |
| payer_account_id | The organization's master/payer account ID |
| business_unit | The team/department the account rolls up to (used for RLS) |
| environment | Production, Staging, Development, or Sandbox |
| team | The internal team that owns the account |
| project | The project/product the account supports |

## Dim_Service
| Column | Description |
|---|---|
| service_key | system-generated surrogate key for each record in the table |
| service_code | AWS's internal service identifier (e.g. AmazonEC2) |
| service_name | simplified service name (e.g. EC2 - Compute) |

## Dim_Region
| Column | Description |
|---|---|
| region_key | system-generated surrogate key for each record in the table |
| region | The AWS region where the usage occurred (e.g. us-east-1) |
| city | city where the AWS data center is situated |
| country | country where the AWS data center is situated |
| latitude | latitudinal direction for the region |
| longitude | longitudinal direction for the region |

## Dim_Resource
| Column | Description |
|---|---|
| resource_key | system-generated surrogate key for each record in the table |
| resource_id | Unique identifier for the specific resource (instance, bucket, table, etc.) |


## Dim_PricingModel
| Column | Description |
|---|---|
| pricing_key | system-generated surrogate key for each record in the table |
| pricing_model | How the usage was purchased: On-Demand, Reserved Instance, Savings Plan, or Spot |

## Dim_UsageType
| Column | Description |
|---|---|
| usage_key | system-generated surrogate key for each record in the table |
| usage_type | The specific metered activity (e.g. BoxUsage:m5.large) |
| usage_unit | The unit that usage is measured in (Hrs, GB, Requests, etc.) |

## Fact_CostUsage
| Column | Description |
|---|---|
| usage_quantity | How much was consumed, in the usage_unit for that row |
| unit_rate | The price charged per unit of usage |
| unblended_cost | The raw cost as it appears on the AWS bill, before any discount spreading |
| amortized_cost | Cost with upfront Reserved Instance/Savings Plan payments spread evenly over time |

---

# Measures

## Core
| Measure | Description |
|---|---|
| Total Cost | The total raw spend/unblended cost for whatever is currently filtered |
| Total Amortized Cost | Total spend with upfront commitments spread evenly |
| Total Usage | The total quantity consumed for whatever is currently filtered |
| Cost per Unit | The average price paid per unit of usage |
| Distinct Resources | Quantifies the individual resources (servers, buckets, etc.) included in the current view |

## Time Intelligence
| Measure | Description |
|---|---|
| MTD Cost | Total cost from the start of the current month to today |
| QTD Cost | Total cost from the start of the current quarter to today |
| YTD Cost | Total cost from the start of the current year to today |
| MoM Cost Change % | Percentage change in cost compared to last month |
| YoY Cost Change % | Percentage change in cost compared to the same time last year |
| Rolling 3-Month Avg Cost | Average monthly cost over the trailing 3 months|
| Rolling 7-Day Avg Cost | Average daily cost over the trailing 7 days |

## Variance
| Measure | Description |
|---|---|
| Cost Variance vs Prior Month | The cost difference between this period's cost and last period's |
| Cost Variance % | The % difference between this period's cost and last period's |
| Daily Cost StdDev | How much the daily cost usually fluctuates |

## FinOps KPIs
| Measure | Description |
|---|---|
| On-Demand Cost | Total cost paid at AWS standard On-Demand rates |
| Committed Cost | Total cost covered by Reserved Instances or Savings Plans |
| Committed Spend Ratio | What share of total spend is covered by a commitment discount |
| Effective Savings Rate | How much is being saved overall by using commitments instead of On-Demand pricing |
| Cost Contribution % | How much each team, account contributes to the total cost


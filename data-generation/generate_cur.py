"""
CloudCost Insights — Synthetic AWS Cost & Usage Report (CUR) Generator
------------------------------------------------------------------------
Generates a realistic, industry-standard-shaped AWS billing dataset for use
as the source layer of a Power BI star schema (CloudCost Insights project).

Design goals:
  - Column vocabulary and value domains mirror real AWS Cost & Usage Reports
    (service codes, usage types, regions, pricing/purchase options) while
    using clean, BI-friendly column names (not the raw "lineItem/..." CUR
    header format, which is unwieldy for direct Power Query modelling).
  - Believable cost behaviour: monthly growth trend, weekday/weekend usage
    dips for compute, S3 storage that only grows, two deliberate cost
    anomaly events for the "Cost Anomaly" narrative in the report.
  - Multi-account, multi-business-unit structure so the RLS/OLS layer has
    something real to secure.

Output: /mnt/user-data/outputs/cloudcost_cur_dataset.csv (+ .parquet)
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta
import hashlib

RNG = np.random.default_rng(42)

# ---------------------------------------------------------------------------
# 1. Reference data — mirrors real AWS product codes, regions, usage types
# ---------------------------------------------------------------------------

REGIONS = [
    "us-east-1", "us-west-2", "eu-west-1", "eu-central-1",
    "ap-southeast-1", "ap-southeast-2", "ca-central-1", "sa-east-1",
]

AZ_SUFFIX = ["a", "b", "c"]

# service_code, service_name, usage_types (unit, base_hourly/unit cost range), pricing eligible
SERVICES = {
    "AmazonEC2": {
        "name": "EC2 - Compute",
        "usage_types": [
            ("BoxUsage:m5.large", "Hrs", (0.08, 0.12)),
            ("BoxUsage:m5.xlarge", "Hrs", (0.16, 0.24)),
            ("BoxUsage:t3.medium", "Hrs", (0.03, 0.05)),
            ("BoxUsage:c5.2xlarge", "Hrs", (0.30, 0.42)),
        ],
        "pricing_models": ["On-Demand", "Reserved Instance", "Savings Plan", "Spot Instance"],
        "resource_prefix": "i-",
    },
    "AmazonS3": {
        "name": "S3 - Storage",
        "usage_types": [
            ("TimedStorage-ByteHrs", "GB-Mo", (0.021, 0.026)),
            ("Requests-Tier1", "Requests", (0.0000045, 0.0000055)),
            ("Requests-Tier2", "Requests", (0.0000004, 0.0000006)),
        ],
        "pricing_models": ["On-Demand"],
        "resource_prefix": "bucket-",
    },
    "AmazonRDS": {
        "name": "RDS - Managed Database",
        "usage_types": [
            ("InstanceUsage:db.r5.large", "Hrs", (0.24, 0.32)),
            ("InstanceUsage:db.t3.medium", "Hrs", (0.07, 0.10)),
            ("RDS:StorageUsage", "GB-Mo", (0.10, 0.14)),
        ],
        "pricing_models": ["On-Demand", "Reserved Instance"],
        "resource_prefix": "db-",
    },
    "AWSLambda": {
        "name": "Lambda - Serverless Compute",
        "usage_types": [
            ("Lambda-GB-Second", "GB-Second", (0.0000166, 0.0000166)),
            ("Request", "Requests", (0.0000002, 0.0000002)),
        ],
        "pricing_models": ["On-Demand"],
        "resource_prefix": "fn-",
    },
    "AmazonCloudFront": {
        "name": "CloudFront - CDN",
        "usage_types": [
            ("DataTransfer-Out-Bytes", "GB", (0.085, 0.12)),
            ("Requests-HTTPS", "Requests", (0.0000075, 0.0000095)),
        ],
        "pricing_models": ["On-Demand"],
        "resource_prefix": "dist-",
    },
    "AmazonDynamoDB": {
        "name": "DynamoDB - NoSQL Database",
        "usage_types": [
            ("ReadCapacityUnit-Hrs", "RCU-Hrs", (0.00013, 0.00013)),
            ("WriteCapacityUnit-Hrs", "WCU-Hrs", (0.00065, 0.00065)),
        ],
        "pricing_models": ["On-Demand"],
        "resource_prefix": "table-",
    },
    "AmazonElastiCache": {
        "name": "ElastiCache - In-Memory Cache",
        "usage_types": [
            ("NodeUsage:cache.r6g.large", "Hrs", (0.18, 0.24)),
        ],
        "pricing_models": ["On-Demand", "Reserved Instance"],
        "resource_prefix": "cache-",
    },
    "AmazonVPC": {
        "name": "VPC - Networking",
        "usage_types": [
            ("NatGateway-Hours", "Hrs", (0.045, 0.045)),
            ("DataTransfer-Regional-Bytes", "GB", (0.01, 0.02)),
        ],
        "pricing_models": ["On-Demand"],
        "resource_prefix": "vpc-",
    },
    "AWSDataTransfer": {
        "name": "Data Transfer",
        "usage_types": [
            ("DataTransfer-Out-Internet", "GB", (0.05, 0.09)),
        ],
        "pricing_models": ["On-Demand"],
        "resource_prefix": "xfer-",
    },
    "AmazonRoute53": {
        "name": "Route 53 - DNS",
        "usage_types": [
            ("HostedZone", "Hrs", (0.0007, 0.0007)),
            ("DNS-Queries", "Requests", (0.0000004, 0.0000006)),
        ],
        "pricing_models": ["On-Demand"],
        "resource_prefix": "zone-",
    },
}

# Business units and the accounts that roll up to them (drives RLS later)
BUSINESS_UNITS = {
    "Engineering":   ["acct-eng-prod", "acct-eng-staging", "acct-eng-dev"],
    "DataPlatform":  ["acct-data-prod", "acct-data-dev"],
    "Marketing":     ["acct-mktg-prod", "acct-mktg-sandbox"],
    "Finance":       ["acct-fin-prod"],
    "SharedServices":["acct-shared-network", "acct-shared-security", "acct-shared-logging"],
}

PAYER_ACCOUNT_ID = "100000000001"

ENVIRONMENTS = ["Production", "Staging", "Development", "Sandbox"]
TEAMS = ["Platform", "Growth", "CoreAPI", "Analytics", "Infra", "Payments"]
PROJECTS = ["Phoenix", "Atlas", "Nimbus", "Falcon", "Horizon", "Vega"]

# Each account gets a stable "profile": which services it uses, home region,
# environment/team/project tags, and a base scale factor for cost realism.
def build_account_profiles():
    profiles = {}
    linked_id_seed = 200000000000
    for bu, accounts in BUSINESS_UNITS.items():
        for acct_name in accounts:
            linked_id_seed += 1
            n_services = RNG.integers(3, 7)
            services = list(RNG.choice(list(SERVICES.keys()), size=n_services, replace=False))
            # Every real org has data transfer + at least one compute service
            if "AWSDataTransfer" not in services:
                services.append("AWSDataTransfer")
            env = "Production" if "prod" in acct_name else RNG.choice(ENVIRONMENTS[1:])
            profiles[acct_name] = {
                "linked_account_id": str(linked_id_seed),
                "business_unit": bu,
                "environment": env,
                "team": RNG.choice(TEAMS),
                "project": RNG.choice(PROJECTS),
                "home_region": RNG.choice(REGIONS),
                "services": services,
                "scale": RNG.uniform(0.6, 2.4),  # relative account size
            }
    return profiles

ACCOUNT_PROFILES = build_account_profiles()


# ---------------------------------------------------------------------------
# 2. Cost behaviour model
# ---------------------------------------------------------------------------

START_DATE = date(2024, 8, 1)
END_DATE = date(2026, 7, 31)   # 24 months, ending the month before "today"

# Anomaly windows: (account, service, date_start, date_end, multiplier)
ANOMALIES = [
    ("acct-data-prod", "AmazonEC2", date(2025, 3, 10), date(2025, 3, 24), 4.5),
    ("acct-mktg-prod", "AmazonCloudFront", date(2025, 11, 20), date(2025, 11, 29), 6.0),  # Black Friday spike
    ("acct-eng-prod", "AmazonRDS", date(2026, 2, 5), date(2026, 2, 12), 3.0),
]

for _acct_name, _service_code, *_rest in ANOMALIES:
    _services = ACCOUNT_PROFILES[_acct_name]["services"]
    if _service_code not in _services:
        _services.append(_service_code)

def month_growth_factor(d: date) -> float:
    """Gentle month-over-month growth trend, ~2% per month compounding."""
    months_elapsed = (d.year - START_DATE.year) * 12 + (d.month - START_DATE.month)
    return 1.02 ** months_elapsed

def weekday_factor(d: date, service_code: str) -> float:
    """Compute/serverless dips ~30% on weekends; storage/DB unaffected."""
    if service_code in ("AmazonEC2", "AWSLambda", "AmazonDynamoDB", "AmazonCloudFront"):
        return 0.7 if d.weekday() >= 5 else 1.0
    return 1.0

def storage_growth_factor(d: date, service_code: str) -> float:
    """S3 and RDS storage only grow — steady linear creep."""
    if service_code in ("AmazonS3",) or "Storage" in service_code:
        days_elapsed = (d - START_DATE).days
        return 1.0 + days_elapsed * 0.0015
    return 1.0

def anomaly_factor(acct_name: str, service_code: str, d: date) -> float:
    for a_acct, a_svc, a_start, a_end, mult in ANOMALIES:
        if acct_name == a_acct and service_code == a_svc and a_start <= d <= a_end:
            return mult
    return 1.0

def stable_resource_id(acct_name: str, service_code: str, usage_type: str, suffix: str) -> str:
    prefix = SERVICES[service_code]["resource_prefix"]
    h = hashlib.md5(f"{acct_name}{service_code}{usage_type}{suffix}".encode()).hexdigest()[:8]
    return f"{prefix}{h}"

# ---------------------------------------------------------------------------
# 3. Generate line items
# ---------------------------------------------------------------------------

def generate():
    rows = []
    current = START_DATE
    total_days = (END_DATE - START_DATE).days + 1

    while current <= END_DATE:
        billing_period = current.strftime("%Y-%m")

        for acct_name, profile in ACCOUNT_PROFILES.items():
            for service_code in profile["services"]:
                svc = SERVICES[service_code]

                # Not every usage type fires every day (adds realistic sparsity)
                for usage_type, unit, (rate_lo, rate_hi) in svc["usage_types"]:
                    if RNG.random() > 0.93:  # ~7% chance a usage type is idle that day
                        continue

                    base_qty = {
                        "Hrs": RNG.uniform(1, 24),
                        "GB-Mo": RNG.uniform(50, 800),
                        "GB": RNG.uniform(5, 400),
                        "Requests": RNG.uniform(1000, 500000),
                        "RCU-Hrs": RNG.uniform(24, 240),
                        "WCU-Hrs": RNG.uniform(24, 240),
                        "GB-Second": RNG.uniform(500, 50000),
                    }.get(unit, RNG.uniform(1, 100))

                    factor = (
                        profile["scale"]
                        * month_growth_factor(current)
                        * weekday_factor(current, service_code)
                        * storage_growth_factor(current, service_code)
                        * anomaly_factor(acct_name, service_code, current)
                        * RNG.uniform(0.85, 1.15)  # daily noise
                    )

                    usage_quantity = round(base_qty * factor, 4)
                    rate = RNG.uniform(rate_lo, rate_hi)
                    unblended_cost = round(usage_quantity * rate, 6)
                    # Amortized differs slightly for RI/Savings Plan (upfront spread)
                    pricing_model = RNG.choice(svc["pricing_models"], p=_pricing_weights(svc["pricing_models"]))
                    amortized_cost = round(
                        unblended_cost * (0.9 if pricing_model in ("Reserved Instance", "Savings Plan") else 1.0), 6
                    )

                    region = profile["home_region"] if RNG.random() > 0.15 else RNG.choice(REGIONS)
                    az = f"{region}{RNG.choice(AZ_SUFFIX)}" if service_code == "AmazonEC2" else None

                    rows.append((
                        current.isoformat(),
                        billing_period,
                        PAYER_ACCOUNT_ID,
                        profile["linked_account_id"],
                        acct_name,
                        profile["business_unit"],
                        service_code,
                        svc["name"],
                        usage_type,
                        unit,
                        region,
                        az,
                        stable_resource_id(acct_name, service_code, usage_type, str(current.month)),
                        pricing_model,
                        usage_quantity,
                        round(rate, 8),
                        unblended_cost,
                        amortized_cost,
                        "USD",
                        profile["environment"],
                        profile["team"],
                        profile["project"],
                    ))

        current += timedelta(days=1)

    columns = [
        "usage_date", "billing_period", "payer_account_id", "linked_account_id",
        "account_name", "business_unit", "service_code", "service_name",
        "usage_type", "usage_unit", "region", "availability_zone", "resource_id",
        "pricing_model", "usage_quantity", "unit_rate", "unblended_cost",
        "amortized_cost", "currency_code", "tag_environment", "tag_team", "tag_project",
    ]
    df = pd.DataFrame(rows, columns=columns)
    return df

def _pricing_weights(models):
    weights = {
        "On-Demand": 0.55,
        "Reserved Instance": 0.25,
        "Savings Plan": 0.15,
        "Spot Instance": 0.05,
    }
    w = np.array([weights[m] for m in models], dtype=float)
    return w / w.sum()

# ---------------------------------------------------------------------------
# 4. Run + export
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    df = generate()

    print(f"Generated {len(df):,} rows across {df['usage_date'].nunique()} days, "
          f"{df['account_name'].nunique()} accounts, {df['service_code'].nunique()} services.")
    print(f"Date range: {df['usage_date'].min()} to {df['usage_date'].max()}")
    print(f"Total unblended cost: ${df['unblended_cost'].sum():,.2f}")
    print()
    print(df.head(10).to_string())

    out_csv = "/mnt/user-data/outputs/cloudcost_cur_dataset.csv"
    out_parquet = "/mnt/user-data/outputs/cloudcost_cur_dataset.parquet"
    df.to_csv(out_csv, index=False)
    df.to_parquet(out_parquet, index=False)
    print(f"\nWritten to {out_csv} and {out_parquet}")

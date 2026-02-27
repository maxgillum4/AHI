"""
generate_benchmark.py — One-time script to create synthetic benchmark dataset.
Run once: python generate_benchmark.py
Produces: data/benchmark_50_users.csv
"""

import csv
import os
import random
import uuid

random.seed(42)

ROLES = [
    "Senior Leadership",
    "Tech Lead",
    "Data Lead",
    "Operations",
    "HR",
    "Finance",
]

UNITS = [
    "Corporate Strategy",
    "Enterprise Data Platform",
    "IT / Engineering",
    "Finance & Accounting",
    "People & Culture",
    "Operations & Supply Chain",
    "Product Management",
    "Risk & Compliance",
]

CATEGORIES = [
    "Leadership & Vision",
    "Ways of Working",
    "Culture & Workforce",
    "Governance Readiness",
    "Technology Readiness",
    "Data Readiness",
]

# Role-specific score distributions (mean, std) per category
# Reflects realistic perception gaps observed in consulting engagements.
ROLE_DISTRIBUTIONS = {
    "Senior Leadership": {
        "Leadership & Vision":    (4.3, 0.5),
        "Ways of Working":        (3.8, 0.6),
        "Culture & Workforce":    (3.9, 0.5),
        "Governance Readiness":   (4.0, 0.5),
        "Technology Readiness":   (3.5, 0.7),  # Leaders often overrate tech
        "Data Readiness":         (3.8, 0.7),  # Leaders often overrate data
    },
    "Tech Lead": {
        "Leadership & Vision":    (3.2, 0.7),
        "Ways of Working":        (3.5, 0.6),
        "Culture & Workforce":    (3.0, 0.7),
        "Governance Readiness":   (3.3, 0.6),
        "Technology Readiness":   (3.8, 0.6),
        "Data Readiness":         (2.8, 0.8),  # Tech leads know where bodies are buried
    },
    "Data Lead": {
        "Leadership & Vision":    (3.0, 0.7),
        "Ways of Working":        (3.3, 0.5),
        "Culture & Workforce":    (2.9, 0.6),
        "Governance Readiness":   (3.1, 0.6),
        "Technology Readiness":   (3.4, 0.6),
        "Data Readiness":         (2.5, 0.9),  # Data leads most pessimistic about data
    },
    "Operations": {
        "Leadership & Vision":    (3.3, 0.6),
        "Ways of Working":        (3.6, 0.5),
        "Culture & Workforce":    (3.4, 0.5),
        "Governance Readiness":   (3.5, 0.5),
        "Technology Readiness":   (3.0, 0.7),
        "Data Readiness":         (2.9, 0.7),
    },
    "HR": {
        "Leadership & Vision":    (3.8, 0.5),
        "Ways of Working":        (3.4, 0.6),
        "Culture & Workforce":    (4.0, 0.5),
        "Governance Readiness":   (3.2, 0.6),
        "Technology Readiness":   (2.8, 0.7),
        "Data Readiness":         (2.5, 0.7),
    },
    "Finance": {
        "Leadership & Vision":    (3.5, 0.6),
        "Ways of Working":        (3.4, 0.6),
        "Culture & Workforce":    (3.2, 0.5),
        "Governance Readiness":   (3.8, 0.5),
        "Technology Readiness":   (2.9, 0.7),
        "Data Readiness":         (3.0, 0.7),
    },
}


def clamp(value: float, lo: float = 1.0, hi: float = 5.0) -> float:
    return round(max(lo, min(hi, value)), 2)


def generate_respondent(role: str) -> dict:
    dist = ROLE_DISTRIBUTIONS[role]
    row: dict = {
        "respondent_id": str(uuid.uuid4())[:8],
        "role": role,
        "organization_unit": random.choice(UNITS),
    }
    scores = []
    for cat in CATEGORIES:
        mean, std = dist[cat]
        score = clamp(random.gauss(mean, std))
        col = cat.replace(" ", "_").replace("&", "and").replace("/", "_")
        row[col] = score
        scores.append(score)
    row["composite_score"] = round(sum(scores) / len(scores), 2)
    return row


def main():
    os.makedirs("data", exist_ok=True)

    rows = []
    # Distribute 50 users proportionally across roles
    role_counts = {
        "Senior Leadership": 10,
        "Tech Lead": 10,
        "Data Lead": 8,
        "Operations": 8,
        "HR": 7,
        "Finance": 7,
    }

    for role, count in role_counts.items():
        for _ in range(count):
            rows.append(generate_respondent(role))

    # Column order
    cat_cols = [
        c.replace(" ", "_").replace("&", "and").replace("/", "_")
        for c in CATEGORIES
    ]
    fieldnames = (
        ["respondent_id", "role", "organization_unit"]
        + cat_cols
        + ["composite_score"]
    )

    out_path = os.path.join("data", "benchmark_50_users.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} respondents -> {out_path}")


if __name__ == "__main__":
    main()

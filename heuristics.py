"""
heuristics.py — AHI Diagnostic Reasoning Engine
Maturity signal configuration. All thresholds and keyword lists live here.
Changing analysis behavior = change this file, not analyzer.py.
"""

# ---------------------------------------------------------------------------
# Maturity Signal Keywords
# ---------------------------------------------------------------------------
SIGNALS = {
    "ownership": [
        "owner", "owns", "responsible", "accountable", "lead", "director",
        "manager", "cto", "cdo", "cio", "cpo", "vp of", "head of",
        "assigned to", "point of contact", "steward",
    ],
    "metrics": [
        "kpi", "metric", "measure", "target", "benchmark", "percentage", "%",
        "score", "index", "dashboard", "roi", "revenue", "cost reduction",
        "cycle time", "throughput", "accuracy", "recall", "precision", "f1",
        "p&l", "basis points", "run rate",
    ],
    "cadence": [
        "quarterly", "monthly", "weekly", "annual", "bi-weekly", "bi-monthly",
        "every sprint", "review cadence", "standup", "sync", "checkpoint",
        "recurring", "scheduled", "on a", "basis",
    ],
    "systems": [
        "jira", "confluence", "salesforce", "snowflake", "databricks",
        "azure", "aws", "gcp", "google cloud", "tableau", "power bi",
        "powerbi", "python", "mlflow", "airflow", "kubernetes", "docker",
        "dbt", "spark", "kafka", "looker", "datalake", "data warehouse",
        "sharepoint", "monday.com", "asana", "notion",
    ],
    "specificity": [
        "in january", "in february", "in march", "in april", "in q1",
        "in q2", "in q3", "in q4", "last quarter", "last year", "last month",
        "version", " v2", " v3", "pilot", "phase 1", "phase 2", "approved",
        "launched", "deployed", "went live",
    ],
}

# All signal keys — used when iterating over all signal types
ALL_SIGNAL_KEYS = list(SIGNALS.keys())

# ---------------------------------------------------------------------------
# Contradiction Signals
# High self-score but text contains "manual / informal" process indicators.
# ---------------------------------------------------------------------------
CONTRADICTION_PATTERNS = {
    "manual_process": [
        "manual", "manually", "spreadsheet", "excel", "google sheet",
        "ad hoc", "ad-hoc", "informal", "no formal", "not yet formalized",
        "working on it", "exploring", "in progress", "not in place",
        "haven't established", "still figuring out",
    ],
    "no_ownership": [
        "no assigned", "nobody owns", "unclear who", "not sure who",
        "shared responsibility", "everyone's job", "nobody's responsible",
    ],
    "alignment_failure": [
        "disagreements", "disagreement", "conflict", "disputes", "dispute",
        "pushback", "resistance", "tension", "not aligned", "misaligned",
        "siloed", "no consensus", "no agreement", "friction", "competing priorities",
    ],
    "data_security_risk": [
        "unsecure", "insecure", "not secure", "confidential information",
        "confidential data", "entering confidential", "no way of knowing",
        "employees entering", "unauthorized access", "data breach",
        "data leak", "no visibility", "no audit trail", "uncontrolled",
        "unmonitored", "shadow ai", "entering data", "sensitive data into",
    ],
}

# Score threshold above which contradictions are flagged
CONTRADICTION_SCORE_THRESHOLD = 4

# ---------------------------------------------------------------------------
# Anti-AI Sentiment Detection
# Text signals that indicate leadership resistance or organizational rejection
# of AI investment. These are critical flags regardless of score.
# ---------------------------------------------------------------------------
ANTI_AI_SIGNALS = [
    "do not invest in ai", "don't invest in ai", "no ai investment",
    "against ai", "reject ai", "not investing in ai", "won't invest in ai",
    "no budget for ai", "ai is not a priority", "ai not a priority",
    "leadership doesn't support ai", "leadership does not support",
    "not interested in ai", "we don't use ai", "we do not use ai",
    "no ai", "avoid ai",
]

# Signals that indicate general strategic resistance (scored questions)
STRATEGIC_RESISTANCE_SIGNALS = [
    "do not invest", "won't invest", "will not invest", "no investment",
    "no budget", "not a priority", "don't see the value",
    "doesn't see the value", "leadership rejected", "board rejected",
    "cancelled", "shut down", "defunded",
]

# ---------------------------------------------------------------------------
# Buzzword / Inflation Signals
# AI jargon without supporting evidence = inflated confidence.
# ---------------------------------------------------------------------------
BUZZWORDS = [
    "ai-powered", "ai powered", "leverage ai", "utilize ai", "transformative",
    "disruptive innovation", "paradigm shift", "game-changer", "cutting-edge",
    "best-in-class", "world-class", "next-generation", "synergistic",
    "holistic approach", "end-to-end", "360-degree", "seamlessly integrated",
    "fully automated", "real-time insights", "data-driven culture",
]

# Text must contain at least this many buzzwords before flagging inflation
BUZZWORD_INFLATION_THRESHOLD = 2

# ---------------------------------------------------------------------------
# Evidence Strength Scoring
# ---------------------------------------------------------------------------
# Minimum signal hits per band
EVIDENCE_STRONG_SIGNAL_COUNT = 3    # 3+ distinct signal categories hit → strength 3
EVIDENCE_MODERATE_SIGNAL_COUNT = 1  # 1-2 categories → strength 2
EVIDENCE_TEXT_MIN_WORDS = 10        # Fewer words than this = strength capped at 1

# ---------------------------------------------------------------------------
# Confidence Computation
# ---------------------------------------------------------------------------
CONFIDENCE_BASE = 0.50
CONFIDENCE_AUDIO_BONUS = 0.10
CONFIDENCE_EVIDENCE_MODERATE_BONUS = 0.15
CONFIDENCE_EVIDENCE_STRONG_BONUS = 0.30   # replaces moderate bonus at strength 3
CONFIDENCE_RED_FLAG_PENALTY = 0.20        # per flag, subtracted
CONFIDENCE_MAX = 0.95
CONFIDENCE_FLOOR = 0.15

# Thresholds for label display
CONFIDENCE_HIGH_THRESHOLD = 0.80
CONFIDENCE_MED_THRESHOLD = 0.50

# ---------------------------------------------------------------------------
# Maturity Stage Map
# ---------------------------------------------------------------------------
STAGE_MAP = [
    (1, 1, "Nascent"),
    (2, 2, "Exploring"),
    (3, 3, "Established"),
    (4, 4, "Integrated"),
    (5, 5, "Optimized"),
]

STAGE_DESCRIPTIONS = {
    "Nascent":    "Foundational gap. No consistent evidence of structured practice or ownership.",
    "Exploring":  "Early-stage activity. Efforts are siloed or informal. Scale requires standardization.",
    "Established":"Standardized practice in place. Focus should shift to measurement and ROI tracking.",
    "Integrated": "Cross-functional alignment achieved. Optimize for governance and strategic leverage.",
    "Optimized":  "Leading practice. AI operates as a core strategic lever with automated governance.",
}

COMPOSITE_STAGE_BANDS = [
    (0.0, 2.19, "Nascent"),
    (2.2, 3.19, "Exploring"),
    (3.2, 4.19, "Established"),
    (4.2, 5.0,  "Optimized / Leading"),
]

# ---------------------------------------------------------------------------
# Category Risk Labels (used in blocker summaries)
# ---------------------------------------------------------------------------
CATEGORY_RISK = {
    "Leadership & Vision":    "Strategic Alignment",
    "Ways of Working":        "Operational Maturity",
    "Culture & Workforce":    "Change Management",
    "Governance Readiness":   "Compliance & Risk",
    "Technology Readiness":   "Technical Debt",
    "Data Readiness":         "Data Infrastructure",
}

# ---------------------------------------------------------------------------
# Quick Win Logic
# A category qualifies as a quick win if score >= this threshold
# AND evidence_strength >= this threshold.
# ---------------------------------------------------------------------------
QUICK_WIN_SCORE_MIN = 4
QUICK_WIN_EVIDENCE_MIN = 2

# A category is a top blocker if avg_score <= this threshold.
BLOCKER_SCORE_MAX = 2

# Human follow-up required if any question has confidence below this.
HUMAN_FOLLOWUP_CONFIDENCE_THRESHOLD = 0.45

# ---------------------------------------------------------------------------
# PII Redaction Patterns (regex strings)
# Applied before any LLM synthesis call.
# ---------------------------------------------------------------------------
PII_PATTERNS = [
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",   # email
    r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",                  # phone (US)
    r"\b\d{3}-\d{2}-\d{4}\b",                              # SSN
]

# ---------------------------------------------------------------------------
# Probe Templates (consultant follow-up questions)
# Keyed by what signal is MISSING.
# ---------------------------------------------------------------------------
PROBE_TEMPLATES = {
    "missing_owner": (
        "Who specifically owns this capability today — name, title, and reporting line? "
        "Without a named accountable executive, this rating cannot be validated."
    ),
    "missing_metric": (
        "What is the single north-star KPI used to measure progress here? "
        "If no KPI exists, what would a meaningful measurement look like in the next 90 days?"
    ),
    "missing_cadence": (
        "How frequently is performance in this area formally reviewed, and who chairs that review?"
    ),
    "missing_system": (
        "Which specific tool or system supports this process? "
        "Name the platform, version, and adoption rate across the team."
    ),
    "low_score_generic": (
        "What is the single most critical blocker preventing progress here, "
        "and which executive has the authority and budget to remove it?"
    ),
    "contradiction_detected": (
        "You rated this area {score}/5, but the evidence describes conflict, manual processes, "
        "or informal execution. Provide one concrete artifact — a policy document, a dashboard, "
        "or a named process owner — that substantiates the {score}/5 rating."
    ),
    "alignment_contradiction": (
        "The evidence describes active disagreement or organizational resistance in an area "
        "you rated {score}/5. What is the specific unresolved conflict, and who has the "
        "authority and mandate to resolve it within 30 days?"
    ),
    "buzzword_inflation": (
        "The response uses transformation-oriented language but lacks operational specifics. "
        "Can you describe the current-state process step by step, without AI or innovation framing?"
    ),
    "data_security_risk": (
        "The response describes active data security risks — employees entering confidential data "
        "into AI systems with no organizational visibility or audit trail. "
        "At {score}/5, your rating implies structured data governance. "
        "Who is accountable for AI data classification controls, and what is the current protocol "
        "when confidential data is exposed to an unsanctioned model?"
    ),
    "anti_ai_sentiment": (
        "The evidence indicates leadership resistance or active rejection of AI investment. "
        "This is the single highest-risk finding in this assessment. "
        "Who specifically holds this position, what is their stated rationale, "
        "and what would change their position?"
    ),
    "strategic_resistance": (
        "The response signals that investment, budget, or leadership support has been withheld "
        "or rejected. Before any maturity score is meaningful, this blocker must be named and "
        "assigned to a specific resolution owner. Who is accountable for resolving this?"
    ),
}

# ---------------------------------------------------------------------------
# McKinsey-voice narrative templates (used when LLM is unavailable)
# Variables: {category}, {score}, {stage}, {risk_label}, {signal_summary}
# ---------------------------------------------------------------------------
BLOCKER_NARRATIVE_TEMPLATE = (
    "{category} ({risk_label}) represents a structural execution risk. "
    "The current maturity score of {score}/5 ({stage}) indicates that without "
    "named ownership and a defined measurement cadence, AI scaling in this domain "
    "will stall at proof-of-concept. Prioritize a 30-day sprint to assign an "
    "accountable executive and establish a north-star KPI."
)

QUICK_WIN_NARRATIVE_TEMPLATE = (
    "{category} demonstrates the highest evidence density in this assessment "
    "({score}/5, {stage}). This represents a replication surface: the operating "
    "model here should be documented and socialized across other business units. "
    "Identify adoption barriers before scaling."
)

ASSESSMENT_QUALITY_NOTE_TEMPLATE = (
    "Confidence is highest where responses include named owners, specific KPIs, "
    "tool names, and review cadence. {low_confidence_count} of {total_questions} "
    "question(s) returned low-confidence scores — validated findings are flagged accordingly."
)

# ---------------------------------------------------------------------------
# Z-score thresholds for outlier detection
# ---------------------------------------------------------------------------
ZSCORE_OUTLIER_THRESHOLD = 1.5      # |z| >= 1.5 → outlier
ZSCORE_PESSIMIST_DIRECTION = -1     # negative z = more pessimistic than peers
ZSCORE_OPTIMIST_DIRECTION = 1       # positive z = more optimistic than peers

# Minimum sample size before computing peer statistics
MIN_BENCHMARK_SAMPLE = 5

# Perception gap: difference between role avg scores that triggers a "Blind Spot" flag
PERCEPTION_GAP_THRESHOLD = 1.5

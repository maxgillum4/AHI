"""
Replay Max/Cmax assessment through the updated engine with all bug fixes applied.
"""
import json
import urllib.request

payload = {
    "payload_version": "1.0",
    "respondent_name": "Max",
    "organization_name": "Cmax",
    "respondent_role": "Tech Lead",
    "selected_sections": ["leadership", "tech", "data", "hr"],
    "questions": [
        {"question_id": "L1",         "category": "Leadership & Vision",   "label": "Strategic AI Vision",              "prompt": "Our organization has a clear and compelling AI vision and roadmap in place.",       "score": 2,    "typed_response": None},
        {"question_id": "L2",         "category": "Leadership & Vision",   "label": "Corporate Strategy Alignment",     "prompt": "AI objectives are explicitly aligned with our primary corporate strategy.",          "score": 2,    "typed_response": None},
        {"question_id": "L3",         "category": "Leadership & Vision",   "label": "AI Enterprise Metrics",            "prompt": "How mature are the KPIs used to track AI investment value and business ROI?",       "score": 1,    "typed_response": None},
        {"question_id": "L_Risk",     "category": "Leadership & Vision",   "label": "AI Risk Appetite",                 "prompt": "What level of AI risk is leadership willing to accept for competitive gain?",       "score": 2,    "typed_response": None},
        {"question_id": "Q_Decision", "category": "Leadership & Vision",   "label": "AI Decision Ownership",            "prompt": "Who holds final accountability for AI investment and deployment decisions?",        "score": None, "typed_response": "do not invest in AI"},
        {"question_id": "W1",         "category": "Ways of Working",       "label": "Technology Designed for Business", "prompt": "Technology is designed with business outcomes and user experience in mind.",        "score": 4,    "typed_response": "Many disagreements in planning, deployment, and budget"},
        {"question_id": "W_Conflict", "category": "Ways of Working",       "label": "Conflict Resolution",              "prompt": "We have effective mechanisms for resolving cross-functional AI conflicts.",          "score": 2,    "typed_response": "Many disagreements in planning, deployment, and budget"},
        {"question_id": "W3",         "category": "Ways of Working",       "label": "Utilize AI-Driven Insights",       "prompt": "Teams regularly utilize AI-driven insights in day-to-day decisions.",               "score": 5,    "typed_response": "Many disagreements in planning, deployment, and budget"},
        {"question_id": "Q_Concerns", "category": "Culture & Workforce",   "label": "Employee Concerns",                "prompt": "What are the primary employee concerns about AI adoption?",                         "score": None, "typed_response": "Money and hiring new employees"},
        {"question_id": "G1",         "category": "Governance Readiness",  "label": "Solid Governance Structure",       "prompt": "We have a solid governance structure for AI initiatives.",                          "score": 3,    "typed_response": None},
        {"question_id": "G4",         "category": "Governance Readiness",  "label": "Effective Risk Mitigation",        "prompt": "We have effective risk mitigation strategies for AI deployment.",                   "score": 3,    "typed_response": None},
        {"question_id": "G_Shadow",   "category": "Governance Readiness",  "label": "Shadow AI Confidence",             "prompt": "We have visibility and control over unsanctioned AI tool usage.",                  "score": 2,    "typed_response": None},
        {"question_id": "T1",         "category": "Technology Readiness",  "label": "Modern Cloud Infrastructure",      "prompt": "We have modern, scalable cloud infrastructure ready for AI workloads.",             "score": 4,    "typed_response": None},
        {"question_id": "T2",         "category": "Technology Readiness",  "label": "Core Systems AI Ready",            "prompt": "Our core systems and APIs are structured and accessible for AI integration.",      "score": 3,    "typed_response": None},
        {"question_id": "T4",         "category": "Technology Readiness",  "label": "ML Ops Maturity",                  "prompt": "We have mature MLOps practices for model deployment and monitoring.",              "score": 4,    "typed_response": None},
        {"question_id": "T5",         "category": "Technology Readiness",  "label": "Security Architecture",            "prompt": "Our security architecture is designed to support safe AI deployment.",              "score": 5,    "typed_response": None},
        {"question_id": "D1",         "category": "Data Readiness",        "label": "Data structured & clean",          "prompt": "Our core data is well-structured, clean, and accessible for AI use cases.",        "score": 2,    "typed_response": None},
        {"question_id": "D2",         "category": "Data Readiness",        "label": "Data integrated for AI",           "prompt": "Cross-functional data is formatted and available for model training.",              "score": 3,    "typed_response": None},
        {"question_id": "D3",         "category": "Data Readiness",        "label": "Data Dictionary and Ownership",    "prompt": "We have clear data dictionaries and assigned domain ownership.",                   "score": 2,    "typed_response": None},
        {"question_id": "Q_Vision",   "category": "Data Readiness",        "label": "Future-State Vision",              "prompt": "What is the desired day-to-day impact of AI in two years?",                       "score": None, "typed_response": "Agents running day to day work with execs making decisions"},
    ],
    "justifications": [
        # Audio recorded but not yet transcribed (whisper not installed)
        {"category": "Leadership & Vision",  "tag_id": "L1",         "tag_label": "L1 - Strategic AI Vision",             "text": None, "has_audio": True},
        {"category": "Leadership & Vision",  "tag_id": "L2",         "tag_label": "L2 - Corporate Strategy Alignment",    "text": None, "has_audio": True},
        {"category": "Leadership & Vision",  "tag_id": "L3",         "tag_label": "L3 - AI Enterprise Metrics",           "text": None, "has_audio": True},
        {"category": "Leadership & Vision",  "tag_id": "L_Risk",     "tag_label": "L_Risk - AI Risk Appetite",            "text": None, "has_audio": True},
        {"category": "Leadership & Vision",  "tag_id": "Q_Decision", "tag_label": "Q_Decision - AI Decision Ownership",  "text": None, "has_audio": True},
        {"category": "Ways of Working",      "tag_id": "W1",         "tag_label": "W1 - Technology Designed for Business","text": None, "has_audio": True},
        {"category": "Ways of Working",      "tag_id": "W_Conflict", "tag_label": "W_Conflict - Conflict Resolution",     "text": None, "has_audio": True},
        {"category": "Ways of Working",      "tag_id": "W3",         "tag_label": "W3 - Utilize AI-Driven Insights",      "text": None, "has_audio": True},
        {"category": "Governance Readiness", "tag_id": "G1",         "tag_label": "G1 - Solid Governance Structure",      "text": None, "has_audio": True},
        {"category": "Governance Readiness", "tag_id": "G4",         "tag_label": "G4 - Effective Risk Mitigation",       "text": None, "has_audio": True},
        {"category": "Governance Readiness", "tag_id": "G_Shadow",   "tag_label": "G_Shadow - Shadow AI Confidence",      "text": None, "has_audio": True},
    ]
}

data = json.dumps(payload).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8001/api/analyze-assessment",
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as r:
    result = json.loads(r.read())

# Save full JSON
with open("max_cmax_reanalysis.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

# ── OVERALL ─────────────────────────────────────────────────────────────────
o = result["overall"]
print("=" * 70)
print("OVERALL")
print("=" * 70)
print(f"  Composite Score : {o['composite_score']}  |  Stage: {o['maturity_stage']}")
print(f"  Human Follow-Up : {o['needs_human_followup']}")
print(f"  Quality Note    : {o['assessment_quality_note']}")

# ── DIMENSIONS ──────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("DIMENSIONS")
print("=" * 70)
for d in result["dimensions"]:
    score_str = f"{d['avg_score']}" if d["avg_score"] is not None else "unscored"
    flag_note = f"  [{len(d['summary_flags'])} flag(s)]" if d["summary_flags"] else ""
    print(f"  {d['category']:<30} score={score_str:<5}  conf={d['confidence_label']}{flag_note}")
    for fl in d["summary_flags"]:
        print(f"    !! {fl}")

# ── FLAGS & PROBES ───────────────────────────────────────────────────────────
flagged = [q for q in result["per_question"] if q["red_flags"]]
print("\n" + "=" * 70)
print(f"FLAGS & PROBES  ({len(flagged)} flagged of {len(result['per_question'])} questions)")
print("=" * 70)
for q in flagged:
    print(f"\n  [{q['question_id']}] {q['label']}")
    print(f"  score={q['self_score']}  conf={q['confidence_label']}  evidence={q['evidence_strength_label']}")
    for f in q["red_flags"]:
        print(f"    FLAG  : {f}")
    for p in q["recommended_followups"]:
        print(f"    PROBE : {p}")

# ── BLOCKERS ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("TOP BLOCKERS")
print("=" * 70)
for b in result["top_blockers"]:
    print(f"  - {b}")

# ── NEXT BEST ACTIONS ────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("NEXT BEST ACTIONS")
print("=" * 70)
for i, a in enumerate(result["next_best_actions"], 1):
    print(f"  {i}. {a}")

# ── HYBRID ANALYST ───────────────────────────────────────────────────────────
h = result["hybrid_analyst"]
print("\n" + "=" * 70)
print("HYBRID ANALYST")
print("=" * 70)
print(f"  {h['benchmark_note']}")
print(f"  Z-score: {h['respondent_zscore']}  |  {h['zscore_interpretation']}")
for g in h["perception_gaps"]:
    print(f"  GAP    : {g}")
for of in h["outlier_flags"]:
    print(f"  OUTLIER: {of}")

print("\nFull JSON saved to: max_cmax_reanalysis.json")

"""
analyzer.py — AHI Diagnostic Reasoning Engine
The ReasoningModule. All qualitative analysis lives here.

Hybrid Math Rule: This file contains ZERO arithmetic on scores.
All score math (averages, composites) is done in routes.py or hybrid_analyst.py.
This file scores EVIDENCE, detects PATTERNS, and generates LANGUAGE.
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Tuple

from heuristics import (
    ALL_SIGNAL_KEYS,
    ANTI_AI_SIGNALS,
    ASSESSMENT_QUALITY_NOTE_TEMPLATE,
    BLOCKER_NARRATIVE_TEMPLATE,
    BLOCKER_SCORE_MAX,
    BUZZWORD_INFLATION_THRESHOLD,
    BUZZWORDS,
    CATEGORY_RISK,
    COMPOSITE_STAGE_BANDS,
    CONFIDENCE_AUDIO_BONUS,
    CONFIDENCE_BASE,
    CONFIDENCE_EVIDENCE_MODERATE_BONUS,
    CONFIDENCE_EVIDENCE_STRONG_BONUS,
    CONFIDENCE_FLOOR,
    CONFIDENCE_HIGH_THRESHOLD,
    CONFIDENCE_MAX,
    CONFIDENCE_MED_THRESHOLD,
    CONFIDENCE_RED_FLAG_PENALTY,
    CONTRADICTION_PATTERNS,
    CONTRADICTION_SCORE_THRESHOLD,
    EVIDENCE_MODERATE_SIGNAL_COUNT,
    EVIDENCE_STRONG_SIGNAL_COUNT,
    EVIDENCE_TEXT_MIN_WORDS,
    HUMAN_FOLLOWUP_CONFIDENCE_THRESHOLD,
    PII_PATTERNS,
    PROBE_TEMPLATES,
    QUICK_WIN_EVIDENCE_MIN,
    QUICK_WIN_NARRATIVE_TEMPLATE,
    QUICK_WIN_SCORE_MIN,
    SIGNALS,
    STAGE_MAP,
    STRATEGIC_RESISTANCE_SIGNALS,
)
from schema import (
    AnalysisResponse,
    AssessmentPayload,
    ConfidenceLabel,
    DimensionSummary,
    EvidenceStrengthLabel,
    FollowupQueueItem,
    OverallAssessment,
    PerQuestionResult,
    QuestionResponse,
    TaggedJustification,
)

# ---------------------------------------------------------------------------
# PII Redaction
# ---------------------------------------------------------------------------

def redact_pii(text: str) -> str:
    """Strip emails, phone numbers, SSNs from text before LLM processing."""
    for pattern in PII_PATTERNS:
        text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)
    return text


# ---------------------------------------------------------------------------
# Text Utilities
# ---------------------------------------------------------------------------

def _word_count(text: Optional[str]) -> int:
    if not text:
        return 0
    return len(text.split())


def _text_lower(text: Optional[str]) -> str:
    return (text or "").lower()


def _excerpt(text: Optional[str], max_chars: int = 250) -> Optional[str]:
    if not text:
        return None
    return text[:max_chars] + ("..." if len(text) > max_chars else "")


# ---------------------------------------------------------------------------
# Signal Extraction
# ---------------------------------------------------------------------------

def extract_signals(combined_text: str) -> Dict[str, bool]:
    """
    Return a dict of {signal_category: True/False} indicating which
    maturity signal types are present in the text.
    """
    lower = combined_text.lower()
    return {
        key: any(kw in lower for kw in SIGNALS[key])
        for key in ALL_SIGNAL_KEYS
    }


def count_distinct_signal_categories(signals: Dict[str, bool]) -> int:
    return sum(1 for v in signals.values() if v)


# ---------------------------------------------------------------------------
# Evidence Strength Scoring  (0–3)
# ---------------------------------------------------------------------------

def score_evidence_strength(
    justification_texts: List[str],
    typed_response: Optional[str],
    has_audio: bool,
) -> int:
    """
    Score the quality of evidence provided for a single question.

    0 = No evidence (no text, no audio)
    1 = Weak  (text exists but too short or no concrete signals)
    2 = Moderate (1–2 signal categories present)
    3 = Strong  (3+ signal categories OR audio + strong text)

    Never touches the Likert score — this is purely about justification quality.
    """
    all_text = " ".join(filter(None, justification_texts + [typed_response]))

    if not all_text.strip() and not has_audio:
        return 0

    if _word_count(all_text) < EVIDENCE_TEXT_MIN_WORDS and not has_audio:
        return 1

    signals = extract_signals(all_text)
    distinct = count_distinct_signal_categories(signals)

    if distinct >= EVIDENCE_STRONG_SIGNAL_COUNT:
        return 3
    if distinct >= EVIDENCE_MODERATE_SIGNAL_COUNT:
        return 2
    if has_audio or _word_count(all_text) >= EVIDENCE_TEXT_MIN_WORDS:
        return 1

    return 0


def evidence_strength_label(strength: int) -> EvidenceStrengthLabel:
    mapping = {
        0: EvidenceStrengthLabel.NONE,
        1: EvidenceStrengthLabel.WEAK,
        2: EvidenceStrengthLabel.MODERATE,
        3: EvidenceStrengthLabel.STRONG,
    }
    return mapping.get(strength, EvidenceStrengthLabel.WEAK)


# ---------------------------------------------------------------------------
# Red Flag Detection
# ---------------------------------------------------------------------------

def detect_red_flags(
    combined_text: str,
    score: Optional[int],
) -> List[str]:
    """
    Detect qualitative warning signals.

    Returns a list of short flag strings. Each flag represents a distinct
    risk category (contradiction, buzzword inflation, vagueness,
    anti-AI sentiment, strategic resistance).
    """
    flags: List[str] = []
    lower = combined_text.lower()

    # 0. Anti-AI sentiment — critical, fires regardless of score
    if any(kw in lower for kw in ANTI_AI_SIGNALS):
        flags.append(
            "CRITICAL: Anti-AI Sentiment Detected — leadership resistance or "
            "active rejection of AI investment stated in response"
        )

    # 0b. Strategic resistance (budget/investment rejection) — fires regardless of score
    if any(kw in lower for kw in STRATEGIC_RESISTANCE_SIGNALS):
        # Don't double-flag if anti-AI already caught it
        if not any("Anti-AI" in f for f in flags):
            flags.append(
                "Strategic Resistance: response indicates withheld investment, "
                "budget rejection, or cancelled initiative"
            )

    # 1. Contradiction: high score + contradictory language
    if score is not None and score >= CONTRADICTION_SCORE_THRESHOLD:
        for pattern_key, keywords in CONTRADICTION_PATTERNS.items():
            if any(kw in lower for kw in keywords):
                flag_label = {
                    "manual_process": (
                        f"Score-Evidence Contradiction: manual/informal process "
                        f"cited at score {score}/5"
                    ),
                    "no_ownership": (
                        f"Score-Evidence Contradiction: unclear ownership "
                        f"cited at score {score}/5"
                    ),
                    "alignment_failure": (
                        f"Score-Evidence Contradiction: organizational conflict or "
                        f"disagreement cited at score {score}/5"
                    ),
                    "data_security_risk": (
                        f"Score-Evidence Contradiction: active data security risk cited at "
                        f"score {score}/5 — confidential data may be entering uncontrolled AI systems"
                    ),
                }.get(pattern_key, f"Contradiction detected at score {score}/5")
                flags.append(flag_label)
                break  # one contradiction flag per response is enough

    # 2. Buzzword inflation: AI jargon without concrete support
    buzzword_hits = [bw for bw in BUZZWORDS if bw in lower]
    if len(buzzword_hits) >= BUZZWORD_INFLATION_THRESHOLD:
        signals = extract_signals(combined_text)
        if count_distinct_signal_categories(signals) < EVIDENCE_MODERATE_SIGNAL_COUNT:
            flags.append(
                "Buzzword Inflation: transformation language without operational evidence"
            )

    # 3. Vagueness: text exists but no signal at all and score >= 4
    if score is not None and score >= 4 and combined_text.strip():
        signals = extract_signals(combined_text)
        if count_distinct_signal_categories(signals) == 0 and _word_count(combined_text) >= EVIDENCE_TEXT_MIN_WORDS:
            flags.append("Vague Evidence: response lacks owner, KPI, system, or cadence")

    return flags


# ---------------------------------------------------------------------------
# Confidence Computation
# ---------------------------------------------------------------------------

def compute_confidence(
    score: Optional[int],
    evidence_strength: int,
    has_audio: bool,
    red_flags: List[str],
) -> float:
    """
    Confidence = f(evidence quality, audio presence, flag penalties).
    Never a function of the Likert score itself.
    """
    conf = CONFIDENCE_BASE

    if evidence_strength == 3:
        conf += CONFIDENCE_EVIDENCE_STRONG_BONUS
    elif evidence_strength == 2:
        conf += CONFIDENCE_EVIDENCE_MODERATE_BONUS

    if has_audio:
        conf += CONFIDENCE_AUDIO_BONUS

    conf -= len(red_flags) * CONFIDENCE_RED_FLAG_PENALTY

    return round(max(CONFIDENCE_FLOOR, min(CONFIDENCE_MAX, conf)), 2)


def confidence_label(confidence: float) -> ConfidenceLabel:
    if confidence >= CONFIDENCE_HIGH_THRESHOLD:
        return ConfidenceLabel.HIGH
    if confidence >= CONFIDENCE_MED_THRESHOLD:
        return ConfidenceLabel.MED
    return ConfidenceLabel.LOW


# ---------------------------------------------------------------------------
# Stage Inference
# ---------------------------------------------------------------------------

def infer_stage(score: Optional[int]) -> str:
    if score is None:
        return "Not Scored"
    for lo, hi, name in STAGE_MAP:
        if lo <= score <= hi:
            return name
    return "Unknown"


def composite_stage(composite: float) -> str:
    for lo, hi, name in COMPOSITE_STAGE_BANDS:
        if lo <= composite <= hi:
            return name
    return "Unknown"


# ---------------------------------------------------------------------------
# Consultant Probe Generation
# ---------------------------------------------------------------------------

def generate_consultant_probes(
    question_id: str,
    label: str,
    score: Optional[int],
    category: str,
    signals: Dict[str, bool],
    red_flags: List[str],
    evidence_strength: int,
) -> List[str]:
    """
    Generate McKinsey-style follow-up questions based on what's MISSING.
    Maximum 3 probes per question to avoid report bloat.
    """
    probes: List[str] = []

    # Prioritize missing signals for low/medium evidence
    if evidence_strength <= 2:
        if not signals.get("ownership"):
            probes.append(PROBE_TEMPLATES["missing_owner"])
        if not signals.get("metrics"):
            probes.append(PROBE_TEMPLATES["missing_metric"])
        if not signals.get("cadence") and len(probes) < 2:
            probes.append(PROBE_TEMPLATES["missing_cadence"])
        if not signals.get("systems") and len(probes) < 2:
            probes.append(PROBE_TEMPLATES["missing_system"])

    # Anti-AI / strategic resistance — highest priority probe
    if any("Anti-AI" in f for f in red_flags):
        probes = [PROBE_TEMPLATES["anti_ai_sentiment"]] + probes[:1]
    elif any("Strategic Resistance" in f for f in red_flags):
        probes = [PROBE_TEMPLATES["strategic_resistance"]] + probes[:1]

    # Data security contradiction probe
    elif any("data security risk" in f.lower() for f in red_flags):
        probes = [
            PROBE_TEMPLATES["data_security_risk"].format(score=score or "N/A")
        ] + probes[:1]

    # Alignment contradiction probe
    elif any("alignment_failure" in f or "disagreement" in f.lower() or "conflict" in f.lower() for f in red_flags):
        probes = [
            PROBE_TEMPLATES["alignment_contradiction"].format(score=score or "N/A")
        ] + probes[:1]

    # Standard contradiction probe
    elif any("Score-Evidence Contradiction" in f for f in red_flags):
        probes = [
            PROBE_TEMPLATES["contradiction_detected"].format(score=score or "N/A")
        ] + probes[:1]

    # Buzzword probe
    if any("Buzzword" in f for f in red_flags) and len(probes) < 3:
        probes.append(PROBE_TEMPLATES["buzzword_inflation"])

    # Fallback for low-score with no other probes
    if score is not None and score <= 2 and not probes:
        probes.append(PROBE_TEMPLATES["low_score_generic"])

    return probes[:3]


# ---------------------------------------------------------------------------
# Per-Question Analysis (the core loop)
# ---------------------------------------------------------------------------

def analyze_question(
    question: QuestionResponse,
    justifications: List[TaggedJustification],
) -> PerQuestionResult:
    """
    Analyze a single question response against its tagged justifications.
    Returns a fully populated PerQuestionResult.
    """
    # Collect all text relevant to this question
    relevant_justifications = [
        j for j in justifications
        if j.tag_id == question.question_id or j.category == question.category
    ]
    justification_texts = [j.text for j in relevant_justifications if j.text]
    has_audio = any(j.has_audio for j in relevant_justifications)

    combined_text = " ".join(filter(None, justification_texts + [question.typed_response]))

    # Signal extraction
    signals = extract_signals(combined_text)

    # Core scoring
    ev_strength = score_evidence_strength(
        justification_texts, question.typed_response, has_audio
    )
    red_flags = detect_red_flags(combined_text, question.score)
    conf = compute_confidence(question.score, ev_strength, has_audio, red_flags)
    conf_label = confidence_label(conf)
    ev_label = evidence_strength_label(ev_strength)
    stage = infer_stage(question.score)

    # Probe generation
    probes = generate_consultant_probes(
        question.question_id,
        question.label,
        question.score,
        question.category,
        signals,
        red_flags,
        ev_strength,
    )

    # Text excerpt (PII-safe, for report display)
    excerpt_raw = " | ".join(filter(None, justification_texts + [question.typed_response]))
    excerpt = _excerpt(redact_pii(excerpt_raw)) if excerpt_raw else None

    return PerQuestionResult(
        question_id=question.question_id,
        category=question.category,
        label=question.label,
        self_score=question.score,
        inferred_stage=stage,
        confidence=conf,
        confidence_label=conf_label,
        evidence_strength=ev_strength,
        evidence_strength_label=ev_label,
        has_supporting_audio=has_audio,
        mentions_metric=signals.get("metrics", False),
        mentions_owner=signals.get("ownership", False),
        mentions_cadence=signals.get("cadence", False),
        mentions_system=signals.get("systems", False),
        red_flags=red_flags,
        recommended_followups=probes,
        supporting_text_excerpt=excerpt,
    )


# ---------------------------------------------------------------------------
# Dimension Roll-up
# ---------------------------------------------------------------------------

def build_dimension_summaries(
    per_question: List[PerQuestionResult],
    scored_questions: List[QuestionResponse],
) -> List[DimensionSummary]:
    """
    Group per-question results by category and compute dimension-level summaries.
    Score averaging is done here with Python sum/len — not Pandas
    (Pandas is reserved for cross-respondent benchmarking in hybrid_analyst.py).
    """
    from collections import defaultdict

    cat_scores: Dict[str, List[float]] = defaultdict(list)
    cat_confs:  Dict[str, List[float]] = defaultdict(list)
    cat_flags:  Dict[str, List[str]]   = defaultdict(list)
    cat_counts: Dict[str, int]         = defaultdict(int)

    for q in per_question:
        cat_confs[q.category].append(q.confidence)
        cat_counts[q.category] += 1
        for flag in q.red_flags:
            if flag not in cat_flags[q.category]:
                cat_flags[q.category].append(flag)

    for q in scored_questions:
        if q.score is not None:
            cat_scores[q.category].append(float(q.score))

    all_cats = sorted(set(cat_confs.keys()))
    summaries: List[DimensionSummary] = []

    for cat in all_cats:
        scores = cat_scores.get(cat, [])
        confs  = cat_confs.get(cat, [])

        avg_score = round(sum(scores) / len(scores), 2) if scores else None
        avg_conf  = round(sum(confs)  / len(confs),  2) if confs  else 0.5

        # Category-level flags
        flags: List[str] = list(cat_flags.get(cat, []))
        if avg_score is not None and avg_score <= BLOCKER_SCORE_MAX:
            risk = CATEGORY_RISK.get(cat, cat)
            flags.insert(0, f"Likely near-term blocker for enterprise AI scaling ({risk})")

        summaries.append(DimensionSummary(
            category=cat,
            avg_score=avg_score,
            avg_confidence=avg_conf,
            confidence_label=confidence_label(avg_conf),
            summary_flags=flags,
            question_count=cat_counts.get(cat, 0),
        ))

    return summaries


# ---------------------------------------------------------------------------
# Blocker & Quick Win Identification
# ---------------------------------------------------------------------------

def identify_blockers_and_wins(
    per_question: List[PerQuestionResult],
    dimensions: List[DimensionSummary],
) -> Tuple[List[str], List[str]]:
    """Return (top_blockers, quick_wins) as human-readable strings."""
    blockers: List[str] = []
    quick_wins: List[str] = []

    for dim in dimensions:
        if dim.avg_score is None:
            continue
        risk = CATEGORY_RISK.get(dim.category, dim.category)

        if dim.avg_score <= BLOCKER_SCORE_MAX:
            blockers.append(
                BLOCKER_NARRATIVE_TEMPLATE.format(
                    category=dim.category,
                    risk_label=risk,
                    score=dim.avg_score,
                    stage=composite_stage(dim.avg_score),
                    signal_summary="",
                )
            )

        if (
            dim.avg_score >= QUICK_WIN_SCORE_MIN
            and dim.avg_confidence >= CONFIDENCE_MED_THRESHOLD
        ):
            # Check evidence strength from per-question data for this category
            cat_qs = [q for q in per_question if q.category == dim.category]
            avg_ev = (
                sum(q.evidence_strength for q in cat_qs) / len(cat_qs)
                if cat_qs else 0
            )
            if avg_ev >= QUICK_WIN_EVIDENCE_MIN:
                quick_wins.append(
                    QUICK_WIN_NARRATIVE_TEMPLATE.format(
                        category=dim.category,
                        score=dim.avg_score,
                        stage=composite_stage(dim.avg_score),
                    )
                )

    return blockers, quick_wins


# ---------------------------------------------------------------------------
# Next Best Actions
# ---------------------------------------------------------------------------

def generate_next_best_actions(
    per_question: List[PerQuestionResult],
    dimensions: List[DimensionSummary],
    needs_human_followup: bool,
) -> List[str]:
    """
    Generate a prioritized action list based on analysis results.
    Ordered: (1) fix the worst blockers, (2) validate shaky high scores,
    (3) capitalize on quick wins.
    """
    actions: List[str] = []

    # 1. Low-confidence high-score items — need validation artifacts
    shaky_highs = [
        q for q in per_question
        if q.self_score is not None
        and q.self_score >= 4
        and q.confidence < CONFIDENCE_MED_THRESHOLD
    ]
    if shaky_highs:
        ids = ", ".join(q.question_id for q in shaky_highs[:3])
        actions.append(
            f"Validate {len(shaky_highs)} high-score area(s) with low confidence ({ids}): "
            "request one concrete artifact per question — a policy document, a dashboard screenshot, "
            "or a named system — within the next 10 business days."
        )

    # 2. Questions missing ownership
    no_owner = [q for q in per_question if not q.mentions_owner and q.self_score is not None]
    if no_owner:
        cats = sorted(set(q.category for q in no_owner))
        actions.append(
            f"Assign named executive owners across {len(cats)} category(ies) "
            f"({', '.join(cats[:3])}). "
            "No area without a named owner and a defined 90-day KPI should be rated above 3/5."
        )

    # 3. Dimensions with measurement gaps
    no_metric = [q for q in per_question if not q.mentions_metric and q.self_score is not None]
    if no_metric:
        actions.append(
            "Define a single north-star KPI for each unmeasured dimension. "
            f"{len(no_metric)} question response(s) contain no measurable outcome. "
            "Without measurement, maturity claims are unverifiable."
        )

    # 4. Contradictions — high priority
    contradictions = [q for q in per_question if any("Contradiction" in f for f in q.red_flags)]
    if contradictions:
        ids = ", ".join(q.question_id for q in contradictions[:3])
        actions.append(
            f"Resolve score-evidence contradictions in {ids}. "
            "A score of 4–5 cannot coexist with manually executed or informal processes. "
            "Either upgrade the process or revise the self-assessment downward."
        )

    # 5. Human follow-up flag
    if needs_human_followup:
        actions.append(
            "Schedule a 60-minute structured interview with the respondent. "
            "Multiple low-confidence findings require live validation before this assessment "
            "can be used to inform investment or strategic planning decisions."
        )

    # Cap to 5 most critical actions
    return actions[:5]


# ---------------------------------------------------------------------------
# LLM Synthesis Hook
# (Optional — used when ANTHROPIC_API_KEY is set in environment)
# Falls back to template-based synthesis transparently.
# ---------------------------------------------------------------------------

def _try_llm_synthesis(prompt: str) -> Optional[str]:
    """
    Attempt a Claude API call for narrative synthesis.
    Returns None on any failure so callers fall through to templates.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=(
                "You are a Senior Partner at McKinsey & Company with 20 years of experience "
                "leading AI transformation engagements for Fortune 500 companies. "
                "Your communication style is clinical, direct, and focused on business impact. "
                "You never use AI hype language. You speak in terms of risk, ROI, ownership, "
                "and operational specificity. Every sentence must advance a strategic argument. "
                "No bullet points — write in concise paragraphs. Maximum 3 sentences per response."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Follow-up Queue Builder
# ---------------------------------------------------------------------------

def build_followup_queue(per_question: List[PerQuestionResult]) -> List[FollowupQueueItem]:
    """
    Build a prioritized follow-up interview queue from per-question results.
    Only includes questions that need human follow-up (Low confidence or red flags).
    Sorted: critical → high → medium.
    """
    _priority_order = {"critical": 0, "high": 1, "medium": 2}
    queue: List[FollowupQueueItem] = []

    for q in per_question:
        needs_followup = (
            q.confidence_label == ConfidenceLabel.LOW
            or bool(q.red_flags)
        )
        if not needs_followup or not q.recommended_followups:
            continue

        priority = (
            "critical" if any("CRITICAL" in f for f in q.red_flags) else
            "high"     if any("Contradiction" in f for f in q.red_flags) else
            "medium"
        )

        queue.append(FollowupQueueItem(
            question_id             = q.question_id,
            category                = q.category,
            label                   = q.label,
            priority                = priority,
            reason                  = q.red_flags or [],
            probe                   = q.recommended_followups[0],
            prior_score             = q.self_score,
            confidence              = q.confidence,
            supporting_text_excerpt = q.supporting_text_excerpt,
        ))

    return sorted(queue, key=lambda x: _priority_order.get(x.priority, 3))


# ---------------------------------------------------------------------------
# Top-Level Assessment Orchestrator
# ---------------------------------------------------------------------------

def analyze_assessment(payload: AssessmentPayload) -> AnalysisResponse:
    """
    Orchestrate the full analysis pipeline for one assessment submission.

    Pipeline:
      1. Per-question evidence analysis
      2. Dimension roll-up
      3. Composite scoring (Python math — single respondent, not cross-respondent)
      4. Blocker / quick win identification
      5. Next best actions
      6. Overall assessment assembly
    """
    # Step 1: Analyze each question
    per_question: List[PerQuestionResult] = [
        analyze_question(q, payload.justifications)
        for q in payload.questions
    ]

    # Step 2: Dimension summaries
    scored_qs = [q for q in payload.questions if q.score is not None]
    dimensions = build_dimension_summaries(per_question, scored_qs)

    # Step 3: Composite score (single-respondent average — no Pandas needed here)
    all_scores = [q.score for q in scored_qs]
    composite  = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0
    mat_stage  = composite_stage(composite)

    # Step 3b: Build follow-up queue (before blockers so it can inform next actions)
    followup_queue = build_followup_queue(per_question)

    # Step 4: Blockers and wins
    blockers, quick_wins = identify_blockers_and_wins(per_question, dimensions)

    # Step 5: Next actions
    low_conf_count = sum(
        1 for q in per_question
        if q.confidence < HUMAN_FOLLOWUP_CONFIDENCE_THRESHOLD
    )
    # Any critical flag (Anti-AI, Strategic Resistance) forces human followup
    critical_flags = sum(
        1 for q in per_question
        if any("CRITICAL" in f or "Strategic Resistance" in f for f in q.red_flags)
    )
    needs_followup = low_conf_count > 0 or critical_flags > 0

    next_actions = generate_next_best_actions(per_question, dimensions, needs_followup)

    # Step 6: Quality note
    quality_note = ASSESSMENT_QUALITY_NOTE_TEMPLATE.format(
        low_confidence_count=low_conf_count,
        total_questions=len(per_question),
    )

    # Optional: LLM synthesis override for quality note
    if low_conf_count > 0:
        llm_note = _try_llm_synthesis(
            f"In 2 sentences, explain why {low_conf_count} of {len(per_question)} questions "
            f"returned low-confidence scores in an AI maturity assessment. Emphasize the "
            f"importance of named owners, specific KPIs, and operational evidence."
        )
        if llm_note:
            quality_note = llm_note

    return AnalysisResponse(
        respondent_name=payload.respondent_name,
        organization_name=payload.organization_name,
        overall=OverallAssessment(
            composite_score=composite,
            maturity_stage=mat_stage,
            needs_human_followup=needs_followup,
            assessment_quality_note=quality_note,
        ),
        dimensions=dimensions,
        per_question=per_question,
        top_blockers=blockers,
        quick_wins=quick_wins,
        next_best_actions=next_actions,
        followup_queue=followup_queue,
        hybrid_analyst=None,  # Populated by hybrid_analyst.py after this call
    )

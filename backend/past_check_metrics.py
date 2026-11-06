"""Statistical evaluation and metrics calculation for Past Check A/B experiment.

Implements:
- Wilson score 95% confidence intervals (formula: Wilson 1927)
- Second-question rate by arm (control vs treatment) with n and Wilson CI
- Difference between arms
- Real vs Decoy Yes-rate comparison
- Small sample warning (< 30)
- Formats every rate with explicit interval and sample size (never a bare percentage)
"""

import math
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from backend.models import Event, Experiment, PastCheckItem, PastCheckSet, Question, User


def wilson_score_interval(
    successes: int,
    total: int,
    confidence: float = 0.95,
) -> Tuple[float, float, float]:
    """
    Calculate Wilson score confidence interval for a binomial proportion.
    Returns: (point_estimate, lower_bound, upper_bound) in range [0.0, 1.0].
    """
    if total <= 0:
        return 0.0, 0.0, 0.0

    p_hat = successes / total
    z = 1.959963984540054  # 95% two-sided normal quantile

    z2 = z * z
    denom = 1.0 + (z2 / total)
    center = (p_hat + (z2 / (2.0 * total))) / denom
    spread = (z * math.sqrt((p_hat * (1.0 - p_hat) / total) + (z2 / (4.0 * total * total)))) / denom

    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)

    return round(p_hat, 4), round(lower, 4), round(upper, 4)


def format_rate_with_ci(successes: int, total: int) -> str:
    """Format rate as: 'XX.X% [95% CI: YY.Y% – ZZ.Z%, n=N]'."""
    p_hat, low, high = wilson_score_interval(successes, total)
    p_pct = round(p_hat * 100.0, 1)
    low_pct = round(low * 100.0, 1)
    high_pct = round(high * 100.0, 1)
    return f"{p_pct}% [95% CI: {low_pct}% – {high_pct}%, n={total}]"


def compute_past_check_experiment_metrics(db: Session) -> Dict[str, Any]:
    """
    Compute comprehensive A/B experiment metrics with Wilson confidence intervals.
    """
    # 1. Map users to experiment arms
    experiments = db.query(Experiment).all()
    user_arms = {exp.user_id: exp.arm for exp in experiments}

    # Count questions asked per user
    user_q_counts = {}
    for q in db.query(Question).all():
        user_q_counts[q.user_id] = user_q_counts.get(q.user_id, 0) + 1

    ctrl_users = [uid for uid, arm in user_arms.items() if arm == "control"]
    treat_users = [uid for uid, arm in user_arms.items() if arm == "treatment"]

    # Free question users who asked at least 1 question
    ctrl_asked_1 = [uid for uid in ctrl_users if user_q_counts.get(uid, 0) >= 1]
    ctrl_asked_2 = [uid for uid in ctrl_asked_1 if user_q_counts.get(uid, 0) >= 2]

    treat_asked_1 = [uid for uid in treat_users if user_q_counts.get(uid, 0) >= 1]
    treat_asked_2 = [uid for uid in treat_asked_1 if user_q_counts.get(uid, 0) >= 2]

    # Rates & Wilson intervals
    n_ctrl = len(ctrl_asked_1)
    x_ctrl = len(ctrl_asked_2)
    p_ctrl, low_ctrl, high_ctrl = wilson_score_interval(x_ctrl, n_ctrl)

    n_treat = len(treat_asked_1)
    x_treat = len(treat_asked_2)
    p_treat, low_treat, high_treat = wilson_score_interval(x_treat, n_treat)

    # Difference between arms
    delta = round(p_treat - p_ctrl, 4)
    delta_pct = round(delta * 100.0, 1)

    # 2. Real vs Decoy statement Yes-rates
    all_items = db.query(PastCheckItem).filter(PastCheckItem.answer.isnot(None)).all()
    real_items = [it for it in all_items if not it.is_decoy]
    decoy_items = [it for it in all_items if it.is_decoy]

    real_yes = sum(1 for it in real_items if it.answer == "yes")
    decoy_yes = sum(1 for it in decoy_items if it.answer == "yes")

    p_real, low_real, high_real = wilson_score_interval(real_yes, len(real_items))
    p_decoy, low_decoy, high_decoy = wilson_score_interval(decoy_yes, len(decoy_items))

    # 3. Past Check Completion Rate
    all_sets = db.query(PastCheckSet).filter(PastCheckSet.is_skipped == False).all()
    completed_sets = [
        s for s in all_sets
        if len(s.items) > 0 and all(it.answer is not None for it in s.items)
    ]
    p_comp, low_comp, high_comp = wilson_score_interval(len(completed_sets), len(all_sets))

    return {
        "control_arm": {
            "sample_size": n_ctrl,
            "converted_count": x_ctrl,
            "rate": p_ctrl,
            "ci_lower": low_ctrl,
            "ci_upper": high_ctrl,
            "formatted": format_rate_with_ci(x_ctrl, n_ctrl),
            "is_small_sample": n_ctrl < 30,
        },
        "treatment_arm": {
            "sample_size": n_treat,
            "converted_count": x_treat,
            "rate": p_treat,
            "ci_lower": low_treat,
            "ci_upper": high_treat,
            "formatted": format_rate_with_ci(x_treat, n_treat),
            "is_small_sample": n_treat < 30,
        },
        "delta": {
            "difference": delta,
            "difference_pct": delta_pct,
            "formatted": f"{'+' if delta_pct > 0 else ''}{delta_pct}%",
        },
        "decoy_analysis": {
            "real_statements": {
                "total_answered": len(real_items),
                "yes_count": real_yes,
                "yes_rate": p_real,
                "formatted": format_rate_with_ci(real_yes, len(real_items)),
                "is_small_sample": len(real_items) < 30,
            },
            "decoy_statements": {
                "total_answered": len(decoy_items),
                "yes_count": decoy_yes,
                "yes_rate": p_decoy,
                "formatted": format_rate_with_ci(decoy_yes, len(decoy_items)),
                "is_small_sample": len(decoy_items) < 30,
            },
            "discrimination_delta_pct": round((p_real - p_decoy) * 100.0, 1),
        },
        "completion": {
            "sets_started": len(all_sets),
            "sets_completed": len(completed_sets),
            "completion_rate": p_comp,
            "formatted": format_rate_with_ci(len(completed_sets), len(all_sets)),
            "is_small_sample": len(all_sets) < 30,
        },
    }

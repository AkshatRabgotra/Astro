"""Evaluation test subset executed during CI runs."""

from evals.runner import run_evaluation_harness


def test_eval_harness_pass_rate():
    """Verify that the 30-question evaluation dataset passes grounding checks."""
    summary = run_evaluation_harness(use_live_llm=False)
    assert summary["total_questions"] == 30
    assert summary["grounding_pass_rate_pct"] >= 95.0
    assert summary["average_overall_score"] >= 4.5

    # Check categories
    cats = summary["categories"]
    assert "career" in cats
    assert "relationships" in cats
    assert "timing" in cats
    assert "edge_cases" in cats

    assert cats["career"]["pass_rate_pct"] == 100.0
    assert cats["relationships"]["pass_rate_pct"] == 100.0
    assert cats["timing"]["pass_rate_pct"] == 100.0
    assert cats["edge_cases"]["pass_rate_pct"] == 100.0

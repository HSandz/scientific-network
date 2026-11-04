"""Two-sided Wilson interval for independently reviewed correct/total counts."""

from math import sqrt
from statistics import NormalDist


def precision_interval(correct: int, total: int, confidence: float = 0.95) -> dict:
    if total <= 0 or not 0 <= correct <= total:
        raise ValueError("require total > 0 and 0 <= correct <= total")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be strictly between 0 and 1")
    p = correct / total
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return {
        "correct": correct, "total": total, "precision": p,
        "confidence": confidence, "wilson_lower": max(0.0, center - radius),
        "wilson_upper": min(1.0, center + radius),
    }

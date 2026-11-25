"""Trend metrics (specification 5.4): per-subject yearly counts and shares, CAGR, OLS slope, year-over-year change, class; group interest.

Classes and thresholds come from ``configs/analysis-final-exam-v1.yaml`` (trends). The classes are descriptive, not confirmatory: no multiple-testing correction.
"""

from __future__ import annotations

from collections import defaultdict

from scipy import stats

from .fx_data import YEARS, Inputs

CAVEATS = [
    "Only two venues (AAAI and IJCAI) are covered, so a trend is a trend in these proceedings, not in the field.",
    "Venue size changes from 2,240 papers in 2021 to 4,042 in 2025; shares correct for it, raw counts do not.",
    "Topic labels come from an embedding classifier with known limits; the topic evaluation is human_review_pending / AI-assessed.",
    "Method, task and dataset labels exist for only part of the papers (about 40%, 28% and 12%); a share is a share of all papers, so low coverage lowers every share.",
    "All enrichment quality figures (entity, relation and linking precision) are AI-assessed, not human annotation; Wilson intervals cover sampling error only.",
]


def year_totals(inputs: Inputs) -> dict[int, int]:
    t = {y: 0 for y in YEARS}
    for y in inputs.paper_year.values():
        if y in t:
            t[y] += 1
    return t


def ols(shares: list[float]) -> tuple[float, float | None]:
    r = stats.linregress(list(YEARS), shares)
    return float(r.slope), (None if r.pvalue != r.pvalue else float(r.pvalue))


def cagr(first: float, last: float, periods: int) -> float | None:
    return None if first <= 0 or last < 0 else (last / first) ** (1 / periods) - 1


def classify(counts: dict[int, int], totals: dict[int, int], cfg: dict) -> dict:
    """Class and the numbers behind it for one count series (invented series in the tests)."""
    t = cfg["trends"]
    cl = t["classes"]
    total = sum(counts.values())
    shares = [counts[y] / totals[y] for y in YEARS]
    base_years, recent_years = t["base_window"], t["recent_window"]
    base_n, recent_n = sum(counts[y] for y in base_years), sum(counts[y] for y in recent_years)
    base_share = base_n / sum(totals[y] for y in base_years)
    recent_share = recent_n / sum(totals[y] for y in recent_years)
    slope, p = ols(shares)
    ratio = None if base_share == 0 else recent_share / base_share
    alpha = t["slope_alpha"]
    significant = p is not None and p <= alpha
    if total < t["minimum_total_papers"]:
        label = "insufficient_data"
    elif base_n <= 2 and recent_n >= 8:
        label = "emerging"
    elif slope > 0 and significant and ratio is not None and ratio >= 1.5 and base_n >= 3:
        label = "rising"
    elif slope < 0 and significant and ratio is not None and ratio <= 2 / 3 and base_n >= 10:
        label = "declining"
    else:
        label = "stable"
    return {"class": label, "total_papers": total, "base_window_papers": base_n, "recent_window_papers": recent_n, "base_share": base_share, "recent_share": recent_share,
            "recent_over_base_share": ratio, "slope_of_share": slope, "slope_p_value": p, "cagr_of_share_2021_2025": cagr(shares[0], shares[-1], len(YEARS) - 1),
            "yoy_change_of_share": {str(YEARS[i]): (None if shares[i - 1] == 0 else shares[i] / shares[i - 1] - 1) for i in range(1, len(YEARS))},
            "papers_by_year": {str(y): counts[y] for y in YEARS}, "share_by_year": {str(y): s for y, s in zip(YEARS, shares)}}


def subject_trends(inputs: Inputs, kind: str, cfg: dict) -> list[dict]:
    totals = year_totals(inputs)
    rows = []
    for subject, papers in inputs.subject_papers[kind].items():
        counts = {y: 0 for y in YEARS}
        for p in papers:
            y = inputs.paper_year.get(p)
            if y in counts:
                counts[y] += 1
        node = inputs.nodes[subject]
        rows.append({"kind": kind, "id": subject, "name": node["name"], **classify(counts, totals, cfg)})
    return sorted(rows, key=lambda r: (-r["total_papers"], r["id"]))


def group_interest(inputs: Inputs, kind: str, groups: dict[str, set[str]], cfg: dict) -> list[dict]:
    """For each (group, subject): share of the group's papers in the subject, revealed comparative advantage, first active year and growth of that share.

    RCA = (group papers in subject / group papers) / (all papers in subject / all papers). Only subjects with at least ``subjects_minimum_total_papers`` papers.
    """
    gi = cfg["trends"]["group_interest"]
    totals = year_totals(inputs)
    all_papers = sum(totals.values())
    rows = []
    for subject, papers in inputs.subject_papers[kind].items():
        if len(papers) < gi["subjects_minimum_total_papers"]:
            continue
        for group, gp in groups.items():
            hit = gp & papers
            if not hit:
                continue
            by_year = {y: 0 for y in YEARS}
            group_year = {y: 0 for y in YEARS}
            for p in gp:
                y = inputs.paper_year.get(p)
                if y in group_year:
                    group_year[y] += 1
            for p in hit:
                y = inputs.paper_year.get(p)
                if y in by_year:
                    by_year[y] += 1
            shares = {y: (by_year[y] / group_year[y] if group_year[y] else None) for y in YEARS}
            first = next((y for y in YEARS if by_year[y]), None)
            early = [shares[y] for y in (2021, 2022) if shares[y] is not None]
            late = [shares[y] for y in (2024, 2025) if shares[y] is not None]
            rows.append({"group": group, "subject": subject, "subject_name": inputs.nodes[subject]["name"], "group_papers": len(gp), "group_papers_in_subject": len(hit),
                         "share_of_group": len(hit) / len(gp), "rca": (len(hit) / len(gp)) / (len(papers) / all_papers), "first_active_year": first,
                         "share_2021_2022_mean": sum(early) / len(early) if early else None, "share_2024_2025_mean": sum(late) / len(late) if late else None,
                         "growth_late_minus_early": (sum(late) / len(late) - sum(early) / len(early)) if early and late else None})
    return rows

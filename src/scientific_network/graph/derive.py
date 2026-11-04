"""Pure per-paper support helpers; callers must supply accepted, resolved core facts."""

from itertools import combinations


def coauthor_contributions(researcher_ids: list[str]) -> dict[tuple[str, str], float]:
    """A k-author core paper contributes 1/(k-1) to each unique pair."""
    authors = sorted(set(researcher_ids))
    if len(authors) < 2:
        return {}
    return {pair: 1 / (len(authors) - 1) for pair in combinations(authors, 2)}


def organization_contributions(
    affiliations: list[tuple[str, str]],
) -> dict[tuple[str, str], float]:
    """Input is (researcher, organization) for ONE paper, already evidence-aligned.

    A pair needs two distinct authors and organizations. Multiple authors/mentions
    on this paper count as one support paper. A sole dual-affiliated author
    contributes no organization collaboration.
    """
    pairs = {
        tuple(sorted((left_org, right_org)))
        for (left_author, left_org), (right_author, right_org)
        in combinations(set(affiliations), 2)
        if left_author != right_author and left_org != right_org
    }
    return {pair: 1 / len(pairs) for pair in pairs}

import pytest

from scientific_network.graph.derive import coauthor_contributions, organization_contributions


def test_sole_dual_affiliated_author_does_not_create_org_collaboration():
    assert organization_contributions([("alice", "uni"), ("alice", "lab")]) == {}


def test_distinct_authors_and_orgs_create_one_support_per_paper():
    observations = [("alice", "uni"), ("bob", "lab"), ("carol", "lab"), ("bob", "lab")]
    assert organization_contributions(observations) == {("lab", "uni"): 1.0}


def test_fractional_org_contributions_sum_to_one_across_eligible_pairs():
    result = organization_contributions([("a", "X"), ("b", "Y"), ("c", "Z")])
    assert len(result) == 3
    assert sum(result.values()) == pytest.approx(1.0)


def test_duplicate_author_mentions_do_not_increase_coauthor_weight():
    result = coauthor_contributions(["a", "a", "b", "c"])
    assert result == {("a", "b"): 0.5, ("a", "c"): 0.5, ("b", "c"): 0.5}
    assert coauthor_contributions(["a", "a"]) == {}

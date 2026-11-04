import pytest

from scientific_network.evaluation.precision import precision_interval


def test_plan_example_wilson_interval():
    result = precision_interval(570, 600)
    assert result["precision"] == 0.95
    assert 0.929 < result["wilson_lower"] < 0.930
    assert result["wilson_upper"] > 0.96


def test_point_precision_alone_does_not_pass_lower_bound_gate():
    assert precision_interval(95, 100)["wilson_lower"] < 0.90
    assert precision_interval(96, 100)["wilson_lower"] > 0.90


@pytest.mark.parametrize("correct,total", [(0, 0), (-1, 20), (21, 20)])
def test_invalid_audit_counts_are_rejected(correct, total):
    with pytest.raises(ValueError):
        precision_interval(correct, total)


@pytest.mark.parametrize("correct,expected", [(0, "wilson_lower"), (50, "wilson_upper")])
def test_all_wrong_or_correct_boundaries(correct, expected):
    result = precision_interval(correct, 50)
    assert result[expected] == pytest.approx(0 if correct == 0 else 1)

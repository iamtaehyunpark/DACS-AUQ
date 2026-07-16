"""Tests for the E1b analysis modules: Kendall tau-b, rank agreement, clustering histogram."""
from src.analysis.rank_agreement import kendall_tau_b, rank_agreement, round_number_histogram


def _rec(a, b):
    return {"probes": {"U_T_verbalized": a, "U_T_posthoc_numeric": b}}


class TestKendall:
    def test_perfect_and_reversed(self):
        assert abs(kendall_tau_b([1, 2, 3, 4], [10, 20, 30, 40]) - 1.0) < 1e-9
        assert abs(kendall_tau_b([1, 2, 3, 4], [40, 30, 20, 10]) + 1.0) < 1e-9

    def test_known_value_with_ties(self):
        # x=[1,2,2,3], y=[1,2,3,4]: C=5, D=0, tx=1, ty=0, n0=6 -> tau_b = 5/sqrt(5*6)
        assert abs(kendall_tau_b([1, 2, 2, 3], [1, 2, 3, 4]) - 5 / (5 * 6) ** 0.5) < 1e-9

    def test_degenerate(self):
        assert kendall_tau_b([1], [1]) != kendall_tau_b([1], [1])  # NaN
        assert kendall_tau_b([1, 1, 1], [1, 2, 3]) != kendall_tau_b([1, 1, 1], [1, 2, 3])


class TestRankAgreement:
    def test_excludes_unparsed(self):
        recs = [_rec(0.1, 0.2), _rec(0.5, None), _rec(None, 0.3), _rec(0.9, 0.8)]
        out = rank_agreement(recs, "U_T_verbalized", "U_T_posthoc_numeric")
        assert out["n"] == 2 and out["n_excluded"] == 2
        assert out["kendall_tau_b"] == 1.0


class TestHistogram:
    def test_percent_binning(self):
        recs = [_rec(0.2, None), _rec(0.2, None), _rec(0.5, None)]
        out = round_number_histogram(recs, "U_T_verbalized")
        assert out["histogram"] == {50: 1, 80: 2} and out["n"] == 3

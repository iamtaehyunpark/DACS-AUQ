"""Tests for the E0 harness: stratified sampling invariants and Cohen's kappa."""
from src.e0.agreement import cohen_kappa
from src.e0.sample_steps import stratified_sample, tau_cell


def _rec(i, tau):
    return {"run_id": "r", "task_id": f"t{i % 30}", "step_idx": i, "tau": tau}


def _corpus():
    recs = []
    for i in range(300):
        recs.append(_rec(i, {"I": 1, "W": 0, "R": 1, "C": "cheap"}))       # big cell
    for i in range(300, 340):
        recs.append(_rec(i, {"I": 0, "W": 1, "R": 1, "C": "cheap"}))       # medium
    for i in range(340, 345):
        recs.append(_rec(i, {"I": 0, "W": 1, "R": 0, "C": "costly"}))      # tiny (5 < min 10)
    return recs


class TestStratifiedSample:
    def test_total_and_floor(self):
        picked = stratified_sample(_corpus(), n=150, min_per_cell=10, seed=7)
        assert len(picked) == 150
        counts = {}
        for r in picked:
            counts[tau_cell(r)] = counts.get(tau_cell(r), 0) + 1
        assert counts["I0W1R0"] == 5            # tiny cell: take ALL (floor capped at size)
        assert counts["I0W1R1"] >= 10           # floor respected
        assert counts["I1W0R1"] > counts["I0W1R1"]  # proportionality preserved

    def test_deterministic(self):
        a = stratified_sample(_corpus(), n=150, seed=7)
        b = stratified_sample(_corpus(), n=150, seed=7)
        assert [r["step_idx"] for r in a] == [r["step_idx"] for r in b]

    def test_n_larger_than_corpus(self):
        small = _corpus()[:20]
        assert len(stratified_sample(small, n=150, seed=7)) == 20


class TestKappa:
    def test_perfect_agreement(self):
        assert cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0

    def test_chance_level(self):
        a = [1, 1, 0, 0]
        b = [1, 0, 1, 0]
        assert abs(cohen_kappa(a, b)) < 1e-9

    def test_known_value(self):
        # 45 agree-1, 15 a1b0, 25 a0b1, 15 agree-0: po=0.60,
        # pe = P(a=1)P(b=1) + P(a=0)P(b=0) = 0.6*0.7 + 0.4*0.3 = 0.54 -> kappa = 0.06/0.46
        a = [1] * 45 + [1] * 15 + [0] * 25 + [0] * 15
        b = [1] * 45 + [0] * 15 + [1] * 25 + [0] * 15
        assert abs(cohen_kappa(a, b) - 0.06 / 0.46) < 1e-9


from src.analysis.loop_steps import (collapse_loop_steps, loop_fraction_by_episode,
                                     loop_step_uids)
from src.e0.sample_steps import stratum


def _step(i, task, act, obs, tau=None):
    return {"run_id": "r", "task_id": task, "step_idx": i, "action_text": act,
            "observation_text": obs,
            "tau": tau or {"I": 1, "W": 0, "R": 1, "C": "cheap"}}


class TestLoopSteps:
    def test_repeated_transition_flagged_first_kept(self):
        ep = [_step(0, "t", "look", "A"), _step(1, "t", "go to desk 1", "B"),
              _step(2, "t", "look", "A"), _step(3, "t", "look", "A")]
        assert loop_step_uids(ep) == {("r", "t", 2), ("r", "t", 3)}
        assert [r["step_idx"] for r in collapse_loop_steps(ep)] == [0, 1]

    def test_same_action_different_observation_is_fresh(self):
        ep = [_step(0, "t", "look", "A"), _step(1, "t", "look", "B")]
        assert loop_step_uids(ep) == set()

    def test_empty_action_never_loops(self):
        ep = [_step(0, "t", "", "Nothing happens."), _step(1, "t", "", "Nothing happens.")]
        assert loop_step_uids(ep) == set()

    def test_scoped_per_episode(self):
        recs = [_step(0, "t1", "look", "A"), _step(0, "t2", "look", "A")]
        assert loop_step_uids(recs) == set()

    def test_fraction_covariate(self):
        ep = [_step(0, "t", "look", "A"), _step(1, "t", "look", "A"),
              _step(2, "t", "look", "A"), _step(3, "t", "go to bed 1", "C")]
        f = loop_fraction_by_episode(ep)[("r", "t")]
        assert f == {"n_steps": 4, "n_loop": 2, "fraction": 0.5}


class TestLoopStratification:
    def _corpus(self):
        recs = []
        for i in range(40):                       # fresh: distinct transitions
            recs.append(_step(i, f"ep{i % 4}", f"go to drawer {i}", f"obs {i}"))
        for i in range(40, 100):                  # loop: one repeated transition per episode
            recs.append(_step(i, f"ep{i % 4}", "look", "You are facing the desk 1."))
        return recs

    def test_strata_cross_loop_and_fresh(self):
        recs = self._corpus()
        loops = loop_step_uids(recs)
        strata = {stratum(r, loops) for r in recs}
        assert "I1W0R1|fresh" in strata and "I1W0R1|loop" in strata

    def test_sample_covers_both_strata(self):
        recs = self._corpus()
        picked = stratified_sample(recs, n=30, min_per_cell=10, seed=7)
        loops = loop_step_uids(recs)
        counts = {}
        for r in picked:
            k = stratum(r, loops)
            counts[k] = counts.get(k, 0) + 1
        assert len(picked) == 30
        assert counts["I1W0R1|fresh"] >= 10 and counts["I1W0R1|loop"] >= 10

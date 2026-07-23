"""One unit test per ALFWorld action family (spec §0.4 guard).

A silent tau mis-tag corrupts E2/E3 while leaving E1 looking fine, so every family in the
authoritative table is pinned here, plus the unrecognized-action -> None contract.
Run: pytest tests/test_tau_map.py
"""
from src.env.tau_map import Tau, normalize_action, tau_of


def test_look_examine_inventory():
    assert tau_of("look") == Tau(1, 0, 1, "free")
    assert tau_of("inventory") == Tau(1, 0, 1, "free")
    assert tau_of("examine desk 1") == Tau(1, 0, 1, "free")


def test_go_to():
    assert tau_of("go to drawer 2") == Tau(1, 0, 1, "cheap")


def test_open_close():
    assert tau_of("open fridge 1") == Tau(0, 1, 1, "cheap")
    assert tau_of("close fridge 1") == Tau(0, 1, 1, "cheap")


def test_take_put():
    assert tau_of("take apple 1 from countertop 1") == Tau(0, 1, 1, "cheap")
    assert tau_of("put apple 1 in/on countertop 1") == Tau(0, 1, 1, "cheap")


def test_heat_cool_clean_irreversible():
    assert tau_of("heat apple 1 with microwave 1") == Tau(0, 1, 0, "costly")
    assert tau_of("cool apple 1 with fridge 1") == Tau(0, 1, 0, "costly")
    assert tau_of("clean apple 1 with sinkbasin 1") == Tau(0, 1, 0, "costly")


def test_slice_irreversible():
    assert tau_of("slice bread 1 with knife 1") == Tau(0, 1, 0, "costly")


def test_use():
    assert tau_of("use desklamp 1") == Tau(0, 1, 1, "cheap")


def test_meta_help():
    # TextWorld meta-command present in every ALFWorld admissible set (found by scripts/smoke_env.py).
    assert tau_of("help") == Tau(1, 0, 1, "free")


def test_unrecognized_returns_none():
    # None is the explicit "log-and-count" signal, never a guessed tag.
    assert tau_of("teleport to narnia") is None
    assert tau_of("") is None
    assert tau_of(None) is None


def test_normalization_is_pure():
    # object names / casing / trailing punctuation must not affect the family.
    assert tau_of("GO TO Drawer 2.") == tau_of("go to drawer 2")
    assert normalize_action("  Open   Fridge 1  ") == "open fridge 1"

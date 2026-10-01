import pytest

from app import tasks


@pytest.fixture(autouse=True)
def defaults(monkeypatch):
    monkeypatch.setattr(tasks, "HOLDOUT_FRACTION", 0.2)
    monkeypatch.setattr(tasks, "MIN_HOLDOUT_SAMPLES", 20)


@pytest.mark.parametrize("n_samples, expected", [
    (50, 20),    # 20% would be 10, raised to the minimum
    (200, 40),   # 20% is already above the minimum
    (30, 15),    # the minimum would leave too little to train on
    (2, 1),
])
def test_holdout_size(n_samples, expected):
    assert tasks.holdout_size(n_samples) == expected


def test_split_holdout_uses_minimum_and_keeps_classes_balanced():
    labels = [0, 1, 2] * 16 + [0, 1]  # 50 samples

    train_idx, holdout_idx = tasks.split_holdout(labels)

    assert len(holdout_idx) == 20
    assert len(train_idx) == 30
    assert set(train_idx).isdisjoint(holdout_idx)
    assert {labels[i] for i in holdout_idx} == {0, 1, 2}

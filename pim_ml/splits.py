from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, LeaveOneOut, KFold


@dataclass(frozen=True)
class FoldIndices:
    fold_id: int
    train_idx: np.ndarray
    test_idx: np.ndarray


def build_splits(
    frame: pd.DataFrame,
    target: pd.Series,
    cv_config: dict,
    group_column: str | None,
    random_state: int,
) -> list[FoldIndices]:
    mode = cv_config.get("mode", "group_kfold")
    splits: list[FoldIndices] = []

    if mode == "group_kfold":
        if not group_column:
            raise ValueError("group_kfold requires a group_column")
        groups = frame[group_column]
        n_groups = groups.nunique()
        n_splits = min(int(cv_config.get("n_splits", 5)), n_groups)
        if n_splits < 2:
            raise ValueError("Need at least two unique groups for GroupKFold")
        splitter = GroupKFold(n_splits=n_splits)
        iterator = splitter.split(frame, target, groups=groups)
    elif mode == "loo":
        splitter = LeaveOneOut()
        iterator = splitter.split(frame, target)
    elif mode == "kfold":
        n_splits = int(cv_config.get("n_splits", 5))
        splitter = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
        iterator = splitter.split(frame, target)
    else:
        raise ValueError(f"Unsupported cv mode: {mode}")

    for fold_id, (train_idx, test_idx) in enumerate(iterator, start=1):
        splits.append(FoldIndices(fold_id=fold_id, train_idx=train_idx, test_idx=test_idx))

    return splits


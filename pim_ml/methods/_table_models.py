from __future__ import annotations

from collections.abc import Callable

from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR


ModelFactory = Callable[[], Pipeline | RandomForestRegressor | HistGradientBoostingRegressor]


def get_table_model_factories(
    model_names: list[str],
    random_state: int,
) -> tuple[dict[str, ModelFactory], list[dict[str, str]]]:
    factories: dict[str, ModelFactory] = {}
    skipped: list[dict[str, str]] = []

    def ridge_factory():
        return Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", Ridge(alpha=1.0)),
            ]
        )

    def svr_factory():
        return Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", SVR(kernel="rbf", C=10.0, epsilon=0.1)),
            ]
        )

    def random_forest_factory():
        return Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=400,
                        random_state=random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        )

    def hist_gb_factory():
        return Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    HistGradientBoostingRegressor(
                        learning_rate=0.05,
                        max_iter=300,
                        early_stopping=True,
                        scoring="loss",
                        validation_fraction=0.2,
                        n_iter_no_change=20,
                        random_state=random_state,
                    ),
                ),
            ]
        )

    registry: dict[str, ModelFactory] = {
        "ridge": ridge_factory,
        "svr": svr_factory,
        "random_forest": random_forest_factory,
        "hist_gb": hist_gb_factory,
    }

    for model_name in model_names:
        if model_name == "xgboost":
            try:
                from xgboost import XGBRegressor
            except ImportError:
                skipped.append(
                    {
                        "model_name": model_name,
                        "reason": "xgboost is not installed in the current Python environment",
                    }
                )
                continue

            def xgboost_factory():
                return Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        (
                            "model",
                            XGBRegressor(
                                n_estimators=400,
                                max_depth=6,
                                learning_rate=0.05,
                                subsample=0.9,
                                colsample_bytree=0.9,
                                objective="reg:squarederror",
                                random_state=random_state,
                                n_jobs=1,
                            ),
                        ),
                    ]
                )

            factories[model_name] = xgboost_factory
            continue

        factory = registry.get(model_name)
        if factory is None:
            skipped.append({"model_name": model_name, "reason": "unknown model name"})
            continue
        factories[model_name] = factory

    return factories, skipped

"""Test suite for best-prediction utilities and 305-day yield estimation.

This module validates core helpers and end-to-end prediction behavior for the
best-prediction implementation in ``lactationcurve.characteristics.best_predict``.

Test Categories:
    - TestUtilityFunctions: matrix-building, preprocessing, covariance helpers.
    - TestPredictionFunctions: single-lactation and multi-lactation prediction.
    - TestIntegration: real-file smoke and leave-one-id-out fit checks.

Author: Meike and Copilot
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lactationcurve.characteristics.best_predict import (
    best_predict_method,
    best_predict_method_single_lac,
    build_covariance_matrix,
    pivot_milk_recordings_to_matrix,
    preprocess_measured_data,
)


@pytest.fixture
def package_data_dir() -> Path:
    """Return package data directory containing standard curve assets."""
    return Path("packages/python/lactation/data")


@pytest.fixture
def test_data_dir() -> Path:
    """Return test data directory containing csv fixtures."""
    return Path("tests/lactationcurve/test_data")


@pytest.fixture
def standard_curve() -> np.ndarray:
    """Return a simple flat standard curve used in deterministic unit tests."""
    return np.full(305, 10.0)


@pytest.fixture
def identity_covariance() -> np.ndarray:
    """Return identity covariance matrix used in deterministic unit tests."""
    return np.eye(305)


@pytest.mark.utility
class TestUtilityFunctions:
    """Test helper behavior used by best prediction."""

    def test_pivot_milk_recordings_to_matrix_enforces_fixed_305_grid(self):
        """Pivoted matrix should always use two dimensions and 305 columns."""
        df = pd.DataFrame(
            {
                "TestId": [1, 1, 2],
                "DaysInMilk": [1, 3, 1],
                "MilkingYield": [10.0, 12.0, 8.0],
            }
        )

        matrix = pivot_milk_recordings_to_matrix(df)

        assert matrix.shape == (2, 305)
        assert matrix[0, 0] == 10.0
        assert np.isnan(matrix[0, 1])
        assert matrix[0, 2] == 12.0
        assert matrix[1, 0] == 8.0

    def test_preprocess_measured_data_returns_305_series_for_valid_days(self, standard_curve):
        """Preprocess should return day-indexed 305-length deviation vector."""
        lactation = pd.DataFrame(
            {
                "DaysInMilk": [1, 10],
                "MilkingYield": [11.0, 8.0],
            }
        )

        corrected = preprocess_measured_data(lactation, standard_curve)

        assert len(corrected) == 305
        assert corrected.index.min() == 1
        assert corrected.index.max() == 305
        assert corrected.loc[1] == 1.0
        assert corrected.loc[10] == -2.0
        assert float(corrected.sum()) == -1.0

    def test_preprocess_measured_data_raises_for_out_of_range_days(self, standard_curve):
        """DIM above 305 should fail because indexing exceeds standard curve."""
        lactation = pd.DataFrame(
            {
                "DaysInMilk": [1, 306],
                "MilkingYield": [11.0, 20.0],
            }
        )

        with pytest.raises(IndexError):
            preprocess_measured_data(lactation, standard_curve)

    def test_build_covariance_matrix_matches_ar1_structure(self):
        """AR(1) covariance helper should match known small matrix values."""
        cov = build_covariance_matrix(rho=0.5, size=4)

        expected = np.array(
            [
                [1.0, 0.5, 0.25, 0.125],
                [0.5, 1.0, 0.5, 0.25],
                [0.25, 0.5, 1.0, 0.5],
                [0.125, 0.25, 0.5, 1.0],
            ]
        )

        assert np.allclose(cov, expected)
        assert np.allclose(cov, cov.T)
        assert np.allclose(np.diag(cov), np.ones(4))


class TestPredictionFunctions:
    """Test prediction behavior for single and multiple lactations."""

    def test_best_predict_method_single_lac_uses_cumulative_sum_adjustment(
        self, standard_curve, identity_covariance
    ):
        """One positive residual with identity covariance should shift total by 1."""
        lactation = pd.DataFrame(
            {
                "DaysInMilk": [1],
                "MilkingYield": [11.0],
            }
        )

        predicted = best_predict_method_single_lac(
            lactation,
            standard_curve,
            identity_covariance,
        )

        assert predicted == 3051.0

    def test_best_predict_method_single_lac_empty_returns_standard_curve_sum(
        self, standard_curve, identity_covariance
    ):
        """If no valid DIM in 1..305 exists, prediction should equal baseline sum."""
        lactation = pd.DataFrame(
            {
                "DaysInMilk": [0, 400],
                "MilkingYield": [11.0, 12.0],
            }
        )

        predicted = best_predict_method_single_lac(
            lactation,
            standard_curve,
            identity_covariance,
        )

        assert predicted == pytest.approx(float(np.sum(standard_curve)))

    def test_best_predict_method_single_lac_duplicate_days_keep_last(
        self, standard_curve, identity_covariance
    ):
        """Duplicate DIM records should use the last value before prediction."""
        lactation = pd.DataFrame(
            {
                "DaysInMilk": [1, 1],
                "MilkingYield": [9.0, 11.0],
            }
        )

        predicted = best_predict_method_single_lac(
            lactation,
            standard_curve,
            identity_covariance,
        )

        assert predicted == 3051.0

    def test_best_predict_method_does_not_mutate_input_dataframe_without_testid(
        self, standard_curve, identity_covariance
    ):
        """Main API should not mutate caller dataframe when creating TestId."""
        df = pd.DataFrame(
            {
                "DaysInMilk": [1, 2],
                "MilkingYield": [11.0, 12.0],
            }
        )
        original_columns = list(df.columns)

        result = best_predict_method(
            df,
            standard_lc=standard_curve,
            covariance_matrix=identity_covariance,
        )

        assert list(df.columns) == original_columns
        assert list(result.columns) == ["TestId", "Predicted305MilkYield"]
        assert len(result) == 1

    def test_best_predict_method_requires_covariance_or_reference(self, standard_curve):
        """Main API should fail fast when neither covariance nor reference is supplied."""
        df = pd.DataFrame(
            {
                "DaysInMilk": [1, 2],
                "MilkingYield": [11.0, 12.0],
            }
        )

        with pytest.raises(ValueError, match="Provide covariance_matrix or reference_df"):
            best_predict_method(df, standard_lc=standard_curve)


class TestIntegration:
    """Integration tests using real fixture files and package-provided matrices."""

    def test_best_predict_method_real_file_smoke_test(self, test_data_dir, package_data_dir):
        """Real-file prediction with provided covariance should be finite and stable."""
        full_lac_single = pd.read_csv(test_data_dir / "l2_anim2_herd654.csv")
        full_lac_single = full_lac_single.rename(columns={"TestDayMilkYield": "MilkingYield"})

        covariance_matrix = np.load(package_data_dir / "covariance_matrix_best_predict.npy")
        standard_curve = np.load(package_data_dir / "standard_lc_wood.npy")

        result = best_predict_method(
            full_lac_single,
            standard_lc=standard_curve,
            covariance_matrix=covariance_matrix,
        )

        assert not result.empty
        assert "Predicted305MilkYield" in result.columns
        assert np.isfinite(result["Predicted305MilkYield"]).all()
        assert result["Predicted305MilkYield"].iloc[0] == pytest.approx(10795.472636)

    def test_best_predict_method_fitted_covariance_within_5_percent_for_testid_1483(
        self, test_data_dir, package_data_dir
    ):
        """Leave-one-id-out fit should predict TestId 1483 within 5% of known total."""
        test_day_df = pd.read_csv(test_data_dir / "TestDataSet.csv")
        test_day_df = test_day_df.rename(columns={"DailyMilkingYield": "MilkingYield"})

        test_id_to_predict = 1483
        actual_production_1483 = 10573.1

        training_data = test_day_df.loc[test_day_df["TestId"] != test_id_to_predict].copy()
        target_data = test_day_df.loc[test_day_df["TestId"] == test_id_to_predict].copy()

        assert not target_data.empty, "TestDataSet.csv does not contain TestId 1483"

        result_cov = best_predict_method(
            target_data,
            standard_lc=np.load(package_data_dir / "standard_lc_wood.npy"),
            reference_df=training_data,
        )

        predicted = float(result_cov["Predicted305MilkYield"].iloc[0])
        relative_error = abs(predicted - actual_production_1483) / actual_production_1483
        assert relative_error <= 0.05

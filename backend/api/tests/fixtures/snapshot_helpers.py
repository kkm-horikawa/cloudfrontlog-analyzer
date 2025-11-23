"""
Snapshot Testing Helpers

Utilities for loading and comparing golden data in snapshot tests.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


class GoldenDataLoader:
    """Load golden data from Parquet files"""

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            # Default to tests/data/golden directory
            self.data_dir = Path(__file__).parent.parent / "data" / "golden"
        else:
            self.data_dir = Path(data_dir)

    def load(self, filename: str) -> pd.DataFrame:
        """Load golden data from Parquet file"""
        filepath = self.data_dir / f"{filename}.parquet"
        if not filepath.exists():
            raise FileNotFoundError(
                f"Golden data file not found: {filepath}\n"
                f"Run collect_golden_data.py to generate golden data."
            )
        return pd.read_parquet(filepath)

    def load_as_dict_list(self, filename: str) -> List[Dict]:
        """Load golden data as list of dictionaries"""
        df = self.load(filename)
        return df.to_dict(orient="records")

    def load_as_dict(self, filename: str) -> Dict:
        """Load golden data as single dictionary (for single-row data)"""
        df = self.load(filename)
        if len(df) != 1:
            raise ValueError(
                f"Expected single row in {filename}, got {len(df)} rows"
            )
        return df.to_dict(orient="records")[0]


class SnapshotComparator:
    """Compare API responses with golden data"""

    def __init__(self, loader: Optional[GoldenDataLoader] = None):
        self.loader = loader or GoldenDataLoader()

    def compare_response(
        self,
        actual: Any,
        golden_filename: str,
        exclude_fields: Optional[List[str]] = None,
        tolerance: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Compare actual API response with golden data

        Args:
            actual: Actual API response (dict or list)
            golden_filename: Name of golden data file (without .parquet extension)
            exclude_fields: List of fields to exclude from comparison (e.g., timestamps)
            tolerance: Tolerance for numeric comparisons (0.0 = exact match)

        Returns:
            Dict with comparison results:
            {
                "match": bool,
                "differences": List[str],
                "actual_count": int,
                "expected_count": int,
            }
        """
        if exclude_fields is None:
            exclude_fields = []

        # Load golden data
        try:
            if isinstance(actual, list):
                expected = self.loader.load_as_dict_list(golden_filename)
            elif isinstance(actual, dict):
                expected = self.loader.load_as_dict(golden_filename)
            else:
                return {
                    "match": False,
                    "differences": [f"Unsupported actual type: {type(actual)}"],
                    "actual_count": 0,
                    "expected_count": 0,
                }
        except FileNotFoundError as e:
            return {
                "match": False,
                "differences": [str(e)],
                "actual_count": 0,
                "expected_count": 0,
            }

        # Convert to DataFrames for comparison
        if isinstance(actual, list):
            actual_df = pd.DataFrame(actual)
            expected_df = pd.DataFrame(expected)
        else:
            actual_df = pd.DataFrame([actual])
            expected_df = pd.DataFrame([expected])

        # Remove excluded fields
        for field in exclude_fields:
            if field in actual_df.columns:
                actual_df = actual_df.drop(columns=[field])
            if field in expected_df.columns:
                expected_df = expected_df.drop(columns=[field])

        # Compare
        differences = []

        # 1. Check row counts
        if len(actual_df) != len(expected_df):
            differences.append(
                f"Row count mismatch: expected {len(expected_df)}, got {len(actual_df)}"
            )

        # 2. Check column names
        actual_cols = set(actual_df.columns)
        expected_cols = set(expected_df.columns)
        if actual_cols != expected_cols:
            missing = expected_cols - actual_cols
            extra = actual_cols - expected_cols
            if missing:
                differences.append(f"Missing columns: {missing}")
            if extra:
                differences.append(f"Extra columns: {extra}")

        # 3. Compare values (only if same shape)
        if len(actual_df) == len(expected_df) and actual_cols == expected_cols:
            # Sort both DataFrames by all columns for consistent comparison
            sort_cols = list(actual_df.columns)
            actual_sorted = actual_df.sort_values(by=sort_cols).reset_index(drop=True)
            expected_sorted = expected_df.sort_values(by=sort_cols).reset_index(
                drop=True
            )

            # Compare each column
            for col in actual_sorted.columns:
                if pd.api.types.is_numeric_dtype(actual_sorted[col]):
                    # Numeric comparison with tolerance
                    if not actual_sorted[col].equals(expected_sorted[col]):
                        max_diff = (
                            (actual_sorted[col] - expected_sorted[col]).abs().max()
                        )
                        if max_diff > tolerance:
                            differences.append(
                                f"Column '{col}' has numeric differences (max: {max_diff})"
                            )
                else:
                    # Exact comparison for non-numeric
                    if not actual_sorted[col].equals(expected_sorted[col]):
                        # Find which rows differ
                        diff_mask = actual_sorted[col] != expected_sorted[col]
                        diff_count = diff_mask.sum()
                        differences.append(
                            f"Column '{col}' has {diff_count} differing values"
                        )

        return {
            "match": len(differences) == 0,
            "differences": differences,
            "actual_count": len(actual_df),
            "expected_count": len(expected_df),
        }

    def assert_matches_snapshot(
        self,
        actual: Any,
        golden_filename: str,
        exclude_fields: Optional[List[str]] = None,
        tolerance: float = 0.0,
    ):
        """
        Assert that actual response matches golden snapshot

        Raises AssertionError if mismatch found
        """
        result = self.compare_response(actual, golden_filename, exclude_fields, tolerance)

        if not result["match"]:
            error_msg = f"\nSnapshot mismatch for '{golden_filename}':\n"
            error_msg += f"Expected {result['expected_count']} rows, got {result['actual_count']} rows\n"
            error_msg += "\nDifferences:\n"
            for diff in result["differences"]:
                error_msg += f"  - {diff}\n"
            raise AssertionError(error_msg)


# Global instances for easy import
golden_loader = GoldenDataLoader()
snapshot_comparator = SnapshotComparator()

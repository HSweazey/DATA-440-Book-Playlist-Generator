"""
io_utils.py
------------
Utility functions for reading and writing data files (CSV, JSON?),
plus helpers for merging split CSVs.

Note: all paths are assumed to be relative to the project root.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Optional, List
from .config import PROJECT_ROOT


# === CSV HANDLING ===

def read_csv(file_path: str, **kwargs) -> Optional[pd.DataFrame]:
    """
    Reads a CSV file into a pandas DataFrame.

    Parameters
    ----------
    file_path : str
        Relative or absolute path to the CSV file.
    kwargs : dict
        Additional keyword arguments for pandas.read_csv().

    Returns
    -------
    pd.DataFrame or None
        The loaded DataFrame, or None if file not found or unreadable.
    """
    path = Path(file_path)
    try:
        return pd.read_csv(path, **kwargs)
    except FileNotFoundError:
        print(f"File not found: {path}")
        return None
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return None


def write_csv(df: pd.DataFrame, file_path: str, **kwargs) -> None:
    """
    Writes a pandas DataFrame to a CSV file.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to write.
    file_path : str
        Destination file path.
    kwargs : dict
        Additional keyword arguments for pandas.DataFrame.to_csv().
    """
    path = Path(file_path)
    path.parent.mkdir(parents = True, exist_ok = True)
    try:
        df.to_csv(path, index = False, **kwargs)
    except Exception as e:
        print(f"Error writing {path}: {e}")


# === JSON HANDLING ===

def read_json(file_path: str) -> Optional[dict]:
    """
    Reads a JSON file and returns it as a dictionary.

    Returns
    -------
    dict or None
        Parsed JSON data or None if failed.
    """
    path = Path(file_path)
    try:
        with open(path, "r", encoding = "utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File not found: {path}")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON format in {path}")
        return None


def write_json(data: dict, file_path: str, indent: int = 4) -> None:
    """
    Writes a Python dictionary to a JSON file.

    Parameters
    ----------
    data : dict
        The data to save.
    file_path : str
        Path to the JSON file.
    indent : int
        Indentation level for readability.
    """
    path = Path(file_path)
    path.parent.mkdir(parents = True, exist_ok = True)
    try:
        with open(path, "w", encoding = "utf-8") as f:
            json.dump(data, f, indent = indent)
    except Exception as e:
        print(f"Error writing JSON to {path}: {e}")


# === MERGE MULTIPLE SPLIT CSVS ===

def merge_split_csvs(
    directory: str,
    base_name: str = "goodreads",
    output_path: Optional[str] = None,
    **read_kwargs
) -> Optional[pd.DataFrame]:
    """
    Merges multiple split CSV files (e.g. goodreads0.csv, goodreads1.csv, ...)
    into a single pandas DataFrame.

    Parameters
    ----------
    directory : str
        Directory containing the split CSV files.
    base_name : str, default="goodreads"
        Common prefix for split files (e.g. "goodreads" for goodreads0.csv).
    output_path : str or None
        Optional path to write the merged CSV file.
    read_kwargs : dict
        Additional kwargs for pandas.read_csv().

    Returns
    -------
    pd.DataFrame or None
        Merged DataFrame or None if no files found.
    """
    dir_path = Path(directory)
    files: List[Path] = sorted(
        dir_path.glob(f"{base_name}*.csv"),
        key = lambda x: int("".join(filter(str.isdigit, x.stem)) or 0)
    )

    if not files:
        print(f"No files found in {dir_path} with base '{base_name}'")
        return None

    try:
        dfs = [pd.read_csv(f, **read_kwargs) for f in files]
        merged_df = pd.concat(dfs, ignore_index = True)
        if output_path:
            write_csv(merged_df, output_path)
        return merged_df
    except Exception as e:
        print(f"Error merging CSVs from {dir_path}: {e}")
        return None

# Load required libraries
import subprocess  # command line commands
import coverage  # not used directly but run in command line
from io import StringIO  # reading byte string (returned by coverage)
import pandas as pd  # working with dataframes
from pathlib import Path  # handling file paths
import re  # working with regular expressions

# TODO update to change badge when unittests fail - red "failing" instead of value?


def parse_coverage_report(coverage_report_string: str) -> pd.DataFrame:
    """Parses byte string returned by coverage report into pandas dataframe

    Args:
        coverage_report_string (bytes): string version of coverage report

    Returns:
        pd.DataFrame: coverage report as dataframe
    """

    # Convert the byte string into pandas dataframe
    coverage_dataframe = pd.read_csv(StringIO(coverage_report_string), sep="\s+")

    # Remove empty rows
    coverage_dataframe = coverage_dataframe[1:-2]
    coverage_dataframe = coverage_dataframe.reset_index(drop=True)

    # Remove percent sign from coverage column and convert to float
    coverage_dataframe.Cover = coverage_dataframe.Cover.str[:-1].astype(float)

    return coverage_dataframe


def run_code_coverage() -> pd.DataFrame:
    """Runs coverage tool in command line and returns report

    Raises:
        Exception: if running coverage tool fails

    Returns:
        pd.DataFrame: coverage report as dataframe
    """

    # Run code coverage calculation
    # Using .call() instead of .run() so we can check runs ok: https://www.datacamp.com/tutorial/python-subprocess
    coverage_command = [
        "python3",
        "-m",
        "coverage",
        "run",
        "--source=.",
        "-m",
        "unittest",
    ]
    return_code = subprocess.call(coverage_command)
    if return_code != 0:
        raise subprocess.CalledProcessError(
            f"Running coverage package command ({' '.join(coverage_command)}) failed! Return code: {return_code}"
        )

    # Generate the report
    report_command = ["python3", "-m", "coverage", "report"]
    try:
        coverage_report = subprocess.check_output(report_command, text=True)

    except subprocess.CalledProcessError as e:
        print(
            f"Generating coverage report command ({' '.join(report_command)}) failed! Return code: {e.returncode}"
        )

    # Convert coverage report output to dataframe
    report_dataframe = parse_coverage_report(coverage_report)

    return report_dataframe


def get_badge_colour(
    value: float,
    poor_max_threshold: float,
    medium_max_threshold: float,
    poor_colour: str = "red",
    medium_colour: str = "orange",
    good_colour: str = "green",
) -> str:
    """Gets coverage badger colour based on value and thresholds

    Args:
        value (float): coverage value
        poor_max_threshold (float): threshold below which badge colour is poor_colour
        medium_max_threshold (float): threshold below which badge colour is medium_colour
        poor_colour (str, optional): colour for badge when value <= poor_max_threshold. Defaults to "red".
        medium_colour (str, optional): colour for badge when value <= medium_max_threshold but more than poor_max_threshold. Defaults to "orange".
        good_colour (str, optional): colour for badge when value > medium_max_threshold. Defaults to "green".

    Returns:
        str: colour for badge
    """

    badge_colour = None
    if value < poor_max_threshold:
        badge_colour = poor_colour
    elif value < medium_max_threshold:
        badge_colour = medium_colour
    else:
        badge_colour = good_colour

    return badge_colour


def make_coverage_badge_url(
    coverage_dataframe: pd.DataFrame,
    poor_max_threshold: float = 25,
    medium_max_threshold: float = 75,
) -> str:
    """Uses shields io to build coverage badge

    Args:
        coverage_dataframe (pd.DataFrame): coverage report as dataframe
        poor_max_threshold (float, optional): threshold below which badge colour is red. Defaults to 25.
        medium_max_threshold (float, optional): threshold below which badge colour is orange. Defaults to 75.

    Returns:
        str: _description_
    """

    # Calculate the average code coverage
    total_statements = sum(coverage_dataframe.Stmts)
    total_statements_missed = sum(coverage_dataframe.Miss)
    average_coverage = (total_statements - total_statements_missed) / total_statements

    # Convert to percentage and round
    average_coverage = round(average_coverage * 100, 1)

    # Note badger colour
    badge_colour = get_badge_colour(
        average_coverage, poor_max_threshold, medium_max_threshold
    )

    # Build badge
    badge_url = (
        f"https://img.shields.io/badge/coverage-{average_coverage}%25-{badge_colour}"
    )

    return badge_url


def replace_regex_in_file(
    file_path: Path, pattern_regex: str, replacement: str, add_to_file: bool = True
):
    """Replace pattern in file with string

    Note if pattern not present this will add string to first line by default

    Args:
        file_path (Path): path to file
        pattern_regex (str): pattern to find
        replacement (str): string to replace pattern when found
        add_to_file (bool): if regex not present will add to top of file if True. Defaults to True
    """

    # Read in file contents
    file_lines = []
    with open(file_path) as file:
        file_lines = file.read().splitlines()

    # Check if badge present
    badge_present = any(bool(re.match(pattern_regex, line)) for line in file_lines)
    if (badge_present == False) & add_to_file:
        # If not add at top
        file_lines.insert(0, replacement)

    else:
        # If it is, update
        file_lines = [re.sub(pattern_regex, replacement, line) for line in file_lines]

    # Write file lines back to file
    with open(file_path, "w") as file:
        file.write("\n".join(file_lines) + "\n")

import os
import sys

import pandas as pd


def transfer_to_excel(csv_df: pd.DataFrame, xlsx_df: pd.DataFrame, title: str):
    # Transfer grades using student ID as the key
    # Convert both to str because student ID in CSV is str, but in Excel it may be int
    csv_df["学生番号"] = csv_df["学生番号"].astype(str)
    xlsx_df["学生番号"] = xlsx_df["学生番号"].astype(str)

    # Create a mapping dictionary for grades only
    score_map = csv_df.set_index("学生番号")["成績"].to_dict()

    # Add a new column (assignment) to xlsx_df
    xlsx_df[title] = xlsx_df["学生番号"].map(score_map)

    # Overwrite the original Excel file with the updated xlsx_df
    xlsx_df.to_excel(xlsx_path, index=False)


def main(assignment_dir: str):
    try:
        csv_df = pd.read_csv(
            os.path.join(assignment_dir, "grades.csv"),
            skiprows=2,  # Skip the first 2 lines (meta information)
            index_col=False,  # Do not use the first column as index
            dtype={"学生番号": str},  # Prevent dropping leading zeros in student ID
        )
    except FileNotFoundError:
        print(f"File not found: {os.path.join(assignment_dir, 'grades.csv')}, skipping this assignment.")
        return
    xlsx_df = pd.read_excel(xlsx_path)
    transfer_to_excel(csv_df, xlsx_df, title=assignment_dir)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python transfer.py <subject_folder> <xlsx_path>")
        sys.exit(1)
    subject_folder = sys.argv[1]
    xlsx_path = sys.argv[2]

    # List all assignment directories (ignore hidden files/folders)
    assignment_dirs = [
        os.path.join(subject_folder, dir) for dir in os.listdir(subject_folder) if not dir.startswith(".")
    ]
    for assignment_dir in assignment_dirs:
        main(assignment_dir)

    print("Successfully transferred!")

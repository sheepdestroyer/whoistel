import pandas as pd
import sys
import os
import re

def sanitize_sheet_name(name):
    """Sanitizes the sheet name to be used as a valid filename component."""
    name = re.sub(r'[^\w\s-]', '', name)  # Remove special characters except underscore, space, hyphen
    name = re.sub(r'\s+', '_', name)       # Replace spaces with underscores
    return name

def convert_xls_to_csv(xls_filepath, output_basepath):
    """
    Converts all sheets in an XLS or XLSX file to CSV files.

    Args:
        xls_filepath (str): Path to the input XLS/XLSX file.
        output_basepath (str): Base path for the output CSV files.
                               Each sheet will be saved as output_basepath_sheetname.csv
    """
    try:
        xls_file = pd.ExcelFile(xls_filepath)
    except FileNotFoundError:
        print(f"Error: XLS file not found at {xls_filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading XLS file {xls_filepath}: {e}", file=sys.stderr)
        sys.exit(1)

    output_dir = os.path.dirname(output_basepath)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for sheet_name in xls_file.sheet_names:
        try:
            df = xls_file.parse(sheet_name)
            sanitized_name = sanitize_sheet_name(sheet_name)
            csv_filepath = f"{output_basepath}_{sanitized_name}.csv"
            df.to_csv(csv_filepath, index=False)
            print(f"Successfully converted sheet '{sheet_name}' to '{csv_filepath}'")
        except Exception as e:
            print(f"Error converting sheet '{sheet_name}' from {xls_filepath}: {e}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python xls_to_csv_converter.py <input_xls_filepath> <output_csv_basepath>", file=sys.stderr)
        print("Example: python xls_to_csv_converter.py arcep/liste-zne.xls arcep/liste-zne", file=sys.stderr)
        sys.exit(1)

    input_xls = sys.argv[1]
    output_base = sys.argv[2]
    convert_xls_to_csv(input_xls, output_base)

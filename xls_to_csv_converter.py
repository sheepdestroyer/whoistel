import pandas as pd
import sys
import os
import re
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def sanitize_sheet_name(name):
    """Sanitizes the sheet name to be used as a valid filename component."""
    logging.debug(f"Sanitizing sheet name: {name}")
    name = re.sub(r'[^\w\s-]', '', name)  # Remove special characters except underscore, space, hyphen
    name = re.sub(r'\s+', '_', name)       # Replace spaces with underscores
    logging.debug(f"Sanitized sheet name: {name}")
    return name

def convert_xls_to_csv(xls_filepath, output_basepath):
    """
    Converts all sheets in an XLS or XLSX file to CSV files.

    Args:
        xls_filepath (str): Path to the input XLS/XLSX file.
        output_basepath (str): Base path for the output CSV files.
                               Each sheet will be saved as output_basepath_sheetname.csv
    """
    logging.info(f"Starting conversion of XLS/XLSX file: {xls_filepath}")
    logging.debug(f"Output base path: {output_basepath}")
    try:
        xls_file = pd.ExcelFile(xls_filepath)
        logging.debug(f"Successfully opened Excel file. Sheets found: {xls_file.sheet_names}")
    except FileNotFoundError:
        logging.error(f"XLS file not found at {xls_filepath}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading XLS file {xls_filepath}: {e}", exc_info=True)
        sys.exit(1)

    output_dir = os.path.dirname(output_basepath)
    if output_dir and not os.path.exists(output_dir):
        logging.debug(f"Output directory {output_dir} does not exist. Creating it.")
        os.makedirs(output_dir)

    for sheet_name in xls_file.sheet_names:
        logging.info(f"Processing sheet: {sheet_name}")
        try:
            df = xls_file.parse(sheet_name)
            logging.debug(f"Parsed sheet '{sheet_name}', shape: {df.shape}")
            sanitized_name = sanitize_sheet_name(sheet_name)
            csv_filepath = f"{output_basepath}_{sanitized_name}.csv"
            logging.debug(f"Target CSV filepath: {csv_filepath}")
            df.to_csv(csv_filepath, index=False)
            logging.info(f"Successfully converted sheet '{sheet_name}' to '{csv_filepath}'")
        except Exception as e:
            logging.error(f"Error converting sheet '{sheet_name}' from {xls_filepath}: {e}", exc_info=True)

if __name__ == "__main__":
    logging.debug(f"xls_to_csv_converter.py called with arguments: {sys.argv}")
    if len(sys.argv) != 3:
        logging.error("Invalid number of arguments.")
        print("Usage: python xls_to_csv_converter.py <input_xls_filepath> <output_csv_basepath>", file=sys.stderr)
        print("Example: python xls_to_csv_converter.py arcep/liste-zne.xls arcep/liste-zne", file=sys.stderr)
        sys.exit(1)

    input_xls = sys.argv[1]
    output_base = sys.argv[2]
    logging.debug(f"Input XLS: {input_xls}, Output Base: {output_base}")
    convert_xls_to_csv(input_xls, output_base)

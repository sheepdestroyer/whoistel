import pandas as pd
import sys
import os

def convert_xls_to_csv(xls_path, output_csv_base_path):
    """
    Reads an XLS file and converts its sheets to CSV files.
    Each sheet will be saved as output_csv_base_path_sheetname.csv.
    """
    try:
        xls_file = pd.ExcelFile(xls_path)
        if not xls_file.sheet_names:
            print(f"No sheets found in {xls_path}")
            return

        print(f"Processing {xls_path}:")

        for sheet_name in xls_file.sheet_names:
            print(f"  Converting sheet: {sheet_name}...")
            df = xls_file.parse(sheet_name)

            # Sanitize sheet name for use in filename
            # Replace non-ASCII and non-alphanumeric characters with underscore
            sanitized_sheet_name = "".join(
                c if c.isalnum() and c.isascii() else "_" for c in sheet_name
            )
            # Replace multiple underscores with a single one
            safe_sheet_name = "_".join(filter(None, sanitized_sheet_name.split("_")))


            # Construct specific CSV path for this sheet
            base, ext = os.path.splitext(output_csv_base_path)
            final_csv_path = f"{base}_{safe_sheet_name}{ext}"
            if not safe_sheet_name: # Handle case where sheet name was all non-alphanumeric/non-ascii
                final_csv_path = f"{base}_sheet_{xls_file.sheet_names.index(sheet_name)}{ext}"


            df.to_csv(final_csv_path, index=False, encoding='utf-8')
            print(f"    Sheet '{sheet_name}' converted to {final_csv_path}")

    except FileNotFoundError:
        print(f"Error: File not found at {xls_path}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while processing {xls_path}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python xls_to_csv_converter.py <path_to_xls_file> <base_path_for_output_csv_files>")
        print("Example: python xls_to_csv_converter.py arcep/data.xls arcep/data.csv")
        print("(This will create arcep/data_Sheet1.csv, arcep/data_Sheet2.csv etc.)")
        sys.exit(1)

    xls_file_path = sys.argv[1]
    output_csv_base = sys.argv[2]

    convert_xls_to_csv(xls_file_path, output_csv_base)
    print("Conversion process completed.")

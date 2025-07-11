import pandas as pd
import sys

def inspect_xls_file(xls_path, csv_path):
    """
    Reads an XLS file, converts it to CSV, prints its head, shape, and column names.
    """
    try:
        # Read all sheets if the XLS file has multiple
        xls_file = pd.ExcelFile(xls_path)
        if not xls_file.sheet_names:
            print(f"No sheets found in {xls_path}")
            return

        print(f"Inspecting {xls_path}:")

        # For simplicity, we'll inspect the first sheet primarily
        # but save all sheets to separate CSVs if multiple exist.
        for i, sheet_name in enumerate(xls_file.sheet_names):
            print(f"\n--- Sheet: {sheet_name} ---")
            df = xls_file.parse(sheet_name)

            output_csv_path = csv_path
            if len(xls_file.sheet_names) > 1:
                # If multiple sheets, append sheet name to csv filename
                base, ext = csv_path.rsplit('.', 1)
                output_csv_path = f"{base}_{sheet_name.replace(' ', '_')}.{ext}"

            df.to_csv(output_csv_path, index=False, encoding='utf-8')
            print(f"Converted '{sheet_name}' to {output_csv_path}")

            print(f"Shape: {df.shape}")
            print(f"Columns: {df.columns.tolist()}")
            print("Head:")
            print(df.head())
            print("--- End of Sheet ---")

    except FileNotFoundError:
        print(f"Error: File not found at {xls_path}")
    except Exception as e:
        print(f"An error occurred while processing {xls_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python inspect_xls.py <path_to_xls_file> <path_to_output_csv_file>")
    else:
        xls_file_path = sys.argv[1]
        csv_file_path = sys.argv[2]
        inspect_xls_file(xls_file_path, csv_file_path)

import os
import pandas as pd

data_dir = r"D:\qlib_source_data_supplement_1min\stock_1min"

try:
    files = os.listdir(data_dir)
    print(f"Found {len(files)} files.")
    if files:
        # Filter for parquet files just in case
        parquet_files = [f for f in files if f.endswith('.parquet')]
        if not parquet_files:
            print("No parquet files found.")
        else:
            first_file = parquet_files[0]
            print(f"Reading first file: {first_file}")
            file_path = os.path.join(data_dir, first_file)
            
            # Read parquet
            try:
                df = pd.read_parquet(file_path)
                print("Columns:", df.columns.tolist())
                print(df.tail()) # Printing tail to see latest dates
                print("Index name:", df.index.name)
            except ImportError as ie:
                 print(f"ImportError: {ie}")
            except Exception as e:
                print(f"Error reading parquet: {e}")

except Exception as e:
    print(f"Error: {e}")

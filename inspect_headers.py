import pandas as pd
from pathlib import Path

file_path = Path("core/invoice_generator/JF25057.xlsx")

try:
    # Read the file, assuming header is at row 9 (0-indexed is 8) based on logs
    df = pd.read_excel(file_path, header=8)
    print("Headers at row 9:")
    print(df.columns.tolist())
    
    # Also print the first few rows to see data
    print("\nFirst 5 rows of data:")
    print(df.head())
except Exception as e:
    print(f"Error reading file: {e}")

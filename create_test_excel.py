import pandas as pd
import os
from datetime import datetime

# Create sample data
data = {
    'order_number': ['ORD001', 'ORD001', 'ORD002', 'ORD002'],
    'transaction_type': ['PICK', 'PICK', 'PICK', 'PICK'],
    'item': ['ITEM001', 'ITEM002', 'ITEM003', 'ITEM004'],
    'quantity': [5, 3, 2, 1]
}

# Create DataFrame
df = pd.DataFrame(data)

# Create the Files directory if it doesn't exist
watch_folder = r'C:\Cursor\RandexInt\Files'
if not os.path.exists(watch_folder):
    os.makedirs(watch_folder)

# Generate filename with timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f'test_order_{timestamp}.xlsx'
file_path = os.path.join(watch_folder, filename)

# Save to Excel
df.to_excel(file_path, index=False)
print(f"Test Excel file created: {filename}")
print("Column names:", list(df.columns))
print("\nSample data:")
print(df) 
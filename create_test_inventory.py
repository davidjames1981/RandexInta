import pandas as pd
import os
from datetime import datetime

# Create test data
test_data = {
    'Item': ['ITEM001', 'ITEM002', 'ITEM003', 'ITEM004', 'ITEM005'],
    'Description': [
        'Test Item 1 Description',
        'Test Item 2 Description',
        'Test Item 3 Description',
        'Test Item 4 Description',
        'Test Item 5 Description'
    ],
    'UOM': ['EA', 'BOX', 'EA', 'CASE', 'EA'],
    'CUS1': ['Custom1-A', 'Custom1-B', 'Custom1-C', 'Custom1-D', 'Custom1-E'],
    'CUS2': ['Custom2-A', 'Custom2-B', 'Custom2-C', 'Custom2-D', 'Custom2-E'],
    'CUS3': ['Custom3-A', 'Custom3-B', 'Custom3-C', 'Custom3-D', 'Custom3-E']
}

# Create DataFrame
df = pd.DataFrame(test_data)

# Create the inventory directory if it doesn't exist
inventory_dir = os.path.join('Files', 'Inventory')
if not os.path.exists(inventory_dir):
    os.makedirs(inventory_dir)

# Generate filename with timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f'test_inventory_{timestamp}.xlsx'
filepath = os.path.join(inventory_dir, filename)

# Save to Excel
df.to_excel(filepath, index=False)
print(f"Test inventory file created: {filepath}") 
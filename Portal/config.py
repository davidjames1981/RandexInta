# Task configuration choices
TASK_CHOICES = [
    ('Portal.tasks.import_order.process_excel_files', 'Excel - Order File Import'),
    ('Portal.tasks.api_order_creation.create_api_orders', 'API - Create Orders'),
    ('Portal.tasks.check_pick_status', 'API - Check Order Status'),
    ('Portal.tasks.import_inventory.process_inventory_files', 'Excel - Inventory File Import'),
    ('Portal.tasks.api_inventory.api_inventory_creation', 'API - Create Inventory API'),
    ('Portal.tasks.export_order.export_completed_orders', 'Excel - Order Export'),
    ('Portal.tasks.import_db_orders', 'DB - Order Import')
] 
from sqlalchemy import create_engine, text

# Create engine
engine = create_engine('postgresql://postgres:root@localhost/IMS')

# SQL statement to drop all tables
sql = '''
DROP TABLE IF EXISTS 
    order_items, 
    orders, 
    inventory_transactions, 
    stock_levels, 
    products, 
    warehouses, 
    audit_logs, 
    tenants, 
    sessions,
    tokens,
    user_roles,
    roles,
    users 
CASCADE;
'''

# Execute the SQL
with engine.connect() as conn:
    conn.execute(text(sql))
    conn.commit()
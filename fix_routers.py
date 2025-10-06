import re

def update_router_refs(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if "inventory.py" in file_path:
        content = content.replace("@router.", "@inventory_router.")
    elif "sales.py" in file_path:
        content = content.replace("@router.", "@sales_router.")
    elif "tenant.py" in file_path:
        content = content.replace("@router.", "@tenant_router.")
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

# Update the files
update_router_refs('api/v1/endpoints/inventory.py')
update_router_refs('api/v1/endpoints/sales.py')
update_router_refs('api/v1/endpoints/tenant.py')
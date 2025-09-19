"""Sample data for testing API endpoints"""

# Sample User Data
SAMPLE_USER_CREATE = {
    "email": "newuser@example.com",
    "password": "strongpass123",
    "full_name": "New Test User",
    "user_name": "newuser",
    "is_active": True,
    "role_names": ["user"],
    "permissions": ["read:items", "write:items"],
    "phone_number": "+1234567890"
}

SAMPLE_USER_UPDATE = {
    "full_name": "Updated User Name",
    "phone_number": "+9876543210",
    "role_names": ["user", "manager"],
    "permissions": ["read:items", "write:items", "delete:items"]
}

SAMPLE_USERS = [
    {
        "email": "manager@example.com",
        "password": "manager123",
        "full_name": "Test Manager",
        "user_name": "manager",
        "is_active": True,
        "role_names": ["manager"],
        "permissions": ["read:items", "write:items", "manage:users"],
        "phone_number": "+1122334455"
    },
    {
        "email": "staff@example.com",
        "password": "staff123",
        "full_name": "Test Staff",
        "user_name": "staff",
        "is_active": True,
        "role_names": ["staff"],
        "permissions": ["read:items", "write:items"],
        "phone_number": "+5544332211"
    },
    {
        "email": "readonly@example.com",
        "password": "readonly123",
        "full_name": "Read Only User",
        "user_name": "reader",
        "is_active": True,
        "role_names": ["reader"],
        "permissions": ["read:items"],
        "phone_number": "+9988776655"
    }
]

# Login Credentials for quick testing
TEST_CREDENTIALS = {
    "admin": {
        "username": "test@example.com",  # existing admin user
        "password": "testpassword"
    },
    "manager": {
        "username": "manager@example.com",
        "password": "manager123"
    },
    "staff": {
        "username": "staff@example.com",
        "password": "staff123"
    },
    "reader": {
        "username": "readonly@example.com",
        "password": "readonly123"
    }
}
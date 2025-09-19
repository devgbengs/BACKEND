import asyncio
import asyncpg
from urllib.parse import urlparse
from core.config import settings

async def create_database() -> None:
    """Create the database if it doesn't exist."""
    try:
        # Extract database name from URL
        db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
        parsed = urlparse(db_url)
        
        db_name = parsed.path.strip('/')
        db_host = parsed.hostname
        db_port = parsed.port or 5432
        db_user = parsed.username
        db_pass = parsed.password

        # Connect to default database
        sys_conn = await asyncpg.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_pass,
            database='postgres'
        )

        # Check if our database exists
        exists = await sys_conn.fetchval(
            'SELECT 1 FROM pg_database WHERE datname = $1',
            db_name
        )

        if not exists:
            # Database doesn't exist, create it
            await sys_conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Created database: {db_name}")
        else:
            print(f"Database {db_name} already exists")

        await sys_conn.close()
        
    except Exception as e:
        print(f"Error creating database: {str(e)}")
        raise e

if __name__ == "__main__":
    asyncio.run(create_database())
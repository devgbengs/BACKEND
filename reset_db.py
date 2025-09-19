from sqlalchemy import create_engine, text

def reset_database():
    # Create the engine
    engine = create_engine('postgresql://postgres:root@localhost/IMS')
    
    # Drop and recreate the schema
    with engine.begin() as conn:
        conn.execute(text('DROP SCHEMA public CASCADE'))
        conn.execute(text('CREATE SCHEMA public'))
        conn.execute(text('GRANT ALL ON SCHEMA public TO postgres'))
        print("Database reset complete.")

if __name__ == '__main__':
    reset_database()
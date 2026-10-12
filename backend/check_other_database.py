from sqlalchemy import create_engine, text
from app.core.config import get_settings

database_url = get_settings().database_url
postgres_url = database_url.replace(
    "/lenny_assistant",
    "/postgres",
)

engine = create_engine(postgres_url)

try:
    with engine.connect() as connection:
        print("Connected to:", connection.execute(
            text("SELECT current_database()")
        ).scalar())

        for table in ("chat_sessions", "messages", "artifacts"):
            exists = connection.execute(
                text("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name = :table_name
                    )
                """),
                {"table_name": table},
            ).scalar()

            print(f"{table} table exists: {exists}")

            if exists:
                count = connection.execute(
                    text(f'SELECT COUNT(*) FROM public."{table}"')
                ).scalar()
                print(f"{table} row count: {count}")
finally:
    engine.dispose()
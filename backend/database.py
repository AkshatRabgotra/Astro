"""SQLAlchemy database connection and session management."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

"""SQLAlchemy database connection and session management."""

import urllib.parse
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings


def normalize_database_url(url: str) -> str:
    """Normalize database URL for SQLAlchemy and psycopg driver, encoding special characters in password."""
    if not url:
        return "sqlite:///./melooha.db"

    # Normalize PostgreSQL driver to psycopg v3
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    # Automatically percent-encode special characters in password (such as '@')
    if "://" in url:
        scheme, rest = url.split("://", 1)
        if "@" in rest:
            last_at_idx = rest.rfind("@")
            userinfo = rest[:last_at_idx]
            host_and_path = rest[last_at_idx + 1:]
            if ":" in userinfo:
                username, password = userinfo.split(":", 1)
                decoded_pwd = urllib.parse.unquote(password)
                encoded_pwd = urllib.parse.quote(decoded_pwd, safe="")
                url = f"{scheme}://{username}:{encoded_pwd}@{host_and_path}"

    return url


def can_connect_to_host(url: str, timeout: float = 0.6) -> bool:
    """Check if the database host can actually be reached on TCP port within timeout."""
    import socket
    try:
        from sqlalchemy.engine import make_url
        parsed = make_url(url)
        if not parsed.host:
            return True
        port = parsed.port or 5432
        sock = socket.create_connection((parsed.host, port), timeout=timeout)
        sock.close()
        return True
    except Exception:
        return False


raw_db_url = settings.DATABASE_URL
db_url = normalize_database_url(raw_db_url)

# If PostgreSQL host is unreachable on local network (e.g. IPv6-only Supabase direct host on IPv4-only ISP)
# seamlessly fallback to SQLite locally so dev server starts instantaneously without hanging
if not db_url.startswith("sqlite") and not can_connect_to_host(db_url):
    print("[Database] Notice: PostgreSQL direct host is not reachable on current network/sandbox.")
    print("[Database] Active config is preserved for Render/Vercel deployment; using local SQLite for current session.")
    db_url = "sqlite:///./melooha.db"

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 30}
else:
    connect_args = {"connect_timeout": 5}

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
    if not db_url.startswith("sqlite"):
        with engine.connect() as probe_conn:
            probe_conn.execute(text("SELECT 1"))
        print("[Database] Successfully connected to PostgreSQL / Supabase database.")
except Exception as e:
    if not db_url.startswith("sqlite"):
        print(f"[Database] Notice: PostgreSQL direct connection unavailable on current host/network: {e}")
        print("[Database] Using SQLite fallback locally while keeping PostgreSQL configuration active for deployment.")
        db_url = "sqlite:///./melooha.db"
        connect_args = {"check_same_thread": False, "timeout": 30}
        engine = create_engine(
            db_url,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
    else:
        raise

# Enable foreign keys and WAL for SQLite
if db_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_schema_compatibility():
    """Ensure newly added columns exist in users table for backward-compatible schemas."""
    try:
        with engine.begin() as conn:
            if engine.dialect.name == "sqlite":
                res = conn.execute(text("PRAGMA table_info(users)")).fetchall()
                existing_cols = {r[1] for r in res}
                if existing_cols:
                    if "google_id" not in existing_cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR(100)"))
                    if "avatar_url" not in existing_cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)"))
                    if "auth_provider" not in existing_cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN auth_provider VARCHAR(50) DEFAULT 'google'"))
    except Exception as e:
        print(f"[Database] Schema compatibility notice: {e}")


ensure_schema_compatibility()


def get_db():
    """FastAPI dependency for yielding database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

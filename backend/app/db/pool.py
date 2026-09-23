from psycopg_pool import ConnectionPool

from app.core.config import settings


pool = ConnectionPool(
    conninfo=settings.database_url.replace(
        "postgresql+psycopg://",
        "postgresql://",
    ),
    min_size=1,
    max_size=5,
    open=False,
)
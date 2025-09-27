"""
Database configuration for Postgres (Supabase-compatible).

Handles database connection settings and provides utilities
for database management.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class DatabaseConfig(BaseModel):
    """
    Database configuration settings for Postgres/Supabase.
    """
    
    # Connection settings (DSN)
    url: str = Field(
        "postgresql://postgres:postgres@supabase-db:5432/paperclip",
        description="Postgres connection URL (DSN)",
    )
    
    # Connection pooling
    min_connections: int = Field(1, description="Minimum connections in pool")
    max_connections: int = Field(10, description="Maximum connections in pool")
    connection_timeout: int = Field(30, description="Connection timeout in seconds")
    
    # Query settings
    query_timeout: int = Field(60, description="Query timeout in seconds")
    
    # Migration settings
    migrations_dir: str = Field("migrations", description="Migrations directory")
    auto_migrate: bool = Field(True, description="Auto-run migrations on startup")
    
    @field_validator("url")
    def validate_url(cls, v):
        """Validate database URL format.

        Allow only Postgres DSNs (postgres/postgresql).
        """
        allowed_prefixes = ("postgres://", "postgresql://")
        if not v.startswith(allowed_prefixes):
            raise ValueError(
                "Database URL must start with postgres:// or postgresql://"
            )
        return v
    
    @field_validator("min_connections", "max_connections")
    def validate_connections(cls, v):
        """Validate connection pool settings."""
        if v < 1:
            raise ValueError("Connection pool size must be at least 1")
        return v
    
    @field_validator("max_connections")
    def validate_max_connections(cls, v, info):
        """Ensure max_connections >= min_connections."""
        values = info.data
        if "min_connections" in values and v < values["min_connections"]:
            raise ValueError("max_connections must be >= min_connections")
        return v
    
    def get_connection_url(self) -> str:
        """Get full database connection URL (as provided)."""
        return self.url
    
    def get_connection_params(self) -> dict:
        """Get connection parameters for async clients (placeholder)."""
        return {"dsn": self.url, "timeout": self.connection_timeout}
    
    # Note: env loading for nested settings is handled by Settings via env_nested_delimiter

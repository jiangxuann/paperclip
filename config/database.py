"""
Database configuration for SurrealDB.

Handles database connection settings and provides utilities
for database management.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator


class DatabaseConfig(BaseModel):
    """
    Database configuration settings.
    
    Supports SurrealDB with connection pooling and authentication.
    """
    
    # Connection settings
    url: str = Field("surrealdb://localhost:8000", description="Database URL")
    namespace: str = Field("paperclip", description="Database namespace")
    database: str = Field("main", description="Database name")
    
    # Authentication
    username: str = Field("root", description="Database username")
    password: str = Field("root", description="Database password")
    
    # Connection pooling
    min_connections: int = Field(1, description="Minimum connections in pool")
    max_connections: int = Field(10, description="Maximum connections in pool")
    connection_timeout: int = Field(30, description="Connection timeout in seconds")
    
    # Query settings
    query_timeout: int = Field(60, description="Query timeout in seconds")
    
    # Migration settings
    migrations_dir: str = Field("migrations", description="Migrations directory")
    auto_migrate: bool = Field(True, description="Auto-run migrations on startup")
    
    @validator("url")
    def validate_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(("surrealdb://", "ws://", "wss://", "http://", "https://")):
            raise ValueError("Database URL must start with surrealdb://, ws://, wss://, http://, or https://")
        return v
    
    @validator("min_connections", "max_connections")
    def validate_connections(cls, v):
        """Validate connection pool settings."""
        if v < 1:
            raise ValueError("Connection pool size must be at least 1")
        return v
    
    @validator("max_connections")
    def validate_max_connections(cls, v, values):
        """Ensure max_connections >= min_connections."""
        if "min_connections" in values and v < values["min_connections"]:
            raise ValueError("max_connections must be >= min_connections")
        return v
    
    def get_connection_url(self) -> str:
        """Get full database connection URL with authentication."""
        # Parse base URL
        if "://" in self.url:
            protocol, rest = self.url.split("://", 1)
        else:
            protocol = "surrealdb"
            rest = self.url
        
        # Add authentication if not already present
        if "@" not in rest:
            auth_part = f"{self.username}:{self.password}@"
            rest = auth_part + rest
        
        # Add namespace and database
        if "?" in rest:
            base_url, params = rest.split("?", 1)
            full_url = f"{protocol}://{base_url}/{self.namespace}/{self.database}?{params}"
        else:
            full_url = f"{protocol}://{rest}/{self.namespace}/{self.database}"
        
        return full_url
    
    def get_connection_params(self) -> dict:
        """Get connection parameters for SurrealDB client."""
        return {
            "url": self.url,
            "namespace": self.namespace,
            "database": self.database,
            "username": self.username,
            "password": self.password,
            "timeout": self.connection_timeout,
        }
    
    class Config:
        env_prefix = "DATABASE_"

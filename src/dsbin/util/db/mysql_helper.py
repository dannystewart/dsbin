from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from logician import Logician

from dsbin.util.db import DatabaseError, QueryResult

if TYPE_CHECKING:
    from collections.abc import Generator
    from logging import Logger

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    from mysql.connector import MySQLConnection
    from mysql.connector.pooling import MySQLConnectionPool, PooledMySQLConnection

    mysql_available = True
except ImportError:
    mysql_available = False

T = TypeVar("T")


@dataclass
class MySQLHelper:
    """Helper class for interacting with MySQL databases."""

    POOL_SIZE: ClassVar[int] = max(os.cpu_count() or 4 * 4, 32)

    host: str
    user: str
    password: str
    database: str
    charset: str = "utf8mb4"
    collation: str = "utf8mb4_general_ci"
    _pool: MySQLConnectionPool | None = None

    logger: Logger = field(init=False)

    def __post_init__(self):
        self.logger = Logician.get_logger()
        if not mysql_available:
            msg = (
                "MySQL functionality requires the mysql-connector-python package. "
                "Install it with: pip install 'dsbin[database]'"
            )
            self.logger.error(msg)
            raise ImportError(msg)

    @property
    def pool(self) -> MySQLConnectionPool:
        """Lazy initialization of MySQL connection pool.

        Raises:
            DatabaseError: If the database connection fails.
        """
        if self._pool is None:
            try:
                self._pool = MySQLConnectionPool(
                    pool_size=self.POOL_SIZE,
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset=self.charset,
                    collation=self.collation,
                )
            except MySQLError as e:
                self.logger.critical("Failed to initialize database pool: %s", str(e))
                msg = "Failed to initialize database connection. Check MySQL connection."
                raise DatabaseError(msg) from e
        return self._pool

    def fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> QueryResult[dict[str, Any]]:
        """Fetch a single row from the database.

        Args:
            query: The SQL query to execute.
            params: The query parameters as a tuple.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            conn = self.pool.get_connection()
            try:
                with conn.cursor(prepared=True) as cur:
                    cur.execute(query, params)
                    if cur.description is None:
                        return QueryResult(data=None, affected_rows=0)

                    columns = [col[0] for col in cur.description]
                    if row := cur.fetchone():
                        return QueryResult(
                            data=dict(zip(columns, row, strict=False)),
                            affected_rows=cur.rowcount,
                        )
                    return QueryResult(data=None, affected_rows=0)
            finally:
                conn.close()
        except mysql.connector.Error as e:
            msg = f"Database error: {e!s}"
            raise DatabaseError(msg) from e

    def fetch_many(
        self, query: str, params: tuple[Any, ...] = ()
    ) -> QueryResult[list[dict[str, Any]]]:
        """Fetch multiple rows from the database.

        Args:
            query: The SQL query to execute.
            params: The query parameters as a tuple.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            conn = self.pool.get_connection()
            try:
                with conn.cursor(prepared=True) as cur:
                    cur.execute(query, params)
                    if cur.description is None:
                        return QueryResult(data=[], affected_rows=0)

                    columns = [col[0] for col in cur.description]
                    rows = cur.fetchall()
                    return QueryResult(
                        data=[dict(zip(columns, row, strict=False)) for row in rows],
                        affected_rows=cur.rowcount,
                    )
            finally:
                conn.close()
        except mysql.connector.Error as e:
            msg = f"Database error: {e!s}"
            raise DatabaseError(msg) from e

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> QueryResult[None]:
        """Execute a write operation.

        Args:
            query: The SQL query to execute.
            params: The query parameters as a tuple.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            with self.transaction() as conn, conn.cursor(prepared=True) as cur:
                cur.execute(query, params)
                affected = cur.rowcount

                return QueryResult(data=None, affected_rows=affected)
        except mysql.connector.Error as e:
            msg = f"Database error: {e!s}"
            raise DatabaseError(msg) from e

    @contextmanager
    def transaction(self) -> Generator[MySQLConnection | PooledMySQLConnection, None, None]:
        """Context manager for managing database transactions.

        Yields:
            MySQLConnection | PooledMySQLConnection: The database connection.
        """
        conn = self.pool.get_connection()
        try:
            conn.start_transaction()
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def close(self) -> None:
        """Close all connections in the pool."""
        if self._pool:
            while True:
                try:
                    conn = self._pool.get_connection()
                    conn.close()
                except MySQLError:
                    break
            self._pool = None

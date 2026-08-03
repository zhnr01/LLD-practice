# P08 - Pluggable Logger
#
# Key pattern: Composite + Strategy
# CompositeLogger is a LogBackend that holds a list of LogBackends.
# It fans out every write() call to all of them.
# This is the Composite pattern: a single object that behaves like a collection.
#
# Why Protocol over ABC here:
# Same reasoning as P07. DatabaseLogger depends on a Database Protocol from P06.
# Nothing forces external database adapters to inherit from our class.

from __future__ import annotations
from enum import IntEnum
from typing import Protocol
from datetime import datetime


# ------------------------------------------------------------------
# Log levels: IntEnum so you can compare (DEBUG < INFO < ERROR)
# ------------------------------------------------------------------

class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40


# ------------------------------------------------------------------
# Abstraction: the shape every backend must satisfy
# ------------------------------------------------------------------

class LogBackend(Protocol):
    """What CompositeLogger needs from any backend.
    Reason to change: logging contract changes (e.g. add context dict)."""

    def write(self, level: LogLevel, message: str) -> None: ...


# ------------------------------------------------------------------
# Concrete backends: one class, one destination, one reason to change
# ------------------------------------------------------------------

class ConsoleLogger:
    """Owns: writing formatted log lines to stdout.
    Reason to change: console output format changes (add color, change timestamp format)."""

    def write(self, level: LogLevel, message: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [{level.name:<7}] {message}")


class FileLogger:
    """Owns: writing log lines to a file on disk.
    Reason to change: file format, path convention, or rotation policy changes."""

    def __init__(self, file_path: str):
        self._path = file_path

    def write(self, level: LogLevel, message: str) -> None:
        with open(self._path, "a") as f:
            ts = datetime.now().isoformat()
            f.write(f"[{ts}] [{level.name}] {message}\n")


# Reusing the Database Protocol from P06 here.
# DatabaseLogger does not care if it is MySQL, Postgres, or InMemory.
class Database(Protocol):
    def save(self, data: dict) -> None: ...


class DatabaseLogger:
    """Owns: persisting log records to a database.
    Reason to change: log table schema or database interaction changes.
    DIP: depends on Database abstraction, not on any concrete DB driver."""

    def __init__(self, db: Database):
        self._db = db

    def write(self, level: LogLevel, message: str) -> None:
        self._db.save({
            "level": level.name,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })


# ------------------------------------------------------------------
# CompositeLogger: the main pattern in this problem
# ------------------------------------------------------------------

class CompositeLogger:
    """Owns: fanning a single log call out to multiple backends.
    Reason to change: fan-out strategy changes (add filtering by level, async writes).

    Composite pattern: CompositeLogger IS a LogBackend AND holds a list of LogBackends.
    This means you can nest CompositeLoggers inside each other if needed.

    OCP: adding a new backend requires zero edits here.
    DIP: depends on LogBackend abstraction. Never imports ConsoleLogger or FileLogger."""

    def __init__(self, backends: list[LogBackend]):
        self._backends = backends

    def write(self, level: LogLevel, message: str) -> None:
        for backend in self._backends:
            backend.write(level, message)

    # Convenience methods so callers do not have to import LogLevel
    def debug(self, message: str) -> None:
        self.write(LogLevel.DEBUG, message)

    def info(self, message: str) -> None:
        self.write(LogLevel.INFO, message)

    def warning(self, message: str) -> None:
        self.write(LogLevel.WARNING, message)

    def error(self, message: str) -> None:
        self.write(LogLevel.ERROR, message)


# ------------------------------------------------------------------
# Fake backend for testing
# ------------------------------------------------------------------

class FakeLogger:
    """Captures log calls in memory. Use in tests to assert what was logged."""

    def __init__(self):
        self.records: list[tuple[LogLevel, str]] = []

    def write(self, level: LogLevel, message: str) -> None:
        self.records.append((level, message))


# ------------------------------------------------------------------
# Composition root
# ------------------------------------------------------------------

if __name__ == "__main__":
    console = ConsoleLogger()
    file_log = FileLogger("app.log")

    logger = CompositeLogger([console, file_log])

    logger.info("Application started")
    logger.warning("Disk usage above 80%")
    logger.error("Database connection failed")
    logger.debug("Request received: GET /health")

    print()

    # Testing: verify logs are captured correctly without real files or DBs
    fake = FakeLogger()
    test_logger = CompositeLogger([fake])
    test_logger.error("Something broke")
    assert fake.records[0] == (LogLevel.ERROR, "Something broke")
    print("Test passed.")

    # Nested Composite: all production logs AND a separate error-only file
    # error_file = FileLogger("errors.log")
    # full_logger = CompositeLogger([console, file_log])
    # you could add a FilteringLogger wrapper that only passes ERROR+ to error_file
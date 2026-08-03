from typing import Protocol


# ORIGINAL PROBLEM: ProductService directly instantiated MySQLDatabase() inside __init__.
# That means:
#   1. You cannot unit test ProductService without a real MySQL connection.
#   2. To switch to Postgres, you have to edit ProductService itself (OCP violation too).
#   3. High-level module (ProductService) depends on low-level module (MySQLDatabase). DIP violated.
#
# THE FIX: define a Database Protocol. Make MySQLDatabase satisfy it.
# Inject the database into ProductService. ProductService never imports or knows about MySQL.


# Step 1: Define the abstraction. This is what ProductService NEEDS, not what MySQL provides.
# ProductService owns this interface, not MySQL.
class Database(Protocol):
    def save(self, data: dict) -> None: ...
    def find(self, query: str) -> dict: ...


# Step 2: Low-level detail satisfies the abstraction.
# MySQLDatabase does not inherit from Database. It just has the right shape (structural typing).
class MySQLDatabase:
    def save(self, data: dict) -> None:
        print(f"[MySQL] Saving {data}")

    def find(self, query: str) -> dict:
        print(f"[MySQL] Finding {query}")
        return {}


# You can now add any other database without touching ProductService.
class PostgresDatabase:
    def save(self, data: dict) -> None:
        print(f"[Postgres] Saving {data}")

    def find(self, query: str) -> dict:
        print(f"[Postgres] Finding {query}")
        return {}


# For tests: a fake in-memory database. No real DB needed.
class InMemoryDatabase:
    def __init__(self):
        self._store: dict = {}

    def save(self, data: dict) -> None:
        self._store[data.get("name")] = data

    def find(self, query: str) -> dict:
        return self._store.get(query, {})


# Step 3: High-level module depends on the abstraction, not on MySQL.
# FIX: __init__ now receives a Database, it does not create one.
class ProductService:
    def __init__(self, db: Database):    # injected, not coupled
        self.db = db

    def create_product(self, name: str, price: float) -> None:
        self.db.save({"name": name, "price": price})

    def get_product(self, name: str) -> dict:
        return self.db.find(name)


# Step 4: Composition root. The only place in the entire codebase that knows
# which concrete database is being used. Everything else works through the Protocol.
service = ProductService(MySQLDatabase())
service.create_product("keyboard", 49.99)
print(service.get_product("keyboard"))

# Switching to Postgres: one line change here, zero changes anywhere else.
# service = ProductService(PostgresDatabase())

# Testing without a real DB: inject the fake.
# service = ProductService(InMemoryDatabase())
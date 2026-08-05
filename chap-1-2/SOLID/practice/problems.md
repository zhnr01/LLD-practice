# LLD Practice Problems — Ch. 1 & 2

> Solve each problem in a separate `.py` file inside this folder.
> Folder naming convention: `p01_encapsulation.py`, `p02_polymorphism.py`, etc.

---

## Level 1 — Single Concept Drills

These isolate one principle at a time. One class, one problem.

---

### P01 — Encapsulation

**File:** `p01_encapsulation.py`

A `TemperatureSensor` class stores temperature readings internally as a list of floats in Celsius.

**Requirements:**
- Callers can add a new reading via `record(celsius: float)`
- Callers can get the latest reading via a `latest` property
- Callers can get the average of all readings via an `average` property
- Callers **cannot** directly access or modify the internal list
- Callers **cannot** set `latest` or `average` directly (read-only)
- `record()` should raise `ValueError` if the temperature is below absolute zero (-273.15°C)

**What this tests:** Proper use of `_private` state, `@property`, input validation.

---

### P02 — Replace a Conditional Ladder with Polymorphism

**File:** `p02_polymorphism.py`

You are given this broken code:

```python
def send_notification(channel: str, message: str) -> None:
    if channel == "email":
        print(f"[EMAIL] {message}")
    elif channel == "sms":
        print(f"[SMS] {message}")
    elif channel == "push":
        print(f"[PUSH] {message}")
    else:
        raise ValueError(f"Unknown channel: {channel}")
```

**Requirements:**
- Replace this function with a `Notifier` Protocol
- Implement `EmailNotifier`, `SMSNotifier`, `PushNotifier` — each a separate class, no inheritance from each other
- Write a `notify(notifier: Notifier, message: str)` function that has no `if/elif` inside it
- Adding a new channel (e.g. `SlackNotifier`) should require adding **only one new class**, no edits to existing code

**What this tests:** Polymorphism replacing conditional ladders, Protocol usage, OCP.

---

### P03 — SRP Violation Fix

**File:** `p03_srp.py`

You are given this class. It violates SRP. Your job is to identify how many responsibilities it has and split it.

```python
class UserManager:
    def __init__(self, db_conn, smtp_client):
        self.db = db_conn
        self.smtp = smtp_client

    def register(self, email: str, password: str) -> None:
        hashed = self._hash(password)
        self.db.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed)
        )
        self.smtp.send(
            to=email,
            subject="Welcome!",
            body="Your account has been created."
        )
        print(f"[LOG] User registered: {email}")

    def login(self, email: str, password: str) -> bool:
        row = self.db.execute("SELECT password FROM users WHERE email=?", (email,))
        return row and row[0] == self._hash(password)

    def _hash(self, password: str) -> str:
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
```

**Requirements:**
- Apply the "And" test and noun grouping to identify responsibilities
- Split into the correct number of classes, each with one clear reason to change
- No single class should have more than one "and" in its description
- Keep all the same behavior — just reorganize it

**What this tests:** SRP, responsibility counting hacks, clean class decomposition.

---

### P04 — LSP Violation Fix

**File:** `p04_lsp.py`

You are given this hierarchy:

```python
class Bird:
    def fly(self) -> str:
        return "flying"

    def eat(self) -> str:
        return "eating"

class Penguin(Bird):
    def fly(self) -> str:
        raise NotImplementedError("Penguins cannot fly")
```

**Requirements:**
- Fix this so `Penguin` no longer violates LSP
- Any code that accepts a `Bird` must work correctly with all subtypes
- `Penguin` should still have an `eat()` method
- You may redesign the hierarchy completely if needed
- Hint: think about what contract `Bird` is actually making

**What this tests:** LSP, when inheritance is wrong, interface segregation thinking.

---

### P05 — Interface Segregation

**File:** `p05_isp.py`

You are given this fat interface:

```python
from abc import ABC, abstractmethod

class Worker(ABC):
    @abstractmethod
    def work(self): ...

    @abstractmethod
    def eat(self): ...

    @abstractmethod
    def sleep(self): ...

class HumanWorker(Worker):
    def work(self): print("Human working")
    def eat(self): print("Human eating")
    def sleep(self): print("Human sleeping")

class RobotWorker(Worker):
    def work(self): print("Robot working")
    def eat(self): raise NotImplementedError("Robots don't eat")
    def sleep(self): raise NotImplementedError("Robots don't sleep")
```

**Requirements:**
- Segregate the `Worker` interface into the minimum number of role interfaces needed
- `HumanWorker` should implement all relevant roles
- `RobotWorker` should implement only what it actually does
- No class should have a `NotImplementedError` method

**What this tests:** ISP, role interface design, avoiding fat interfaces.

---

### P06 — Dependency Inversion

**File:** `p06_dip.py`

You are given this code that violates DIP:

```python
class MySQLDatabase:
    def save(self, data: dict) -> None:
        print(f"[MySQL] Saving {data}")

    def find(self, query: str) -> dict:
        print(f"[MySQL] Finding {query}")
        return {}

class ProductService:
    def __init__(self):
        self.db = MySQLDatabase()    # directly coupled

    def create_product(self, name: str, price: float) -> None:
        self.db.save({"name": name, "price": price})

    def get_product(self, name: str) -> dict:
        return self.db.find(name)
```

**Requirements:**
- Define a `Database` abstraction (ABC or Protocol, your choice)
- Refactor `ProductService` to depend on the abstraction
- Implement `MySQLDatabase` and `InMemoryDatabase` (a fake for tests) both implementing the abstraction
- Write a simple test that uses `InMemoryDatabase` without touching a real database

**What this tests:** DIP, dependency injection, testability, ABC vs Protocol choice.

---

## Level 2 — Combined Concepts

These require applying two or more principles together.

---

### P07 — Notification Service Design

**File:** `p07_notification_service.py`

Design a notification service from scratch for an e-commerce platform.

**Requirements:**
- Support `Email`, `SMS`, and `WhatsApp` channels
- Each channel has its own configuration (email needs SMTP credentials, SMS needs API key, etc.)
- A `NotificationService` class should accept a list of channels and send a message to all of them
- Adding a new channel should require zero edits to `NotificationService`
- The service must be testable with fake channels (no real sending in tests)
- Each channel class should have exactly one responsibility

**Constraints:**
- Apply SRP, OCP, and DIP together
- Use Protocol or ABC for the channel abstraction, justify your choice
- No `if/elif` anywhere in the service logic

**What this tests:** SRP + OCP + DIP combined, Strategy-like design.

---

### P08 — Pluggable Logger

**File:** `p08_logger.py`

Design a logging system that can write to multiple backends.

**Requirements:**
- Support `ConsoleLogger`, `FileLogger`, and `DatabaseLogger`
- A `Logger` interface that all backends implement
- Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- A `CompositeLogger` that fans out a single log call to multiple backends
- `FileLogger` should write to a file path passed at construction time
- `DatabaseLogger` should accept any `Database` abstraction (reuse P06 if you want)

**Constraints:**
- `CompositeLogger` must not know about any concrete logger class
- Adding a new backend requires zero changes to `CompositeLogger`
- Apply SRP — each class has one reason to change

**What this tests:** OCP, SRP, DIP, composition over inheritance.

---

## Level 3 — Mini LLD Problems

These simulate real interview-style problems. Scope, design, then code.

---

### P09 — Vending Machine

**File:** `p09_vending_machine.py`

Design the core logic of a vending machine.

**Requirements:**
- Products: each product has a name, price, and quantity in stock
- A user can insert coins (accept any denomination)
- A user can select a product
- The machine dispenses the product and returns change if the inserted amount exceeds price
- If the product is out of stock, it should inform the user
- If the inserted amount is insufficient, it should inform the user
- The machine should be able to refill products (admin operation)

**Constraints:**
- At least three clearly separated responsibilities
- No `if/elif` chain for deciding machine behavior based on some `state` string — use polymorphism or OOP state management
- Every class must pass the "And" test with at most one "and"

**Deliverable:** Class diagram comment at the top of the file (even a text ASCII diagram is fine), then skeleton code.

**What this tests:** SRP, OCP, encapsulation, decomposition thinking.

---

### P10 — Parking Lot

**File:** `p10_parking_lot.py`

Design the core of a parking lot system.

**Requirements:**
- Parking lot has multiple floors, each floor has multiple spots
- Spot types: `Compact`, `Large`, `Motorcycle`
- A vehicle enters and gets assigned the nearest available spot matching its type
- A vehicle exits and the spot is freed
- The system can report: total spots, available spots, occupied spots (by type)
- Vehicles: `Car` (needs Compact or Large), `Truck` (needs Large), `Motorcycle` (needs Motorcycle)

**Constraints:**
- Spot assignment logic must be extensible — adding a new vehicle type should not require modifying existing spot or floor classes
- Apply SRP: `ParkingSpot`, `Floor`, `ParkingLot`, `Vehicle` should each have clear, single responsibilities
- Justify every design decision in a comment above each class

**Deliverable:** ASCII class diagram at the top of the file, then skeleton code with docstrings.

**What this tests:** SRP, OCP, LSP (vehicle substitution), encapsulation, real LLD interview problem.

---

## Grading Yourself

For each problem, review your solution against these questions:

1. Can I describe every class in one sentence without using "and" more than once?
2. If a new variant is needed, do I add a new class or edit an existing one?
3. Does every `__init__` have 3 or fewer dependencies?
4. Is there any `if/elif` chain I could replace with polymorphism?
5. Can I swap a fake implementation in for testing without changing production code?

If all five are yes, the solution is solid.
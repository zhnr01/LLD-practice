# LLD Design Mastery — Personal Notes

> Source: LLD Design Mastery Book (Ch. 1–2) + Interview Prep Sessions

---

## Chapter 1 — Introduction to LLD

### What is LLD?

LLD translates an abstract problem into **concrete, code-ready class and component structures**.

The key question LLD answers: *how is each module structured internally* — its classes, interfaces, methods, relationships, state machines, and contracts.

---

### LLD vs HLD vs System Design

These are different **zoom levels** of the same system. Conflating them costs candidates offers.

| Dimension | HLD / System Design | LLD |
|---|---|---|
| Primary unit | Service, queue, database, cache | Class, interface, method |
| Key questions | Throughput? Latency? Availability? | Extensible? Testable? SOLID? |
| Diagrams | Architecture, data flow, deployment | Class, sequence, state, activity |
| Output | Capacity plan, topology, API contracts | Skeleton code, class diagram |
| Interview length | 45–60 min | 45–90 min |
| Tooling mindset | Kafka, Redis, sharding, CDN | Design patterns, SOLID, UML |

**Concrete example:** System design asks you to design Uber end-to-end. LLD asks you to design only the Trip matching engine or only the Pricing service.

---

### LLD Interview Deliverables

**Three artifacts:**
1. Class diagram — structural skeleton
2. Sequence diagram — for the most complex interaction (usually one with concurrency or external calls)
3. Skeleton code — in your strongest language

**Plus one ongoing dialogue** — constant narration of trade-offs:
> "I am introducing a Strategy here because pricing rules vary by region. If we later need to combine rules, I would upgrade to Chain of Responsibility."

The dialogue is the actual product. The artifacts are just receipts.

---

### Three Failure Modes Interviewers Flag

1. Jumping into code before agreeing on requirements
2. Inventing god-classes that do everything
3. Never naming the design patterns being applied

### Opening Ritual (signals seniority)

Say this at the start of every LLD round:

> "Before I design, let me confirm scope. Who are the actors? What are the top three flows? What can I assume is out of scope?"

This 30-second ritual protects you from designing the wrong system.

---

## The Four Pillars of OOP

Treat these as **design levers** you actively pull, not vocabulary to recite.

---

### 1. Encapsulation

Bundle state with the methods that operate on it. Hide internal representation behind a stable public interface.

**Why it matters:** When internal representation changes (list → dict, float → Decimal), only the class changes. Every caller keeps working.

```python
class BankAccount:
    def __init__(self, owner: str, initial_balance: float = 0.0):
        self.owner = owner
        self._balance = initial_balance         # protected by convention
        self._transactions: list[float] = []    # internal state — hidden

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("amount must be positive")
        self._balance += amount
        self._transactions.append(amount)

    def withdraw(self, amount: float) -> None:
        if amount > self._balance:
            raise ValueError("insufficient funds")
        self._balance -= amount
        self._transactions.append(-amount)

    @property
    def balance(self) -> float:
        return self._balance  # read-only view, callers cannot mutate directly
```

> **Rule:** Internal state is private. Only behaviours are public.

---

### 2. Abstraction

Expose **what** an object does, not **how** it does it.

- Encapsulation hides **state**.
- Abstraction hides **implementation complexity**.

```python
from abc import ABC, abstractmethod

class PaymentProcessor(ABC):
    """Clients depend on this interface, not on Stripe or PayPal."""
    @abstractmethod
    def charge(self, amount: float, currency: str) -> str: ...

class StripeProcessor(PaymentProcessor):
    def charge(self, amount: float, currency: str) -> str:
        # 30 lines of Stripe SDK glue — hidden from the caller
        return f"stripe_charge_{amount}{currency}"

class PaypalProcessor(PaymentProcessor):
    def charge(self, amount: float, currency: str) -> str:
        return f"paypal_charge_{amount}{currency}"

# Caller depends only on the abstraction
def checkout(processor: PaymentProcessor, total: float) -> str:
    return processor.charge(total, "USD")
```

---

### 3. Inheritance

Models an **is-a** relationship. A `SavingsAccount` is-a `BankAccount`.

> **Warning:** Most overused and dangerous pillar. Deep hierarchies become rigid and fragile. Prefer **composition (has-a)** over **inheritance (is-a)**. Two or three levels is fine. Five levels is almost always a bug.

```python
class SavingsAccount(BankAccount):
    def __init__(self, owner: str, balance: float = 0.0, rate: float = 0.02):
        super().__init__(owner, balance)
        self.rate = rate

    def withdraw(self, amount: float) -> None:
        if amount > 500:
            raise ValueError("Savings withdrawal limit is 500")
        super().withdraw(amount)
```

---

### 4. Polymorphism

Same call site, different behavior at runtime. Greek for "many forms."

**Two flavors:**
- **Subtype polymorphism** — base reference holding a derived object
- **Parametric polymorphism** — generics, same code works for any type

**The key LLD insight:** Polymorphism exists to **replace conditional ladders**.

```python
# BAD — conditional ladder
def apply_discount(discount_type: str, total: float) -> float:
    if discount_type == "none":
        return total
    elif discount_type == "percentage":
        return total * 0.9
    elif discount_type == "bogo":
        return total / 2
    # adding "loyalty" = edit this function forever

# GOOD — polymorphism
from typing import Protocol

class Discount(Protocol):
    def apply(self, total: float) -> float: ...

class NoDiscount:
    def apply(self, total: float) -> float:
        return total

class PercentageOff:
    def __init__(self, pct: float): self.pct = pct
    def apply(self, total: float) -> float: return total * (1 - self.pct)

class BuyOneGetOneFree:
    def apply(self, total: float) -> float: return total / 2

# One call site. No if/elif. New discount = new class, zero edits to existing code.
def price_cart(total: float, discount: Discount) -> float:
    return discount.apply(total)
```

---

### ABC vs Protocol

Python gives you two tools to express abstraction. Know when to use each.

| | ABC | Protocol |
|---|---|---|
| Contract style | Explicit — must inherit | Implicit — just have the methods |
| Works with external classes | No | Yes |
| Runtime `isinstance` | Yes | Only with `@runtime_checkable` |
| Best for | Internal class hierarchies | Interface definitions, loose coupling |

**Use ABC** when defining a family of related classes you control: `PaymentMethod`, `Shape`, `Notification`.

**Use Protocol** when defining what a function *needs* from its input, especially when types can come from anywhere.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Drawable(Protocol):
    def draw(self) -> None: ...

class Circle:       # no inheritance needed
    def draw(self): print("drawing circle")

class Square:       # no inheritance needed
    def draw(self): print("drawing square")

def render(shape: Drawable):
    shape.draw()

# Works for both, mypy is happy, isinstance works too
print(isinstance(Circle(), Drawable))  # True
```

---

## Chapter 2 — SOLID Principles

SOLID bundles five principles that describe what good OO structure looks like at the class and component level.

---

### S — Single Responsibility Principle (SRP)

> A class should have one, and only one, reason to change.

"Reason to change" maps to **actor** — who in the organisation asks for a change to this class.

**Classic violation — God Object:**

```python
# BAD — three actors own this one class
class Invoice:
    def calculate_total(self): ...   # accounting team
    def save_to_db(self, conn): ...  # DBA team
    def email_pdf(self, to): ...     # email infra team
```

Any of those three teams wants a change, they edit this class, and risk breaking the other two.

**Fix:**

```python
class Invoice:              # accounting team owns
    def calculate_total(self): ...

class InvoiceRepository:    # DBA team owns
    def save(self, inv, conn): ...

class InvoiceMailer:        # email infra team owns
    def send(self, inv, to): ...
```

---

#### Hacks to Count Responsibilities Instantly

**Hack 1 — The "And" Test (fastest, use this first)**

Describe the class in one sentence out loud. Count every "and."

> "This class handles auth **and** sends emails **and** logs events." = 3 responsibilities.

Every "and" is a responsibility boundary. If you struggle to describe it without "and," the class is already confused.

**Hack 2 — Group Methods by the Noun They Touch**

Scan all methods. What object or data does each one operate on? Each noun cluster is one responsibility.

```python
class OrderService:
    def create_order()        # noun: Order
    def cancel_order()        # noun: Order
    def calculate_tax()       # noun: Pricing
    def apply_discount()      # noun: Pricing
    def send_confirmation()   # noun: Notification
    def log_order_event()     # noun: Log
# 4 noun clusters = 4 responsibilities. Split this.
```

**Hack 3 — Count `__init__` Dependencies**

```python
def __init__(self, db, email_client, logger, payment_gateway, cache):
    # 5 injected dependencies = almost certainly 5 responsibilities
```

More than 3 constructor args is a smell. More than 4 is a guarantee the class is doing too much.

**Hack 4 — The "Who Would Call Me?" Test**

Ask which different people or systems would ask you to change this class.
- The DBA wants to change the query. One responsibility.
- The product team wants to change the business rule. Another.
- DevOps wants to change the log format. Another.

Three different callers = three different responsibilities.

**Hack 5 — Scan the Import Block**

```python
import smtplib       # email
import psycopg2      # database
import logging       # logging
import stripe        # payments
import redis         # caching
```

Each unrelated import family is a responsibility. This class is doing five things. Imports don't lie.

**The 10-Second Checklist:**

```
1. Say it in one sentence. How many "and"s?
2. Scan __init__. More than 3 dependencies?
3. Scan imports. How many unrelated domains?
4. Group methods by noun. How many clusters?
```

> **Rule:** Refuse to let any single class exceed three responsibilities. One is ideal. Two is acceptable. Three is the last warning. Four or more = refactor immediately.

---

### O — Open/Closed Principle (OCP)

> Software entities should be open for extension but closed for modification.

Add a new variant by adding a new class that implements an existing interface, without editing any existing class.

**Signal of violation:** A `switch` statement or long `if/elif` chain keyed on a type field.

**Violation:**

```python
# BAD — adding "drone" forces you to edit this function
def calculate_shipping(cost: float, ship_type: str) -> float:
    if ship_type == "air": return cost * 1.5
    elif ship_type == "ground": return cost * 1.0
    elif ship_type == "sea": return cost * 0.7
```

**Fix:**

```python
class ShippingStrategy:
    def cost(self, base: float) -> float: ...

class AirShipping(ShippingStrategy):
    def cost(self, base: float) -> float: return base * 1.5

class GroundShipping(ShippingStrategy):
    def cost(self, base: float) -> float: return base * 1.0

# Adding drone = one new class, zero edits to existing code
class DroneShipping(ShippingStrategy):
    def cost(self, base: float) -> float: return base * 2.0
```

> **Mechanism:** OCP works through polymorphism + dependency inversion together.

---

### L — Liskov Substitution Principle (LSP)

> Subtypes must be substitutable for their base types without altering correctness.

**Diagnostic question:** Does the subclass honor every contract (preconditions, postconditions, invariants) of the parent?

## Think of a Class as a Contract

When you write a class, you are making promises to whoever calls it. Those promises fall into three categories.

---

### Precondition: "What I need from YOU before I run"

It is the rule the caller must satisfy before calling a method.

```python
class BankAccount:
    def deposit(self, amount: float):
        # precondition: amount must be positive
        if amount <= 0:
            raise ValueError("amount must be positive")
        self._balance += amount
```

The parent says: "give me a positive number, I will deposit it."

Now a subclass **tightens** that rule:

```python
class PremiumAccount(BankAccount):
    def deposit(self, amount: float):
        # precondition TIGHTENED: now minimum is 100
        if amount < 100:
            raise ValueError("minimum deposit is 100")
        self._balance += amount
```

This **breaks LSP**. Why? Because code written for `BankAccount` might call `deposit(50)`. That worked fine on the parent. Now you swap in `PremiumAccount` and it explodes. The subclass made the entry requirement harder, so it can no longer stand in for the parent.

**LSP rule for preconditions:** subclass can only make them **equal or weaker** (accept more, not less).

---

### Postcondition: "What I PROMISE to give back after I run"

It is the guarantee about what the method will produce or what state it will leave things in.

```python
class BankAccount:
    def withdraw(self, amount: float):
        # postcondition: balance is always reduced by exactly amount
        self._balance -= amount
```

Now a subclass **weakens** that guarantee:

```python
class BonusAccount(BankAccount):
    def withdraw(self, amount: float):
        # sometimes deducts more due to "fees"
        self._balance -= amount * 1.2  # surprise fees
```

This **breaks LSP**. Code that expected `withdraw(100)` to reduce balance by exactly 100 now gets a different result. The subclass delivered less than promised.

**LSP rule for postconditions:** subclass can only make them **equal or stronger** (deliver more, not less).

---

### Invariant: "What is ALWAYS true about this object, forever"

It is a rule that must hold before AND after every single method call, no matter what.

```python
class Rectangle:
    # invariant: width and height are independent of each other
    def set_width(self, w): self._w = w
    def set_height(self, h): self._h = h
```

The invariant here is: setting width never touches height, and vice versa. That is always true for a Rectangle.

Now Square violates it:

```python
class Square(Rectangle):
    def set_width(self, w):
        self._w = w
        self._h = w   # BREAKS invariant: touching width changes height
```

Any code that does this:

```python
r = get_some_rectangle()  # could be Rectangle or Square
r.set_width(5)
r.set_height(10)
print(r.area())  # expects 50
```

Gets `100` when `r` is a `Square` because setting height also reset width to 10. The invariant that "sides are independent" was silently destroyed.

---

## The One-Line Memory Hook

> Subclass can **accept more, promise more**, but can never **accept less or promise less**.

| Contract | Parent says | Subclass can | Subclass cannot |
|---|---|---|---|
| Precondition | "give me X" | "give me anything, including less than X" | "give me more than X" |
| Postcondition | "I will give Y" | "I will give at least Y, maybe better" | "I will give less than Y" |
| Invariant | "this is always true" | keep it true | silently break it |

---

## Back to Square/Rectangle

All three violations happen at once there.

The invariant "sides are independent" is broken. The postcondition "only width changes when I call `set_width`" is broken. And any caller who relied on those guarantees gets wrong results silently, no error, no warning, just wrong math. That is why it is the textbook LSP example.

**Classic violation — Square inheriting Rectangle:**

```python
class Rectangle:
    def set_width(self, w): self._w = w
    def set_height(self, h): self._h = h
    def area(self): return self._w * self._h

class Square(Rectangle):
    # Surprise — setting one dimension sets both. Breaks Rectangle's invariant.
    def set_width(self, w): self._w = self._h = w
    def set_height(self, h): self._w = self._h = h

def double_width(r: Rectangle):
    r.set_width(r._w * 2)
    return r.area()

r = Rectangle(3, 4)
assert double_width(r) == 24     # 6 * 4, correct

sq = Square(3, 3)
assert double_width(sq) == 18    # FAILS — actually returns 36. Contract broken.
```

**Other common LSP violations:**
- `ReadOnlyList(List)` that throws on `add()`
- `Penguin(Bird)` that throws on `fly()`

**Fix:** Use composition or a finer-grained interface hierarchy. If the subclass cannot honor all parent contracts, inheritance is the wrong tool.

---

### I — Interface Segregation Principle (ISP)

> Clients should not be forced to depend on interfaces they do not use.

**Violation — fat interface:**

```python
class Machine:
    def print(self, doc): ...
    def scan(self, doc): ...
    def fax(self, doc): ...

class SimplePrinter(Machine):
    def print(self, doc): print(doc)
    def scan(self, doc): raise NotImplementedError   # forced and ugly
    def fax(self, doc): raise NotImplementedError    # forced and ugly
```

**Fix — segregated role interfaces:**

```python
class Printer:  def print(self, doc): ...
class Scanner:  def scan(self, doc): ...
class Fax:      def fax(self, doc): ...

class SimplePrinter(Printer):
    def print(self, doc): print(doc)    # clean, no dead methods

class MultiFunctionDevice(Printer, Scanner, Fax):
    def print(self, doc): ...
    def scan(self, doc): ...
    def fax(self, doc): ...
```

> **Rule:** Many small role interfaces beat one fat interface.

---

### D — Dependency Inversion Principle (DIP)

> High-level modules should not depend on low-level modules. Both should depend on abstractions.

**Why it matters:** If your service depends on an interface, you can substitute a fake in tests. If it depends on a concrete SDK call, you cannot test without hitting the real service.

**Violation:**

```python
class OrderService:
    def __init__(self):
        self._gateway = StripeGateway()   # directly coupled, untestable
```

**Fix:**

```python
from abc import ABC, abstractmethod

class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, amount: float) -> str: ...

class StripeGateway(PaymentGateway):
    def charge(self, amount: float) -> str: return f"stripe:{amount}"

class FakeGateway(PaymentGateway):      # for tests
    def charge(self, amount: float) -> str: return f"fake:{amount}"

class OrderService:
    def __init__(self, gateway: PaymentGateway):    # injected
        self._gateway = gateway

    def checkout(self, total: float) -> str:
        return self._gateway.charge(total)

# Composition root — the only place that knows about concrete classes
service = OrderService(StripeGateway())
test_service = OrderService(FakeGateway())
```

> **Rule:** Define the interface from the high-level module's needs, not from what the low-level module provides.

---

## Quick Reference — SOLID Violations Cheat Sheet

| Principle | Signal of Violation | Fix |
|---|---|---|
| SRP | Class description has multiple "and"s, too many `__init__` args | Split into smaller, focused classes |
| OCP | `if/elif` chain keyed on type field | Replace with polymorphism + Strategy pattern |
| LSP | Subclass throws `NotImplementedError` or breaks parent invariant | Use composition or finer interfaces |
| ISP | Class forced to implement methods it does not use | Split fat interface into role-specific ones |
| DIP | High-level class imports and instantiates concrete low-level class | Inject an abstraction, depend on interface |

---

## Design Thinking Triggers

Use these in interviews to signal strong design instincts:

- See a long `if/elif` checking types → "I'll replace this with polymorphism."
- See a class doing multiple unrelated things → "I'll split along responsibility boundaries."
- See a class instantiating its own dependencies → "I'll invert this dependency and inject it."
- See an interface with methods you'll never use → "I'll segregate this into role interfaces."
- See a subclass that can't honor the parent's contract → "Inheritance is wrong here. I'll use composition."
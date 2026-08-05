# LLD Notes: Second-Tier Principles
> DRY, KISS, YAGNI, Law of Demeter, Composition over Inheritance, SoC, Tell-Don't-Ask

---

## Why These Matter in Interviews

SOLID gets you through the first half of the round. These seven principles are what
senior interviewers use to separate mid-level from senior candidates. You do not recite
all seven. You apply one or two explicitly, name them out loud, and let the rest be
invisible in your design.

---

## 1. DRY: Don't Repeat Yourself

**One line:** Every piece of knowledge must have a single representation in the system.

**The common misunderstanding:** DRY is not about duplicate lines of code.
It is about duplicate knowledge. Two functions that look similar but encode
different business rules are fine. The same business rule written in five places
is the violation.

**The test:** If a business rule changes and you have to edit more than one file, DRY is violated.

---

### Example 1: Magic Numbers (most common violation)

```python
# VIOLATION: tax rate is 17% but nobody knows that. It is just 0.17 everywhere.
class OrderService:
    def calculate_total(self, price: float, qty: int) -> float:
        subtotal = price * qty
        return subtotal + (subtotal * 0.17)   # what is 0.17?

class InvoiceService:
    def invoice_amount(self, price: float, qty: int) -> float:
        subtotal = price * qty
        return subtotal + (subtotal * 0.17)   # same. different file. same knowledge.

class CartService:
    def preview_total(self, price: float, qty: int) -> float:
        subtotal = price * qty
        return subtotal + (subtotal * 0.17)   # now in three places.
```

Tax rate changes to 18%? You grep for `0.17` and pray you find all three.

```python
# FIX: knowledge in one place
TAX_RATE = 0.17
BULK_DISCOUNT_THRESHOLD = 500
BULK_DISCOUNT_RATE = 0.10

def calculate_final_price(subtotal: float) -> float:
    discount = subtotal * BULK_DISCOUNT_RATE if subtotal > BULK_DISCOUNT_THRESHOLD else 0
    return subtotal - discount + ((subtotal - discount) * TAX_RATE)

class OrderService:
    def calculate_total(self, price: float, qty: int) -> float:
        return calculate_final_price(price * qty)

class InvoiceService:
    def invoice_amount(self, price: float, qty: int) -> float:
        return calculate_final_price(price * qty)
```

---

### Example 2: Duplicated Validation Logic

```python
# VIOLATION: email validation logic written three times
class UserController:
    def register(self, email: str, password: str):
        if "@" not in email or "." not in email:   # validation
            return {"error": "invalid email"}, 400
        ...

class AdminController:
    def create_user(self, email: str, role: str):
        if "@" not in email or "." not in email:   # same validation
            return {"error": "invalid email"}, 400
        ...

class InviteService:
    def send_invite(self, email: str):
        if "@" not in email or "." not in email:   # same validation again
            raise ValueError("invalid email")
        ...
```

```python
# FIX: validation knowledge in one place
def is_valid_email(email: str) -> bool:
    return "@" in email and "." in email

class UserController:
    def register(self, email: str, password: str):
        if not is_valid_email(email):
            return {"error": "invalid email"}, 400
        ...
```

---

### Example 3: Duplicated Query Logic

```python
# VIOLATION: the "find active users" query in multiple repositories
class OrderRepository:
    def get_orders_for_active_users(self):
        return self.db.query(
            "SELECT * FROM orders WHERE user_id IN "
            "(SELECT id FROM users WHERE is_active = true AND deleted_at IS NULL)"
        )

class NotificationRepository:
    def get_pending_notifications(self):
        return self.db.query(
            "SELECT * FROM notifications WHERE user_id IN "
            "(SELECT id FROM users WHERE is_active = true AND deleted_at IS NULL)"
        )
```

```python
# FIX: active user subquery defined once
ACTIVE_USERS_SUBQUERY = "SELECT id FROM users WHERE is_active = true AND deleted_at IS NULL"

class OrderRepository:
    def get_orders_for_active_users(self):
        return self.db.query(
            f"SELECT * FROM orders WHERE user_id IN ({ACTIVE_USERS_SUBQUERY})"
        )
```

---

## 2. KISS: Keep It Simple, Stupid

**One line:** Prefer the simplest design that works. Complexity is a cost paid with every edit.

**What it fights:** The engineer's instinct to over-engineer. Every extra class, every
extra abstraction is a concept the next reader must hold in their head.

**The test:** Could a junior engineer understand this in 30 seconds? If not, ask why the complexity exists.

---

### Example 1: Over-engineered addition (classic)

```python
# VIOLATION: strategy + handler chain to add two numbers
class AdditionHandler(ABC):
    @abstractmethod
    def handle(self, a: float, b: float) -> float: ...

class SumStrategy:
    def execute(self, handler: AdditionHandler, a: float, b: float) -> float:
        return handler.handle(a, b)

class ConcreteAdder(AdditionHandler):
    def handle(self, a: float, b: float) -> float:
        return a + b

result = SumStrategy().execute(ConcreteAdder(), 3, 4)

# FIX:
def add(a: float, b: float) -> float:
    return a + b

result = add(3, 4)
```

---

### Example 2: Over-engineered config reader

```python
# VIOLATION: factory + strategy + registry to read one environment variable
class ConfigStrategy(ABC):
    @abstractmethod
    def read(self, key: str) -> str: ...

class EnvConfigStrategy(ConfigStrategy):
    def read(self, key: str) -> str:
        import os
        return os.environ.get(key, "")

class ConfigFactory:
    _strategies = {"env": EnvConfigStrategy}

    def get(self, strategy_type: str) -> ConfigStrategy:
        return self._strategies[strategy_type]()

config = ConfigFactory().get("env").read("DATABASE_URL")

# FIX:
import os
database_url = os.environ.get("DATABASE_URL", "")
```

---

### Example 3: Knowing WHEN a pattern IS justified (KISS does not mean no patterns)

```python
# KISS does not mean never use patterns.
# It means: the problem must justify the complexity.

# KISS violation: Strategy pattern for a system that sends only emails today
class NotificationStrategy(ABC):
    @abstractmethod
    def send(self, message: str): ...

class EmailStrategy(NotificationStrategy):
    def send(self, message: str): ...

# The above is over-engineering if you only have one strategy and no second one planned.

# KISS compliant: Strategy pattern for a payment system with three known providers
class PaymentGateway(Protocol):
    def charge(self, amount: float) -> str: ...

class StripeGateway:
    def charge(self, amount: float) -> str: ...

class PayPalGateway:
    def charge(self, amount: float) -> str: ...
# Three real variants exist today. Pattern is justified. KISS is satisfied.
```

---

## 3. YAGNI: You Aren't Gonna Need It

**One line:** Do not build features or extension points for requirements that do not exist yet.

**What it fights:** Speculative generality. Building for a future that never arrives.

**The test:** Is there a parameter, class, or method that no running code calls today? Delete it.

---

### Example 1: Unused parameters

```python
# VIOLATION: system only sends emails. None of these params are used today.
class NotificationService:
    def send(
        self,
        message: str,
        channel: str = "email",               # not used
        batch: bool = False,                   # not used
        priority: int = 1,                     # not used
        retry_count: int = 3,                  # not used
        fallback_channel: str | None = None    # not used
    ) -> None:
        self.email_client.send(message)

# FIX: ship what exists. Add params when they are real requirements.
class NotificationService:
    def send(self, message: str) -> None:
        self.email_client.send(message)
```

---

### Example 2: Plugin system for a feature with one implementation

```python
# VIOLATION: building a full plugin registry for a report generator
# that currently only generates PDFs and has no second format planned.
class ReportPlugin(ABC):
    @abstractmethod
    def generate(self, data: dict) -> bytes: ...

class ReportPluginRegistry:
    _plugins: dict[str, type[ReportPlugin]] = {}

    @classmethod
    def register(cls, name: str, plugin: type[ReportPlugin]) -> None:
        cls._plugins[name] = plugin

    @classmethod
    def get(cls, name: str) -> ReportPlugin:
        return cls._plugins[name]()

class PDFReportPlugin(ReportPlugin):
    def generate(self, data: dict) -> bytes: ...

ReportPluginRegistry.register("pdf", PDFReportPlugin)

# FIX: one format, one class. Build the registry when a second format is requested.
class ReportGenerator:
    def generate_pdf(self, data: dict) -> bytes: ...
```

---

### Example 3: Generic type parameters nobody needs

```python
# VIOLATION: making a repository generic when you only ever store Users
from typing import Generic, TypeVar

T = TypeVar("T")

class Repository(Generic[T]):
    def save(self, entity: T) -> T: ...
    def find_by_id(self, id: int) -> T | None: ...

class UserRepository(Repository[User]):
    pass
# This is fine IF you have multiple entity repositories.
# YAGNI violation if UserRepository is the only one and you have no second planned.

# FIX: just write UserRepository directly.
class UserRepository:
    def save(self, user: User) -> User: ...
    def find_by_id(self, id: int) -> User | None: ...
# Add generics when you need a second repository.
```

---

### OCP vs YAGNI Side by Side

```
Scenario: Building a payment system.

You KNOW you will support Stripe, PayPal, and possibly more.
OCP says: create a PaymentGateway abstraction NOW.
Adding PayPal tomorrow must not require editing OrderService.

You do NOT know if you will need multi-currency, installments, or crypto.
YAGNI says: do not build those extension points.
Ship checkout(total: float). Add currency param when it is a real ticket.

They work together:
- OCP at the seams you KNOW will move.
- YAGNI at the seams you are only guessing might move.
```

---

## 4. Law of Demeter: Principle of Least Knowledge

**One line:** A method should only talk to its immediate friends, not friends of friends.

**Diagnostic symptom:** Train wreck expressions. Three or more dots chaining across domains.

**The rule:** Your method can call methods on:
- `self`
- objects passed as arguments
- objects you created inside the method
- direct attributes of `self`

Anything beyond this is reaching through someone else's internals.

**The real test:** Are you crossing domain boundaries? Not: how many dots are there?

---

### Example 1: Order -> Customer -> Address (classic)

```python
# VIOLATION: controller knows the internal structure of Order, Customer, and Address
class OrderController:
    def process(self, order: Order) -> None:
        zip_code = order.get_customer().get_address().get_zip_code()
        tax = self.tax_service.calculate(zip_code)

# If Address changes how zip is stored, this controller breaks.
# The controller has nothing to do with addresses.

# FIX: move the knowledge into Order
class Order:
    def shipping_zip(self) -> str:
        return self.customer.address.zip_code   # internals hidden here

class OrderController:
    def process(self, order: Order) -> None:
        tax = self.tax_service.calculate(order.shipping_zip())
```

---

### Example 2: Request -> Session -> User -> Permissions

```python
# VIOLATION: handler reaches through request internals to check permissions
class PostHandler:
    def create_post(self, request: HttpRequest, content: str) -> str:
        if not request.session.user.permissions.can_publish:
            return "forbidden"
        ...

# FIX: request exposes what the handler needs
class HttpRequest:
    def can_user_publish(self) -> bool:
        return self.session.user.permissions.can_publish

class PostHandler:
    def create_post(self, request: HttpRequest, content: str) -> str:
        if not request.can_user_publish():
            return "forbidden"
        ...
```

---

### Example 3: Delivery fee calculation

```python
# VIOLATION: pricing service reaches through order to get city names
class PricingService:
    def calculate_fee(self, order: Order) -> float:
        from_city = order.get_restaurant().get_location().get_city()
        to_city = order.get_customer().get_address().get_city()
        return self._base_fee(from_city, to_city)

# FIX: order tells you what you need
class Order:
    def restaurant_city(self) -> str:
        return self.restaurant.location.city

    def customer_city(self) -> str:
        return self.customer.address.city

class PricingService:
    def calculate_fee(self, order: Order) -> float:
        return self._base_fee(order.restaurant_city(), order.customer_city())
```

---

### Example 4: Fluent API (NOT a violation)

```python
# This looks like it violates Demeter (many dots) but it does NOT.
# Every method returns the SAME object. You are not crossing domain boundaries.
query = (
    QueryBuilder()
    .select("users")
    .where("is_active = true")
    .order_by("created_at DESC")
    .limit(10)
)

# Same with SQLAlchemy:
users = db.session.query(User).filter(User.is_active == True).order_by(User.name).all()

# This is fine. Demeter applies to cross-domain chains, not fluent APIs.
```

---

## 5. Composition over Inheritance

**One line:** Prefer has-a over is-a. Build behavior by combining small objects, not deep hierarchies.

**Why inheritance breaks:**
- Static. Once a subclass inherits, the relationship is fixed forever.
- Deep hierarchies couple every level to the one above.
- Cannot combine behaviors from two branches.

**Rule of thumb:** More than two levels of inheritance is a warning sign.
More than three is almost always a bug.

---

### Example 1: Deep animal hierarchy (classic)

```python
# VIOLATION: 5 levels deep
class Animal: ...
class Pet(Animal): ...
class Dog(Pet): ...
class TrainedDog(Dog): ...
class ServiceDog(TrainedDog): ...

# Now you need SwimmingServiceDog.
# It needs ServiceDog behavior AND swimming behavior.
# You cannot inherit from two parents cleanly in Python.

# FIX: behaviors are injected objects
class Dog:
    def __init__(
        self,
        trainer: Trainer | None = None,
        service_role: ServiceRole | None = None,
        swim_skill: SwimSkill | None = None
    ):
        self._trainer = trainer
        self._service_role = service_role
        self._swim_skill = swim_skill

swimming_service_dog = Dog(
    trainer=GuideDogTrainer(),
    service_role=BlindGuidanceRole(),
    swim_skill=BasicSwimSkill()
)
```

---

### Example 2: Notification with behaviors (Decorator-style)

```python
# VIOLATION: deep inheritance to combine behaviors
class BaseNotifier:
    def send(self, message: str) -> None:
        print(f"Sending: {message}")

class LoggedNotifier(BaseNotifier):
    def send(self, message: str) -> None:
        print("[LOG] Sending")
        super().send(message)

class RetryNotifier(LoggedNotifier):
    def send(self, message: str) -> None:
        for i in range(3):
            super().send(message)

class ThrottledRetryNotifier(RetryNotifier):
    def send(self, message: str) -> None:
        import time; time.sleep(1)
        super().send(message)

# Need LoggedThrottledNotifier (no retry)? Impossible without duplicating code.

# FIX: each behavior wraps a notifier
class Notifier(Protocol):
    def send(self, message: str) -> None: ...

class EmailNotifier:
    def send(self, message: str) -> None:
        print(f"[EMAIL] {message}")

class LoggedNotifier:
    def __init__(self, inner: Notifier):
        self._inner = inner

    def send(self, message: str) -> None:
        print("[LOG] Sending message")
        self._inner.send(message)

class RetryNotifier:
    def __init__(self, inner: Notifier, retries: int = 3):
        self._inner = inner
        self._retries = retries

    def send(self, message: str) -> None:
        for i in range(self._retries):
            try:
                self._inner.send(message)
                return
            except Exception:
                print(f"Retry {i + 1}")

# Combine any behaviors freely:
email = EmailNotifier()
logged_email = LoggedNotifier(email)                    # logging only
retried_email = RetryNotifier(email)                    # retry only
logged_retried = LoggedNotifier(RetryNotifier(email))   # both
```

---

### Example 3: Repository with caching (backend-specific)

```python
# VIOLATION: inheritance to add caching to a repository
class UserRepository:
    def find_by_id(self, id: int) -> User: ...

class CachedUserRepository(UserRepository):   # inherits all DB methods
    def find_by_id(self, id: int) -> User:
        cached = self.cache.get(f"user:{id}")
        if cached:
            return cached
        user = super().find_by_id(id)
        self.cache.set(f"user:{id}", user)
        return user
# Problem: CachedUserRepository is tightly coupled to UserRepository's internals.

# FIX: composition. CachedUserRepository HAS a UserRepository.
class CachedUserRepository:
    def __init__(self, repo: UserRepository, cache: Cache):
        self._repo = repo
        self._cache = cache

    def find_by_id(self, id: int) -> User:
        cached = self._cache.get(f"user:{id}")
        if cached:
            return cached
        user = self._repo.find_by_id(id)
        self._cache.set(f"user:{id}", user)
        return user
# Swap the inner repo anytime. Swap the cache anytime. No inheritance needed.
```

---

## 6. Separation of Concerns (SoC)

**One line:** Each module, class, or function should address exactly one concern and address it fully.

**Relationship to SRP:** SoC is the parent idea. SRP is SoC at the class level.
SoC applies at every level: files, layers, modules, microservices.

**This is the principle behind:**
- MVC: separating model, view, controller
- Layered architecture: controller, service, repository
- Hexagonal architecture: ports and adapters

**The diagnostic test:** Can you split a class's methods into two unrelated groups?
If yes, the class has two concerns and should be split.

---

### Example 1: All four concerns in one controller

```python
# VIOLATION: four concerns in one class
class UserController:
    def register(self, email: str, password: str):
        if not email or not password:                    # HTTP concern
            return {"error": "missing fields"}, 400

        if len(password) < 8:                           # business logic concern
            return {"error": "password too short"}, 400

        self.db.execute(                                 # database concern
            "INSERT INTO users VALUES (?, ?)", email, hash(password)
        )

        self.smtp.send(email, "Welcome!")               # notification concern
        return {"message": "registered"}, 201

# Four teams would edit this file: API team, product team, DBA, email team.

# FIX: each concern in its own layer
class UserController:
    def register(self, request: RegisterRequest) -> RegisterResponse:
        user = self.service.register(request.email, request.password)
        return RegisterResponse(id=user.id), 201        # HTTP only

class UserService:
    def register(self, email: str, password: str) -> User:
        if len(password) < 8:
            raise ValueError("password too short")      # business logic only
        user = self.repo.save(User(email, hash(password)))
        self.mailer.notify(f"Welcome {email}")
        return user

class UserRepository:
    def save(self, user: User) -> User:
        self.db.execute("INSERT INTO users ...", user)  # database only
        return user
```

---

### Example 2: Business logic mixed into a model

```python
# VIOLATION: User model doing HTTP serialization and email formatting
class User:
    def __init__(self, id: int, email: str, name: str):
        self.id = id
        self.email = email
        self.name = name

    def to_json(self) -> dict:                          # presentation concern
        return {"id": self.id, "email": self.email, "name": self.name}

    def send_welcome_email(self, smtp_client) -> None:  # notification concern
        smtp_client.send(self.email, f"Welcome {self.name}!")

    def save(self, db_conn) -> None:                    # persistence concern
        db_conn.execute("INSERT INTO users ...", self)

# FIX: User is pure data and business rules only
class User:
    def __init__(self, id: int, email: str, name: str):
        self.id = id
        self.email = email
        self.name = name

    def assert_can_publish(self) -> None:               # business rule (belongs here)
        if not self.is_active:
            raise PermissionError("inactive account")

# Serialization lives in a serializer. Email in a mailer. DB in a repository.
```

---

### Example 3: One function doing too many things

```python
# VIOLATION: process_order does five different jobs
def process_order(order_data: dict) -> dict:
    # Concern 1: validation
    if not order_data.get("items"):
        return {"error": "no items"}

    # Concern 2: price calculation
    total = sum(item["price"] * item["qty"] for item in order_data["items"])
    tax = total * 0.17
    final = total + tax

    # Concern 3: inventory check
    for item in order_data["items"]:
        if inventory[item["id"]] < item["qty"]:
            return {"error": f"out of stock: {item['id']}"}

    # Concern 4: database write
    db.execute("INSERT INTO orders ...", order_data, final)

    # Concern 5: email notification
    smtp.send(order_data["email"], f"Order placed. Total: {final}")

    return {"status": "placed", "total": final}

# FIX: each concern becomes its own function or class
def validate_order(order_data: dict) -> None: ...
def calculate_total(items: list) -> float: ...
def check_inventory(items: list) -> None: ...
def save_order(order_data: dict, total: float) -> None: ...
def notify_customer(email: str, total: float) -> None: ...
```

---

## 7. Tell-Don't-Ask

**One line:** Tell objects what to do. Do not query their state and decide for them.

**What it fights:** The procedural habit of pulling data out of an object and making
decisions about it outside. This scatters business rules across callers.

**Connection to encapsulation:** Tell-Don't-Ask is encapsulation in action.
The rule lives with the data it governs.

---

### Example 1: BankAccount (classic)

```python
# VIOLATION: the withdrawal rule lives OUTSIDE BankAccount
# Every caller must know and repeat "balance >= amount"
if account.balance >= amount:
    account.withdraw(amount)
else:
    raise InsufficientFundsError()

# This if-check is now copied across OrderService, PaymentController, RefundService.

# FIX: the rule lives INSIDE the object that owns the data
class BankAccount:
    def withdraw(self, amount: float) -> None:
        if self._balance < amount:
            raise InsufficientFundsError("Insufficient funds.")
        self._balance -= amount

# Callers just tell it what to do.
account.withdraw(amount)   # one line. no if. no duplicated rule.
```

---

### Example 2: User permissions (backend-specific)

```python
# VIOLATION: permission rules scattered across every service
class PostService:
    def create_post(self, user: User, content: str) -> Post:
        if not user.is_active:
            raise PermissionError("inactive")
        if user.subscription_tier < 2:
            raise PermissionError("upgrade required")
        if user.posts_this_month >= user.monthly_limit:
            raise PermissionError("limit reached")
        return self.repo.save(Post(content, user.id))

class VideoService:
    def upload_video(self, user: User, file: bytes) -> Video:
        if not user.is_active:                             # same check again
            raise PermissionError("inactive")
        if user.subscription_tier < 3:                    # similar check again
            raise PermissionError("upgrade required")
        return self.repo.save(Video(file, user.id))

# FIX: tell User to assert its own permissions
class User:
    def assert_can_publish_post(self) -> None:
        if not self.is_active:
            raise PermissionError("inactive account")
        if self.subscription_tier < 2:
            raise PermissionError("upgrade your plan to publish")
        if self.posts_this_month >= self.monthly_limit:
            raise PermissionError("monthly post limit reached")

    def assert_can_upload_video(self) -> None:
        if not self.is_active:
            raise PermissionError("inactive account")
        if self.subscription_tier < 3:
            raise PermissionError("upgrade your plan to upload videos")

class PostService:
    def create_post(self, user: User, content: str) -> Post:
        user.assert_can_publish_post()                     # one line. rule is in User.
        return self.repo.save(Post(content, user.id))

class VideoService:
    def upload_video(self, user: User, file: bytes) -> Video:
        user.assert_can_upload_video()                     # one line.
        return self.repo.save(Video(file, user.id))
```

---

### Example 3: Order status checks

```python
# VIOLATION: order state rules scattered across callers
class ShipmentService:
    def ship(self, order: Order) -> None:
        if order.status != "paid":
            raise ValueError("cannot ship unpaid order")
        order.status = "shipped"

class RefundService:
    def refund(self, order: Order) -> None:
        if order.status not in ("paid", "shipped"):
            raise ValueError("cannot refund this order")
        order.status = "refunded"

# FIX: Order owns its own state transition rules
class Order:
    def mark_shipped(self) -> None:
        if self.status != "paid":
            raise ValueError("cannot ship unpaid order")
        self.status = "shipped"

    def mark_refunded(self) -> None:
        if self.status not in ("paid", "shipped"):
            raise ValueError("cannot refund this order")
        self.status = "refunded"

class ShipmentService:
    def ship(self, order: Order) -> None:
        order.mark_shipped()   # tell. done.

class RefundService:
    def refund(self, order: Order) -> None:
        order.mark_refunded()  # tell. done.
```

---

### Example 4: Inventory management

```python
# VIOLATION: stock check scattered across multiple services
class OrderService:
    def place_order(self, product_id: int, qty: int) -> None:
        product = self.repo.find(product_id)
        if product.stock < qty:
            raise ValueError("insufficient stock")
        product.stock -= qty
        self.repo.save(product)

class ReservationService:
    def reserve(self, product_id: int, qty: int) -> None:
        product = self.repo.find(product_id)
        if product.stock < qty:           # same rule again
            raise ValueError("insufficient stock")
        product.stock -= qty
        self.repo.save(product)

# FIX: Product manages its own stock
class Product:
    def deduct_stock(self, qty: int) -> None:
        if self._stock < qty:
            raise ValueError(f"insufficient stock. available: {self._stock}")
        self._stock -= qty

class OrderService:
    def place_order(self, product_id: int, qty: int) -> None:
        product = self.repo.find(product_id)
        product.deduct_stock(qty)          # tell
        self.repo.save(product)

class ReservationService:
    def reserve(self, product_id: int, qty: int) -> None:
        product = self.repo.find(product_id)
        product.deduct_stock(qty)          # same tell, no duplicated rule
        self.repo.save(product)
```

---

## Quick Reference

| Principle | Violation Signal | One-line Fix |
|---|---|---|
| DRY | Same number or rule in multiple files | Extract to a constant or method |
| KISS | Pattern used where a function would do | Delete until it hurts, then stop |
| YAGNI | Parameters or classes nobody calls yet | Delete it, add it when needed |
| Law of Demeter | Three or more dots chaining across domains | Move the knowledge into the middle object |
| Composition over Inheritance | Four-level class hierarchy | Inject behavior objects instead |
| SoC | Methods split into unrelated groups | Split the class at the boundary |
| Tell-Don't-Ask | `if obj.state: obj.do()` outside the class | Move the if inside the object |

---

## Common Interview Questions

---

### Q: Can two classes violate SRP even if each has only one method?

**Yes. SRP is about reasons to change, not method count.**

A one-method class can still have two reasons to change if that one method mixes two concerns.

```python
# Example 1: one method, two concerns
class UserRegistrar:
    def register(self, email: str, password: str) -> None:
        self.db.execute("INSERT INTO users ...", email, hash(password))  # persistence
        self.smtp.send(email, "Welcome!")                                # notification

# Who calls you to change this?
# DBA if the query changes. Email team if the welcome message changes.
# Two callers. Two reasons. SRP violated even with one method.
```

```python
# Example 2: one method, two concerns (less obvious)
class InvoiceProcessor:
    def process(self, invoice: Invoice) -> None:
        total = invoice.subtotal * 1.17      # business logic: tax calculation
        self.db.save(invoice.id, total)      # persistence: saving the result

# Accounting team changes the tax rule. DBA changes the schema.
# One method. Two callers. Still a violation.
```

```python
# Example 3: even a tiny class can violate SRP
class Logger:
    def log(self, message: str) -> None:
        print(message)                       # console output
        open("app.log", "a").write(message)  # file persistence

# DevOps changes console format. Storage team changes file path.
# Two callers. SRP violated.

# FIX: split even tiny classes when their concerns are distinct
class ConsoleLogger:
    def log(self, message: str) -> None:
        print(message)

class FileLogger:
    def log(self, message: str) -> None:
        open("app.log", "a").write(message)
```

**Memory hook:** Count callers, not methods.

---

### Q: How is OCP different from YAGNI? Both seem to be about future change.

**They point in opposite directions.**

OCP says: when a new variant arrives, design so you do not edit existing code.
Design clean seams NOW at the places you KNOW will change.

YAGNI says: do not pre-build variants that have not arrived yet.
Do not build seams at places you are only GUESSING might change.

```python
# Scenario: payment system. You know Stripe, PayPal, and possibly more are coming.

# OCP applied correctly: abstraction designed now because change is certain.
class PaymentGateway(Protocol):
    def charge(self, amount: float) -> str: ...

class StripeGateway:
    def charge(self, amount: float) -> str: return f"stripe:{amount}"

class OrderService:
    def __init__(self, gateway: PaymentGateway): self._gateway = gateway
    def checkout(self, total: float) -> str: return self._gateway.charge(total)

# Adding PayPal: one new class, zero edits to OrderService. OCP works.
class PayPalGateway:
    def charge(self, amount: float) -> str: return f"paypal:{amount}"
```

```python
# Same system. You do NOT know if multi-currency will ever be needed.
# YAGNI says: do not add it.

# VIOLATION (YAGNI):
class OrderService:
    def checkout(self, total: float, currency: str = "USD",
                 installments: int = 1, crypto: bool = False) -> str:
        ...   # none of these are used today

# FIX (YAGNI):
class OrderService:
    def checkout(self, total: float) -> str:
        return self._gateway.charge(total)
# Add currency when it is a real ticket. Refactoring takes one hour.
# Maintaining dead params costs hours every sprint.
```

```python
# Another clear example: notification system.

# You KNOW email, SMS, and WhatsApp are all needed on day one.
# OCP: build NotificationChannel abstraction now. Correct.

# You are NOT sure if Telegram will be needed.
# YAGNI: do not build TelegramChannel yet. Add it when requested.

# One-line rule:
# OCP = design for extension at seams you KNOW will move.
# YAGNI = do not speculate about seams that MIGHT move.
```

---

### Q: Does LSP forbid overriding methods that throw new exceptions?

**It forbids throwing broader or unrelated exceptions. Same or narrower is fine.**

The reason: callers are written to handle what the parent contract declares.
If a subclass throws something outside that contract, callers break silently.

```python
# Parent contract: charge() may raise PaymentError
class PaymentGateway:
    def charge(self, amount: float) -> str:
        raise PaymentError("declined")   # declared in contract

# FINE: same exception. Callers catching PaymentError will catch this.
class StripeGateway(PaymentGateway):
    def charge(self, amount: float) -> str:
        raise PaymentError("card declined")

# FINE: narrower exception (subclass of PaymentError).
# Callers catching PaymentError will still catch InsufficientFundsError.
class StrictGateway(PaymentGateway):
    def charge(self, amount: float) -> str:
        raise InsufficientFundsError("not enough balance")
        # InsufficientFundsError is a subclass of PaymentError

# LSP VIOLATION: completely unrelated exception.
# Callers catching PaymentError will NEVER catch DatabaseError. Silent failure.
class BrokenGateway(PaymentGateway):
    def charge(self, amount: float) -> str:
        raise DatabaseError("connection failed")   # nothing to do with payments
```

```python
# Caller written for the base contract:
try:
    gateway.charge(100)
except PaymentError:
    handle_payment_failure()

# Works with StripeGateway. Works with StrictGateway.
# Completely breaks with BrokenGateway. DatabaseError flies past the except block.
# That is the LSP violation: the subclass broke the caller's assumption.
```

```python
# Second example: file reader
class FileReader:
    def read(self, path: str) -> str:
        raise FileNotFoundError   # contract: may raise FileNotFoundError

class CachedFileReader(FileReader):
    def read(self, path: str) -> str:
        raise MemoryError("cache full")   # LSP VIOLATION: unrelated exception
        # Callers expecting FileNotFoundError will not catch MemoryError
```

**Rule:** If the caller's except block would miss your exception, it is an LSP violation.

---

### Q: Is the Law of Demeter a hard rule or a guideline?

**Guideline. Apply judgment, not dot counting.**

The letter of Demeter says: never chain more than one dot on an external object.
But this would outlaw fluent builder APIs, which are widely accepted as good design.

```python
# This has many dots. Violates the LETTER of Demeter. But this is FINE.
query = (
    QueryBuilder()
    .select("users")
    .where("is_active = true")
    .order_by("created_at DESC")
    .limit(10)
)
# Every dot returns the SAME object (QueryBuilder).
# You are not crossing domain boundaries.
# You are just chaining operations on one thing.

# SQLAlchemy: same idea. Many dots, one domain, zero violation.
users = db.session.query(User).filter(User.is_active).order_by(User.name).all()
```

```python
# This has fewer dots but IS a real Demeter violation.
city = order.customer.address.city   # crossing Order -> Customer -> Address
# Three different domain objects. Change Address, controller breaks.
# This is the violation. Not the dot count.
```

```python
# The test is domain crossing, not dot counting.

# BAD: crossing Order domain, Customer domain, Address domain
zip_code = order.get_customer().get_address().get_zip_code()

# FINE: chaining on one domain object
result = request.build_response().with_status(200).with_body(data).send()

# BAD: crossing User domain, Subscription domain, Plan domain
limit = user.get_subscription().get_plan().get_monthly_post_limit()

# FIX: User exposes what you need directly
limit = user.monthly_post_limit()   # User knows how to reach it internally
```

**Memory hook:** Demeter is about domain crossing, not dot counting.

---

## Interview Talking Points

**When asked about a design decision you regret:**
Name a SOLID or second-tier violation you committed, which principle would have
prevented it, and the refactor you applied. This signals reflection, not theory.

**Do not recite all seven in a round:**
Apply one or two explicitly, name them out loud, and let the rest be invisible in your design.
Engineers who recite theory instead of designing code are the ones who fail.
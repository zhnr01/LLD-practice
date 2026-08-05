# Practice Problems: Second-Tier Principles
> DRY, KISS, YAGNI, Law of Demeter, Composition over Inheritance, SoC, Tell-Don't-Ask

---

## P11: DRY Violation Fix
**File:** `p11_dry.py`

You are given this code from an e-commerce backend.

```python
class OrderService:
    def calculate_total(self, price: float, quantity: int) -> float:
        subtotal = price * quantity
        discount = subtotal * 0.10 if subtotal > 500 else 0
        tax = (subtotal - discount) * 0.17
        return subtotal - discount + tax

class InvoiceService:
    def generate_amount(self, price: float, quantity: int) -> float:
        subtotal = price * quantity
        discount = subtotal * 0.10 if subtotal > 500 else 0
        tax = (subtotal - discount) * 0.17
        return subtotal - discount + tax

class CartService:
    def preview_total(self, price: float, quantity: int) -> float:
        subtotal = price * quantity
        discount = subtotal * 0.10 if subtotal > 500 else 0
        tax = (subtotal - discount) * 0.17
        return subtotal - discount + tax
```

**Requirements:**
- Identify every piece of duplicated knowledge (not just duplicated lines)
- Extract each piece of knowledge to exactly one place
- All three services must still work correctly after your fix
- Changing the tax rate or discount threshold should require editing exactly one line

**What this tests:** DRY, extracting knowledge vs extracting code.

---

## P12: Law of Demeter Fix
**File:** `p12_demeter.py`

You are given this controller from a food delivery backend.

```python
class DeliveryController:
    def __init__(self, pricing_service, notification_service):
        self.pricing = pricing_service
        self.notifier = notification_service

    def place_order(self, order: Order) -> dict:
        # Train wreck 1: reaching through order internals
        delivery_fee = self.pricing.calculate(
            order.get_restaurant().get_location().get_city(),
            order.get_customer().get_address().get_city()
        )

        # Train wreck 2: reaching through customer internals
        self.notifier.send(
            order.get_customer().get_contact().get_email(),
            f"Your order total is {order.get_items_total() + delivery_fee}"
        )

        return {"status": "placed", "total": order.get_items_total() + delivery_fee}
```

**Requirements:**
- Eliminate all train wreck chains (no more than one dot on external objects)
- Move knowledge of how to reach deeply nested data into the objects that own it
- The controller should only talk to `order`, `pricing_service`, and `notification_service`
- Add the necessary methods to `Order` to support this

**What this tests:** Law of Demeter, moving knowledge to the right place.

---

## P13: Tell-Don't-Ask Fix
**File:** `p13_tell_dont_ask.py`

You are given this service. It is full of asking instead of telling.

```python
class SubscriptionService:
    def publish_post(self, user: User, content: str) -> str:
        if not user.is_active:
            return "Account is inactive."

        if user.subscription_tier < 2:
            return "Upgrade your plan to publish posts."

        if user.posts_this_month >= user.monthly_post_limit:
            return "Monthly post limit reached."

        user.posts_this_month += 1
        return self.post_repo.save(content, user.id)


    def send_message(self, sender: User, receiver: User, content: str) -> str:
        if not sender.is_active:
            return "Your account is inactive."

        if sender.subscription_tier < 1:
            return "Upgrade your plan to send messages."

        if not receiver.is_active:
            return "Recipient account is inactive."

        return self.message_repo.save(content, sender.id, receiver.id)
```

**Requirements:**
- Move all state-checking rules into the `User` class where the data lives
- `SubscriptionService` methods should contain zero `if user.X` checks
- `User` should raise meaningful exceptions when rules are violated
- The service just tells the user to do something and handles exceptions if needed

**What this tests:** Tell-Don't-Ask, encapsulation, moving rules to the right owner.

---

## P14: Composition over Inheritance Fix
**File:** `p14_composition.py`

You are given this inheritance hierarchy for a notification system.

```python
class BaseNotifier:
    def send(self, message: str) -> None:
        print(f"Sending: {message}")

class LoggedNotifier(BaseNotifier):
    def send(self, message: str) -> None:
        print(f"[LOG] Sending message")
        super().send(message)

class RetryNotifier(LoggedNotifier):
    def send(self, message: str) -> None:
        for attempt in range(3):
            try:
                super().send(message)
                break
            except Exception:
                print(f"Retry {attempt + 1}")

class ThrottledRetryNotifier(RetryNotifier):
    def send(self, message: str) -> None:
        import time
        time.sleep(1)
        super().send(message)
```

You now need a `LoggedThrottledNotifier` that logs and throttles but does NOT retry.
With this hierarchy, that is impossible without duplicating code.

**Requirements:**
- Redesign using composition so behaviors (logging, retry, throttling) are mix-and-match
- Any combination should work: logging only, retry only, logging plus throttle, all three
- Adding a new behavior (e.g. rate limiting) should require one new class, zero edits elsewhere
- No inheritance deeper than one level

**Hint:** Each behavior wraps a notifier. A logged notifier has a notifier inside it.

**What this tests:** Composition over inheritance, Decorator pattern thinking.

---

## P15: Combined Principles (Mini LLD)
**File:** `p15_combined.py`

Design a simple **blog post system** for a multi-tier subscription platform.

**Requirements:**
- Users have a subscription tier: `FREE`, `BASIC`, `PREMIUM`
- `FREE` users can read posts but cannot publish
- `BASIC` users can publish up to 5 posts per month
- `PREMIUM` users have unlimited posts
- Published posts have a title, content, and author
- The system should notify the author by email when their post is published
- An admin can change a user's subscription tier

**Constraints:**
- Apply Tell-Don't-Ask: publishing rules live inside `User`, not inside a service
- Apply DRY: subscription tier limits are defined in exactly one place
- Apply SoC: HTTP handling, business logic, database, and notification are in separate classes
- Apply Composition over Inheritance: use composition for the notification behavior
- No if/elif chain checking tier names anywhere except one mapping dict

**Deliverable:**
1. A comment at the top listing every class and its single responsibility
2. Skeleton code with all classes, methods, and docstrings
3. A composition root at the bottom showing how everything wires together

**What this tests:** All seven principles applied together in a realistic design.

---

## Grading Checklist

After each solution, ask yourself:

| Question | Principle |
|---|---|
| Is any number, threshold, or rule written in more than one place? | DRY |
| Is there a pattern or abstraction that a simple function would replace? | KISS |
| Is there a parameter or class that no running code calls today? | YAGNI |
| Does any method chain more than one dot across different domain objects? | Law of Demeter |
| Is there an inheritance hierarchy deeper than two levels? | Composition over Inheritance |
| Can you split any class's methods into two unrelated groups? | SoC |
| Does any method query an object's state and then decide for it? | Tell-Don't-Ask |

If all answers are no, the solution is solid.
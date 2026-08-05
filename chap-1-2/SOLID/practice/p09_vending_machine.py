# P09 - Vending Machine
#
# Pattern used: State Pattern
#
# The problem says: no if/elif chain for state-based behavior.
# Without State pattern, you end up with this:
#
#   def insert_coin(self, amount):
#       if self.state == "idle":
#           ...
#       elif self.state == "has_money":
#           ...
#
# That is a conditional ladder keyed on a state string. Classic OCP violation.
# Every new state means editing this function.
#
# With the State pattern:
# - Each state is a class that knows its own behavior.
# - VendingMachine holds the current state and delegates to it.
# - Adding a new state = add one new class. Zero edits to VendingMachine.
#
# CLASS DIAGRAM
# =============
#
#   +-------------+       +--------------+
#   |   Product   |       |  Inventory   |
#   |-------------|       |--------------|
#   | name: str   |<------| _stock: dict |
#   | price: float|       | add()        |
#   +-------------+       | get()        |
#                         | in_stock()   |
#                         | dispense()   |
#                         +--------------+
#                                |
#   +-------------+              |
#   |  MoneySlot  |       +--------------+
#   |-------------|       | VendingMachine|
#   | _amount     |<------| _inventory   |
#   | insert()    |       | _money_slot  |
#   | total()     |       | _state       |
#   | reset()     |       | insert_coin()|
#   | change_for()|       | select()     |
#   +-------------+       | cancel()     |
#                         +--------------+
#                                |
#                         [delegates to]
#                                |
#                +---------------+---------------+
#                |                               |
#         +------------+               +--------------------+
#         |  IdleState |               | MoneyInsertedState |
#         |------------|               |--------------------|
#         | insert_coin|               | insert_coin()      |
#         | select()   |               | select_product()   |
#         | cancel()   |               | cancel()           |
#         +------------+               +--------------------+
#
# Responsibilities:
#   Product           - holds product data (name, price)
#   Inventory         - manages stock (add, check, dispense)
#   MoneySlot         - tracks inserted money, calculates change
#   IdleState         - machine behavior when no money is inserted
#   MoneyInsertedState - machine behavior after money is inserted
#   VendingMachine    - owns state transitions, delegates all behavior to current state

from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


# ------------------------------------------------------------------
# Product: pure data, no behavior
# ------------------------------------------------------------------

@dataclass
class Product:
    """Owns: product data.
    Reason to change: product attributes change (add calories, weight, etc)."""
    name: str
    price: float


# ------------------------------------------------------------------
# Inventory: manages stock levels
# ------------------------------------------------------------------

class Inventory:
    """Owns: stock management for all products.
    Reason to change: stock rules change (e.g. max stock per slot, expiry tracking)."""

    def __init__(self):
        self._stock: dict[str, tuple[Product, int]] = {}

    def add(self, product: Product, quantity: int) -> None:
        if product.name in self._stock:
            existing, qty = self._stock[product.name]
            self._stock[product.name] = (existing, qty + quantity)
        else:
            self._stock[product.name] = (product, quantity)

    def get(self, name: str) -> Product | None:
        entry = self._stock.get(name)
        return entry[0] if entry else None

    def in_stock(self, name: str) -> bool:
        entry = self._stock.get(name)
        return entry is not None and entry[1] > 0

    def dispense(self, name: str) -> None:
        product, qty = self._stock[name]
        self._stock[name] = (product, qty - 1)


# ------------------------------------------------------------------
# MoneySlot: tracks inserted coins and calculates change
# ------------------------------------------------------------------

class MoneySlot:
    """Owns: inserted money tracking and change calculation.
    Reason to change: currency handling rules change (e.g. denomination validation)."""

    def __init__(self):
        self._inserted: float = 0.0

    def insert(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        self._inserted = round(self._inserted + amount, 2)

    def total(self) -> float:
        return self._inserted

    def calculate_change(self, price: float) -> float:
        return round(self._inserted - price, 2)

    def reset(self) -> None:
        self._inserted = 0.0


# ------------------------------------------------------------------
# State Protocol + concrete states
# ------------------------------------------------------------------

class VendingMachineState(Protocol):
    """Shape every machine state must satisfy.
    Reason to change: the state interface contract changes."""

    def insert_coin(self, amount: float, machine: VendingMachine) -> str: ...
    def select_product(self, name: str, machine: VendingMachine) -> str: ...
    def cancel(self, machine: VendingMachine) -> str: ...


class IdleState:
    """Behavior when no money has been inserted.
    Reason to change: idle state rules change (e.g. add out-of-service mode).

    Notice: insert_coin() transitions to MoneyInsertedState.
    select_product() and cancel() reject the action with a clear message.
    No if/elif needed. The state itself knows what is valid."""

    def insert_coin(self, amount: float, machine: VendingMachine) -> str:
        machine.money_slot.insert(amount)
        machine.set_state(MoneyInsertedState())
        return f"Inserted {amount}. Total: {machine.money_slot.total()}"

    def select_product(self, name: str, machine: VendingMachine) -> str:
        return "Please insert money first."

    def cancel(self, machine: VendingMachine) -> str:
        return "No money to return."


class MoneyInsertedState:
    """Behavior after money has been inserted.
    Reason to change: dispensing rules or change-return logic changes.

    select_product() checks stock and balance, dispenses, transitions back to Idle.
    cancel() returns all inserted money, transitions back to Idle."""

    def insert_coin(self, amount: float, machine: VendingMachine) -> str:
        machine.money_slot.insert(amount)
        return f"Added {amount}. Total: {machine.money_slot.total()}"

    def select_product(self, name: str, machine: VendingMachine) -> str:
        product = machine.inventory.get(name)

        if product is None:
            return f"Product '{name}' not found."

        if not machine.inventory.in_stock(name):
            return f"'{name}' is out of stock."

        if machine.money_slot.total() < product.price:
            shortfall = round(product.price - machine.money_slot.total(), 2)
            return (
                f"Insufficient funds. '{name}' costs {product.price}. "
                f"Please insert {shortfall} more."
            )

        change = machine.money_slot.calculate_change(product.price)
        machine.inventory.dispense(name)
        machine.money_slot.reset()
        machine.set_state(IdleState())

        if change > 0:
            return f"Dispensing '{name}'. Your change: {change}"
        return f"Dispensing '{name}'. Exact amount, no change."

    def cancel(self, machine: VendingMachine) -> str:
        amount = machine.money_slot.total()
        machine.money_slot.reset()
        machine.set_state(IdleState())
        return f"Cancelled. Returning {amount}."


# ------------------------------------------------------------------
# VendingMachine: owns state and delegates everything to current state
# ------------------------------------------------------------------

class VendingMachine:
    """Owns: state transitions and orchestration of inventory and money.
    Reason to change: overall machine workflow changes (e.g. add maintenance mode).

    Key insight: there is no logic here. Every method is one line: delegate to state.
    The state object decides what happens. This is the entire point of State pattern.
    Adding a new state (MaintenanceState, OutOfServiceState) = add one class, zero edits here."""

    def __init__(self):
        self.inventory = Inventory()
        self.money_slot = MoneySlot()
        self._state: VendingMachineState = IdleState()

    def set_state(self, state: VendingMachineState) -> None:
        self._state = state

    def insert_coin(self, amount: float) -> str:
        return self._state.insert_coin(amount, self)

    def select_product(self, name: str) -> str:
        return self._state.select_product(name, self)

    def cancel(self) -> str:
        return self._state.cancel(self)

    def refill(self, product: Product, quantity: int) -> None:
        """Admin operation: restock a product. Does not go through state."""
        self.inventory.add(product, quantity)


# ------------------------------------------------------------------
# Composition root
# ------------------------------------------------------------------

if __name__ == "__main__":
    machine = VendingMachine()
    machine.refill(Product("Coke", 1.50), 5)
    machine.refill(Product("Chips", 2.00), 3)

    print(machine.select_product("Coke"))        # Please insert money first.
    print(machine.insert_coin(1.00))              # Inserted 1.0. Total: 1.0
    print(machine.insert_coin(0.75))              # Added 0.75. Total: 1.75
    print(machine.select_product("Coke"))         # Dispensing 'Coke'. Your change: 0.25
    print()
    print(machine.insert_coin(2.00))              # Inserted 2.0. Total: 2.0
    print(machine.select_product("Chips"))        # Dispensing 'Chips'. Exact amount, no change.
    print()
    print(machine.insert_coin(1.00))
    print(machine.cancel())                       # Cancelled. Returning 1.0.
    print()
    print(machine.insert_coin(0.50))
    print(machine.select_product("Coke"))         # Insufficient funds.
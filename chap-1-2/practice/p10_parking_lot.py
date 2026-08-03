# P10 - Parking Lot
#
# Patterns used: Strategy (spot assignment), Composition, OCP via dict mapping
#
# The key OCP challenge: vehicle types needing different spot types.
# Wrong approach: if/elif in assign() checking vehicle type.
# Right approach: a COMPATIBLE_SPOTS dict that maps vehicle -> compatible spot types.
# Adding a new vehicle type = add one entry to the dict. Zero edits to assign logic.
#
# CLASS DIAGRAM
# =============
#
#   +----------+      +-------------+      +---------+
#   | SpotType |      | ParkingSpot |      |  Floor  |
#   | (Enum)   |      |-------------|      |---------|
#   | COMPACT  |<-----| spot_id     |<-----| number  |
#   | LARGE    |      | spot_type   |      | spots   |
#   | MOTORCYCLE      | is_occupied |      | find_spot|
#   +----------+      | occupy()    |      | available|
#                     | free()      |      | report() |
#                     +-------------+      +---------+
#                                                |
#   +------------+    +----------------------+   |
#   | VehicleType|    | SpotAssignmentStrategy|  |
#   | (Enum)     |    |----------------------|   |
#   | CAR        |    | assign(vehicle,floors)|  |
#   | TRUCK      |    +----------------------+   |
#   | MOTORCYCLE |              |           +----------+
#   +------------+    NearestFirstStrategy  |ParkingLot|
#          |                                |----------|
#   +------------+                          | floors   |
#   |  Vehicle   |                          | strategy |
#   |------------|                          | park()   |
#   | plate: str |                          | leave()  |
#   | type       |                          | report() |
#   +------------+                          +----------+
#
# Responsibilities:
#   SpotType              - enumerates spot categories
#   VehicleType           - enumerates vehicle categories
#   COMPATIBLE_SPOTS      - data-driven mapping, replaces all if/elif on vehicle type
#   ParkingSpot           - owns one spot's state (occupied/free)
#   Floor                 - owns all spots on one floor, finds available spots
#   Vehicle               - holds vehicle identity and type
#   SpotAssignmentStrategy - Protocol for pluggable assignment logic
#   NearestFirstStrategy  - concrete strategy: scan floors top-down for first available
#   ParkingLot            - entry/exit orchestration and reporting

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol


# ------------------------------------------------------------------
# Enums: pure data, no behavior
# ------------------------------------------------------------------

class SpotType(Enum):
    COMPACT = auto()
    LARGE = auto()
    MOTORCYCLE = auto()


class VehicleType(Enum):
    CAR = auto()
    TRUCK = auto()
    MOTORCYCLE = auto()


# ------------------------------------------------------------------
# Compatibility mapping: the OCP trick for vehicle -> spot assignment
#
# Instead of:
#   if vehicle.type == CAR: return COMPACT or LARGE
#   elif vehicle.type == TRUCK: return LARGE only
#   ...
#
# We use a dict. Adding VehicleType.VAN = [SpotType.LARGE] is one line.
# NearestFirstStrategy reads this dict, never checks vehicle type directly.
# ------------------------------------------------------------------

COMPATIBLE_SPOTS: dict[VehicleType, list[SpotType]] = {
    VehicleType.CAR: [SpotType.COMPACT, SpotType.LARGE],
    VehicleType.TRUCK: [SpotType.LARGE],
    VehicleType.MOTORCYCLE: [SpotType.MOTORCYCLE],
}


# ------------------------------------------------------------------
# Vehicle: pure data
# ------------------------------------------------------------------

@dataclass
class Vehicle:
    """Owns: vehicle identity and type.
    Reason to change: vehicle attributes change (add EV flag, size, etc)."""
    plate: str
    vehicle_type: VehicleType


# ------------------------------------------------------------------
# ParkingSpot: manages one spot's occupied state
# ------------------------------------------------------------------

class ParkingSpot:
    """Owns: a single parking spot's state.
    Reason to change: spot-level rules change (reserved spots, EV charging, time limits).

    Encapsulation: _occupied is private. Callers use occupy() and free(), not direct writes."""

    def __init__(self, spot_id: str, spot_type: SpotType):
        self._id = spot_id
        self._type = spot_type
        self._occupied = False
        self._vehicle: Vehicle | None = None

    @property
    def spot_id(self) -> str:
        return self._id

    @property
    def spot_type(self) -> SpotType:
        return self._type

    @property
    def is_occupied(self) -> bool:
        return self._occupied

    def occupy(self, vehicle: Vehicle) -> None:
        self._occupied = True
        self._vehicle = vehicle

    def free(self) -> None:
        self._occupied = False
        self._vehicle = None


# ------------------------------------------------------------------
# Floor: manages all spots on one floor
# ------------------------------------------------------------------

class Floor:
    """Owns: managing all spots on one floor and finding available ones.
    Reason to change: floor-level rules change (VIP floor, floor weight limits).

    Floor does not know which vehicle is looking for a spot.
    It only knows: here is a list of compatible spot types, find me one."""

    def __init__(self, floor_number: int, spots: list[ParkingSpot]):
        self._number = floor_number
        self._spots = spots

    @property
    def floor_number(self) -> int:
        return self._number

    def find_spot(self, compatible_types: list[SpotType]) -> ParkingSpot | None:
        """Returns first available spot whose type is in compatible_types."""
        for spot in self._spots:
            if not spot.is_occupied and spot.spot_type in compatible_types:
                return spot
        return None

    def available_count(self, spot_type: SpotType | None = None) -> int:
        spots = self._spots if spot_type is None else [
            s for s in self._spots if s.spot_type == spot_type
        ]
        return sum(1 for s in spots if not s.is_occupied)

    def total_count(self, spot_type: SpotType | None = None) -> int:
        if spot_type is None:
            return len(self._spots)
        return sum(1 for s in self._spots if s.spot_type == spot_type)


# ------------------------------------------------------------------
# Assignment strategy: pluggable, swappable without touching ParkingLot
# ------------------------------------------------------------------

class SpotAssignmentStrategy(Protocol):
    """Shape for any spot assignment algorithm.
    Reason to change: the strategy interface changes.

    ParkingLot depends on this Protocol, not on NearestFirstStrategy.
    Swapping strategy (nearest vs. spread-evenly vs. VIP-first) = inject a different object."""

    def assign(self, vehicle: Vehicle, floors: list[Floor]) -> ParkingSpot | None: ...


class NearestFirstStrategy:
    """Owns: finding the nearest available compatible spot across all floors.
    Reason to change: assignment priority changes (e.g. prefer ground floor, prefer EV spots).

    Uses COMPATIBLE_SPOTS dict instead of if/elif.
    Adding VehicleType.VAN requires zero edits here."""

    def assign(self, vehicle: Vehicle, floors: list[Floor]) -> ParkingSpot | None:
        compatible = COMPATIBLE_SPOTS.get(vehicle.vehicle_type, [])
        for floor in floors:
            spot = floor.find_spot(compatible)
            if spot:
                return spot
        return None


# ------------------------------------------------------------------
# ParkingLot: orchestrates entry, exit, and reporting
# ------------------------------------------------------------------

class ParkingLot:
    """Owns: vehicle entry, exit, and lot-level reporting.
    Reason to change: lot-level policies change (pricing, max vehicles per type, waitlists).

    DIP: depends on SpotAssignmentStrategy Protocol, not on NearestFirstStrategy.
    Inject a different strategy object to change assignment behavior with zero edits here."""

    def __init__(self, floors: list[Floor], strategy: SpotAssignmentStrategy):
        self._floors = floors
        self._strategy = strategy
        self._parked: dict[str, ParkingSpot] = {}  # plate -> spot

    def park(self, vehicle: Vehicle) -> str:
        if vehicle.plate in self._parked:
            return f"Vehicle {vehicle.plate} is already parked."

        spot = self._strategy.assign(vehicle, self._floors)
        if spot is None:
            return f"No available spot for {vehicle.vehicle_type.name}."

        spot.occupy(vehicle)
        self._parked[vehicle.plate] = spot
        return (
            f"Vehicle {vehicle.plate} ({vehicle.vehicle_type.name}) "
            f"parked at spot {spot.spot_id} "
            f"(Floor {spot.spot_id.split('-')[0]}, {spot.spot_type.name})."
        )

    def leave(self, plate: str) -> str:
        spot = self._parked.pop(plate, None)
        if spot is None:
            return f"Vehicle {plate} not found in the lot."

        spot.free()
        return f"Vehicle {plate} has left. Spot {spot.spot_id} is now free."

    def report(self) -> None:
        print("\n--- Parking Lot Report ---")
        for floor in self._floors:
            print(f"\nFloor {floor.floor_number}:")
            for spot_type in SpotType:
                total = floor.total_count(spot_type)
                available = floor.available_count(spot_type)
                occupied = total - available
                print(f"  {spot_type.name:<12} {available}/{total} available  ({occupied} occupied)")


# ------------------------------------------------------------------
# Composition root
# ------------------------------------------------------------------

if __name__ == "__main__":
    floor1 = Floor(1, [
        ParkingSpot("F1-C1", SpotType.COMPACT),
        ParkingSpot("F1-C2", SpotType.COMPACT),
        ParkingSpot("F1-L1", SpotType.LARGE),
        ParkingSpot("F1-M1", SpotType.MOTORCYCLE),
    ])
    floor2 = Floor(2, [
        ParkingSpot("F2-C1", SpotType.COMPACT),
        ParkingSpot("F2-L1", SpotType.LARGE),
        ParkingSpot("F2-L2", SpotType.LARGE),
    ])

    lot = ParkingLot([floor1, floor2], NearestFirstStrategy())

    car1   = Vehicle("ABC-001", VehicleType.CAR)
    car2   = Vehicle("ABC-002", VehicleType.CAR)
    truck  = Vehicle("TRK-001", VehicleType.TRUCK)
    bike   = Vehicle("MTC-007", VehicleType.MOTORCYCLE)

    print(lot.park(car1))
    print(lot.park(car2))
    print(lot.park(truck))
    print(lot.park(bike))
    print(lot.park(car1))   # already parked

    lot.report()

    print()
    print(lot.leave("ABC-001"))
    print(lot.leave("ZZZ-999"))  # not found

    lot.report()
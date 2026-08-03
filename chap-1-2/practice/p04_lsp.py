from typing import Protocol


# FIX 1: Removed the concrete SeaBird class. Concrete base classes are a design smell.
#         If a class exists only to be inherited, it should be a Protocol or ABC.
#
# FIX 2: Instead of one Bird class that promises fly() to everyone,
#         we now have two Protocols: one for birds that fly, one for birds that don't.
#         Penguin satisfies NonFlyingBird. It never even claims to fly.
#         The contract mismatch is caught by the type checker, not at runtime.
#
# Your instinct (don't make Penguin inherit from Bird) was exactly right.
# The only gap was leaving SeaBird as a concrete class and not using Protocols.


# Contract for birds that can fly AND eat.
class FlyingBird(Protocol):
    def fly(self) -> str: ...
    def eat(self) -> str: ...


# Contract for birds that can only eat (no fly promise made at all).
class NonFlyingBird(Protocol):
    def eat(self) -> str: ...


# Satisfies FlyingBird: has both fly() and eat().
class Sparrow:
    def fly(self) -> str:
        return "flying"

    def eat(self) -> str:
        return "eating"


# Satisfies NonFlyingBird: has eat(), never promises fly().
# No NotImplementedError. No broken contract. Penguin just IS what it is.
class Penguin:
    def eat(self) -> str:
        return "eating"


# This function only accepts FlyingBird. Penguin cannot be passed here.
# The type checker catches it before runtime. No surprises.
def make_fly(bird: FlyingBird) -> str:
    return bird.fly()


# This function accepts anything that can eat, flying or not.
def feed(bird: NonFlyingBird) -> str:
    return bird.eat()


sparrow = Sparrow()
penguin = Penguin()

print(make_fly(sparrow))   # fine
print(feed(sparrow))       # fine
print(feed(penguin))       # fine

# make_fly(penguin)        # mypy error: Penguin has no fly(). Caught before runtime.
from abc import ABC, abstractmethod


# FIX 1: Removed the original fat Worker ABC. It was the problem, not part of the solution.
#         Keeping it alongside the fix is like leaving a bug in code after writing the patch.
#
# FIX 2: Renamed WorkerCanEat -> Eatable, WorkerCanSleep -> Sleepable, WorkerCanWork -> Workable.
#         Python convention: role interfaces are named as adjectives (Eatable, Iterable, Comparable)
#         or short nouns (Eater, Sleeper), not verb phrases (WorkerCanEat).
#         This is not just style. When you read HumanWorker(Workable, Eatable, Sleepable)
#         it reads like English: "A HumanWorker is workable, eatable, and sleepable."
#         When you read HumanWorker(WorkerCanWork, WorkerCanEat, WorkerCanSleep) it reads like
#         a sentence someone translated from another language.
#
# The logic is identical to what you wrote. Only the fat interface is removed and names are fixed.


class Workable(ABC):
    @abstractmethod
    def work(self): ...


class Eatable(ABC):
    @abstractmethod
    def eat(self): ...


class Sleepable(ABC):
    @abstractmethod
    def sleep(self): ...


# HumanWorker implements all three roles because humans actually do all three.
class HumanWorker(Workable, Eatable, Sleepable):
    def work(self): print("Human working")
    def eat(self):  print("Human eating")
    def sleep(self): print("Human sleeping")


# RobotWorker implements only Workable because robots only work.
# No NotImplementedError. No forced contract. Clean.
class RobotWorker(Workable):
    def work(self): print("Robot working")


human = HumanWorker()
robot = RobotWorker()

human.work()
human.eat()
human.sleep()
robot.work()
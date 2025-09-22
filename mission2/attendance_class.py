from enum import Enum
from dataclasses import dataclass
from typing import Dict, List
from pathlib import Path
from abc import ABC, abstractmethod

FILE_PATH = "attendance_weekday_500.txt"

GRADE_GOLD_THRESH = 50
GRADE_SILVER_THRESH = 30

POINTS_WED = 3
POINTS_WEEKEND = 2
POINTS_NORMAL = 1

BONUS_WED_THRESH = 10
BONUS_WEEKEND_THRESH = 10
BONUS_POINTS_WED = 10
BONUS_POINTS_WEEKEND = 10


class DayOfWeek(Enum):
    MONDAY = (0, POINTS_NORMAL)
    TUESDAY = (1, POINTS_NORMAL)
    WEDNESDAY = (2, POINTS_WED)
    THURSDAY = (3, POINTS_NORMAL)
    FRIDAY = (4, POINTS_NORMAL)
    SATURDAY = (5, POINTS_WEEKEND)
    SUNDAY = (6, POINTS_WEEKEND)

    def __init__(self, index: int, points: int):
        self.index = index
        self.points = points

    @classmethod
    def from_string(cls, day_str: str) -> "DayOfWeek":
        return cls[day_str.upper()]


class GradeFactory(Enum):
    GOLD = 1
    SILVER = 2
    NORMAL = 0

    @classmethod
    def points_to_grade(cls, points: int) -> "GradeFactory":
        if points >= GRADE_GOLD_THRESH:
            return cls.GOLD
        elif points >= GRADE_SILVER_THRESH:
            return cls.SILVER
        else:
            return cls.NORMAL


@dataclass
class User:
    name: str
    id: int
    attendance: List[int]  # Attendance count per day
    points: int = 0
    wednesday_count: int = 0
    weekend_count: int = 0
    grade: GradeFactory = GradeFactory.NORMAL


class IAttendanceSystem(ABC):
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.next_id: int = 0

    def process_file(self, filename: str) -> None:
        try:
            with Path(filename).open(encoding="utf-8") as file:
                for line in file:
                    parts = line.strip().split()
                    if len(parts) == 2:
                        self.add_attendance(parts[0], parts[1])
                self.calculate_grades()
                self.print_results()
        except FileNotFoundError:
            print("파일을 찾을 수 없습니다.")

    def print_results(self) -> None:
        for user in self.users.values():
            print(f"NAME: {user.name}, POINT: {user.points}, GRADE: {user.grade.name}")

        print("\nRemoved player")
        print("==============")
        for user in self.users.values():
            if (
                user.grade == GradeFactory.NORMAL
                and user.wednesday_count == 0
                and user.weekend_count == 0
            ):
                print(user.name)

    def create_user(self, name: str) -> None:
        self.next_id += 1
        self.users[name] = User(name=name, id=self.next_id, attendance=[0] * 7)

    @abstractmethod
    def add_attendance(self, name: str, day: str) -> None:
        pass

    @abstractmethod
    def calculate_grades(self) -> None:
        pass


class AttendanceSystem(IAttendanceSystem):
    def __init__(self):
        super().__init__()

    def add_attendance(self, name: str, day: str) -> None:
        if name not in self.users:
            self.create_user(name)

        user = self.users[name]
        day_info = DayOfWeek.from_string(day)

        user.attendance[day_info.index] += 1
        user.points += day_info.points

        if day_info in (DayOfWeek.WEDNESDAY,):
            user.wednesday_count += 1
        if day_info in (DayOfWeek.SATURDAY, DayOfWeek.SUNDAY):
            user.weekend_count += 1

    def calculate_grades(self) -> None:
        for user in self.users.values():
            # Bonus points
            if user.attendance[DayOfWeek.WEDNESDAY.index] > BONUS_WED_THRESH - 1:
                user.points += BONUS_POINTS_WED
            if (
                sum(user.attendance[DayOfWeek.SATURDAY.index :])
                > BONUS_WEEKEND_THRESH - 1
            ):
                user.points += BONUS_POINTS_WEEKEND

            # Assign grade using factory method
            user.grade = GradeFactory.points_to_grade(user.points)


def main():
    system = AttendanceSystem()
    system.process_file(FILE_PATH)


if __name__ == "__main__":
    main()

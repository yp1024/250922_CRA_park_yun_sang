from typing import List, OrderedDict
from collections import OrderedDict

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


def read_attendance(file_path: str) -> List:
    attendance = []
    try:
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    attendance.append((parts[0], parts[1].lower()))
    except FileNotFoundError:
        print("파일을 찾을 수 없습니다.")
        return []
    return attendance


def process_attendance(attendance_data: List):
    users = OrderedDict()  # name: {"attendance", "points"}
    day_map = {
        "monday": (0, POINTS_NORMAL),  # "day of week": (index_day, points)
        "tuesday": (1, POINTS_NORMAL),
        "wednesday": (2, POINTS_WED),
        "thursday": (3, POINTS_NORMAL),
        "friday": (4, POINTS_NORMAL),
        "saturday": (5, POINTS_WEEKEND),
        "sunday": (6, POINTS_WEEKEND),
    }
    for name, day in attendance_data:
        if day not in day_map:
            continue
        if name not in users:
            users[name] = {"attendance": [0] * 7, "points": 0}
        user = users[name]
        idx, pts = day_map[day]
        user["attendance"][idx] += 1
        user["points"] += pts
    return users


def add_bonuses(users: OrderedDict) -> None:
    for user in users.values():
        att = user["attendance"]
        if att[2] > BONUS_WED_THRESH - 1:
            user["points"] += BONUS_POINTS_WED
        if att[5] + att[6] > BONUS_WEEKEND_THRESH - 1:
            user["points"] += BONUS_POINTS_WEEKEND


def assign_grades(users: OrderedDict):
    for user in users.values():
        pts = user["points"]
        if pts >= GRADE_GOLD_THRESH:
            user["grade"] = "GOLD"
        elif pts >= GRADE_SILVER_THRESH:
            user["grade"] = "SILVER"
        else:
            user["grade"] = "NORMAL"


def print_results(users: OrderedDict):
    for name, user in users.items():
        print(f"NAME : {name}, POINT : {user['points']}, GRADE : {user['grade']}")


def print_removed(users: OrderedDict):
    print("\nRemoved player")
    print("==============")
    for name, user in users.items():
        att = user["attendance"]
        if user["grade"] == "NORMAL" and att[2] == 0 and (att[5] + att[6]) == 0:
            print(name)


def main():
    attendance_data = read_attendance(FILE_PATH)
    if attendance_data:
        users = process_attendance(attendance_data)
        add_bonuses(users)
        assign_grades(users)
        print_results(users)
        print_removed(users)


if __name__ == "__main__":
    main()

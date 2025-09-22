import pytest

from attendance_class import (
    DayOfWeek,
    GradeFactory,
    User,
    AttendanceSystem,
)


@pytest.fixture
def attendance_system():
    return AttendanceSystem()


def test_day_of_week_enum():
    assert DayOfWeek.MONDAY.index == 0
    assert DayOfWeek.MONDAY.points == 1
    assert DayOfWeek.WEDNESDAY.points == 3
    assert DayOfWeek.SATURDAY.points == 2
    assert DayOfWeek.from_string("monday") == DayOfWeek.MONDAY
    assert DayOfWeek.from_string("WEDNESDAY") == DayOfWeek.WEDNESDAY
    with pytest.raises(KeyError):
        DayOfWeek.from_string("invalid_day")


def test_user_dataclass():
    user = User(name="test", id=1, attendance=[0] * 7)
    assert user.name == "test"
    assert user.id == 1
    assert user.points == 0
    assert user.wednesday_count == 0
    assert user.weekend_count == 0
    assert user.grade == GradeFactory.NORMAL


def test_attendance_system_init(attendance_system):
    assert attendance_system.users == {}
    assert attendance_system.next_id == 0


def test_create_user(attendance_system):
    attendance_system.add_attendance("user1", "monday")
    assert "user1" in attendance_system.users
    user = attendance_system.users["user1"]
    assert user.id == 1
    assert user.name == "user1"
    assert user.attendance == [1, 0, 0, 0, 0, 0, 0]
    assert user.points == 1
    assert user.wednesday_count == 0
    assert user.weekend_count == 0


def test_add_attendance_existing_user(attendance_system):
    attendance_system.add_attendance("user1", "monday")
    attendance_system.add_attendance("user1", "tuesday")
    user = attendance_system.users["user1"]
    assert user.attendance == [1, 1, 0, 0, 0, 0, 0]
    assert user.points == 2


def test_add_attendance_different_days(attendance_system):
    attendance_system.add_attendance("user1", "monday")  # +1
    attendance_system.add_attendance("user1", "wednesday")  # +3, wed+1
    attendance_system.add_attendance("user1", "saturday")  # +2, weekend+1
    user = attendance_system.users["user1"]
    assert user.points == 6
    assert user.wednesday_count == 1
    assert user.weekend_count == 1
    assert user.attendance[0] == 1
    assert user.attendance[2] == 1
    assert user.attendance[5] == 1


def test_add_attendance_multiple_users(attendance_system):
    attendance_system.add_attendance("user1", "monday")
    attendance_system.add_attendance("user2", "tuesday")
    assert len(attendance_system.users) == 2
    assert attendance_system.users["user1"].id == 1
    assert attendance_system.users["user2"].id == 2


def test_calculate_grades_no_bonus(attendance_system):
    attendance_system.add_attendance("user1", "monday")  # points=1
    attendance_system.calculate_grades()
    user = attendance_system.users["user1"]
    assert user.points == 1
    assert user.grade == GradeFactory.NORMAL


def test_calculate_grades_with_wed_bonus(attendance_system):
    for _ in range(10):
        attendance_system.add_attendance(
            "user1", "wednesday"
        )  # 10*3 = 30 +10 bonus =40
    attendance_system.calculate_grades()
    user = attendance_system.users["user1"]
    assert user.points == 40
    assert user.grade == GradeFactory.SILVER


def test_calculate_grades_with_weekend_bonus(attendance_system):
    for _ in range(5):
        attendance_system.add_attendance("user1", "saturday")  # 5*2=10
        attendance_system.add_attendance(
            "user1", "sunday"
        )  # 5*2=10, total weekends=10, +10 bonus, total points=30
    attendance_system.calculate_grades()
    user = attendance_system.users["user1"]
    assert user.points == 30
    assert user.grade == GradeFactory.SILVER


def test_calculate_grades_gold(attendance_system):
    for _ in range(20):
        attendance_system.add_attendance("user1", "wednesday")  # 20*3=60 +10 bonus=70
    attendance_system.calculate_grades()
    user = attendance_system.users["user1"]
    assert user.points == 70
    assert user.grade == GradeFactory.GOLD


def test_calculate_grades_combined_bonuses(attendance_system):
    for _ in range(10):
        attendance_system.add_attendance("user1", "wednesday")  # 30 +10=40
    for _ in range(10):
        attendance_system.add_attendance(
            "user1", "saturday"
        )  # 20 +10=30, total points=70
    attendance_system.calculate_grades()
    user = attendance_system.users["user1"]
    assert user.points == 70
    assert user.grade == GradeFactory.GOLD


def test_print_results(capsys, attendance_system):
    attendance_system.add_attendance(
        "user1", "monday"
    )  # NORMAL, wed=0, weekend=0 -> removed
    attendance_system.add_attendance(
        "user2", "wednesday"
    )  # points=3, NORMAL, wed=1 -> not removed
    attendance_system.add_attendance(
        "user3", "saturday"
    )  # points=2, NORMAL, weekend=1 -> not removed
    for _ in range(20):
        attendance_system.add_attendance("user4", "monday")  # points=20, SILVER
    for _ in range(30):
        attendance_system.add_attendance("user5", "monday")  # points=30, SILVER
    for _ in range(50):
        attendance_system.add_attendance("user6", "monday")  # points=50, GOLD
    attendance_system.calculate_grades()
    attendance_system.print_results()
    captured = capsys.readouterr()
    output = captured.out
    assert "NAME: user1, POINT: 1, GRADE: NORMAL" in output
    assert "NAME: user2, POINT: 3, GRADE: NORMAL" in output
    assert "NAME: user3, POINT: 2, GRADE: NORMAL" in output
    assert (
        "NAME: user4, POINT: 20, GRADE: NORMAL" in output
    )  # Wait, 20 mondays=20, <30, NORMAL
    # Fix: to test SILVER, need >=30
    # Actually in test, user4:20->20 NORMAL, user5:30->30 SILVER, user6:50->50 GOLD
    assert "NAME: user5, POINT: 30, GRADE: SILVER" in output
    assert "NAME: user6, POINT: 50, GRADE: GOLD" in output
    assert "\nRemoved player\n==============\n" in output
    assert "user1\n" in output
    assert "user2" not in output.split("==============")[1]  # Not removed
    assert "user3" not in output.split("==============")[1]  # Not removed


def test_process_file(tmp_path, capsys):
    # create a temporary file with test data
    file_content = """
        user1 monday
        user1 wednesday
        user2 saturday
        user3 monday extra  # len>2, skipped
        """
    test_file = tmp_path / "attendance_weekday_500.txt"
    test_file.write_text(file_content, encoding="utf-8")

    system = AttendanceSystem()
    system.process_file(str(test_file))
    captured = capsys.readouterr()
    output = captured.out

    assert "NAME: user1, POINT: 4, GRADE: NORMAL" in output
    assert "NAME: user2, POINT: 2, GRADE: NORMAL" in output
    assert "\nRemoved player\n==============\n" in output


def test_file_not_found(capsys):
    system = AttendanceSystem()
    system.process_file("./FileDoNotExist.txt")

    captured = capsys.readouterr()
    assert "파일을 찾을 수 없습니다." in captured.out


# def test_process_file_not_found(monkeypatch):
#     def mock_open(*args, **kwargs):
#         raise FileNotFoundError
#
#     monkeypatch.setattr(Path, "open", mock_open)
#     system = AttendanceSystem()
#     with pytest.raises(FileNotFoundError):
#         system.process_file()  # But actually, it catches and prints
#
#     # Wait, the code catches FileNotFoundError and prints message
#     # So, use capsys
#     def test_process_file_not_found(capsys, monkeypatch):
#         def mock_open(*args, **kwargs):
#             raise FileNotFoundError
#
#         monkeypatch.setattr(Path, "open", mock_open)
#         system = AttendanceSystem()
#         system.process_file()
#         captured = capsys.readouterr()
#         assert "파일을 찾을 수 없습니다." in captured.out

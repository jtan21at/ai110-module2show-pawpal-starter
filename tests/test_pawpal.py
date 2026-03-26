"""Automated tests for PawPal+ core scheduling behaviors."""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_owner() -> Owner:
    """Return an Owner with two pets and several tasks for today."""
    owner = Owner("TestOwner")
    today = date.today()

    dog = Pet("Rex", "dog", 2)
    dog.add_task(Task("Walk", "09:00", 20, "high", "daily", due_date=today))
    dog.add_task(Task("Feed", "07:00", 10, "medium", "daily", due_date=today))
    dog.add_task(Task("Play", "14:00", 15, "low", "once", due_date=today))

    cat = Pet("Whiskers", "cat", 3)
    cat.add_task(Task("Feed", "07:30", 10, "high", "daily", due_date=today))
    cat.add_task(Task("Litter", "12:00", 5, "medium", "daily", due_date=today))

    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner


# ---------------------------------------------------------------------------
# Task Completion
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    """Calling mark_complete() must flip Task.completed to True."""
    task = Task("Bath", "10:00", 20, "medium", "once", due_date=date.today())
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_scheduler_mark_task_complete_returns_true_when_found():
    """Scheduler.mark_task_complete returns True for an existing task."""
    owner = _make_owner()
    scheduler = Scheduler(owner)
    result = scheduler.mark_task_complete("Rex", "Walk")
    assert result is True


def test_scheduler_mark_task_complete_returns_false_when_not_found():
    """Scheduler.mark_task_complete returns False for a nonexistent pet/task."""
    owner = _make_owner()
    scheduler = Scheduler(owner)
    assert scheduler.mark_task_complete("Rex", "Nonexistent task") is False
    assert scheduler.mark_task_complete("Ghost", "Walk") is False


# ---------------------------------------------------------------------------
# Task Addition
# ---------------------------------------------------------------------------

def test_add_task_increases_count():
    """Adding a task to a Pet must increase its task count by one."""
    pet = Pet("Buddy", "dog", 1)
    initial = len(pet.tasks)
    pet.add_task(Task("Bath", "11:00", 30, "medium", "weekly", due_date=date.today()))
    assert len(pet.tasks) == initial + 1


def test_remove_task_decreases_count():
    """Removing a task must decrease the pet's task count."""
    pet = Pet("Buddy", "dog", 1)
    pet.add_task(Task("Bath", "11:00", 30, "medium", "weekly", due_date=date.today()))
    assert pet.remove_task("Bath") is True
    assert len(pet.tasks) == 0


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

def test_sort_by_time_is_chronological():
    """Tasks returned by sort_by_time must be in ascending HH:MM order."""
    owner = _make_owner()
    scheduler = Scheduler(owner)
    times = [t.time for _, t in scheduler.sort_by_time()]
    assert times == sorted(times)


def test_sort_by_priority_then_time_high_first():
    """High-priority tasks must come before medium and low in the sorted list."""
    owner = _make_owner()
    scheduler = Scheduler(owner)
    priorities = [t.priority for _, t in scheduler.sort_by_priority_then_time()]
    order_values = {"high": 0, "medium": 1, "low": 2}
    numeric = [order_values[p] for p in priorities]
    assert numeric == sorted(numeric)


# ---------------------------------------------------------------------------
# Recurrence Logic
# ---------------------------------------------------------------------------

def test_daily_recurring_task_creates_next_occurrence():
    """Completing a daily task must add a new task due the following day."""
    owner = Owner("A")
    pet = Pet("Pip", "cat", 1)
    today = date.today()
    pet.add_task(Task("Feed", "08:00", 10, "high", "daily", due_date=today))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    scheduler.mark_task_complete("Pip", "Feed")

    assert len(pet.tasks) == 2
    new_task = pet.tasks[1]
    assert new_task.due_date == today + timedelta(days=1)
    assert new_task.completed is False


def test_weekly_recurring_task_creates_next_occurrence():
    """Completing a weekly task must add a new task due seven days later."""
    owner = Owner("B")
    pet = Pet("Max", "dog", 3)
    today = date.today()
    pet.add_task(Task("Grooming", "10:00", 45, "medium", "weekly", due_date=today))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    scheduler.mark_task_complete("Max", "Grooming")

    assert len(pet.tasks) == 2
    assert pet.tasks[1].due_date == today + timedelta(weeks=1)


def test_once_task_does_not_create_next_occurrence():
    """Completing a one-off task must NOT create a follow-up task."""
    owner = Owner("C")
    pet = Pet("Nemo", "fish", 1)
    today = date.today()
    pet.add_task(Task("Vet visit", "09:00", 60, "high", "once", due_date=today))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    scheduler.mark_task_complete("Nemo", "Vet visit")

    assert len(pet.tasks) == 1  # no new task added


# ---------------------------------------------------------------------------
# Conflict Detection
# ---------------------------------------------------------------------------

def test_conflict_detection_flags_same_time_same_pet():
    """Two tasks for the same pet at the same time must produce one warning."""
    owner = Owner("D")
    pet = Pet("Bear", "dog", 2)
    today = date.today()
    pet.add_task(Task("Walk", "10:00", 20, "high", "daily", due_date=today))
    pet.add_task(Task("Grooming", "10:00", 30, "medium", "once", due_date=today))
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 1
    assert "10:00" in warnings[0]
    assert "Bear" in warnings[0]


def test_no_conflict_when_different_times():
    """Tasks at different times must not trigger any conflict warning."""
    owner = _make_owner()
    scheduler = Scheduler(owner)
    # _make_owner builds tasks at distinct times per pet
    warnings = scheduler.detect_conflicts()
    assert warnings == []


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def test_filter_by_status_returns_only_pending():
    """filter_by_status(False) must return only incomplete tasks."""
    owner = _make_owner()
    scheduler = Scheduler(owner)
    incomplete = scheduler.filter_by_status(False)
    assert all(not t.completed for _, t in incomplete)


def test_filter_by_pet_returns_correct_pet_only():
    """filter_by_pet must return only tasks belonging to the named pet."""
    owner = _make_owner()
    scheduler = Scheduler(owner)
    rex_tasks = scheduler.filter_by_pet("Rex")
    assert all(p.name == "Rex" for p, _ in rex_tasks)
    assert len(rex_tasks) == 3


# ---------------------------------------------------------------------------
# Data Persistence
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip(tmp_path):
    """Saving an Owner to JSON and loading it back must preserve all data."""
    owner = _make_owner()
    filepath = str(tmp_path / "data.json")
    owner.save_to_json(filepath)

    restored = Owner.load_from_json(filepath)
    assert restored.name == owner.name
    assert len(restored.pets) == len(owner.pets)
    original_tasks = [t.description for _, t in owner.get_all_tasks()]
    restored_tasks = [t.description for _, t in restored.get_all_tasks()]
    assert sorted(original_tasks) == sorted(restored_tasks)

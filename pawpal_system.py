"""PawPal+ logic layer: Task, Pet, Owner, and Scheduler class skeletons."""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class Task:
    """Represents a single pet care activity."""

    description: str
    time: str  # HH:MM format
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    frequency: str  # "once", "daily", "weekly"
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> None:
        """Mark this task as complete."""
        pass

    def is_due_today(self) -> bool:
        """Return True if the task is due today."""
        pass


class Pet:
    """Stores pet details and a list of tasks."""

    def __init__(self, name: str, species: str, age: int) -> None:
        self.name = name
        self.species = species
        self.age = age
        self.tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        pass

    def remove_task(self, description: str) -> bool:
        """Remove the first task whose description matches; return True if removed."""
        pass

    def get_tasks(self) -> List[Task]:
        """Return all tasks for this pet."""
        pass


class Owner:
    """Manages multiple pets and provides access to all their tasks."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list."""
        pass

    def get_all_tasks(self) -> List[tuple]:
        """Return all (Pet, Task) pairs across every pet."""
        pass

    def get_pet(self, name: str) -> Optional[Pet]:
        """Find and return a pet by name (case-insensitive), or None."""
        pass

    def save_to_json(self, filepath: str) -> None:
        """Serialize owner + pets + tasks to a JSON file."""
        pass

    @classmethod
    def load_from_json(cls, filepath: str) -> "Owner":
        """Deserialize and return an Owner instance from a JSON file."""
        pass


class Scheduler:
    """The 'Brain' that retrieves, organises, and manages tasks across pets."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def get_all_tasks(self) -> List[tuple]:
        """Return all (Pet, Task) pairs from the owner."""
        pass

    def sort_by_time(self) -> List[tuple]:
        """Return tasks sorted chronologically by HH:MM time string."""
        pass

    def sort_by_priority_then_time(self) -> List[tuple]:
        """Return tasks sorted by priority (high first), then by time."""
        pass

    def filter_by_status(self, completed: bool) -> List[tuple]:
        """Return tasks filtered by completion status."""
        pass

    def filter_by_pet(self, pet_name: str) -> List[tuple]:
        """Return tasks belonging to the named pet (case-insensitive)."""
        pass

    def detect_conflicts(self) -> List[str]:
        """Return warning strings for tasks scheduled at the same time for the same pet."""
        pass

    def mark_task_complete(self, pet_name: str, description: str) -> bool:
        """Mark a task complete and auto-reschedule recurring tasks. Return True if found."""
        pass

    def today_schedule(self) -> List[tuple]:
        """Return today's incomplete tasks sorted by priority then time."""
        pass

    def get_next_available_slot(self, after_time: str = "07:00") -> Optional[str]:
        """Return the next 30-minute time slot (HH:MM) with no task, starting after_time."""
        pass

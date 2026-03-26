"""PawPal+ logic layer: Task, Pet, Owner, and Scheduler classes."""

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple


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
        self.completed = True

    def is_due_today(self) -> bool:
        """Return True if the task is due today."""
        return self.due_date == date.today()


class Pet:
    """Stores pet details and a list of tasks."""

    def __init__(self, name: str, species: str, age: int) -> None:
        self.name = name
        self.species = species
        self.age = age
        self.tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove the first task whose description matches; return True if removed."""
        for i, t in enumerate(self.tasks):
            if t.description == description:
                del self.tasks[i]
                return True
        return False

    def get_tasks(self) -> List[Task]:
        """Return all tasks for this pet."""
        return self.tasks


class Owner:
    """Manages multiple pets and provides access to all their tasks."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's list."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Tuple[Pet, Task]]:
        """Return all (Pet, Task) pairs across every pet."""
        return [(pet, task) for pet in self.pets for task in pet.get_tasks()]

    def get_pet(self, name: str) -> Optional[Pet]:
        """Find and return a pet by name (case-insensitive), or None."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def save_to_json(self, filepath: str) -> None:
        """Serialize owner + pets + tasks to a JSON file."""
        data: Dict = {
            "name": self.name,
            "pets": [
                {
                    "name": pet.name,
                    "species": pet.species,
                    "age": pet.age,
                    "tasks": [
                        {
                            "description": t.description,
                            "time": t.time,
                            "duration_minutes": t.duration_minutes,
                            "priority": t.priority,
                            "frequency": t.frequency,
                            "completed": t.completed,
                            "due_date": t.due_date.isoformat(),
                        }
                        for t in pet.tasks
                    ],
                }
                for pet in self.pets
            ],
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str) -> "Owner":
        """Deserialize and return an Owner instance from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        owner = cls(data["name"])
        for pd in data["pets"]:
            pet = Pet(pd["name"], pd["species"], pd["age"])
            for td in pd["tasks"]:
                task = Task(
                    description=td["description"],
                    time=td["time"],
                    duration_minutes=td["duration_minutes"],
                    priority=td["priority"],
                    frequency=td["frequency"],
                    completed=td["completed"],
                    due_date=date.fromisoformat(td["due_date"]),
                )
                pet.add_task(task)
            owner.add_pet(pet)
        return owner


class Scheduler:
    """The 'Brain' that retrieves, organises, and manages tasks across pets."""

    _PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def get_all_tasks(self) -> List[Tuple[Pet, Task]]:
        """Return all (Pet, Task) pairs from the owner."""
        return self.owner.get_all_tasks()

    def sort_by_time(self) -> List[Tuple[Pet, Task]]:
        """Return tasks sorted chronologically by HH:MM time string."""
        return sorted(self.get_all_tasks(), key=lambda pt: pt[1].time)

    def sort_by_priority_then_time(self) -> List[Tuple[Pet, Task]]:
        """Return tasks sorted by priority (high first), then by time."""
        return sorted(
            self.get_all_tasks(),
            key=lambda pt: (self._PRIORITY_ORDER.get(pt[1].priority, 99), pt[1].time),
        )

    def filter_by_status(self, completed: bool) -> List[Tuple[Pet, Task]]:
        """Return tasks filtered by completion status."""
        return [(p, t) for p, t in self.get_all_tasks() if t.completed == completed]

    def filter_by_pet(self, pet_name: str) -> List[Tuple[Pet, Task]]:
        """Return tasks belonging to the named pet (case-insensitive)."""
        return [
            (p, t)
            for p, t in self.get_all_tasks()
            if p.name.lower() == pet_name.lower()
        ]

    def detect_conflicts(self) -> List[str]:
        """Return warning strings for tasks scheduled at the same time for the same pet."""
        warnings: List[str] = []
        seen: Dict[Tuple[str, str], str] = {}
        for pet, task in self.get_all_tasks():
            key = (pet.name, task.time)
            if key in seen:
                warnings.append(
                    f"⚠️ Conflict: {pet.name} has two tasks at {task.time}: "
                    f'"{seen[key]}" and "{task.description}"'
                )
            else:
                seen[key] = task.description
        return warnings

    def mark_task_complete(self, pet_name: str, description: str) -> bool:
        """Mark a task complete and auto-reschedule recurring tasks. Return True if found."""
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return False
        for task in pet.tasks:
            if task.description == description and not task.completed:
                task.mark_complete()
                self._reschedule_if_recurring(pet, task)
                return True
        return False

    def _reschedule_if_recurring(self, pet: Pet, task: Task) -> None:
        """Create the next occurrence of a recurring task after it is completed."""
        if task.frequency == "daily":
            delta = timedelta(days=1)
        elif task.frequency == "weekly":
            delta = timedelta(weeks=1)
        else:
            return
        next_task = Task(
            description=task.description,
            time=task.time,
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            frequency=task.frequency,
            completed=False,
            due_date=task.due_date + delta,
        )
        pet.add_task(next_task)

    def today_schedule(self) -> List[Tuple[Pet, Task]]:
        """Return today's incomplete tasks sorted by priority then time."""
        today = date.today()
        return [
            (p, t)
            for p, t in self.sort_by_priority_then_time()
            if t.due_date == today and not t.completed
        ]

    def get_next_available_slot(self, after_time: str = "07:00") -> Optional[str]:
        """Return the next free 30-minute slot (HH:MM) with no task, starting after_time."""
        scheduled = {task.time for _, task in self.get_all_tasks()}
        h, m = map(int, after_time.split(":"))
        for _ in range(48):  # up to 24 hours in 30-min steps
            slot = f"{h:02d}:{m:02d}"
            if slot not in scheduled:
                return slot
            m += 30
            if m >= 60:
                m -= 60
                h += 1
            if h >= 24:
                break
        return None

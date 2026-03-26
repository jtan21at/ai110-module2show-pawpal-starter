"""Demo script for PawPal+: verifies backend logic in the terminal."""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(scheduler: Scheduler) -> None:
    """Print today's tasks sorted by priority then time."""
    tasks = scheduler.sort_by_priority_then_time()
    print(f"\n{'=' * 56}")
    print(f"  📋 TODAY'S SCHEDULE  ({date.today()})")
    print(f"{'=' * 56}")
    if not tasks:
        print("  No tasks scheduled.")
    for pet, task in tasks:
        status = "✅" if task.completed else "⏳"
        priority_label = task.priority.upper().ljust(6)
        print(
            f"  {status} [{priority_label}] {task.time}  "
            f"{pet.name}: {task.description} ({task.duration_minutes} min, {task.frequency})"
        )
    print(f"{'=' * 56}\n")


def main() -> None:
    """Build a sample owner, add pets and tasks, then demonstrate scheduler features."""
    owner = Owner("Jordan")

    # --- create pets ---
    mochi = Pet("Mochi", "dog", 3)
    luna = Pet("Luna", "cat", 5)

    # --- add tasks to Mochi ---
    mochi.add_task(Task("Morning walk", "08:00", 30, "high", "daily", due_date=date.today()))
    mochi.add_task(Task("Evening walk", "18:00", 25, "medium", "daily", due_date=date.today()))
    mochi.add_task(Task("Flea medication", "09:00", 5, "high", "weekly", due_date=date.today()))
    # intentional conflict to demonstrate detection
    mochi.add_task(Task("Grooming session", "08:00", 45, "medium", "once", due_date=date.today()))

    # --- add tasks to Luna ---
    luna.add_task(Task("Feeding", "07:30", 10, "high", "daily", due_date=date.today()))
    luna.add_task(Task("Playtime", "15:00", 20, "low", "daily", due_date=date.today()))
    luna.add_task(Task("Litter box clean", "12:00", 5, "medium", "daily", due_date=date.today()))

    owner.add_pet(mochi)
    owner.add_pet(luna)

    scheduler = Scheduler(owner)

    # --- today's schedule ---
    print_schedule(scheduler)

    # --- conflict detection ---
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        print("⚠️  CONFLICTS DETECTED:")
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("✅ No scheduling conflicts.")

    # --- filtering examples ---
    print("\n🔍 High-priority tasks only:")
    for pet, task in scheduler.sort_by_priority_then_time():
        if task.priority == "high":
            print(f"   {pet.name}: {task.description} @ {task.time}")

    print("\n🐶 Mochi's tasks only:")
    for pet, task in scheduler.filter_by_pet("Mochi"):
        print(f"   {task.time}  {task.description}")

    # --- mark a recurring task complete ---
    print("\n✔  Marking 'Feeding' complete for Luna...")
    scheduler.mark_task_complete("Luna", "Feeding")
    print(f"   Luna now has {len(luna.tasks)} tasks (original + next occurrence)")

    # --- next available slot ---
    slot = scheduler.get_next_available_slot("09:00")
    print(f"\n🕐 Next free 30-min slot after 09:00: {slot}")

    # --- data persistence ---
    scheduler.owner.save_to_json("/tmp/pawpal_data.json")
    restored = Owner.load_from_json("/tmp/pawpal_data.json")
    print(f"\n💾 Saved and restored owner '{restored.name}' with {len(restored.pets)} pets.")


if __name__ == "__main__":
    main()

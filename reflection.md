# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I started by identifying three core user actions:

1. **Add a pet** — an owner should be able to register a pet with its name, species, and age.
2. **Schedule a care task** — an owner should be able to attach a task (description, start time, duration, priority, frequency) to a specific pet.
3. **View today's sorted schedule** — the app should display all tasks for the day, ordered by priority first and time second, with any time conflicts flagged as warnings.

From these actions I derived four classes:

- **Task** (Python dataclass) — holds a single activity: description, HH:MM time, duration in minutes, priority (low/medium/high), frequency (once/daily/weekly), completion status, and due date. It exposes `mark_complete()` and `is_due_today()`.
- **Pet** — owns a list of `Task` objects. Provides `add_task`, `remove_task`, and `get_tasks`.
- **Owner** — owns a list of `Pet` objects. Aggregates all tasks via `get_all_tasks`, looks up pets by name, and handles JSON persistence with `save_to_json` / `load_from_json`.
- **Scheduler** — the coordination layer. It accepts an `Owner` and exposes sorting, filtering, conflict detection, recurring-task logic, and the "next available slot" finder.

**b. Design changes**

The main change from my first sketch was splitting "sort" into two methods — `sort_by_time` (pure chronological) and `sort_by_priority_then_time` (priority band first, then time). My initial plan had a single sort method, but once I wired the UI I realised the default view should be priority-aware, while tests needed a simpler time-only sort. I also added `get_next_available_slot` after finishing the demo script — it was not in the original UML but made the UI noticeably more useful.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints:

1. **Priority** (high / medium / low) — used as the primary sort key so the most important tasks are always at the top of the list.
2. **Time** (HH:MM) — used as a tiebreaker within the same priority band, so the owner reads tasks in the order they should happen.
3. **Due date** — `today_schedule()` filters to only today's tasks, so future or past occurrences do not clutter the view.

I decided priority mattered most because a pet's medication is more important than a play session regardless of what time it falls.

**b. Tradeoffs**

The conflict detector uses *exact start-time matching* — it flags two tasks only if they share the same HH:MM string for the same pet. This is simple and never crashes, but it misses overlapping tasks that start at different times yet cover the same minutes (e.g., a 30-minute walk at 08:00 and a 20-minute grooming at 08:15 overlap from 08:15 to 08:30 but are not flagged). For a household-pet planner where the owner is physically present, exact-time conflicts are the most common mistake, so this tradeoff is reasonable.

---

## 3. AI Collaboration

**a. How you used AI**

I used Copilot Chat to brainstorm the initial class structure and to generate the Mermaid UML diagram. The most effective prompts were concrete and scoped — for example: "Given these four classes and their attributes, generate a Mermaid class diagram." For debugging I used inline chat on specific method bodies and asked "why would this return an empty list?" rather than asking about the whole file.

For the recurring-task feature I asked: "How should I use Python's `timedelta` to calculate the next due date for a daily vs weekly task?" That gave me the `timedelta(days=1)` / `timedelta(weeks=1)` pattern I used in `_reschedule_if_recurring`.

**b. Judgment and verification**

When I asked Copilot to suggest conflict-detection logic, it proposed comparing every pair of tasks with a nested loop (O(n²)). I replaced that with a single-pass dictionary approach (`seen: Dict[(pet_name, time), description]`) which is O(n). I verified the change was correct by running the conflict-detection tests and confirming they still caught duplicate times while not flagging distinct times.

---

## 4. Testing and Verification

**a. What you tested**

I wrote 15 automated tests in `tests/test_pawpal.py` covering:

- `mark_complete()` flips `completed` to `True`
- Adding and removing tasks changes the pet's task count
- `sort_by_time` returns tasks in ascending HH:MM order
- `sort_by_priority_then_time` puts high-priority tasks before lower ones
- Marking a daily task complete creates a new task due tomorrow
- Marking a weekly task complete creates a new task due in 7 days
- Marking a one-off task complete does NOT create a follow-up
- Conflict detection fires exactly once for a same-pet same-time pair
- No conflicts fire when all times are distinct
- `filter_by_status` returns only tasks matching the requested status
- `filter_by_pet` returns only tasks belonging to the named pet
- `save_to_json` + `load_from_json` round-trips all data losslessly

These tests are important because they cover the three most likely sources of bugs: state mutation (completion), algorithmic output (sorting/filtering), and edge-case control flow (recurrence and conflict detection).

**b. Confidence**

All 15 tests pass — ⭐⭐⭐⭐ (4 / 5). I would add the following tests next if time allowed:

- Tasks that span midnight (e.g., `time="23:45"` + 30-minute duration)
- Overlapping but non-identical start times (duration-aware conflict detection)
- An owner with zero pets (empty schedule)
- Unicode pet names and task descriptions in the JSON round-trip

---

## 5. Reflection

**a. What went well**

I am most satisfied with the clean separation between the logic layer (`pawpal_system.py`) and the UI (`app.py`). Because `Scheduler` only depends on `Owner`, I could write and test the entire backend before opening Streamlit, which made debugging fast and kept the UI code simple.

**b. What you would improve**

If I had another iteration I would add duration-aware conflict detection — the current exact-match approach is a known simplification. I would also add a proper `due_date` picker in the UI so users can schedule tasks for future days, not just today.

**c. Key takeaway**

The most important thing I learned is that AI tools are excellent *accelerators* for the "how do I write this?" question but cannot replace the designer's role in answering "should I write this at all, and in what shape?" Every Copilot suggestion I accepted went through a mental review: Does this fit the design? Is it the simplest correct solution? Does it introduce hidden complexity? Keeping that review habit made the AI collaboration genuinely productive rather than just fast.

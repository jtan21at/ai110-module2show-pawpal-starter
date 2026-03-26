"""PawPal+ Streamlit UI — connected to the pawpal_system backend."""

import re
from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Your smart pet care planning assistant")

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

# ---------------------------------------------------------------------------
# Owner Setup
# ---------------------------------------------------------------------------
with st.expander("👤 Owner Setup", expanded=st.session_state.owner is None):
    owner_name_input = st.text_input("Owner name", value="Jordan", key="owner_name_input")
    if st.button("Set Owner"):
        st.session_state.owner = Owner(owner_name_input.strip() or "Jordan")
        st.success(f"Owner set to **{st.session_state.owner.name}**!")

if st.session_state.owner is None:
    st.info("Please set an owner name above to get started.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Add a Pet
# ---------------------------------------------------------------------------
with st.expander("🐶 Add a Pet"):
    col1, col2, col3 = st.columns(3)
    with col1:
        new_pet_name = st.text_input("Pet name", key="new_pet_name")
    with col2:
        new_pet_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"], key="new_pet_species")
    with col3:
        new_pet_age = st.number_input("Age (years)", min_value=0, max_value=30, value=1, key="new_pet_age")

    if st.button("Add Pet"):
        name = new_pet_name.strip()
        if not name:
            st.error("Pet name cannot be empty.")
        elif owner.get_pet(name):
            st.warning(f"A pet named **{name}** already exists.")
        else:
            owner.add_pet(Pet(name, new_pet_species, int(new_pet_age)))
            st.success(f"Added **{name}** ({new_pet_species}, age {new_pet_age})!")

# ---------------------------------------------------------------------------
# Schedule a Task
# ---------------------------------------------------------------------------
if owner.pets:
    with st.expander("📋 Schedule a Task"):
        col1, col2 = st.columns(2)
        with col1:
            task_pet = st.selectbox("Pet", [p.name for p in owner.pets], key="task_pet")
            task_desc = st.text_input("Task description", value="Morning walk", key="task_desc")
            task_time = st.text_input("Time (HH:MM)", value="08:00", key="task_time")
        with col2:
            task_duration = st.number_input(
                "Duration (min)", min_value=1, max_value=480, value=20, key="task_duration"
            )
            task_priority = st.selectbox("Priority", ["low", "medium", "high"], index=2, key="task_priority")
            task_frequency = st.selectbox("Frequency", ["once", "daily", "weekly"], key="task_frequency")

        if st.button("Add Task"):
            pet = owner.get_pet(task_pet)
            if pet and task_desc.strip():
                if not re.match(r"^\d{2}:\d{2}$", task_time):
                    st.error("Time must be in HH:MM format (e.g. 08:30).")
                else:
                    pet.add_task(
                        Task(
                            description=task_desc.strip(),
                            time=task_time,
                            duration_minutes=int(task_duration),
                            priority=task_priority,
                            frequency=task_frequency,
                            due_date=date.today(),
                        )
                    )
                    st.success(f"Scheduled **{task_desc}** for **{task_pet}** at {task_time}.")
            else:
                st.error("Task description cannot be empty.")

st.divider()

# ---------------------------------------------------------------------------
# Today's Schedule
# ---------------------------------------------------------------------------
st.subheader("📅 Today's Schedule")

if not owner.pets:
    st.info("Add a pet and some tasks to generate a schedule.")
else:
    scheduler = Scheduler(owner)

    # Conflict warnings
    conflicts = scheduler.detect_conflicts()
    for warning in conflicts:
        st.warning(warning)

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        pet_filter = st.selectbox(
            "Filter by pet", ["All"] + [p.name for p in owner.pets], key="filter_pet"
        )
    with col2:
        status_filter = st.selectbox(
            "Filter by status", ["All", "Pending", "Completed"], key="filter_status"
        )

    tasks = scheduler.sort_by_priority_then_time()

    if pet_filter != "All":
        tasks = [(p, t) for p, t in tasks if p.name == pet_filter]
    if status_filter == "Pending":
        tasks = [(p, t) for p, t in tasks if not t.completed]
    elif status_filter == "Completed":
        tasks = [(p, t) for p, t in tasks if t.completed]

    _PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}

    if not tasks:
        st.info("No tasks match your filters.")
    else:
        rows = [
            {
                "Status": "✅" if task.completed else "⏳",
                "Priority": f"{_PRIORITY_EMOJI.get(task.priority, '')} {task.priority.capitalize()}",
                "Time": task.time,
                "Pet": pet.name,
                "Task": task.description,
                "Duration": f"{task.duration_minutes} min",
                "Frequency": task.frequency,
            }
            for pet, task in tasks
        ]
        st.table(rows)

    # -----------------------------------------------------------------------
    # Mark Task Complete
    # -----------------------------------------------------------------------
    st.subheader("✔️ Mark Task Complete")
    pending = [(p, t) for p, t in scheduler.get_all_tasks() if not t.completed]
    if pending:
        options = [f"{p.name}: {t.description} @ {t.time}" for p, t in pending]
        choice = st.selectbox("Select task to complete", options, key="complete_choice")
        if st.button("Mark as Complete"):
            idx = options.index(choice)
            pet, task = pending[idx]
            scheduler.mark_task_complete(pet.name, task.description)
            if task.frequency in ("daily", "weekly"):
                st.success(f"✅ Done! Next {task.frequency} occurrence auto-scheduled.")
            else:
                st.success("✅ Task marked as complete!")
    else:
        st.info("All tasks are complete. 🎉")

    # -----------------------------------------------------------------------
    # Next Available Slot
    # -----------------------------------------------------------------------
    slot = scheduler.get_next_available_slot()
    if slot:
        st.info(f"🕐 Next free 30-minute slot today: **{slot}**")


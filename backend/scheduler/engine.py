"""
Scheduler Engine using Google OR-Tools CP-SAT Solver.

This module generates conflict-free timetables based on hard constraints:
- Teacher Conflict: A faculty cannot teach two classes at the same time
- Room Conflict: A room cannot host two classes at the same time
- Section Conflict: A section cannot attend two classes at the same time
- Session Count: Each assignment gets exactly sessions_per_week slots
"""

import django
import os

# Setup Django environment if running standalone
if not django.apps.apps.ready:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scheduler.settings')
    django.setup()

from ortools.sat.python import cp_model
from core.models import CourseAssignment, Room, Faculty, StudentSection, GeneratedSchedule


# Constants
NUM_DAYS = 5  # Monday to Friday
NUM_SLOTS = 8  # 8 slots per day (0-7)
TOTAL_TIMESLOTS = NUM_DAYS * NUM_SLOTS  # 40 total slots

DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']


def get_timeslot_index(day: int, slot: int) -> int:
    """Convert (day, slot) to a single timeslot index."""
    return day * NUM_SLOTS + slot


def get_day_slot_from_index(timeslot_index: int) -> tuple[int, int]:
    """Convert timeslot index back to (day, slot)."""
    day = timeslot_index // NUM_SLOTS
    slot = timeslot_index % NUM_SLOTS
    return day, slot


def fetch_data():
    """Fetch all required data from Django ORM."""
    assignments = list(CourseAssignment.objects.select_related(
        'faculty', 'course', 'section'
    ).all())
    rooms = list(Room.objects.all())
    faculties = list(Faculty.objects.all())
    sections = list(StudentSection.objects.all())
    
    return {
        'assignments': assignments,
        'rooms': rooms,
        'faculties': faculties,
        'sections': sections,
    }


def create_variables(model: cp_model.CpModel, assignments: list, rooms: list) -> dict:
    """
    Create boolean decision variables.
    
    For each assignment and each session of that assignment,
    create a variable for each (room, timeslot) combination.
    
    x[assignment_id][session_num][room_id][timeslot] = 1 
    means session `session_num` of `assignment` is scheduled 
    in `room` at `timeslot`.
    """
    x = {}
    
    for assignment in assignments:
        assignment_id = assignment.id
        x[assignment_id] = {}
        
        for session_num in range(assignment.sessions_per_week):
            x[assignment_id][session_num] = {}
            
            for room in rooms:
                room_id = room.id
                x[assignment_id][session_num][room_id] = {}
                
                for timeslot in range(TOTAL_TIMESLOTS):
                    var_name = f"x_{assignment_id}_{session_num}_{room_id}_{timeslot}"
                    x[assignment_id][session_num][room_id][timeslot] = model.NewBoolVar(var_name)
    
    return x


def add_session_count_constraint(model: cp_model.CpModel, x: dict, assignments: list, rooms: list):
    """
    Constraint: Each session must be assigned to exactly one (room, timeslot).
    """
    for assignment in assignments:
        assignment_id = assignment.id
        
        for session_num in range(assignment.sessions_per_week):
            # Sum over all rooms and timeslots for this session
            all_options = []
            for room in rooms:
                for timeslot in range(TOTAL_TIMESLOTS):
                    all_options.append(x[assignment_id][session_num][room.id][timeslot])
            
            # Exactly one option must be selected
            model.Add(sum(all_options) == 1)


def add_room_conflict_constraint(model: cp_model.CpModel, x: dict, assignments: list, rooms: list):
    """
    Constraint: A room cannot host more than one class at a time.
    """
    for room in rooms:
        for timeslot in range(TOTAL_TIMESLOTS):
            # Collect all sessions that could use this room at this timeslot
            sessions_at_slot = []
            
            for assignment in assignments:
                for session_num in range(assignment.sessions_per_week):
                    sessions_at_slot.append(x[assignment.id][session_num][room.id][timeslot])
            
            # At most one session can use this room at this timeslot
            model.Add(sum(sessions_at_slot) <= 1)


def add_teacher_conflict_constraint(model: cp_model.CpModel, x: dict, assignments: list, rooms: list):
    """
    Constraint: A faculty cannot teach more than one class at a time.
    """
    # Group assignments by faculty
    faculty_assignments = {}
    for assignment in assignments:
        faculty_id = assignment.faculty_id
        if faculty_id not in faculty_assignments:
            faculty_assignments[faculty_id] = []
        faculty_assignments[faculty_id].append(assignment)
    
    for faculty_id, faculty_assign_list in faculty_assignments.items():
        for timeslot in range(TOTAL_TIMESLOTS):
            # Collect all sessions of this faculty at this timeslot
            sessions_at_slot = []
            
            for assignment in faculty_assign_list:
                for session_num in range(assignment.sessions_per_week):
                    for room in rooms:
                        sessions_at_slot.append(x[assignment.id][session_num][room.id][timeslot])
            
            # At most one session for this faculty at this timeslot
            model.Add(sum(sessions_at_slot) <= 1)


def add_section_conflict_constraint(model: cp_model.CpModel, x: dict, assignments: list, rooms: list):
    """
    Constraint: A student section cannot attend more than one class at a time.
    """
    # Group assignments by section
    section_assignments = {}
    for assignment in assignments:
        section_id = assignment.section_id
        if section_id not in section_assignments:
            section_assignments[section_id] = []
        section_assignments[section_id].append(assignment)
    
    for section_id, section_assign_list in section_assignments.items():
        for timeslot in range(TOTAL_TIMESLOTS):
            # Collect all sessions of this section at this timeslot
            sessions_at_slot = []
            
            for assignment in section_assign_list:
                for session_num in range(assignment.sessions_per_week):
                    for room in rooms:
                        sessions_at_slot.append(x[assignment.id][session_num][room.id][timeslot])
            
            # At most one session for this section at this timeslot
            model.Add(sum(sessions_at_slot) <= 1)


def extract_solution(solver: cp_model.CpSolver, x: dict, assignments: list, rooms: list) -> list:
    """
    Extract the solution from the solver.
    Returns a list of (assignment, room, day, slot) tuples.
    """
    solution = []
    
    # Create lookup dictionaries
    assignment_lookup = {a.id: a for a in assignments}
    room_lookup = {r.id: r for r in rooms}
    
    for assignment in assignments:
        for session_num in range(assignment.sessions_per_week):
            for room in rooms:
                for timeslot in range(TOTAL_TIMESLOTS):
                    if solver.Value(x[assignment.id][session_num][room.id][timeslot]) == 1:
                        day, slot = get_day_slot_from_index(timeslot)
                        solution.append({
                            'assignment': assignment,
                            'room': room,
                            'day': day,
                            'slot': slot,
                        })
    
    return solution


def print_schedule(solution: list):
    """Print the schedule in a readable format."""
    print("\n" + "=" * 80)
    print("GENERATED TIMETABLE")
    print("=" * 80)
    print(f"{'Day':<12} | {'Slot':<4} | {'Room':<10} | {'Course':<15} | {'Section':<12} | {'Teacher'}")
    print("-" * 80)
    
    # Sort by day, then slot
    sorted_solution = sorted(solution, key=lambda x: (x['day'], x['slot']))
    
    for entry in sorted_solution:
        day_name = DAY_NAMES[entry['day']]
        slot = entry['slot']
        room = entry['room'].code
        course = entry['assignment'].course.code
        section = entry['assignment'].section.section_id
        teacher = entry['assignment'].faculty.name
        
        print(f"{day_name:<12} | {slot:<4} | {room:<10} | {course:<15} | {section:<12} | {teacher}")
    
    print("=" * 80)
    print(f"Total scheduled sessions: {len(solution)}")
    print("=" * 80 + "\n")


def save_schedule_to_db(solution: list):
    """Save the generated schedule to the database."""
    # Clear previous schedules
    GeneratedSchedule.objects.all().delete()
    
    # Create new schedule entries
    schedule_entries = []
    for entry in solution:
        schedule_entries.append(GeneratedSchedule(
            day=entry['day'],
            slot=entry['slot'],
            room=entry['room'],
            course=entry['assignment'].course,
            section=entry['assignment'].section,
            faculty=entry['assignment'].faculty,
        ))
    
    # Bulk create for efficiency
    GeneratedSchedule.objects.bulk_create(schedule_entries)
    print(f"Saved {len(schedule_entries)} schedule entries to database.")


def generate_schedule() -> bool:
    """
    Main function to generate a conflict-free timetable.
    
    Returns:
        True if a solution was found, False otherwise.
    """
    print("Fetching data from database...")
    data = fetch_data()
    
    assignments = data['assignments']
    rooms = data['rooms']
    
    if not assignments:
        print("No course assignments found. Please add course assignments first.")
        return False
    
    if not rooms:
        print("No rooms found. Please add rooms first.")
        return False
    
    print(f"Found {len(assignments)} assignments and {len(rooms)} rooms.")
    
    # Calculate total sessions needed
    total_sessions = sum(a.sessions_per_week for a in assignments)
    print(f"Total sessions to schedule: {total_sessions}")
    
    # Create the model
    print("Creating OR-Tools CP-SAT model...")
    model = cp_model.CpModel()
    
    # Create variables
    print("Creating decision variables...")
    x = create_variables(model, assignments, rooms)
    
    # Add constraints
    print("Adding constraints...")
    
    print("  - Session count constraint (each session assigned exactly once)")
    add_session_count_constraint(model, x, assignments, rooms)
    
    print("  - Room conflict constraint (no double-booking of rooms)")
    add_room_conflict_constraint(model, x, assignments, rooms)
    
    print("  - Teacher conflict constraint (no double-booking of faculty)")
    add_teacher_conflict_constraint(model, x, assignments, rooms)
    
    print("  - Section conflict constraint (no double-booking of student sections)")
    add_section_conflict_constraint(model, x, assignments, rooms)
    
    # Solve
    print("Solving...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0  # 1 minute timeout
    
    status = solver.Solve(model)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"Solution found! Status: {'OPTIMAL' if status == cp_model.OPTIMAL else 'FEASIBLE'}")
        
        # Extract and display solution
        solution = extract_solution(solver, x, assignments, rooms)
        print_schedule(solution)
        
        # Save to database
        save_schedule_to_db(solution)
        
        return True
    else:
        print("\n" + "=" * 80)
        print("Infeasible: Conflict detected.")
        print("=" * 80)
        print("The scheduler could not find a valid timetable with the given constraints.")
        print("Possible reasons:")
        print("  - Too many sessions for the available rooms/timeslots")
        print("  - Faculty workload exceeds available slots")
        print("  - Conflicting section requirements")
        print("=" * 80 + "\n")
        
        return False


if __name__ == "__main__":
    generate_schedule()

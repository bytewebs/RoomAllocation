import random
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
import json
from datetime import datetime

@dataclass
class Room:
    """Represents a single room in the hostel."""
    building: str
    floor: str
    number: str
    capacity: int = 2
    occupied_by: List[str] = field(default_factory=list)
    
    @property
    def room_id(self) -> str:
        """Returns unique room identifier."""
        return f"{self.building}{self.floor}-{self.number}"
    
    @property
    def is_available(self) -> bool:
        """Check if room has available space."""
        return len(self.occupied_by) < self.capacity
    
    @property
    def available_slots(self) -> int:
        """Returns number of available slots in the room."""
        return self.capacity - len(self.occupied_by)

@dataclass
class Floor:
    """Represents a floor in a building."""
    building: str
    floor_number: str
    rooms: List[Room] = field(default_factory=list)
    
    @property
    def floor_id(self) -> str:
        """Returns unique floor identifier."""
        return f"{self.building}{self.floor_number}"
    
    @property
    def available_rooms(self) -> List[Room]:
        """Returns list of rooms with available space."""
        return [room for room in self.rooms if room.is_available]
    
    @property
    def total_available_slots(self) -> int:
        """Returns total number of available slots on the floor."""
        return sum(room.available_slots for room in self.available_rooms)
    
    def get_continuous_available_rooms(self) -> List[List[Room]]:
        """Returns groups of continuous available rooms."""
        if not self.available_rooms:
            return []
        
        # Sort rooms by number
        sorted_rooms = sorted(self.available_rooms, key=lambda r: r.number)
        continuous_groups = []
        current_group = [sorted_rooms[0]]
        
        for i in range(1, len(sorted_rooms)):
            # Check if rooms are continuous (difference of 1 in room numbers)
            if int(sorted_rooms[i].number) - int(sorted_rooms[i-1].number) == 1:
                current_group.append(sorted_rooms[i])
            else:
                continuous_groups.append(current_group)
                current_group = [sorted_rooms[i]]
        
        continuous_groups.append(current_group)
        return continuous_groups

class HostelAllocationSystem:
    """Main system for managing hostel room allocations."""
    
    def __init__(self):
        self.buildings = {}
        self.allocation_history = []
        self._initialize_buildings()
    
    def _initialize_buildings(self):
        """Initialize the hostel structure with all rooms."""
        # Building A initialization
        building_a_rooms = {
            'A0': ['001', '002', '003', '004', '005', '013', '014', '015', '016', '017', 
                   '022', '023', '024', '025', '026'],
            'A1': ['101', '102', '103', '104', '105', '114', '115', '116', '117', '118',
                   '122', '123', '124', '125', '126'],
            'A2': ['201', '202', '203', '204', '205', '214', '215', '216', '217', '218',
                   '221', '222', '223', '224', '225'],
            'A3': ['301', '302', '303', '304', '305', '314', '315', '316', '317', '318',
                   '319', '320', '321', '322', '323']
        }
        
        self.buildings['A'] = {}
        for floor, room_numbers in building_a_rooms.items():
            floor_obj = Floor(building='A', floor_number=floor[1])
            for room_num in room_numbers:
                room = Room(building='A', floor=floor[1], number=room_num)
                floor_obj.rooms.append(room)
            self.buildings['A'][floor] = floor_obj
        
        # Building B initialization
        self.buildings['B'] = {}
        for floor_num in ['1', '2']:
            floor_obj = Floor(building='B', floor_number=floor_num)
            for i in range(1, 25):
                room_num = f"{i:03d}"
                room = Room(building='B', floor=floor_num, number=room_num)
                floor_obj.rooms.append(room)
            self.buildings['B'][f'B{floor_num}'] = floor_obj
    
    def get_all_floors_with_availability(self) -> List[Tuple[Floor, int]]:
        """Returns all floors with their available slot count, sorted by availability."""
        floors_with_availability = []
        
        for building in self.buildings.values():
            for floor in building.values():
                available_slots = floor.total_available_slots
                if available_slots > 0:
                    floors_with_availability.append((floor, available_slots))
        
        # Sort by available slots (descending) for better group placement
        floors_with_availability.sort(key=lambda x: x[1], reverse=True)
        return floors_with_availability
    
    def allocate_rooms(self, group_size: int, roll_numbers: List[str]) -> Dict[str, str]:
        """
        Allocate rooms for a group of students (one representative per room).
        
        Args:
            group_size: Number of rooms needed for the group
            roll_numbers: List of representative student roll numbers (one per room)
            
        Returns:
            Dictionary mapping roll numbers to room IDs
        """
        if len(roll_numbers) != group_size:
            raise ValueError(f"Number of rooms ({group_size}) doesn't match number of roll numbers ({len(roll_numbers)})")
        
        if group_size > 15:  # Max 15 rooms per group
            raise ValueError("Group size cannot exceed 15 rooms")
        
        allocation = {}
        remaining_students = roll_numbers.copy()
        random.shuffle(remaining_students)  # Randomize student order for fairness
        
        # Get all floors with availability
        floors_with_availability = self.get_all_floors_with_availability()
        
        if not floors_with_availability:
            raise ValueError("No available rooms in the hostel")
        
        # Try to allocate the entire group on a single floor
        allocated = self._try_single_floor_allocation(remaining_students, floors_with_availability, allocation)
        
        if not allocated:
            # If single floor allocation fails, try multi-floor allocation
            self._multi_floor_allocation(remaining_students, floors_with_availability, allocation)
        
        # Record allocation in history
        self.allocation_history.append({
            'timestamp': datetime.now().isoformat(),
            'group_size': group_size,
            'allocation': allocation.copy()
        })
        
        return allocation
    
    def _try_single_floor_allocation(self, students: List[str], floors: List[Tuple[Floor, int]], 
                                    allocation: Dict[str, str]) -> bool:
        """Try to allocate all students on a single floor (one student per room)."""
        required_rooms = len(students)  # Each student represents one room
        
        # Randomize floor selection for fairness
        available_floors = [(f, slots) for f, slots in floors if slots >= required_rooms * 2]  # Need 2 slots per room
        if not available_floors:
            return False
        
        selected_floor, _ = random.choice(available_floors)
        
        # Get continuous room groups on the selected floor
        continuous_groups = selected_floor.get_continuous_available_rooms()
        
        # Try to allocate in continuous rooms
        student_idx = 0
        for group in continuous_groups:
            for room in group:
                if room.is_available and room.available_slots == 2 and student_idx < len(students):
                    # Mark room as fully occupied with the representative student
                    room.occupied_by.append(students[student_idx])
                    room.occupied_by.append(f"{students[student_idx]}_roommate")  # Placeholder for roommate
                    allocation[students[student_idx]] = room.room_id
                    student_idx += 1
        
        return student_idx == len(students)
    
    def _multi_floor_allocation(self, students: List[str], floors: List[Tuple[Floor, int]], 
                               allocation: Dict[str, str]):
        """Allocate students across multiple floors, keeping subgroups together (one student per room)."""
        remaining_students = students.copy()
        
        while remaining_students:
            # Refresh available floors
            floors_with_availability = self.get_all_floors_with_availability()
            if not floors_with_availability:
                raise ValueError(f"Not enough rooms available. {len(remaining_students)} rooms couldn't be allocated.")
            
            # Select a floor (randomized for fairness)
            selected_floor, available_slots = random.choice(floors_with_availability)
            
            # Determine how many rooms to allocate on this floor
            available_rooms = available_slots // 2  # Each room needs 2 slots
            rooms_to_place = min(len(remaining_students), available_rooms)
            floor_students = remaining_students[:rooms_to_place]
            
            # Allocate on the selected floor
            continuous_groups = selected_floor.get_continuous_available_rooms()
            student_idx = 0
            
            for group in continuous_groups:
                for room in group:
                    if room.is_available and room.available_slots == 2 and student_idx < len(floor_students):
                        room.occupied_by.append(floor_students[student_idx])
                        room.occupied_by.append(f"{floor_students[student_idx]}_roommate")
                        allocation[floor_students[student_idx]] = room.room_id
                        student_idx += 1
            
            # Remove allocated students
            remaining_students = remaining_students[rooms_to_place:]
    
    def get_hostel_status(self) -> Dict:
        """Get current status of all rooms in the hostel."""
        status = {
            'total_rooms': 0,
            'occupied_rooms': 0,
            'available_rooms': 0,
            'total_slots': 0,
            'occupied_slots': 0,
            'available_slots': 0,
            'buildings': {}
        }
        
        for building_name, building in self.buildings.items():
            building_status = {
                'floors': {}
            }
            
            for floor_name, floor in building.items():
                floor_status = {
                    'total_rooms': len(floor.rooms),
                    'available_rooms': len(floor.available_rooms),
                    'available_slots': floor.total_available_slots,
                    'rooms': []
                }
                
                for room in floor.rooms:
                    room_info = {
                        'room_id': room.room_id,
                        'occupied_by': room.occupied_by,
                        'available_slots': room.available_slots
                    }
                    floor_status['rooms'].append(room_info)
                
                building_status['floors'][floor_name] = floor_status
                
                # Update totals
                status['total_rooms'] += len(floor.rooms)
                status['available_rooms'] += len(floor.available_rooms)
                status['total_slots'] += len(floor.rooms) * 2
                status['available_slots'] += floor.total_available_slots
        
        status['occupied_rooms'] = status['total_rooms'] - status['available_rooms']
        status['occupied_slots'] = status['total_slots'] - status['available_slots']
        status['buildings'] = building_status
        
        return status
    
    def reset_allocations(self):
        """Reset all room allocations."""
        self._initialize_buildings()
        self.allocation_history = []
    
    def save_state(self, filename: str):
        """Save current allocation state to a file."""
        state = {
            'hostel_status': self.get_hostel_status(),
            'allocation_history': self.allocation_history
        }
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, filename: str):
        """Load allocation state from a file."""
        with open(filename, 'r') as f:
            state = json.load(f)
        
        # Reconstruct allocations from history
        self.reset_allocations()
        for allocation_record in state['allocation_history']:
            # Re-apply allocations
            for roll_number, room_id in allocation_record['allocation'].items():
                building, floor_room = room_id.split('-')
                floor_id = building[:2]
                room_number = floor_room
                
                # Find and allocate the room
                floor = self.buildings[building[0]][floor_id]
                for room in floor.rooms:
                    if room.number == room_number and len(room.occupied_by) == 0:
                        room.occupied_by.append(roll_number)
                        room.occupied_by.append(f"{roll_number}_roommate")
                        break


# Command-line interface
def main():
    """Simple CLI for room allocation."""
    system = HostelAllocationSystem()
    
    print("=== Hostel Room Allocation System ===")
    print("Commands: allocate, status, reset, save, load, exit")
    
    while True:
        command = input("\nEnter command: ").strip().lower()
        
        if command == 'exit':
            break
        
        elif command == 'allocate':
            try:
                group_size = int(input("Enter number of rooms needed: "))
                roll_numbers_input = input("Enter roll numbers (one per room, comma-separated): ")
                roll_numbers = [r.strip() for r in roll_numbers_input.split(',')]
                
                allocation = system.allocate_rooms(group_size, roll_numbers)
                
                print("\n=== Allocation Result ===")
                for roll, room in allocation.items():
                    print(f"{roll}: {room}")
                
            except Exception as e:
                print(f"Error: {e}")
        
        elif command == 'status':
            status = system.get_hostel_status()
            print(f"\n=== Hostel Status ===")
            print(f"Total Rooms: {status['total_rooms']}")
            print(f"Occupied Rooms: {status['occupied_rooms']}")
            print(f"Available Rooms: {status['available_rooms']}")
            print(f"Total Slots: {status['total_slots']}")
            print(f"Occupied Slots: {status['occupied_slots']}")
            print(f"Available Slots: {status['available_slots']}")
        
        elif command == 'reset':
            system.reset_allocations()
            print("All allocations have been reset.")
        
        elif command == 'save':
            filename = input("Enter filename to save: ")
            system.save_state(filename)
            print(f"State saved to {filename}")
        
        elif command == 'load':
            filename = input("Enter filename to load: ")
            try:
                system.load_state(filename)
                print(f"State loaded from {filename}")
            except Exception as e:
                print(f"Error loading file: {e}")
        
        else:
            print("Invalid command. Try: allocate, status, reset, save, load, exit")


if __name__ == "__main__":
    main()

"""
world.py — Room-based world simulation for the Commons Sentience Sandbox.

v0.3: Rooms now contain named WorldObjects with mutable states.
      The agent can inspect and interact with individual objects.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class WorldObject:
    """A named, stateful object that lives inside a room."""

    name: str
    description: str
    state: str
    states: List[str] = field(default_factory=list)
    interactions: List[str] = field(default_factory=list)

    def inspect(self) -> str:
        return f"{self.name} [{self.state}]: {self.description}"

    def set_state(self, new_state: str) -> bool:
        if new_state in self.states:
            self.state = new_state
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "state": self.state,
            "states": self.states,
            "interactions": self.interactions,
        }


class Room:
    """A single location in the simulation world."""

    def __init__(self, name: str, data: dict) -> None:
        self.name = name
        self.description: str = data.get("description", "")
        self.actions: List[str] = data.get("actions", [])
        self.connected_rooms: List[str] = data.get("connected_rooms", [])

        # Build WorldObject instances from the objects dict
        raw_objects = data.get("objects", {})
        if isinstance(raw_objects, dict):
            self.objects: Dict[str, WorldObject] = {
                obj_name: WorldObject(
                    name=obj_name,
                    description=obj_data.get("description", ""),
                    state=obj_data.get("state", "idle"),
                    states=obj_data.get("states", [obj_data.get("state", "idle")]),
                    interactions=obj_data.get("interactions", []),
                )
                for obj_name, obj_data in raw_objects.items()
            }
        else:
            # Backwards-compatible: list of strings
            self.objects = {
                obj: WorldObject(name=obj, description="", state="idle", states=["idle"])
                for obj in raw_objects
            }

    def describe(self) -> str:
        return f"{self.name}: {self.description}"

    def available_actions(self) -> List[str]:
        return list(self.actions)

    def object_names(self) -> List[str]:
        return list(self.objects.keys())

    def inspect_object(self, obj_name: str) -> Optional[str]:
        obj = self.objects.get(obj_name)
        return obj.inspect() if obj else None

    def interact_with_object(
        self, obj_name: str, interaction: str
    ) -> Tuple[bool, str]:
        """Apply an interaction to an object, advancing its state if appropriate.

        Returns (success, message).
        """
        obj = self.objects.get(obj_name)
        if obj is None:
            return False, f"Object '{obj_name}' not found in {self.name}."
        if interaction not in obj.interactions:
            return False, (
                f"'{interaction}' is not a valid interaction for {obj_name}. "
                f"Valid: {obj.interactions}"
            )
        # Advance state cyclically on interaction
        if len(obj.states) > 1:
            current_idx = obj.states.index(obj.state) if obj.state in obj.states else 0
            next_idx = (current_idx + 1) % len(obj.states)
            obj.state = obj.states[next_idx]
        return True, f"Interacted with {obj_name}: now [{obj.state}]."

    def objects_snapshot(self) -> List[str]:
        """Return a list of object inspection strings for the narrative."""
        return [obj.inspect() for obj in self.objects.values()]

    def __repr__(self) -> str:
        return f"Room({self.name!r})"


class World:
    """Container for all rooms and world-state management."""

    def __init__(self, rooms_path: str) -> None:
        with open(rooms_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.rooms: Dict[str, Room] = {
            name: Room(name, info) for name, info in data.items()
        }
        self.turn: int = 0
        self._room_names: List[str] = list(self.rooms.keys())

    @property
    def room_names(self) -> List[str]:
        return self._room_names

    def get_room(self, name: str) -> Optional[Room]:
        return self.rooms.get(name)

    def adjacent_rooms(self, current_room: str) -> List[str]:
        room = self.get_room(current_room)
        if room is None:
            return []
        return room.connected_rooms

    def move_to(self, current_room: str, target_room: str) -> bool:
        """Return True if movement is valid (target is adjacent)."""
        return target_room in self.adjacent_rooms(current_room)

    def observe(self, room_name: str) -> dict:
        """Return an observation snapshot of the current room."""
        room = self.get_room(room_name)
        if room is None:
            return {}
        return {
            "room": room.name,
            "description": room.description,
            "objects": room.objects_snapshot(),
            "available_actions": room.actions,
            "connected_rooms": room.connected_rooms,
        }

    def inspect_object(self, room_name: str, obj_name: str) -> Optional[str]:
        room = self.get_room(room_name)
        if room is None:
            return None
        return room.inspect_object(obj_name)

    def interact_with_object(
        self, room_name: str, obj_name: str, interaction: str
    ) -> Tuple[bool, str]:
        room = self.get_room(room_name)
        if room is None:
            return False, f"Room '{room_name}' not found."
        return room.interact_with_object(obj_name, interaction)

    def choose_next_room(
        self, current_room: str, preferred_room: Optional[str] = None
    ) -> str:
        """Select the next room for the agent to move to."""
        adjacent = self.adjacent_rooms(current_room)
        if not adjacent:
            return current_room
        if preferred_room and preferred_room in adjacent:
            return preferred_room
        return random.choice(adjacent)


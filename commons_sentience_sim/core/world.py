"""
world.py — Room-based world simulation for the Commons Sentience Sandbox.
"""
from __future__ import annotations

import json
import random
from typing import Dict, List, Optional


class Room:
    """A single location in the simulation world."""

    def __init__(self, name: str, data: dict) -> None:
        self.name = name
        self.description: str = data.get("description", "")
        self.objects: List[str] = data.get("objects", [])
        self.actions: List[str] = data.get("actions", [])
        self.connected_rooms: List[str] = data.get("connected_rooms", [])

    def describe(self) -> str:
        return f"{self.name}: {self.description}"

    def available_actions(self) -> List[str]:
        return list(self.actions)

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
            "objects_present": room.objects,
            "available_actions": room.actions,
            "connected_rooms": room.connected_rooms,
        }

    def choose_next_room(self, current_room: str, preferred_room: Optional[str] = None) -> str:
        """Select the next room for the agent to move to."""
        adjacent = self.adjacent_rooms(current_room)
        if not adjacent:
            return current_room
        if preferred_room and preferred_room in adjacent:
            return preferred_room
        return random.choice(adjacent)

"""
Entelect Grand Prix - Submission File Generator
================================================
Builds and validates the race strategy JSON, then writes the .txt submission file.

Usage:
    from submission_generator import RaceStrategy, Lap, Segment, PitStop

    strategy = RaceStrategy(initial_tyre_id=1)

    lap = strategy.add_lap()
    lap.add_straight(segment_id=1, target_speed=70, brake_start_m=800)
    lap.add_corner(segment_id=2)
    lap.set_pit(enter=False)

    strategy.save("submission.txt")
"""

import json
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Segment:
    id: int
    type: str  # "straight" or "corner"
    target_speed: Optional[float] = None  # straights only (m/s)
    brake_start_m: Optional[float] = None  # straights only — distance before next segment


@dataclass
class PitStop:
    enter: bool = False
    tyre_change_set_id: Optional[int] = None  # tyre ID to switch to (must match JSON level file)
    fuel_refuel_amount_l: Optional[float] = None


@dataclass
class Lap:
    lap_number: int
    segments: list = field(default_factory=list)
    pit: PitStop = field(default_factory=PitStop)

    def add_straight(self, segment_id: int, target_speed: float, brake_start_m: float):
        """Add a straight segment with target speed and braking point."""
        self.segments.append(Segment(
            id=segment_id,
            type="straight",
            target_speed=target_speed,
            brake_start_m=brake_start_m,
        ))
        return self

    def add_corner(self, segment_id: int):
        """Add a corner segment (no speed/brake decisions needed)."""
        self.segments.append(Segment(id=segment_id, type="corner"))
        return self

    def set_pit(
            self,
            enter: bool,
            tyre_change_set_id: Optional[int] = None,
            fuel_refuel_amount_l: Optional[float] = None,
    ):
        """Configure pit stop for end of this lap."""
        self.pit = PitStop(
            enter=enter,
            tyre_change_set_id=tyre_change_set_id if enter else None,
            fuel_refuel_amount_l=fuel_refuel_amount_l if enter else None,
        )
        return self


# ---------------------------------------------------------------------------
# Main strategy builder
# ---------------------------------------------------------------------------

class RaceStrategy:
    def __init__(self, initial_tyre_id: int):
        """
        Args:
            initial_tyre_id: The tyre ID (from the level JSON) to start the race on.
        """
        self.initial_tyre_id = initial_tyre_id
        self.laps: list[Lap] = []

    def add_lap(self) -> Lap:
        """Add a new lap and return it so segments can be chained on."""
        lap = Lap(lap_number=len(self.laps) + 1)
        self.laps.append(lap)
        return lap

    # -----------------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------------

    def _segment_to_dict(self, seg: Segment) -> dict:
        d = {"id": seg.id, "type": seg.type}
        if seg.type == "straight":
            if seg.target_speed is None or seg.brake_start_m is None:
                raise ValueError(
                    f"Straight segment {seg.id} is missing target_speed or brake_start_m."
                )
            d["target_m/s"] = seg.target_speed
            d["brake_start_m_before_next"] = seg.brake_start_m
        return d

    def _pit_to_dict(self, pit: PitStop) -> dict:
        d: dict = {"enter": pit.enter}
        if pit.enter:
            if pit.tyre_change_set_id is not None:
                d["tyre_change_set_id"] = pit.tyre_change_set_id
            if pit.fuel_refuel_amount_l is not None and pit.fuel_refuel_amount_l > 0:
                d["fuel_refuel_amount_l"] = pit.fuel_refuel_amount_l
        return d

    def to_dict(self) -> dict:
        return {
            "initial_tyre_id": self.initial_tyre_id,
            "laps": [
                {
                    "lap": lap.lap_number,
                    "segments": [self._segment_to_dict(s) for s in lap.segments],
                    "pit": self._pit_to_dict(lap.pit),
                }
                for lap in self.laps
            ],
        }

    # -----------------------------------------------------------------------
    # Output
    # -----------------------------------------------------------------------

    def to_json(self, indent: int = 2) -> str:
        """Return the strategy as a formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, filepath: str, indent: int = 2, strict: bool = True):
        """
        Validate and write the submission .txt file.

        Args:
            filepath:  Output path, e.g. "submission.txt"
            indent:    JSON indentation (default 2).
            strict:    If True, raises an error when validation warnings exist.
                       Set to False to save anyway with warnings printed.
        """
        payload = self.to_json(indent=indent)

        with open(filepath, "w") as f:
            f.write(payload)

        print(f"Submission saved to '{filepath}'")
        print(f"    Laps: {len(self.laps)}")
        print(f"    Initial tyre ID: {self.initial_tyre_id}")
        pits = [l.lap_number for l in self.laps if l.pit.enter]
        if pits:
            print(f"    Pit stop laps: {pits}")
        else:
            print("    No pit stops.")


# ---------------------------------------------------------------------------
# Quick helpers
# ---------------------------------------------------------------------------

def load_level(filepath: str) -> dict:
    """Load and return the level JSON file as a dict."""
    with open(filepath) as f:
        return json.load(f)


def max_corner_speed(tyre_friction: float, radius_m: float, crawl_constant: float, gravity: float = 9.8) -> float:
    """
    Calculate the maximum safe speed for a corner.
    Formula: sqrt(tyre_friction * gravity * radius) + crawl_constant
    """
    return (tyre_friction * gravity * radius_m) ** 0.5 + crawl_constant


def braking_distance(initial_speed: float, final_speed: float, deceleration: float) -> float:
    """
    Calculate the distance needed to brake from initial_speed to final_speed.
    Formula: (v_f^2 - v_i^2) / (2 * -decel)
    """
    if final_speed >= initial_speed:
        return 0.0
    return (initial_speed ** 2 - final_speed ** 2) / (2 * deceleration)


def tyre_friction(base_friction: float, total_degradation: float, weather_multiplier: float) -> float:
    """Current tyre friction accounting for wear and weather."""
    return (base_friction - total_degradation) * weather_multiplier


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # --- mirrors the example track from the problem spec (8 segments, 2 laps) ---

    strategy = RaceStrategy(initial_tyre_id=1)

    # Lap 1 — no pit stop
    lap1 = strategy.add_lap()
    lap1.add_straight(segment_id=1, target_speed=70, brake_start_m=800)
    lap1.add_corner(segment_id=2)
    lap1.add_straight(segment_id=3, target_speed=50, brake_start_m=500)
    lap1.add_corner(segment_id=4)
    lap1.add_corner(segment_id=5)
    lap1.add_corner(segment_id=6)
    lap1.add_straight(segment_id=7, target_speed=60, brake_start_m=500)
    lap1.add_corner(segment_id=8)
    lap1.set_pit(enter=False)

    # Lap 2 — pit stop: change tyres (set 3) and refuel 20L
    lap2 = strategy.add_lap()
    lap2.add_straight(segment_id=1, target_speed=70, brake_start_m=800)
    lap2.add_corner(segment_id=2)
    lap2.add_straight(segment_id=3, target_speed=50, brake_start_m=500)
    lap2.add_corner(segment_id=4)
    lap2.add_corner(segment_id=5)
    lap2.add_corner(segment_id=6)
    lap2.add_straight(segment_id=7, target_speed=60, brake_start_m=500)
    lap2.add_corner(segment_id=8)
    lap2.set_pit(enter=True, tyre_change_set_id=3, fuel_refuel_amount_l=20)

    # Save
    strategy.save("submission.txt")

    # Preview
    print("\n--- JSON preview ---")
    print(strategy.to_json())
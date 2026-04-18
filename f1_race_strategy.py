"""
Entelect Grand Prix F1 Race Strategy Solver
Skeleton + Optimization Algorithm
"""

import json
import math
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum
import copy

# ============================================================================
# DATA STRUCTURES (SKELETON)
# ============================================================================

class Weather(Enum):
    DRY = "dry"
    COLD = "cold"
    LIGHT_RAIN = "light_rain"
    HEAVY_RAIN = "heavy_rain"

class SegmentType(Enum):
    STRAIGHT = "straight"
    CORNER = "corner"

@dataclass
class CarSpec:
    """Car physical properties"""
    max_speed: float  # m/s
    accel: float  # m/s²
    brake: float  # m/s²
    limp_speed: float  # m/s (when fuel/tyre fails)
    crawl_speed: float  # m/s (when crash)
    fuel_capacity: float  # litres
    initial_fuel: float  # litres

@dataclass
class TyreProperties:
    """Properties of a single tyre compound"""
    compound: str  # "Soft", "Medium", "Hard", "Intermediate", "Wet"
    base_friction: float
    dry_multiplier: float
    cold_multiplier: float
    light_rain_multiplier: float
    heavy_rain_multiplier: float
    dry_degradation: float
    cold_degradation: float
    light_rain_degradation: float
    heavy_rain_degradation: float

@dataclass
class TyreSet:
    """A specific tyre set instance (has an ID and health)"""
    tyre_id: int
    compound: str
    total_degradation: float = 0.0  # cumulative wear

@dataclass
class Segment:
    """A track segment (straight or corner)"""
    segment_id: int
    segment_type: SegmentType
    length: float  # metres
    radius: Optional[float] = None  # metres (only for corners)

@dataclass
class RaceConfig:
    """Full race configuration"""
    name: str
    laps: int
    pit_tyre_swap_time: float  # seconds
    base_pit_stop_time: float  # seconds
    pit_refuel_rate: float  # litres/second
    corner_crash_penalty: float  # seconds
    pit_exit_speed: float  # m/s
    fuel_soft_cap: float  # litres
    time_reference: float  # seconds (reference lap time for scoring)
    gravity: float = 9.8

# ============================================================================
# PHYSICS CONSTANTS
# ============================================================================

K_STRAIGHT = 0.0000166
K_BRAKING = 0.0398
K_CORNER = 0.000265

K_BASE_FUEL = 0.0005  # l/m
K_DRAG_FUEL = 0.0000000015  # l/m

CRAWL_CONSTANT = 10  # m/s added to corner formula


# ============================================================================
# PHYSICS CALCULATIONS
# ============================================================================

def get_weather_multiplier(tyre: TyreProperties, weather: Weather) -> float:
    """Get friction multiplier for tyre in given weather"""
    if weather == Weather.DRY:
        return tyre.dry_multiplier
    elif weather == Weather.COLD:
        return tyre.cold_multiplier
    elif weather == Weather.LIGHT_RAIN:
        return tyre.light_rain_multiplier
    elif weather == Weather.HEAVY_RAIN:
        return tyre.heavy_rain_multiplier
    return 1.0

def get_degradation_rate(tyre: TyreProperties, weather: Weather) -> float:
    """Get degradation rate for tyre in given weather"""
    if weather == Weather.DRY:
        return tyre.dry_degradation
    elif weather == Weather.COLD:
        return tyre.cold_degradation
    elif weather == Weather.LIGHT_RAIN:
        return tyre.light_rain_degradation
    elif weather == Weather.HEAVY_RAIN:
        return tyre.heavy_rain_degradation
    return 0.0

def calculate_tyre_friction(tyre: TyreProperties, total_degradation: float, weather: Weather) -> float:
    """
    Calculate current tyre friction based on wear and weather
    friction = (base_friction - degradation) * weather_multiplier
    """
    multiplier = get_weather_multiplier(tyre, weather)
    friction = (tyre.base_friction - total_degradation) * multiplier
    return max(friction, 0.0)  # Can't go below 0

def calculate_max_corner_speed(tyre: TyreProperties, total_degradation: float, 
                               weather: Weather, radius: float, gravity: float = 9.8) -> float:
    """
    Maximum safe corner speed
    max_speed = sqrt(friction * gravity * radius) + crawl_constant
    """
    friction = calculate_tyre_friction(tyre, total_degradation, weather)
    max_speed = math.sqrt(friction * gravity * radius) + CRAWL_CONSTANT
    return max_speed

def calculate_acceleration_time(initial_speed: float, final_speed: float, accel: float) -> float:
    """Time to accelerate from initial to final speed"""
    if accel == 0:
        return 0
    return (final_speed - initial_speed) / accel

def calculate_acceleration_distance(initial_speed: float, final_speed: float, accel: float) -> float:
    """Distance covered during acceleration"""
    if accel == 0:
        return 0
    return (final_speed**2 - initial_speed**2) / (2 * accel)

def calculate_braking_distance(initial_speed: float, final_speed: float, brake: float) -> float:
    """Distance needed to brake from initial to final speed"""
    if brake == 0:
        return 0
    return (initial_speed**2 - final_speed**2) / (2 * brake)

def calculate_fuel_used(initial_speed: float, final_speed: float, distance: float) -> float:
    """
    Fuel consumption formula
    fuel = (K_base + K_drag * avg_speed²) * distance
    """
    avg_speed = (initial_speed + final_speed) / 2
    return (K_BASE_FUEL + K_DRAG_FUEL * (avg_speed**2)) * distance

def calculate_straight_degradation(tyre: TyreProperties, weather: Weather, distance: float) -> float:
    """Tyre degradation on a straight"""
    rate = get_degradation_rate(tyre, weather)
    return rate * distance * K_STRAIGHT

def calculate_braking_degradation(tyre: TyreProperties, weather: Weather, 
                                  initial_speed: float, final_speed: float) -> float:
    """Tyre degradation during braking"""
    rate = get_degradation_rate(tyre, weather)
    speed_factor = ((initial_speed / 100)**2) - ((final_speed / 100)**2)
    return speed_factor * K_BRAKING * rate

def calculate_corner_degradation(tyre: TyreProperties, weather: Weather, 
                                 speed: float, radius: float) -> float:
    """Tyre degradation in a corner"""
    rate = get_degradation_rate(tyre, weather)
    return K_CORNER * (speed**2 / radius) * rate

def calculate_pit_stop_time(refuel_amount: float, pit_swap_time: float, 
                           base_pit_time: float, refuel_rate: float) -> float:
    """Total pit stop time"""
    refuel_time = refuel_amount / refuel_rate if refuel_rate > 0 else 0
    return refuel_time + pit_swap_time + base_pit_time


# ============================================================================
# RACE SIMULATION ENGINE
# ============================================================================

@dataclass
class SegmentResult:
    """Result of simulating one segment"""
    distance: float
    time: float
    fuel_used: float
    tyre_degradation: float
    entry_speed: float
    exit_speed: float
    crashed: bool = False
    limp_mode: bool = False
    fuel_depleted: bool = False
    tyre_blowout: bool = False

@dataclass
class LapResult:
    """Result of simulating one complete lap"""
    lap_number: int
    time: float
    fuel_used: float
    total_tyre_degradation: float
    segments: List[SegmentResult]
    pit_time: float = 0.0
    pit_refueled: float = 0.0
    pit_tyre_changed: bool = False
    penalties: float = 0.0  # crash penalties
    final_fuel: float = 0.0
    final_tyre_health: Dict[int, float] = None

class RaceSimulator:
    """Simulates a complete race given a strategy"""
    
    def __init__(self, car: CarSpec, track: List[Segment], tyres_db: Dict[str, TyreProperties],
                 race_config: RaceConfig, available_tyre_sets: Dict[int, TyreSet],
                 weather_schedule: List[Tuple[float, Weather]]):
        self.car = car
        self.track = track
        self.tyres_db = tyres_db
        self.race_config = race_config
        self.available_tyre_sets = available_tyre_sets
        self.weather_schedule = weather_schedule  # [(time_s, weather), ...]
        
    def get_weather_at_time(self, current_time: float) -> Weather:
        """Get current weather condition at a given race time"""
        weather = Weather.DRY
        for time, w in self.weather_schedule:
            if current_time >= time:
                weather = w
            else:
                break
        return weather
    
    def simulate_segment(self, segment: Segment, current_speed: float, target_speed: Optional[float],
                        brake_point_m: Optional[float], tyre_set: TyreSet, 
                        current_time: float, fuel: float) -> SegmentResult:
        """
        Simulate a single track segment
        target_speed and brake_point_m are only for straights
        """
        weather = self.get_weather_at_time(current_time)
        tyre_props = self.tyres_db[tyre_set.compound]
        
        result = SegmentResult(
            distance=segment.length,
            time=0.0,
            fuel_used=0.0,
            tyre_degradation=0.0,
            entry_speed=current_speed,
            exit_speed=current_speed
        )
        
        if segment.segment_type == SegmentType.CORNER:
            # Corner: maintain constant entry speed, check for crash
            max_safe_speed = calculate_max_corner_speed(
                tyre_props, tyre_set.total_degradation, weather, segment.radius, self.race_config.gravity
            )
            
            if current_speed > max_safe_speed:
                # CRASH
                result.crashed = True
                result.time = segment.length / self.car.crawl_speed
                result.exit_speed = self.car.crawl_speed
                result.tyre_degradation += 0.1  # Penalty degradation
                # But still consume fuel at crawl speed
                result.fuel_used = calculate_fuel_used(self.car.crawl_speed, self.car.crawl_speed, segment.length)
                return result
            
            # Safe corner: constant speed through
            result.time = segment.length / current_speed if current_speed > 0 else float('inf')
            result.exit_speed = current_speed
            result.fuel_used = calculate_fuel_used(current_speed, current_speed, segment.length)
            result.tyre_degradation = calculate_corner_degradation(
                tyre_props, weather, current_speed, segment.radius
            )
            return result
        
        else:  # STRAIGHT
            # Straight: accelerate, cruise, brake
            if target_speed is None:
                target_speed = self.car.max_speed
            
            target_speed = min(target_speed, self.car.max_speed)
            
            # Phase 1: Accelerate from current speed to target speed
            accel_distance = calculate_acceleration_distance(current_speed, target_speed, self.car.accel)
            accel_time = calculate_acceleration_time(current_speed, target_speed, self.car.accel)
            accel_fuel = calculate_fuel_used(current_speed, target_speed, accel_distance)
            accel_degradation = calculate_straight_degradation(tyre_props, weather, accel_distance)
            
            # Phase 2: Cruise at target speed
            remaining_before_brake = segment.length - accel_distance
            if brake_point_m is not None:
                remaining_before_brake = min(remaining_before_brake, brake_point_m)
            
            cruise_distance = remaining_before_brake
            cruise_time = cruise_distance / target_speed if target_speed > 0 else float('inf')
            cruise_fuel = calculate_fuel_used(target_speed, target_speed, cruise_distance)
            cruise_degradation = calculate_straight_degradation(tyre_props, weather, cruise_distance)
            
            # Phase 3: Brake to next segment's safe speed
            brake_distance = segment.length - accel_distance - cruise_distance
            
            # For now, assume next segment is a corner with a max safe speed
            # This is simplified - in a full solution you'd check what's next
            next_safe_speed = self.car.crawl_speed  # Simplified
            
            brake_time = (brake_distance / ((target_speed + next_safe_speed) / 2)) if (target_speed + next_safe_speed) > 0 else 0
            brake_fuel = calculate_fuel_used(target_speed, next_safe_speed, brake_distance)
            brake_degradation = calculate_braking_degradation(
                tyre_props, weather, target_speed, next_safe_speed
            )
            
            # Accumulate
            result.time = accel_time + cruise_time + brake_time
            result.fuel_used = accel_fuel + cruise_fuel + brake_fuel
            result.tyre_degradation = accel_degradation + cruise_degradation + brake_degradation
            result.exit_speed = next_safe_speed
            
            return result
    
    def simulate_lap(self, lap_number: int, initial_speed: float, initial_fuel: float,
                    tyre_set: TyreSet, starting_time: float,
                    segment_strategy: List[Dict]) -> LapResult:
        """
        Simulate one complete lap
        segment_strategy: [{"target_m/s": 70, "brake_start_m_before_next": 800}, ...]
        """
        current_speed = initial_speed
        current_fuel = initial_fuel
        current_time = starting_time
        tyre_degradation_accum = 0.0
        segment_results = []
        penalties = 0.0
        
        # Make a copy of the tyre set for this lap
        current_tyre = copy.deepcopy(tyre_set)
        
        for i, segment in enumerate(self.track):
            strategy = segment_strategy[i] if i < len(segment_strategy) else {}
            
            # Get target speed and brake point from strategy
            target_speed = strategy.get("target_m/s", None)
            brake_point = strategy.get("brake_start_m_before_next", None)
            
            # Simulate segment
            seg_result = self.simulate_segment(
                segment, current_speed, target_speed, brake_point, current_tyre, current_time, current_fuel
            )
            
            # Check for out-of-fuel or tyre blowout
            current_fuel -= seg_result.fuel_used
            current_tyre.total_degradation += seg_result.tyre_degradation
            
            if current_fuel <= 0:
                seg_result.fuel_depleted = True
                current_speed = self.car.limp_speed
            elif current_tyre.total_degradation >= 1.0:
                seg_result.tyre_blowout = True
                current_speed = self.car.limp_speed
            else:
                current_speed = seg_result.exit_speed
            
            if seg_result.crashed:
                penalties += self.race_config.corner_crash_penalty
            
            current_time += seg_result.time
            tyre_degradation_accum += seg_result.tyre_degradation
            segment_results.append(seg_result)
        
        lap_result = LapResult(
            lap_number=lap_number,
            time=sum(s.time for s in segment_results) + penalties,
            fuel_used=sum(s.fuel_used for s in segment_results),
            total_tyre_degradation=tyre_degradation_accum,
            segments=segment_results,
            penalties=penalties,
            final_fuel=current_fuel,
            final_tyre_health={tyre_set.tyre_id: current_tyre.total_degradation}
        )
        
        return lap_result
    
    def simulate_race(self, strategy_dict: Dict) -> Dict:
        """
        Simulate entire race given a strategy dict
        {
          "initial_tyre_id": 1,
          "laps": [
            {"segments": [...], "pit": {...}},
            ...
          ]
        }
        """
        current_fuel = self.car.initial_fuel
        current_time = 0.0
        current_speed = 0.0  # Race starts at 0
        current_tyre_id = strategy_dict["initial_tyre_id"]
        current_tyre = self.available_tyre_sets[current_tyre_id]
        
        all_lap_results = []
        total_race_time = 0.0
        total_fuel_used = 0.0
        
        for lap_data in strategy_dict["laps"]:
            lap_num = lap_data["lap"]
            segment_strategy = lap_data["segments"]
            
            # Simulate lap
            lap_result = self.simulate_lap(
                lap_num, current_speed, current_fuel, current_tyre, current_time, segment_strategy
            )
            
            all_lap_results.append(lap_result)
            total_race_time += lap_result.time
            total_fuel_used += lap_result.fuel_used
            current_fuel = lap_result.final_fuel
            current_time += lap_result.time
            
            # Handle pit stop
            pit_data = lap_data.get("pit", {})
            if pit_data.get("enter", False):
                refuel_amount = pit_data.get("fuel_refuel_amount_l", 0)
                new_tyre_id = pit_data.get("tyre_change_set_id", None)
                
                pit_time = calculate_pit_stop_time(
                    refuel_amount,
                    self.race_config.pit_tyre_swap_time,
                    self.race_config.base_pit_stop_time,
                    self.race_config.pit_refuel_rate
                )
                
                total_race_time += pit_time
                current_fuel = min(current_fuel + refuel_amount, self.car.fuel_capacity)
                current_speed = self.race_config.pit_exit_speed
                
                if new_tyre_id is not None:
                    current_tyre = copy.deepcopy(self.available_tyre_sets[new_tyre_id])
                    current_tyre_id = new_tyre_id
        
        return {
            "total_time": total_race_time,
            "total_fuel_used": total_fuel_used,
            "lap_results": all_lap_results,
            "valid": total_fuel_used <= self.car.fuel_capacity * 2  # Simple validity check
        }


# ============================================================================
# OPTIMIZATION ENGINE
# ============================================================================

class RaceOptimizer:
    """Finds the best race strategy using search algorithms"""
    
    def __init__(self, car: CarSpec, track: List[Segment], tyres_db: Dict[str, TyreProperties],
                 race_config: RaceConfig, available_tyre_sets: Dict[int, TyreSet],
                 weather_schedule: List[Tuple[float, Weather]]):
        self.car = car
        self.track = track
        self.tyres_db = tyres_db
        self.race_config = race_config
        self.available_tyre_sets = available_tyre_sets
        self.weather_schedule = weather_schedule
        self.simulator = RaceSimulator(car, track, tyres_db, race_config, available_tyre_sets, weather_schedule)
    
    def calculate_score(self, race_result: Dict) -> float:
        """
        Calculate score using Level 1 formula (basic)
        Higher is better
        """
        if not race_result["valid"]:
            return -float('inf')
        
        time = race_result["total_time"]
        base_score = 500000 * (self.race_config.time_reference / time) ** 3
        return base_score
    
    def generate_default_segment_strategy(self, segment: Segment, 
                                         tyre_set: TyreSet) -> Dict:
        """
        Generate a default strategy for a segment
        Conservative: 80% of max safe speed, brake early
        """
        if segment.segment_type == SegmentType.STRAIGHT:
            tyre_props = self.tyres_db[tyre_set.compound]
            weather = self.weather_schedule[0][1] if self.weather_schedule else Weather.DRY
            
            # Conservative target speed: 80% of car's max
            target_speed = self.car.max_speed * 0.8
            
            # Brake point: 70% of the way through the straight
            brake_point = segment.length * 0.7
            
            return {
                "id": segment.segment_id,
                "type": "straight",
                "target_m/s": target_speed,
                "brake_start_m_before_next": int(brake_point)
            }
        else:
            return {
                "id": segment.segment_id,
                "type": "corner"
            }
    
    def generate_strategy(self, initial_tyre_id: int, pit_laps: List[Tuple[int, int, float]]) -> Dict:
        """
        Generate a complete race strategy
        pit_laps: [(lap_number, new_tyre_id, refuel_amount), ...]
        """
        pit_set = {lap for lap, _, _ in pit_laps}
        pit_map = {lap: (tyre_id, refuel) for lap, tyre_id, refuel in pit_laps}
        
        laps = []
        current_tyre_id = initial_tyre_id
        current_tyre = copy.deepcopy(self.available_tyre_sets[initial_tyre_id])
        
        for lap_num in range(1, self.race_config.laps + 1):
            segments = []
            for segment in self.track:
                seg_strategy = self.generate_default_segment_strategy(segment, current_tyre)
                segments.append(seg_strategy)
            
            pit_data = {"enter": False}
            if lap_num in pit_set:
                new_tyre_id, refuel = pit_map[lap_num]
                pit_data = {
                    "enter": True,
                    "tyre_change_set_id": new_tyre_id,
                    "fuel_refuel_amount_l": refuel
                }
                current_tyre_id = new_tyre_id
                current_tyre = copy.deepcopy(self.available_tyre_sets[new_tyre_id])
            
            laps.append({
                "lap": lap_num,
                "segments": segments,
                "pit": pit_data
            })
        
        return {
            "initial_tyre_id": initial_tyre_id,
            "laps": laps
        }
    
    def optimize_grid_search(self, max_iterations: int = 100) -> Tuple[Dict, float]:
        """
        Grid search over initial tyre, pit timing, and pit tyres
        Returns: (best_strategy, best_score)
        """
        best_strategy = None
        best_score = -float('inf')
        iterations = 0
        
        tyre_ids = list(self.available_tyre_sets.keys())
        
        # Try each initial tyre
        for initial_tyre in tyre_ids:
            if iterations >= max_iterations:
                break
            
            # Try different pit stop patterns
            # Simple: 0 pits, 1 pit (at lap 1), 1 pit (at mid-lap), etc.
            pit_configs = [
                [],  # No pit stops
                [(1, initial_tyre, 30)],  # Pit at lap 1, refuel 30L
                [(self.race_config.laps // 2, initial_tyre, 50)],  # Pit at mid-race
                [(1, initial_tyre, 50), (self.race_config.laps // 2, initial_tyre, 50)],  # Two pits
            ]
            
            for pit_config in pit_configs:
                if iterations >= max_iterations:
                    break
                
                strategy = self.generate_strategy(initial_tyre, pit_config)
                race_result = self.simulator.simulate_race(strategy)
                score = self.calculate_score(race_result)
                
                print(f"Iteration {iterations}: Initial Tyre={initial_tyre}, Pits={len(pit_config)}, Score={score:.1f}, Time={race_result['total_time']:.1f}s")
                
                if score > best_score:
                    best_score = score
                    best_strategy = strategy
                
                iterations += 1
        
        return best_strategy, best_score


# ============================================================================
# MAIN RUNNER
# ============================================================================

def load_level_json(filepath: str) -> Tuple[CarSpec, List[Segment], Dict[str, TyreProperties], 
                                             RaceConfig, Dict[int, TyreSet], List[Tuple[float, Weather]]]:
    """Load and parse a level JSON file following Level 4/5 specifications."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # 1. Parse Car Specifications
    car_data = data['car']
    car = CarSpec(
        max_speed=car_data['max_speed_m/s'],
        accel=car_data['accel_m/se2'],
        brake=car_data['brake_m/se2'],
        limp_speed=car_data['limp_constant_m/s'],
        crawl_speed=car_data['crawl_constant_m/s'],
        fuel_capacity=car_data['fuel_tank_capacity_l'],
        initial_fuel=car_data['initial_fuel_l']
    )
    
    # 2. Parse Race Configuration
    race_data = data['race']
    race_config = RaceConfig(
        name=race_data['name'],
        laps=race_data['laps'],
        pit_tyre_swap_time=race_data['pit_tyre_swap_time_s'],
        base_pit_stop_time=race_data['base_pit_stop_time_s'],
        pit_refuel_rate=race_data['pit_refuel_rate_l/s'],
        corner_crash_penalty=race_data['corner_crash_penalty_s'],
        pit_exit_speed=race_data['pit_exit_speed_m/s'],
        fuel_soft_cap=race_data['fuel_soft_cap_limit_l'],
        time_reference=race_data.get('time_reference', 7300.0)
    )
    
    # 3. Parse Track Segments
    track = []
    for seg_data in data['track']['segments']:
        segment = Segment(
            segment_id=seg_data['id'],
            segment_type=SegmentType(seg_data['type']),
            length=seg_data['length_m'],
            radius=seg_data.get('radius_m', None) # Radius is None for straights
        )
        track.append(segment)
    
    # 4. Parse Tyre Properties (Compounds)
    tyres_db = {}
    tyre_props_data = data['tyres']['properties']
    for compound, props in tyre_props_data.items():
        tyre = TyreProperties(
            compound=compound,
            base_friction=props['life_span'],
            dry_multiplier=props['dry_friction_multiplier'],
            cold_multiplier=props['cold_friction_multiplier'],
            light_rain_multiplier=props['light_rain_friction_multiplier'],
            heavy_rain_multiplier=props['heavy_rain_friction_multiplier'],
            dry_degradation=props['dry_degradation'],
            cold_degradation=props['cold_degradation'],
            light_rain_degradation=props['light_rain_degradation'],
            heavy_rain_degradation=props['heavy_rain_degradation']
        )
        tyres_db[compound] = tyre
    
    # 5. Parse Available Tyre Sets (Individual IDs)
    available_sets = {}
    for set_data in data['tyres']['available_sets']:
        compound = set_data['compound']
        for tyre_id in set_data['ids']:
            available_sets[tyre_id] = TyreSet(
                tyre_id=tyre_id,
                compound=compound,
                total_degradation=0.0
            )
    
    # 6. Parse Weather Schedule (Cumulative Timing)
    weather_schedule = []
    current_time_offset = 0.0
    if 'weather' in data and 'conditions' in data['weather']:
        for cond in data['weather']['conditions']:
            weather_type = Weather(cond['condition'])
            # Each condition starts after the previous one ends
            weather_schedule.append((current_time_offset, weather_type))
            current_time_offset += cond['duration_s']
    else:
        weather_schedule = [(0.0, Weather.DRY)]
    
    return car, track, tyres_db, race_config, available_sets, weather_schedule

def main():
    """Main entry point"""
    print("=" * 80)
    print("ENTELECT GRAND PRIX - RACE STRATEGY OPTIMIZER")
    print("=" * 80)
    
    # Example usage (you would load from actual JSON)
    # For now, we'll create a minimal test case
    
    car = CarSpec(
        max_speed=90,
        accel=10,
        brake=20,
        limp_speed=20,
        crawl_speed=10,
        fuel_capacity=150,
        initial_fuel=150
    )
    
    track = [
        Segment(1, SegmentType.STRAIGHT, 850),
        Segment(2, SegmentType.CORNER, 120, radius=60),
        Segment(3, SegmentType.STRAIGHT, 850),
        Segment(4, SegmentType.CORNER, 120, radius=60),
    ]
    
    tyres_db = {
        "Soft": TyreProperties("Soft", 1.8, 1.18, 1.00, 0.92, 0.80, 0.14, 0.11, 0.12, 0.13),
        "Medium": TyreProperties("Medium", 1.7, 1.08, 0.97, 0.88, 0.74, 0.10, 0.08, 0.09, 0.10),
        "Hard": TyreProperties("Hard", 1.6, 0.98, 0.92, 0.82, 0.68, 0.07, 0.06, 0.07, 0.08),
    }
    
    race_config = RaceConfig(
        name="Test Race",
        laps=2,
        pit_tyre_swap_time=10,
        base_pit_stop_time=20,
        pit_refuel_rate=5,
        corner_crash_penalty=10,
        pit_exit_speed=20,
        fuel_soft_cap=1400,
        time_reference=7300
    )
    
    available_sets = {
        1: TyreSet(1, "Soft"),
        2: TyreSet(2, "Medium"),
        3: TyreSet(3, "Hard"),
    }
    
    weather_schedule = [(0.0, Weather.DRY)]
    
    # Create optimizer
    optimizer = RaceOptimizer(car, track, tyres_db, race_config, available_sets, weather_schedule)
    
    # Run optimization
    print("\nStarting grid search optimization...")
    best_strategy, best_score = optimizer.optimize_grid_search(max_iterations=20)
    
    print(f"\n{'='*80}")
    print(f"BEST STRATEGY FOUND")
    print(f"{'='*80}")
    print(f"Score: {best_score:.1f}")
    print(f"Strategy: {json.dumps(best_strategy, indent=2)}")
    
    # Save to output file
    with open('race_strategy.txt', 'w') as f:
        json.dump(best_strategy, f, indent=2)
    print(f"\nStrategy saved to: /mnt/user-data/outputs/race_strategy.json")


if __name__ == "__main__":
    main()

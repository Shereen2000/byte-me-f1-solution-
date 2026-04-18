"""
Advanced Race Optimizer
Multiple search strategies to find the optimal race strategy
"""

import json
import math
import random
from typing import List, Dict, Tuple, Optional, Callable
from f1_race_strategy import (
    RaceOptimizer, RaceSimulator, RaceConfig, CarSpec, Segment, TyreProperties, TyreSet, Weather
)

class AdvancedOptimizer(RaceOptimizer):
    """Extended optimizer with multiple search algorithms"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iteration_count = 0
        self.best_score_history = []
    
    def log_iteration(self, strategy: Dict, score: float, label: str = ""):
        """Log optimization progress"""
        self.iteration_count += 1
        self.best_score_history.append(score)
        print(f"[{self.iteration_count:4d}] {label:30s} Score: {score:15.1f}")
    
    # ========================================================================
    # ALGORITHM 1: ENHANCED GRID SEARCH
    # ========================================================================
    
    def optimize_grid_search_enhanced(self, max_iterations: int = 200) -> Tuple[Dict, float]:
        """
        Exhaustive grid search over:
        - Initial tyre (5 choices)
        - Pit stop patterns (many configurations)
        - Refuel amounts (discrete)
        """
        print("\n" + "="*80)
        print("ALGORITHM 1: ENHANCED GRID SEARCH")
        print("="*80)
        
        best_strategy = None
        best_score = -float('inf')
        self.iteration_count = 0
        
        tyre_ids = sorted(self.available_tyre_sets.keys())
        
        # Generate pit configurations
        pit_configs = self._generate_pit_configs()
        
        for initial_tyre in tyre_ids:
            for pit_config in pit_configs:
                if self.iteration_count >= max_iterations:
                    break
                
                strategy = self.generate_strategy(initial_tyre, pit_config)
                race_result = self.simulator.simulate_race(strategy)
                score = self.calculate_score(race_result)
                
                pit_summary = f"Tyres={initial_tyre}, Pits={len(pit_config)}"
                self.log_iteration(strategy, score, pit_summary)
                
                if score > best_score:
                    best_score = score
                    best_strategy = strategy
            
            if self.iteration_count >= max_iterations:
                break
        
        return best_strategy, best_score
    
    def _generate_pit_configs(self) -> List[List[Tuple[int, int, float]]]:
        """Generate different pit stop configurations"""
        configs = [
            [],  # No pit stops
        ]
        
        tyre_ids = list(self.available_tyre_sets.keys())
        refuel_amounts = [30, 50, 70, 100]
        
        # Single pit stops at different laps
        for lap in range(1, self.race_config.laps):
            for tyre_id in tyre_ids:
                for refuel in refuel_amounts:
                    configs.append([(lap, tyre_id, refuel)])
        
        # Two pit stops (simpler: same tyre, different refuel amounts)
        if self.race_config.laps >= 3:
            lap1 = 1
            lap2 = self.race_config.laps - 1
            for refuel1 in [40, 60]:
                for refuel2 in [40, 60]:
                    configs.append([
                        (lap1, tyre_ids[0], refuel1),
                        (lap2, tyre_ids[0], refuel2)
                    ])
        
        return configs[:100]  # Limit for performance
    
    # ========================================================================
    # ALGORITHM 2: LOCAL SEARCH (HILL CLIMBING)
    # ========================================================================
    
    def optimize_local_search(self, initial_strategy: Optional[Dict] = None, 
                            max_iterations: int = 500) -> Tuple[Dict, float]:
        """
        Hill climbing: start with a strategy, make small tweaks, keep if better
        """
        print("\n" + "="*80)
        print("ALGORITHM 2: LOCAL SEARCH (HILL CLIMBING)")
        print("="*80)
        
        # Start with initial strategy or generate one
        if initial_strategy is None:
            initial_strategy = self.generate_strategy(1, [])  # Start with tyre 1, no pits
        
        current_strategy = initial_strategy
        current_score = self.calculate_score(self.simulator.simulate_race(current_strategy))
        self.iteration_count = 0
        
        best_strategy = current_strategy
        best_score = current_score
        self.log_iteration(current_strategy, current_score, "INITIAL")
        
        improved = True
        while improved and self.iteration_count < max_iterations:
            improved = False
            
            # Try tweaking each parameter
            for lap_idx in range(len(current_strategy['laps'])):
                if self.iteration_count >= max_iterations:
                    break
                
                # Try adding a pit stop
                if not current_strategy['laps'][lap_idx]['pit']['enter']:
                    for tyre_id in self.available_tyre_sets.keys():
                        for refuel in [30, 50, 70]:
                            new_strategy = self._tweak_pit_stop(current_strategy, lap_idx, tyre_id, refuel)
                            score = self.calculate_score(self.simulator.simulate_race(new_strategy))
                            self.log_iteration(new_strategy, score, f"Tweak pit at lap {lap_idx+1}")
                            
                            if score > current_score:
                                current_score = score
                                current_strategy = new_strategy
                                improved = True
                                
                                if score > best_score:
                                    best_score = score
                                    best_strategy = new_strategy
                            
                            if self.iteration_count >= max_iterations:
                                break
        
        return best_strategy, best_score
    
    def _tweak_pit_stop(self, strategy: Dict, lap_idx: int, tyre_id: int, refuel: float) -> Dict:
        """Create a new strategy with a pit stop added/modified"""
        new_strategy = json.loads(json.dumps(strategy))  # Deep copy
        new_strategy['laps'][lap_idx]['pit'] = {
            'enter': True,
            'tyre_change_set_id': tyre_id,
            'fuel_refuel_amount_l': refuel
        }
        return new_strategy
    
    # ========================================================================
    # ALGORITHM 3: GENETIC ALGORITHM
    # ========================================================================
    
    def optimize_genetic(self, population_size: int = 30, generations: int = 50) -> Tuple[Dict, float]:
        """
        Genetic algorithm: evolve a population of strategies
        """
        print("\n" + "="*80)
        print("ALGORITHM 3: GENETIC ALGORITHM")
        print(f"Population: {population_size}, Generations: {generations}")
        print("="*80)
        
        self.iteration_count = 0
        
        # Initialize population
        population = [
            self.generate_strategy(random.choice(list(self.available_tyre_sets.keys())), [])
            for _ in range(population_size)
        ]
        
        scores = [self.calculate_score(self.simulator.simulate_race(s)) for s in population]
        
        for gen in range(generations):
            # Evaluate
            scores = [self.calculate_score(self.simulator.simulate_race(s)) for s in population]
            best_idx = scores.index(max(scores))
            best_score = scores[best_idx]
            
            self.log_iteration(population[best_idx], best_score, f"GEN {gen+1:3d} (pop avg: {sum(scores)/len(scores):.0f})")
            self.iteration_count += 1
            
            # Selection: keep top 20%, duplicate them
            sorted_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
            elite_count = max(1, population_size // 5)
            elite = [population[i] for i in sorted_idx[:elite_count]]
            
            # Mutation & crossover: create new individuals
            new_population = elite.copy()
            while len(new_population) < population_size:
                if len(elite) >= 2 and random.random() < 0.5:
                    # Crossover: mix two strategies
                    p1 = random.choice(elite)
                    p2 = random.choice(elite)
                    child = self._crossover(p1, p2)
                else:
                    # Mutation: tweak a strategy
                    parent = random.choice(elite)
                    child = self._mutate(parent)
                
                new_population.append(child)
            
            population = new_population[:population_size]
        
        # Final evaluation
        scores = [self.calculate_score(self.simulator.simulate_race(s)) for s in population]
        best_idx = scores.index(max(scores))
        
        return population[best_idx], scores[best_idx]
    
    def _crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        """Combine two strategies"""
        child = json.loads(json.dumps(parent1))
        # Randomly replace pit stops from parent2
        for i in range(len(child['laps'])):
            if random.random() < 0.5:
                child['laps'][i]['pit'] = parent2['laps'][i]['pit']
        return child
    
    def _mutate(self, strategy: Dict) -> Dict:
        """Randomly tweak a strategy"""
        mutated = json.loads(json.dumps(strategy))
        
        # Mutation type 1: Toggle pit stop on a random lap
        if random.random() < 0.3:
            lap_idx = random.randint(0, len(mutated['laps']) - 1)
            if mutated['laps'][lap_idx]['pit']['enter']:
                mutated['laps'][lap_idx]['pit'] = {'enter': False}
            else:
                mutated['laps'][lap_idx]['pit'] = {
                    'enter': True,
                    'tyre_change_set_id': random.choice(list(self.available_tyre_sets.keys())),
                    'fuel_refuel_amount_l': random.choice([30, 50, 70])
                }
        
        # Mutation type 2: Change target speeds slightly
        if random.random() < 0.3:
            lap_idx = random.randint(0, len(mutated['laps']) - 1)
            seg_idx = random.randint(0, len(mutated['laps'][lap_idx]['segments']) - 1)
            seg = mutated['laps'][lap_idx]['segments'][seg_idx]
            
            if seg['type'] == 'straight' and 'target_m/s' in seg:
                delta = random.choice([-5, -2, 2, 5])
                seg['target_m/s'] = max(10, min(self.car.max_speed, seg['target_m/s'] + delta))
        
        return mutated
    
    # ========================================================================
    # ALGORITHM 4: SIMULATED ANNEALING
    # ========================================================================
    
    def optimize_simulated_annealing(self, initial_temp: float = 100.0, 
                                    cooling_rate: float = 0.95,
                                    iterations_per_temp: int = 10) -> Tuple[Dict, float]:
        """
        Simulated annealing: probabilistically accept worse solutions early,
        deterministically accept better solutions late (high temperature → low temperature)
        """
        print("\n" + "="*80)
        print("ALGORITHM 4: SIMULATED ANNEALING")
        print(f"Initial Temp: {initial_temp}, Cooling Rate: {cooling_rate}")
        print("="*80)
        
        self.iteration_count = 0
        
        # Start with random strategy
        current = self.generate_strategy(random.choice(list(self.available_tyre_sets.keys())), [])
        current_score = self.calculate_score(self.simulator.simulate_race(current))
        
        best = current
        best_score = current_score
        
        self.log_iteration(current, current_score, "INITIAL")
        
        temperature = initial_temp
        while temperature > 1.0 and self.iteration_count < 500:
            for _ in range(iterations_per_temp):
                if self.iteration_count >= 500:
                    break
                
                # Generate neighbor by mutation
                neighbor = self._mutate(current)
                neighbor_score = self.calculate_score(self.simulator.simulate_race(neighbor))
                
                # Accept/reject decision
                delta = neighbor_score - current_score
                if delta > 0 or random.random() < math.exp(delta / (temperature + 0.1)):
                    current = neighbor
                    current_score = neighbor_score
                    
                    if current_score > best_score:
                        best = current
                        best_score = current_score
                        self.log_iteration(current, current_score, f"SA IMPROVED (T={temperature:.1f})")
                
                self.iteration_count += 1
            
            temperature *= cooling_rate
            print(f"  Temperature: {temperature:.2f}")
        
        return best, best_score
    
    # ========================================================================
    # ALGORITHM 5: HYBRID (Best of multiple algorithms)
    # ========================================================================
    
    def optimize_hybrid(self, strategies: Optional[List[str]] = None) -> Tuple[Dict, float]:
        """
        Run multiple algorithms and return the best result
        strategies: ["grid_search", "local_search", "genetic", "annealing"]
        """
        if strategies is None:
            strategies = ["grid_search", "local_search"]  # Default: fast algorithms
        
        print("\n" + "="*80)
        print("ALGORITHM 5: HYBRID (Running multiple algorithms)")
        print(f"Strategies: {strategies}")
        print("="*80)
        
        results = []
        
        if "grid_search" in strategies:
            print("\n>>> Running Grid Search...")
            s, score = self.optimize_grid_search_enhanced(max_iterations=100)
            results.append(("Grid Search", s, score))
        
        if "local_search" in strategies:
            print("\n>>> Running Local Search...")
            s, score = self.optimize_local_search(max_iterations=100)
            results.append(("Local Search", s, score))
        
        if "genetic" in strategies:
            print("\n>>> Running Genetic Algorithm...")
            s, score = self.optimize_genetic(population_size=20, generations=30)
            results.append(("Genetic Algorithm", s, score))
        
        if "annealing" in strategies:
            print("\n>>> Running Simulated Annealing...")
            s, score = self.optimize_simulated_annealing(initial_temp=50.0)
            results.append(("Simulated Annealing", s, score))
        
        # Return best
        print("\n" + "="*80)
        print("HYBRID RESULTS")
        print("="*80)
        for name, s, score in results:
            print(f"{name:30s}: {score:15.1f}")
        
        best = max(results, key=lambda x: x[2])
        return best[1], best[2]


# ============================================================================
# DEMONSTRATION & MAIN
# ============================================================================

def demonstrate_all_algorithms():
    """Run all algorithms on a test case"""
    
    # Setup (same as before)
    from f1_race_strategy import CarSpec, Segment, SegmentType, TyreProperties, RaceConfig, TyreSet, Weather
    
    car = CarSpec(
        max_speed=90, accel=10, brake=20,
        limp_speed=20, crawl_speed=10,
        fuel_capacity=150, initial_fuel=150
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
    optimizer = AdvancedOptimizer(car, track, tyres_db, race_config, available_sets, weather_schedule)
    
    # Run hybrid (best of all)
    best_strategy, best_score = optimizer.optimize_hybrid(
        strategies=["grid_search", "local_search", "genetic"]
    )
    
    print(f"\n{'='*80}")
    print("FINAL BEST STRATEGY")
    print(f"{'='*80}")
    print(f"Score: {best_score:.1f}")
    print(json.dumps(best_strategy, indent=2))
    
    # Save
    with open('/mnt/user-data/outputs/best_race_strategy.json', 'w') as f:
        json.dump(best_strategy, f, indent=2)
    print(f"\nSaved to: /mnt/user-data/outputs/best_race_strategy.json")


if __name__ == "__main__":
    demonstrate_all_algorithms()

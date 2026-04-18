car = {
    "max_speed_m/s": 90,
    "accel_m/se2": 10,
    "brake_m/se2": 20,
    "limp_constant_m/s": 20,
    "crawl_constant_m/s": 10,
    "fuel_tank_capacity_l": 150.0,
    "initial_fuel_l": 150.0,
    "fuel_consumption_l/m": 0.0005,
}

race = {
    "name": "Entelect GP Level 0",
    "laps": 2,
    "base_pit_stop_time_s": 20.0,
    "pit_tyre_swap_time_s": 10.0,
    "pit_refuel_rate_l/s": 5.0,
    "corner_crash_penalty_s": 10.0,
    "pit_exit_speed_m/s": 20.0,
    "fuel_soft_cap_limit_l": 1400.0,
    "starting_weather_condition_id": 1,
    "time_reference": 7300.0,
}

track = {
    "name": "Neo Kyalami Example",
    "segments": [
        {"id": 1, "type": "straight", "length_m": 850},
        {"id": 2, "type": "corner", "radius_m": 60, "length_m": 120},
        {"id": 3, "type": "straight", "length_m": 850},
        {"id": 4, "type": "corner", "radius_m": 60, "length_m": 120},
        {"id": 5, "type": "corner", "radius_m": 45, "length_m": 90},
        {"id": 6, "type": "corner", "radius_m": 80, "length_m": 140},
        {"id": 7, "type": "straight", "length_m": 650},
        {"id": 8, "type": "corner", "radius_m": 80, "length_m": 140},
    ],
}

tyre_properties = {
    "Soft": {
        "life_span": 1,
        "dry_friction_multiplier": 1.18,
        "cold_friction_multiplier": 1.00,
        "light_rain_friction_multiplier": 0.92,
        "heavy_rain_friction_multiplier": 0.80,
        "dry_degradation": 0.14,
        "cold_degradation": 0.11,
        "light_rain_degradation": 0.12,
        "heavy_rain_degradation": 0.13,
    },
    "Medium": {
        "life_span": 1,
        "dry_friction_multiplier": 1.08,
        "cold_friction_multiplier": 0.97,
        "light_rain_friction_multiplier": 0.88,
        "heavy_rain_friction_multiplier": 0.74,
        "dry_degradation": 0.10,
        "cold_degradation": 0.08,
        "light_rain_degradation": 0.09,
        "heavy_rain_degradation": 0.10,
    },
    "Hard": {
        "life_span": 1,
        "dry_friction_multiplier": 0.98,
        "cold_friction_multiplier": 0.92,
        "light_rain_friction_multiplier": 0.82,
        "heavy_rain_friction_multiplier": 0.68,
        "dry_degradation": 0.07,
        "cold_degradation": 0.06,
        "light_rain_degradation": 0.07,
        "heavy_rain_degradation": 0.08,
    },
    "Intermediate": {
        "life_span": 1,
        "dry_friction_multiplier": 0.90,
        "cold_friction_multiplier": 0.96,
        "light_rain_friction_multiplier": 1.08,
        "heavy_rain_friction_multiplier": 1.02,
        "dry_degradation": 0.11,
        "cold_degradation": 0.09,
        "light_rain_degradation": 0.08,
        "heavy_rain_degradation": 0.09,
    },
    "Wet": {
        "life_span": 1,
        "dry_friction_multiplier": 0.72,
        "cold_friction_multiplier": 0.88,
        "light_rain_friction_multiplier": 1.02,
        "heavy_rain_friction_multiplier": 1.20,
        "dry_degradation": 0.16,
        "cold_degradation": 0.12,
        "light_rain_degradation": 0.09,
        "heavy_rain_degradation": 0.05,
    },
}

# Implementation: tyre_sets[1] = "Soft" then tyre_properties["Soft"] = Stats
tyre_sets = {
    1: "Soft",
    2: "Soft",
    3: "Soft",
    4: "Medium",
    5: "Medium",
    6: "Medium",
    7: "Hard",
    8: "Hard",
    9: "Hard",
    10: "Intermediate",
    11: "Intermediate",
    12: "Intermediate",
    13: "Wet",
    14: "Wet",
    15: "Wet",
}

weather_conditions = {
    1: {
        "condition": "cold",
        "duration_s": 1000.0,
        "acceleration_multiplier": 0.95,
        "deceleration_multiplier": 0.95,
    },
    2: {
        "condition": "light_rain",
        "duration_s": 3000.0,
        "acceleration_multiplier": 0.80,
        "deceleration_multiplier": 0.80,
    },
    # Find Dry and Heavy Rain data
}
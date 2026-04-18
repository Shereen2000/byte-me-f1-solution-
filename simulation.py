import math



def tyre_friction(base_friction_coefficient, total_degradation, weather_multiplier):

    return (base_friction_coefficient - total_corner_degradation) * weather_multiplier

def max_corner_speed(tyre_friction, gravity, corner_radius, crawl_constant):
    return math.sqrt(tyre_friction*gravity*corner_radius) + crawl_constant




def braking_degradation(initial_speed, final_speed, k_braking, tyre_degradation_rate):
    return (((initial_speed/100)**2) - ((final_speed/100)**2))**2 * k_braking * tyre_degradation_rate

def total_corner_degradation(k_corner, speed, corner_radius, tyre_degradation_rate):
    return k_corner * (speed**2/corner_radius) * tyre_degradation_rate


def fuel_usage(k_base, k_drag, initial_speed, final_speed, distance):
    return k_base + (k_drag * (((initial_speed + final_speed)/2)**2) * distance)



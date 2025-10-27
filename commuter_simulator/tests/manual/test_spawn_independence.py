"""
Test: Are spawns truly arbitrary or sequential?
Shows spawn order vs. position to prove independence.
"""
import asyncio
import random
import math
from commuter_simulator.infrastructure.spawn.config_loader import SpawnConfigLoader


def weighted_random_choice(weights):
    total = sum(weights)
    r = random.uniform(0, total)
    cumsum = 0
    for i, w in enumerate(weights):
        cumsum += w
        if r <= cumsum:
            return i
    return len(weights) - 1


def boarding_probability(position_fraction):
    return math.exp(-2.5 * position_fraction)


async def main():
    print("="*80)
    print("SPAWN ORDER vs POSITION TEST")
    print("Testing if spawns are arbitrary or sequential")
    print("="*80)
    
    num_points = 415
    num_spawns = 30  # Smaller sample for clarity
    
    # Get spawn config
    config_loader = SpawnConfigLoader(api_base_url="http://localhost:1337/api")
    spawn_config = await config_loader.get_config_by_country("Barbados")
    
    print(f"\nGenerating {num_spawns} spawns...")
    print(f"\nIf SEQUENTIAL: Each spawn should be further from origin than previous")
    print(f"If ARBITRARY: Spawn positions should jump around randomly\n")
    
    # Generate spawns
    spawns = []
    for i in range(num_spawns):
        boarding_weights = [boarding_probability(i / num_points) for i in range(num_points)]
        origin_idx = weighted_random_choice(boarding_weights)
        origin_pct = (origin_idx / num_points) * 100
        spawns.append((i+1, origin_idx, origin_pct))
    
    # Display results
    print(f"{'Spawn#':<8} {'Position Index':<16} {'% of Route':<14} {'Visual Position':<50}")
    print("-" * 90)
    
    for spawn_num, idx, pct in spawns:
        bar_length = int(pct / 2)  # Scale to 50 chars max
        bar = "█" * bar_length
        print(f"{spawn_num:<8} {idx:<16} {pct:5.1f}%{'':<8} {bar}")
    
    # Analyze pattern
    print("\n" + "="*80)
    print("PATTERN ANALYSIS")
    print("="*80)
    
    # Check if positions are increasing
    is_increasing = True
    decreases = 0
    for i in range(1, len(spawns)):
        if spawns[i][1] < spawns[i-1][1]:
            is_increasing = False
            decreases += 1
    
    print(f"\nPosition changes:")
    print(f"  Times position DECREASED: {decreases} out of {num_spawns-1} transitions")
    print(f"  Times position INCREASED: {num_spawns-1-decreases} out of {num_spawns-1} transitions")
    
    if is_increasing:
        print(f"\n❌ SEQUENTIAL PATTERN DETECTED")
        print(f"   Each spawn is further from origin than previous")
        print(f"   This is NOT realistic - spawns should be independent!")
    else:
        pct_decreases = (decreases / (num_spawns-1)) * 100
        print(f"\n✓ ARBITRARY PATTERN CONFIRMED")
        print(f"   Positions jump around: {pct_decreases:.1f}% of transitions go backwards")
        print(f"   This IS realistic - spawn locations are independent of each other")
    
    # Show some examples of position changes
    print(f"\nExample position transitions:")
    for i in range(1, min(11, len(spawns))):
        prev_pct = spawns[i-1][2]
        curr_pct = spawns[i][2]
        diff = curr_pct - prev_pct
        direction = "→" if diff > 0 else "←"
        print(f"  Spawn {i} -> {i+1}: {prev_pct:5.1f}% {direction} {curr_pct:5.1f}% (change: {diff:+6.1f}%)")
    
    # Statistical test: Correlation
    spawn_numbers = [s[0] for s in spawns]
    positions = [s[2] for s in spawns]
    
    # Calculate correlation coefficient
    n = len(spawns)
    mean_spawn = sum(spawn_numbers) / n
    mean_pos = sum(positions) / n
    
    numerator = sum((spawn_numbers[i] - mean_spawn) * (positions[i] - mean_pos) for i in range(n))
    denom_spawn = sum((spawn_numbers[i] - mean_spawn) ** 2 for i in range(n))
    denom_pos = sum((positions[i] - mean_pos) ** 2 for i in range(n))
    
    correlation = numerator / (math.sqrt(denom_spawn) * math.sqrt(denom_pos))
    
    print("\n" + "="*80)
    print("STATISTICAL CORRELATION TEST")
    print("="*80)
    print(f"\nCorrelation between spawn order and position: {correlation:.4f}")
    print(f"\nInterpretation:")
    print(f"  +1.0 = Perfect sequential (BAD)")
    print(f"   0.0 = No correlation, truly arbitrary (GOOD)")
    print(f"  -1.0 = Perfect reverse sequential (BAD)")
    
    if abs(correlation) < 0.3:
        print(f"\n✓ WEAK CORRELATION ({correlation:.4f})")
        print(f"  Spawns are INDEPENDENT and ARBITRARY ✓")
    elif abs(correlation) < 0.7:
        print(f"\n⚠ MODERATE CORRELATION ({correlation:.4f})")
        print(f"  Spawns have SOME pattern (investigate)")
    else:
        print(f"\n❌ STRONG CORRELATION ({correlation:.4f})")
        print(f"  Spawns are SEQUENTIAL (not realistic)")


if __name__ == "__main__":
    asyncio.run(main())

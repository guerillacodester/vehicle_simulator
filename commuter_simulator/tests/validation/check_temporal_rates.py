import asyncio
from commuter_simulator.infrastructure.spawn.config_loader import SpawnConfigLoader

async def check_hourly_rates():
    loader = SpawnConfigLoader(api_base_url='http://localhost:1337/api')
    config = await loader.get_config_by_country('Barbados')
    
    print('HOURLY SPAWN RATES FROM CONFIG')
    print('=' * 60)
    print('Hour | Spawn Rate | Expected Demand')
    print('-' * 60)
    
    for hour in range(5, 10):
        rate = loader.get_hourly_rate(config, hour)
        if rate < 0.5:
            demand = 'VERY LOW (pre-dawn/night)'
        elif rate < 1.0:
            demand = 'LOW (early morning)'
        elif rate < 2.0:
            demand = 'MODERATE (morning)'
        elif rate < 2.5:
            demand = 'HIGH (peak start)'
        else:
            demand = 'PEAK (rush hour)'
        
        print(f'{hour:>4} | {rate:>10.2f} | {demand}')
    
    print()
    print('SIMULATION ANALYSIS:')
    print('Simulation spawns passengers 6:00-7:00 AM')
    rate_6am = loader.get_hourly_rate(config, 6)
    rate_7am = loader.get_hourly_rate(config, 7)
    print(f'  Hour 6 rate: {rate_6am:.2f}')
    print(f'  Hour 7 rate: {rate_7am:.2f}')
    print(f'  Average: {(rate_6am + rate_7am)/2:.2f}')
    print()
    
    # Check what probability we're getting
    day_mult = loader.get_day_multiplier(config, 'sunday')
    building_weight = loader.get_building_weight(config, 'residential', apply_peak_multiplier=True)
    
    prob_6am = loader.calculate_spawn_probability(config, building_weight, 6, 'sunday')
    prob_7am = loader.calculate_spawn_probability(config, building_weight, 7, 'sunday')
    
    print(f'SPAWN PROBABILITIES (residential buildings on Sunday):')
    print(f'  6 AM: {prob_6am:.2f}')
    print(f'  7 AM: {prob_7am:.2f}')
    print()
    print(f'For rural area with 48 passengers in 1 hour:')
    print(f'  This suggests spawn rate might be too high for 6 AM!')
    print(f'  Expected: <20 passengers for pre-dawn rural area')

asyncio.run(check_hourly_rates())

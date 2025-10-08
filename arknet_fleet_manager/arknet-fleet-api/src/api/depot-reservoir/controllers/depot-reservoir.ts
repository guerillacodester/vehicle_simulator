/**
 * Depot Reservoir Controller - TypeScript
 * Integrates with the actual DepotReservoir Python system
 */

import { spawn } from 'child_process';
import * as path from 'path';

interface SpawnRequest {
  hour: number;
  time_window_minutes: number;
  depot_ids: string[];
}

interface CommuterData {
  commuter_id: string;
  depot_id: string;
  route_id: string;
  current_location: { lat: number; lon: number };
  destination: { lat: number; lon: number };
  direction: string;
  priority: number;
  max_walking_distance: number;
  spawn_time: string;
}

export default {
  async spawnBatch(ctx: any) {
    try {
      const { hour = 8, time_window_minutes = 5, depot_ids = [] }: SpawnRequest = ctx.request.body;

      console.log(`🏢 Spawning commuters from ${depot_ids.length} depots for hour ${hour}...`);

      // Execute the production depot reservoir Python script
      const pythonScript = path.join(__dirname, '..', '..', '..', '..', 'depot_reservoir_api.py');
      
      return new Promise<void>((resolve, reject) => {
        const python = spawn('python', ['-c', `
import sys
sys.path.append('${path.dirname(pythonScript).replace(/\\/g, '/')}')
import asyncio
from depot_reservoir_api import handle_batch_spawn_request

async def main():
    result = await handle_batch_spawn_request(${hour}, ${time_window_minutes}, ${JSON.stringify(depot_ids)})
    print('RESULT_START')
    import json
    print(json.dumps(result))
    print('RESULT_END')

asyncio.run(main())
        `], {
          cwd: path.dirname(pythonScript)
        });

        let output = '';
        let error = '';

        python.stdout.on('data', (data) => {
          output += data.toString();
        });

        python.stderr.on('data', (data) => {
          error += data.toString();
        });

        python.on('close', (code) => {
          if (code === 0) {
            try {
              const startIndex = output.indexOf('RESULT_START');
              const endIndex = output.indexOf('RESULT_END');
              
              if (startIndex !== -1 && endIndex !== -1) {
                const jsonStr = output.substring(startIndex + 12, endIndex).trim();
                const result = JSON.parse(jsonStr);
                
                console.log(`✅ Depot reservoir spawned ${result.spawned_commuters?.length || 0} commuters`);
                ctx.body = result;
                resolve();
              } else {
                throw new Error('Could not parse result from depot reservoir');
              }
            } catch (parseError) {
              console.error('❌ Error parsing depot reservoir result:', parseError);
              ctx.body = {
                success: false,
                error: 'Failed to parse depot reservoir result',
                spawned_commuters: []
              };
              resolve();
            }
          } else {
            console.error('❌ Depot reservoir failed:', error);
            ctx.body = {
              success: false,
              error: 'Depot reservoir failed',
              spawned_commuters: []
            };
            resolve();
          }
        });

        setTimeout(() => {
          python.kill();
          ctx.body = {
            success: false,
            error: 'Depot reservoir timeout',
            spawned_commuters: []
          };
          resolve();
        }, 30000);
      });

    } catch (error) {
      console.error('❌ Depot reservoir API error:', error);
      ctx.body = {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        spawned_commuters: []
      };
    }
  },

  async getStatus(ctx: any) {
    try {
      const { depotId } = ctx.params;
      
      // This would call the depot reservoir status endpoint
      ctx.body = {
        depot_id: depotId,
        queue_length: 0,
        total_spawned: 0,
        total_picked_up: 0,
        message: 'Status endpoint not yet implemented'
      };
    } catch (error) {
      ctx.body = {
        success: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  },
};
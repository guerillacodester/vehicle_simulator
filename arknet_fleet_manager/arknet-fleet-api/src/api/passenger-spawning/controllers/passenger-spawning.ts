/**
 * Passenger Spawning Controller - TypeScript
 * Integrates with the PoissonGeoJSONSpawner system
 */

import { spawn } from 'child_process';
import * as path from 'path';

interface SpawnRequest {
  hour: number;
  time_window_minutes: number;
  country_code: string;
}

export default {
  async generate(ctx: any) {
    try {
      const { hour = 8, time_window_minutes = 5, country_code = 'barbados' }: SpawnRequest = ctx.request.body;

      console.log(`🚀 Generating spawn requests for hour ${hour}...`);

      // Execute database-direct spawning (maintains single source of truth without circular dependency)
      const pythonScript = path.resolve(process.cwd(), 'database_spawning_api.py');
      
      return new Promise<void>((resolve, reject) => {
        const python = spawn('python', [pythonScript, hour.toString(), time_window_minutes.toString()], {
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
              // Extract JSON result from output
              const startIndex = output.indexOf('RESULT_START');
              const endIndex = output.indexOf('RESULT_END');
              
              if (startIndex !== -1 && endIndex !== -1) {
                const jsonStr = output.substring(startIndex + 12, endIndex).trim();
                const result = JSON.parse(jsonStr);
                
                console.log(`✅ Generated ${result.spawn_requests?.length || 0} spawn requests`);
                ctx.body = result;
                resolve();
              } else {
                throw new Error('Could not parse result from Python script');
              }
            } catch (parseError) {
              console.error('❌ Error parsing Python result:', parseError);
              console.error('Python output:', output);
              ctx.body = {
                success: false,
                error: 'Failed to parse spawning result',
                spawn_requests: []
              };
              resolve();
            }
          } else {
            console.error('❌ Python script failed:', error);
            ctx.body = {
              success: false,
              error: 'Python spawning script failed',
              spawn_requests: []
            };
            resolve();
          }
        });

        // Set timeout
        setTimeout(() => {
          python.kill();
          ctx.body = {
            success: false,
            error: 'Spawning request timed out',
            spawn_requests: []
          };
          resolve();
        }, 30000); // 30 second timeout
      });

    } catch (error) {
      console.error('❌ Spawning API error:', error);
      ctx.body = {
        success: false,
        error: error instanceof Error ? error.message : String(error),
        spawn_requests: []
      };
    }
  },
};
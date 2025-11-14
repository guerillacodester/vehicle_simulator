"use strict";
/**
 * Depot Reservoir Controller - TypeScript
 * Integrates with the actual DepotReservoir Python system
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
exports.default = {
    async spawnBatch(ctx) {
        try {
            const { hour = 8, time_window_minutes = 5, depot_ids = [] } = ctx.request.body;
            console.log(`🏢 Spawning commuters from ${depot_ids.length} depots for hour ${hour}...`);
            // Execute the production depot reservoir Python script  
            const pythonScript = path.join(__dirname, '..', '..', '..', '..', 'depot_reservoir_api.py');
            return new Promise((resolve, reject) => {
                const python = (0, child_process_1.spawn)('python', ['-c', `
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
                    var _a;
                    if (code === 0) {
                        try {
                            const startIndex = output.indexOf('RESULT_START');
                            const endIndex = output.indexOf('RESULT_END');
                            if (startIndex !== -1 && endIndex !== -1) {
                                const jsonStr = output.substring(startIndex + 12, endIndex).trim();
                                const result = JSON.parse(jsonStr);
                                console.log(`✅ Depot reservoir spawned ${((_a = result.spawned_commuters) === null || _a === void 0 ? void 0 : _a.length) || 0} commuters`);
                                ctx.body = result;
                                resolve();
                            }
                            else {
                                throw new Error('Could not parse result from depot reservoir');
                            }
                        }
                        catch (parseError) {
                            console.error('❌ Error parsing depot reservoir result:', parseError);
                            ctx.body = {
                                success: false,
                                error: 'Failed to parse depot reservoir result',
                                spawned_commuters: []
                            };
                            resolve();
                        }
                    }
                    else {
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
        }
        catch (error) {
            console.error('❌ Depot reservoir API error:', error);
            ctx.body = {
                success: false,
                error: error instanceof Error ? error.message : String(error),
                spawned_commuters: []
            };
        }
    },
    async getStatus(ctx) {
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
        }
        catch (error) {
            ctx.body = {
                success: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    },
};
//# sourceMappingURL=depot-reservoir.js.map
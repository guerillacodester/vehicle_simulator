"use strict";
/**
 * Passenger Spawning Controller - TypeScript
 * Integrates with the PoissonGeoJSONSpawner system
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
    async generate(ctx) {
        try {
            const { hour = 8, time_window_minutes = 5, country_code = 'barbados' } = ctx.request.body;
            console.log(`🚀 Generating spawn requests for hour ${hour}...`);
            // Execute database-direct spawning (maintains single source of truth without circular dependency)
            const pythonScript = path.resolve(process.cwd(), 'database_spawning_api.py');
            return new Promise((resolve, reject) => {
                const python = (0, child_process_1.spawn)('python', [pythonScript, hour.toString(), time_window_minutes.toString()], {
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
                            // Extract JSON result from output
                            const startIndex = output.indexOf('RESULT_START');
                            const endIndex = output.indexOf('RESULT_END');
                            if (startIndex !== -1 && endIndex !== -1) {
                                const jsonStr = output.substring(startIndex + 12, endIndex).trim();
                                const result = JSON.parse(jsonStr);
                                console.log(`✅ Generated ${((_a = result.spawn_requests) === null || _a === void 0 ? void 0 : _a.length) || 0} spawn requests`);
                                ctx.body = result;
                                resolve();
                            }
                            else {
                                throw new Error('Could not parse result from Python script');
                            }
                        }
                        catch (parseError) {
                            console.error('❌ Error parsing Python result:', parseError);
                            console.error('Python output:', output);
                            ctx.body = {
                                success: false,
                                error: 'Failed to parse spawning result',
                                spawn_requests: []
                            };
                            resolve();
                        }
                    }
                    else {
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
        }
        catch (error) {
            console.error('❌ Spawning API error:', error);
            ctx.body = {
                success: false,
                error: error instanceof Error ? error.message : String(error),
                spawn_requests: []
            };
        }
    },
};
//# sourceMappingURL=passenger-spawning.js.map
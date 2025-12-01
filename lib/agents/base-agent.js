System.register(["zod"], function (exports_1, context_1) {
    "use strict";
    var zod_1, AgentInputSchema, AgentOutputSchema, BaseAgent;
    var __moduleName = context_1 && context_1.id;
    return {
        setters: [
            function (zod_1_1) {
                zod_1 = zod_1_1;
            }
        ],
        execute: function () {
            /**
             * Base Agent Schema
             * All agents must conform to this structure for interoperability
             */
            exports_1("AgentInputSchema", AgentInputSchema = zod_1.z.object({
                framework: zod_1.z.string(),
                context: zod_1.z.object({
                    birthData: zod_1.z
                        .object({
                        date: zod_1.z.string(),
                        time: zod_1.z.string(),
                        location: zod_1.z.object({
                            latitude: zod_1.z.number(),
                            longitude: zod_1.z.number(),
                        }),
                    })
                        .optional(),
                    healthMetrics: zod_1.z.record(zod_1.z.string(), zod_1.z.any()).optional(),
                    journalThemes: zod_1.z.array(zod_1.z.string()).optional(),
                    userQuery: zod_1.z.string().optional(),
                }),
            }));
            exports_1("AgentOutputSchema", AgentOutputSchema = zod_1.z.object({
                calculation: zod_1.z.any().optional(),
                correlations: zod_1.z.array(zod_1.z.string()).optional(),
                interpretationSeed: zod_1.z.string(),
                visualizationData: zod_1.z.any().optional(),
                method: zod_1.z.string(),
                confidence: zod_1.z.number().min(0).max(1).optional(),
            }));
            /**
             * Base Agent Class
             * All agents extend this for consistent interface
             */
            BaseAgent = class BaseAgent {
                /**
                 * Validate input against schema
                 */
                validateInput(input) {
                    return AgentInputSchema.parse(input);
                }
                /**
                 * Validate output against schema
                 */
                validateOutput(output) {
                    return AgentOutputSchema.parse(output);
                }
            };
            exports_1("BaseAgent", BaseAgent);
        }
    };
});

import { z } from 'zod';

/**
 * Base Agent Schema
 * All agents must conform to this structure for interoperability
 */
export const AgentInputSchema = z.object({
  framework: z.string(),
  context: z.object({
    birthData: z
      .object({
        date: z.string(),
        time: z.string(),
        location: z.object({
          latitude: z.number(),
          longitude: z.number(),
        }),
      })
      .optional(),
    healthMetrics: z.record(z.string(), z.any()).optional(),
    journalThemes: z.array(z.string()).optional(),
    userQuery: z.string().optional(),
  }),
});

export const AgentOutputSchema = z.object({
  calculation: z.any().optional(),
  correlations: z.array(z.string()).optional(),
  interpretationSeed: z.string(),
  visualizationData: z.any().optional(),
  method: z.string(),
  confidence: z.number().min(0).max(1).optional(),
});

export type AgentInput = z.infer<typeof AgentInputSchema>;
export type AgentOutput = z.infer<typeof AgentOutputSchema>;

/**
 * Base Agent Class
 * All agents extend this for consistent interface
 */
export abstract class BaseAgent {
  abstract name: string;
  abstract description: string;
  abstract frameworks: string[];

  /**
   * Validate input against schema
   */
  protected validateInput(input: unknown): AgentInput {
    return AgentInputSchema.parse(input);
  }

  /**
   * Validate output against schema
   */
  protected validateOutput(output: unknown): AgentOutput {
    return AgentOutputSchema.parse(output);
  }

  /**
   * Main execution method - must be implemented by each agent
   */
  abstract execute(input: AgentInput): Promise<AgentOutput>;

  /**
   * Optional: Get prompt template for this agent
   */
  getPromptTemplate?(): string;
}

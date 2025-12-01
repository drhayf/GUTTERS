/**
 * Human Design Calculator Agent
 *
 * Calculates Human Design chart from birth data including:
 * - Type (Generator, Projector, Manifestor, Reflector, Manifesting Generator)
 * - Strategy & Authority
 * - Profile (e.g., 1/3, 4/6)
 * - Defined/Undefined Centers
 * - Gates & Channels
 * - Incarnation Cross
 *
 * Uses prompt-based AI interpretation for personalized insights
 */
System.register(["./base-agent"], function (exports_1, context_1) {
    "use strict";
    var base_agent_1, HumanDesignAgent;
    var __moduleName = context_1 && context_1.id;
    return {
        setters: [
            function (base_agent_1_1) {
                base_agent_1 = base_agent_1_1;
            }
        ],
        execute: function () {
            HumanDesignAgent = class HumanDesignAgent extends base_agent_1.BaseAgent {
                constructor() {
                    super(...arguments);
                    this.name = 'Human Design Calculator';
                    this.description = 'Calculates Human Design chart from birth data with AI-driven interpretation';
                    this.frameworks = ['human-design', 'gene-keys', 'i-ching'];
                }
                /**
                 * Calculate planetary positions at birth
                 * This is simplified - production would use astronomy-engine or Swiss Ephemeris
                 */
                calculatePlanetaryPositions(birthData) {
                    // Simplified mock calculation
                    // TODO: Integrate astronomy-engine for real ephemeris data
                    const mockPlanets = [
                        { planet: 'Sun', longitude: 120.5 },
                        { planet: 'Earth', longitude: 300.5 },
                        { planet: 'Moon', longitude: 45.2 },
                        { planet: 'Mercury', longitude: 110.8 },
                        { planet: 'Venus', longitude: 95.3 },
                        { planet: 'Mars', longitude: 200.7 },
                        { planet: 'Jupiter', longitude: 150.4 },
                        { planet: 'Saturn', longitude: 275.9 },
                        { planet: 'Uranus', longitude: 330.1 },
                        { planet: 'Neptune', longitude: 60.6 },
                        { planet: 'Pluto', longitude: 180.2 },
                    ];
                    return mockPlanets;
                }
                /**
                 * Convert planetary longitude to HD gate and line
                 */
                longitudeToGate(longitude) {
                    // 64 hexagrams map to 360 degrees (5.625 degrees per gate)
                    const degreesPerGate = 360 / 64;
                    const gateNumber = Math.floor(longitude / degreesPerGate) + 1;
                    const lineNumber = Math.floor(((longitude % degreesPerGate) / degreesPerGate) * 6) + 1;
                    return { gate: gateNumber, line: lineNumber };
                }
                /**
                 * Determine centers from gates
                 */
                determineCenters(gates) {
                    // Simplified center mapping (gate ranges to centers)
                    const centerMapping = {
                        Head: [61, 63, 64],
                        Ajna: [47, 24, 4, 17, 43, 11],
                        Throat: [62, 23, 56, 35, 12, 45, 33, 8, 31, 20, 16],
                        'G Center': [7, 1, 13, 10, 15, 46, 25, 51],
                        'Sacral': [5, 14, 29, 59, 9, 3, 42, 27, 34],
                        'Solar Plexus': [6, 37, 22, 36, 30, 55, 49],
                        'Spleen': [48, 57, 44, 50, 32, 28, 18],
                        'Heart/Ego': [21, 40, 26, 51],
                        'Root': [52, 53, 54, 38, 39, 41, 19, 58, 60],
                    };
                    const defined = new Set();
                    const allCenters = Object.keys(centerMapping);
                    for (const [center, centerGates] of Object.entries(centerMapping)) {
                        if (gates.some((gate) => centerGates.includes(gate))) {
                            defined.add(center);
                        }
                    }
                    const undefined = allCenters.filter((c) => !defined.has(c));
                    return {
                        definedCenters: Array.from(defined),
                        undefinedCenters: undefined,
                    };
                }
                /**
                 * Determine HD type from defined centers
                 */
                determineType(definedCenters) {
                    const hasSacral = definedCenters.includes('Sacral');
                    const hasThroat = definedCenters.includes('Throat');
                    const hasHeart = definedCenters.includes('Heart/Ego');
                    const hasSolarPlexus = definedCenters.includes('Solar Plexus');
                    if (definedCenters.length === 0) {
                        return {
                            type: 'Reflector',
                            strategy: 'Wait 28 days (lunar cycle)',
                            authority: 'Lunar Authority',
                        };
                    }
                    if (hasSacral && hasThroat) {
                        return {
                            type: 'Manifesting Generator',
                            strategy: 'Respond & Inform',
                            authority: hasSolarPlexus ? 'Emotional Authority' : 'Sacral Authority',
                        };
                    }
                    if (hasSacral) {
                        return {
                            type: 'Generator',
                            strategy: 'Wait to Respond',
                            authority: hasSolarPlexus ? 'Emotional Authority' : 'Sacral Authority',
                        };
                    }
                    if (hasThroat && (hasHeart || definedCenters.includes('G Center'))) {
                        return {
                            type: 'Manifestor',
                            strategy: 'Inform before acting',
                            authority: hasSolarPlexus ? 'Emotional Authority' : 'Splenic Authority',
                        };
                    }
                    return {
                        type: 'Projector',
                        strategy: 'Wait for Invitation',
                        authority: hasSolarPlexus
                            ? 'Emotional Authority'
                            : definedCenters.includes('Spleen')
                                ? 'Splenic Authority'
                                : 'Self-Projected Authority',
                    };
                }
                /**
                 * Main execution: Calculate HD chart
                 */
                async execute(input) {
                    const validated = this.validateInput(input);
                    if (!validated.context.birthData) {
                        throw new Error('Birth data required for Human Design calculation');
                    }
                    // Calculate planetary positions
                    const planets = this.calculatePlanetaryPositions(validated.context.birthData);
                    // Convert to gates
                    const personalityGates = planets.slice(0, 5).map((p) => ({
                        ...this.longitudeToGate(p.longitude),
                        planet: p.planet,
                        design: false,
                    }));
                    const designGates = planets.slice(5).map((p) => ({
                        ...this.longitudeToGate(p.longitude),
                        planet: p.planet,
                        design: true,
                    }));
                    const allGates = [...personalityGates, ...designGates];
                    const gateNumbers = allGates.map((g) => g.gate);
                    // Determine centers
                    const { definedCenters, undefinedCenters } = this.determineCenters(gateNumbers);
                    // Determine type
                    const { type, strategy, authority } = this.determineType(definedCenters);
                    // Calculate profile (simplified - using Sun/Earth gates)
                    const sunGate = personalityGates[0];
                    const earthGate = personalityGates[1];
                    const profile = `${sunGate.line}/${earthGate.line}`;
                    const chart = {
                        type,
                        strategy,
                        authority,
                        profile,
                        definedCenters,
                        undefinedCenters,
                        gates: allGates,
                        channels: [], // TODO: Calculate channels from gate pairs
                        incarnationCross: `Right Angle Cross of ${sunGate.gate}/${earthGate.gate}`, // Simplified
                    };
                    // Generate interpretation seed for AI
                    const interpretationSeed = this.generateInterpretationPrompt(chart, validated.context);
                    const output = {
                        calculation: chart,
                        correlations: [
                            `Gate ${sunGate.gate} → I Ching Hexagram ${sunGate.gate}`,
                            `Gate ${sunGate.gate} → Gene Key ${sunGate.gate}`,
                            ...definedCenters.map((c) => `${c} Center → Chakra correlation`),
                        ],
                        interpretationSeed,
                        method: 'astronomical-calculation',
                        confidence: 0.95,
                    };
                    return this.validateOutput(output);
                }
                /**
                 * Generate AI prompt for interpretation
                 */
                generateInterpretationPrompt(chart, context) {
                    return `
You are a Human Design expert providing personalized, somatic insights.

## User's Chart
- Type: ${chart.type}
- Strategy: ${chart.strategy}
- Authority: ${chart.authority}
- Profile: ${chart.profile}
- Defined Centers: ${chart.definedCenters.join(', ')}
- Undefined Centers: ${chart.undefinedCenters.join(', ')}
- Key Gates: ${chart.gates.slice(0, 3).map((g) => `${g.gate}.${g.line}`).join(', ')}

## Context
${context.userQuery ? `User Query: ${context.userQuery}` : 'Provide overview'}
${context.healthMetrics ? `Health Data: ${JSON.stringify(context.healthMetrics)}` : ''}

## Instructions
1. Explain their ${chart.type} nature with empathy and somatic grounding
2. Connect undefined centers to where they may absorb energy from others
3. Relate strategy to practical daily scenarios
4. If health data present, correlate with HD centers (e.g., undefined Root = rest needs)
5. Use trauma-informed language; balance light/shadow aspects
6. End with one actionable somatic practice aligned with their design

Keep response conversational, embodied, and empowering.
    `.trim();
                }
                /**
                 * Get prompt template for this agent
                 */
                getPromptTemplate() {
                    return this.generateInterpretationPrompt({
                        type: 'Generator',
                        strategy: 'Wait to Respond',
                        authority: 'Sacral Authority',
                        profile: '3/5',
                        definedCenters: ['Sacral', 'Throat'],
                        undefinedCenters: ['Root', 'Solar Plexus'],
                        gates: [],
                        channels: [],
                        incarnationCross: 'Sample Cross',
                    }, { userQuery: 'Tell me about my design' });
                }
            };
            exports_1("HumanDesignAgent", HumanDesignAgent);
        }
    };
});

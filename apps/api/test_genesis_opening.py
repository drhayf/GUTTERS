"""Test script for Genesis opening message."""
import asyncio
from src.agents.genesis_profiler import GenesisProfilerAgent
from src.core.schemas import AgentInput, AgentContext

async def test_opening():
    agent = GenesisProfilerAgent()
    
    input_data = AgentInput(
        framework='genesis',
        context=AgentContext(userQuery='Begin the Genesis profiling process')
    )
    
    result = await agent.execute(input_data)
    
    print('✅ Opening generated:')
    print(f'Message length: {len(result.interpretationSeed)}')
    print(f'Message: {result.interpretationSeed[:200]}...')
    print(f'Components: {len(result.visualizationData.get("components", []))} components')
    print('\nComponent types:')
    for i, comp in enumerate(result.visualizationData.get("components", [])):
        print(f'  {i+1}. {comp.get("type")}')

if __name__ == "__main__":
    asyncio.run(test_opening())

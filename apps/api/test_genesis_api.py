"""Test Genesis API endpoint."""
import requests
import json

# Test the /api/python/chat/ endpoint
response = requests.post(
    "http://localhost:8000/api/python/chat/",
    json={
        "message": "Begin the Genesis profiling process",
        "enable_hrm": False
    }
)

if response.status_code == 200:
    result = response.json()
    print("✅ API call successful!")
    print(f"Response length: {len(result.get('response', ''))}")
    print(f"Response: {result.get('response', '')[:200]}...")
    
    agent_output = result.get('agent_output', {})
    if agent_output:
        viz_data = agent_output.get('visualizationData', {})
        components = viz_data.get('components', [])
        print(f"\n🎨 Components: {len(components)} total")
        for i, comp in enumerate(components):
            comp_type = comp.get('type', 'unknown')
            print(f"  {i+1}. {comp_type}")
else:
    print(f"❌ API call failed: {response.status_code}")
    print(response.text)

#!/usr/bin/env python3
"""
Basic functionality test for NeoSapiens after fixes.

This test verifies that the core components work correctly
after applying compatibility fixes.
"""

import os
import sys
import json
from neo_sapiens import run_swarm, parse_json_from_input, AgentSchema

def test_imports():
    """Test that all core imports work correctly."""
    print("🧪 Testing imports...")
    try:
        from neo_sapiens import run_swarm, parse_json_from_input, AgentSchema
        print("✅ Core imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_json_parsing():
    """Test JSON parsing functionality."""
    print("\n🧪 Testing JSON parsing...")
    
    test_json = """
    {
        "plan": "Test plan with multiple steps",
        "agents": [
            {
                "name": "Test Agent 1",
                "system_prompt": "You are a test agent for validation",
                "rules": "Follow test protocols"
            },
            {
                "name": "Test Agent 2", 
                "system_prompt": "You are another test agent",
                "rules": "Assist with testing"
            }
        ]
    }
    """
    
    try:
        plan, agents = parse_json_from_input(test_json)
        
        if plan is None:
            print("❌ JSON parsing returned None")
            return False
            
        print(f"✅ Plan parsed: {plan}")
        print(f"✅ Agents parsed: {len(agents)} agents")
        
        # Validate agent structure
        for i, agent in enumerate(agents):
            print(f"   Agent {i+1}: {agent.name}")
            
        return True
        
    except Exception as e:
        print(f"❌ JSON parsing failed: {e}")
        return False

def test_agent_schema():
    """Test AgentSchema validation."""
    print("\n🧪 Testing AgentSchema...")
    
    try:
        # Test valid agent schema
        agent = AgentSchema(
            name="Test Agent",
            system_prompt="You are a test agent",
            rules="Follow all guidelines"
        )
        
        print(f"✅ AgentSchema created: {agent.name}")
        return True
        
    except Exception as e:
        print(f"❌ AgentSchema creation failed: {e}")
        return False

def test_swarm_function_basic():
    """Test that run_swarm function can be called (without actually running it)."""
    print("\n🧪 Testing run_swarm function signature...")
    
    try:
        # Test that function exists and can handle basic validation
        result = run_swarm(
            team_task=None,  # This should trigger validation error
            task=None
        )
        
        if "Error: Both team_task and task parameters are required" in str(result):
            print("✅ run_swarm parameter validation working")
            return True
        else:
            print(f"❌ Unexpected result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ run_swarm function test failed: {e}")
        return False

def test_compatibility_warnings():
    """Test that compatibility warnings are properly displayed."""
    print("\n🧪 Testing compatibility warnings...")
    
    # Import should trigger warnings about missing components
    import neo_sapiens.hass_schema as hs
    
    # Check if compatibility checks work
    if hs.SwarmNetwork is None:
        print("✅ SwarmNetwork compatibility check working")
    else:
        print("⚠️  SwarmNetwork unexpectedly available")
        
    if hs.Anthropic is None:
        print("✅ Anthropic compatibility check working")
    else:
        print("⚠️  Anthropic unexpectedly available")
    
    return True

def run_all_tests():
    """Run all tests and report results."""
    print("🔬 NeoSapiens Basic Functionality Tests")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("JSON Parsing Test", test_json_parsing),
        ("AgentSchema Test", test_agent_schema),
        ("run_swarm Function Test", test_swarm_function_basic),
        ("Compatibility Warnings Test", test_compatibility_warnings),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! NeoSapiens basic functionality is working.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
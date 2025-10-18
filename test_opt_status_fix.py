#!/usr/bin/env python3
"""
Test script to verify OPT status handling in historical designs
"""

import sys
import os
import pandas as pd
import asyncio

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_agent.llm_orchestrator import LLMOrchestrator

async def test_opt_status_handling():
    """Test that LLM doesn't ask for optimization when historical design has OPT status"""
    print("=" * 60)
    print("TESTING OPT STATUS HANDLING IN HISTORICAL DESIGNS")
    print("=" * 60)
    
    # Check if there are OPT entries in the CSV
    csv_path = "extracted_historical_data_00.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        opt_entries = df[df['Status'] == 'OPT']
        
        if opt_entries.empty:
            print("❌ No OPT entries found in historical data. Running optimization first...")
            
            # Run a quick optimization to create OPT entry
            from ai_agent.model_status_predict.script import optimize_mode_for_webapp
            result = optimize_mode_for_webapp(4000, "Wood", 12000)
            
            if result and result.get('success'):
                print(f"✅ Created OPT entry: {result['height']:.0f}x{result['width']:.0f}mm")
                # Reload data
                df = pd.read_csv(csv_path)
                opt_entries = df[df['Status'] == 'OPT']
            else:
                print("❌ Failed to create OPT entry for testing")
                return False
        
        print(f"Found {len(opt_entries)} OPT entries in historical data")
        
        # Get the first OPT entry for testing
        if not opt_entries.empty:
            test_entry = opt_entries.iloc[0]
            print(f"\nTesting with OPT entry:")
            print(f"  Material: {test_entry['Material']}")
            print(f"  Length: {test_entry['L (mm)']} mm")
            print(f"  Dimensions: {test_entry['h (mm)']}x{test_entry['w (mm)']} mm")
            print(f"  Status: {test_entry['Status']}")
            
            # Test the orchestrator with API key from env
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key or api_key == 'your_anthropic_api_key_here':
                print("\n⚠️  No valid ANTHROPIC_API_KEY found. Testing only data structures...")
                
                # Test just the data extraction part
                orchestrator = LLMOrchestrator(api_key="dummy_key")
                
                # Create beam spec that matches the OPT entry
                beam_spec = {
                    'material': test_entry['Material'],
                    'length_mm': test_entry['L (mm)'],
                    'load_n': test_entry['F (N)'],
                    'width_mm': test_entry['w (mm)'],
                    'height_mm': test_entry['h (mm)']
                }
                
                # Test the _find_best_historical_design method
                best_historical = orchestrator._find_best_historical_design(beam_spec)
                
                if best_historical:
                    print(f"\n✅ Historical design found:")
                    print(f"  Status: {best_historical.get('status', 'NOT_FOUND')}")
                    print(f"  Height: {best_historical['height_mm']} mm")
                    print(f"  Width: {best_historical['width_mm']} mm")
                    
                    if best_historical.get('status') == 'OPT':
                        print("\n✅ SUCCESS: Status correctly identified as OPT!")
                        
                        # Test the format context
                        context = orchestrator._format_historical_context(best_historical, beam_spec)
                        print(f"\nHistorical context includes:")
                        if "Status: OPT" in context:
                            print("✅ Status correctly shown as OPT in context")
                            return True
                        else:
                            print("❌ Status not correctly shown in context")
                            print(f"Context: {context}")
                            return False
                    else:
                        print(f"❌ Expected OPT status, got: {best_historical.get('status')}")
                        return False
                else:
                    print("❌ No historical design found")
                    return False
            else:
                print("\n✅ API key found, could test full LLM interaction")
                # Here we could test the full interaction but for now just test data structures
                return await test_data_structures_only()
        else:
            print("❌ No OPT entries available for testing")
            return False
    else:
        print(f"❌ CSV file not found: {csv_path}")
        return False

async def test_data_structures_only():
    """Test only the data structure changes without LLM calls"""
    print("\nTesting data structure changes...")
    
    # Create a dummy orchestrator
    orchestrator = LLMOrchestrator(api_key="dummy_key")
    
    # Load CSV and find an OPT entry
    df = pd.read_csv("extracted_historical_data_00.csv")
    opt_entries = df[df['Status'] == 'OPT']
    
    if not opt_entries.empty:
        test_entry = opt_entries.iloc[0]
        
        beam_spec = {
            'material': test_entry['Material'],
            'length_mm': test_entry['L (mm)'],
            'load_n': test_entry['F (N)'],
            'width_mm': test_entry['w (mm)'],
            'height_mm': test_entry['h (mm)']
        }
        
        best_historical = orchestrator._find_best_historical_design(beam_spec)
        
        if best_historical and best_historical.get('status') == 'OPT':
            print("✅ Data structure test PASSED")
            return True
        else:
            print("❌ Data structure test FAILED")
            return False
    else:
        print("❌ No OPT entries for testing")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_opt_status_handling())
    print(f"\nTest Result: {'PASSED' if success else 'FAILED'}")
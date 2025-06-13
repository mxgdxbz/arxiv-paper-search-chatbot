#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from research_server import search_primary_analysis

def test_search_primary_analysis():
    """Test the search_primary_analysis tool with sample parameters."""
    
    print("Testing search_primary_analysis tool with enhanced matching...")
    print("=" * 60)
    
    # Test cases - now including the correct indication (melanoma)
    test_cases = [
        ("Phase III", "Oncology", "Melanoma"),        # Should match - correct indication
        ("Phase III", "Oncology", "Breast Cancer"),   # Should NOT match - wrong indication
        ("Phase III", "Dermatology", "Melanoma"),     # Should match - dermatology includes melanoma
        ("Phase II", "Oncology", "Melanoma"),         # Should NOT match - wrong phase
    ]
    
    for i, (phase, therapeutic, indication) in enumerate(test_cases, 1):
        print(f"\n{'='*15} TEST CASE {i} {'='*15}")
        print(f"Searching for:")
        print(f"  Phase: {phase}")
        print(f"  Therapeutic: {therapeutic}")
        print(f"  Indication: {indication}")
        print()
        
        # Call the tool
        result = search_primary_analysis(phase, therapeutic, indication)
        
        print("Result:")
        print("-" * 40)
        if result.startswith("{"):
            print("✅ MATCH FOUND!")
            # Parse and show key fields
            import json
            try:
                data = json.loads(result)
                print(f"  Title: {data.get('title', 'N/A')}")
                print(f"  Detected Indication: {data.get('detected_indication', 'N/A')}")
                print(f"  Search Indication: {data.get('search_indication', 'N/A')}")
                print(f"  Primary Endpoint: {data.get('primary_analysis_endpoint', 'N/A')}")
                print(f"  Sample Size: {data.get('sample_size', 'N/A')}")
            except:
                print("  (Could not parse JSON)")
        else:
            print("❌ NO MATCH:")
            print(f"  {result}")
        print("-" * 40)

if __name__ == "__main__":
    test_search_primary_analysis() 
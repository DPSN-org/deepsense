#!/usr/bin/env python3
"""
Test script for Helius tools
Calls the solana_blockchain_data tool with specified arguments and stores response in JSON
"""

import json
import os
from datetime import datetime
from tools.helius_tools import HeliusTool

def test_helius_transactions():
    """
    Test the Helius tool with transactions action
    """
    # Test arguments
    test_args = {
        'name': 'solana_blockchain_data',
        'args': {
            'action': 'transactions',
            'address': '8EtW9c4EmGvJ7P3CkKKH9i9aCj8wdqAmcBe2gXAwEyzz',
            'limit': 100
        }
    }
    
    print("Testing Helius tool with arguments:")
    print(json.dumps(test_args, indent=2))
    print("\n" + "="*50 + "\n")
    
    try:
        # Create the Helius tool instance
        helius_tool = HeliusTool()
        
        # Call the tool with the specified arguments
        print("Calling Helius tool...")
        response = helius_tool._run(
            action=test_args['args']['action'],
            address=test_args['args']['address'],
            limit=test_args['args']['limit']
        )
        
        # Parse the response if it's a JSON string
        if isinstance(response, str):
            try:
                response_data = json.loads(response)
            except json.JSONDecodeError:
                response_data = {"raw_response": response}
        else:
            response_data = response
        
        # Create the final result structure
        result = response_data
        
        
        # Save to JSON file
        output_filename = f"helius_test_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Test completed successfully!")
        print(f"📁 Response saved to: {output_filename}")
        print(f"📊 Response size: {len(json.dumps(result, indent=2))} characters")
        
        # Print a summary of the response
        if isinstance(response_data, dict):
            if "data" in response_data:
                data = response_data["data"]
                if isinstance(data, list):
                    print(f"📈 Number of transactions returned: {len(data)}")
                elif isinstance(data, dict):
                    print(f"📈 Response contains: {list(data.keys())}")
            elif "error" in response_data:
                print(f"❌ Error in response: {response_data['error']}")
        
        return result
        
    except Exception as e:
        error_result = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "tool_name": test_args['name'],
                "test_args": test_args['args']
            },
            "error": str(e),
            "error_type": type(e).__name__
        }
        
        # Save error to JSON file
        error_filename = f"helius_test_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(error_filename, 'w', encoding='utf-8') as f:
            json.dump(error_result, f, indent=2, ensure_ascii=False)
        
        print(f"❌ Test failed with error: {e}")
        print(f"📁 Error details saved to: {error_filename}")
        
        return error_result

def test_helius_balance():
    """
    Test the Helius tool with balance action
    """
    # Test arguments for balance
    test_args = {
        'name': 'solana_blockchain_data',
        'args': {
            'action': 'balance',
            'address': '8EtW9c4EmGvJ7P3CkKKH9i9aCj8wdqAmcBe2gXAwEyzz'
        }
    }
    
    print("\n" + "="*50)
    print("Testing Helius tool with balance action:")
    print(json.dumps(test_args, indent=2))
    print("\n" + "="*50 + "\n")
    
    try:
        # Create the Helius tool instance
        helius_tool = HeliusTool()
        
        # Call the tool with the specified arguments
        print("Calling Helius tool for balance...")
        response = helius_tool._run(
            action=test_args['args']['action'],
            address=test_args['args']['address']
        )
        
        # Parse the response if it's a JSON string
        if isinstance(response, str):
            try:
                response_data = json.loads(response)
            except json.JSONDecodeError:
                response_data = {"raw_response": response}
        else:
            response_data = response
        
        # Create the final result structure
        result = response_data
        
        
        # Save to JSON file
        output_filename = f"helius_balance_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Balance test completed successfully!")
        print(f"📁 Response saved to: {output_filename}")
        
        return result
        
    except Exception as e:
        error_result = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "tool_name": test_args['name'],
                "test_args": test_args['args']
            },
            "error": str(e),
            "error_type": type(e).__name__
        }
        
        print(f"❌ Balance test failed with error: {e}")
        
        return error_result

if __name__ == "__main__":
    print("🚀 Starting Helius Tools Test")
    print("="*50)
    
    # Check if HELIUS_API_KEY is set
    if not os.getenv("HELIUS_API_KEY"):
        print("⚠️  Warning: HELIUS_API_KEY environment variable not set")
        print("   The tool may return an error or use fallback behavior")
        print()
    
    # Run the main test
    transactions_result = test_helius_transactions()
    
    # Run balance test as well
    balance_result = test_helius_balance()
    
    print("\n" + "="*50)
    print("🎉 All tests completed!")
    print("="*50) 
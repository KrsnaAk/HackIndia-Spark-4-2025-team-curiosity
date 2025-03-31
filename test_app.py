import requests
import json
import time

def test_categories_endpoint():
    """Test the categories endpoint to verify it returns category counts"""
    try:
        print("Testing categories endpoint...")
        response = requests.get("http://localhost:8000/api/knowledge_graph/categories")
        
        if response.status_code == 200:
            data = response.json()
            categories = data.get("categories", [])
            
            print(f"Success! Found {len(categories)} categories:")
            for category in categories:
                print(f"  - {category['name']}: {category['count']} items")
                if category.get('description'):
                    print(f"    Description: {category['description']}")
            
            return True
        else:
            print(f"Error: Received status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error testing categories endpoint: {str(e)}")
        return False

def test_chat_with_filter():
    """Test the chat endpoint with category filters"""
    try:
        print("\nTesting chat endpoint with category filters...")
        
        # Create a chat request with investment filter
        request_data = {
            "message": "Tell me about stocks",
            "filters": {
                "investment": True
            },
            "history": []
        }
        
        response = requests.post(
            "http://localhost:8000/api/chat",
            json=request_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print("Success! Received response:")
            print(f"  Response: {data['response']}")
            
            if data.get('knowledge_graph'):
                filters = data['knowledge_graph'].get('applied_filters', [])
                print(f"  Applied filters: {', '.join(filters)}")
            
            return True
        else:
            print(f"Error: Received status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error testing chat endpoint: {str(e)}")
        return False

if __name__ == "__main__":
    print("Running API tests...")
    
    # First, make sure the server is running
    server_ready = False
    max_retries = 3
    retry_count = 0
    
    while not server_ready and retry_count < max_retries:
        try:
            health_check = requests.get("http://localhost:8000/health")
            if health_check.status_code == 200:
                server_ready = True
                print("Server is running!")
            else:
                print(f"Server returned status code {health_check.status_code}")
                retry_count += 1
                time.sleep(2)
        except requests.exceptions.ConnectionError:
            print(f"Server not ready. Retrying in 2 seconds... (Attempt {retry_count+1}/{max_retries})")
            retry_count += 1
            time.sleep(2)
    
    if not server_ready:
        print("Error: Server is not running. Please start the server with 'python -m app.main' first.")
        exit(1)
    
    # Run the tests
    categories_test = test_categories_endpoint()
    chat_test = test_chat_with_filter()
    
    # Summarize results
    print("\nTest Results:")
    print(f"  Categories API: {'✅ PASSED' if categories_test else '❌ FAILED'}")
    print(f"  Chat with Filters: {'✅ PASSED' if chat_test else '❌ FAILED'}")
    
    if categories_test and chat_test:
        print("\n🎉 All tests passed! The category filtering feature is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the logs for details.") 
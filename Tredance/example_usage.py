"""
Example usage of the Workflow Graph Engine API.
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def example_code_review():
    """Example: Run the Code Review workflow."""
    print("=" * 60)
    print("Example: Code Review Workflow")
    print("=" * 60)
    
    code = """
def calculate_price(items, discount_rate):
    if discount_rate > 0:
        if discount_rate < 0.5:
            if discount_rate < 0.25:
                total = 0
                for item in items:
                    if item.price > 100:
                        total += item.price * (1 - discount_rate) * 1.1
                    else:
                        total += item.price * (1 - discount_rate)
                return total * 0.95
            else:
                return sum(item.price for item in items) * (1 - discount_rate)
        else:
            return sum(item.price for item in items) * 0.5
    return sum(item.price for item in items)
"""
    
    response = requests.post(
        f"{BASE_URL}/workflow/code-review/run",
        json={
            "code": code,
            "quality_threshold": 70,
            "max_loop_iterations": 3
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nRun ID: {result['run_id']}")
        print(f"Iterations: {result['iterations']}")
        print(f"\nFinal Quality Score: {result['final_state'].get('quality_score', 'N/A')}")
        print(f"\nIssues Found: {result['final_state'].get('issue_count', 0)}")
        print(f"Suggestions: {result['final_state'].get('suggestion_count', 0)}")
        
        print("\n--- Execution Log ---")
        for log_entry in result['execution_log']:
            print(f"[{log_entry['status']}] {log_entry['node_id']}: {log_entry['message']}")
        
        print("\n--- Final State ---")
        print(json.dumps(result['final_state'], indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def example_custom_graph():
    """Example: Create and run a custom graph."""
    print("\n" + "=" * 60)
    print("Example: Custom Graph")
    print("=" * 60)
    
    # Create a graph
    create_response = requests.post(
        f"{BASE_URL}/graph/create",
        json={
            "name": "Simple Pipeline",
            "nodes": [
                {"node_id": "start", "description": "Start node"},
                {"node_id": "process", "description": "Process node"},
                {"node_id": "end", "description": "End node"}
            ],
            "edges": [
                {"from_node": "start", "to_node": "process"},
                {"from_node": "process", "to_node": "end"}
            ],
            "entry_node": "start",
            "exit_nodes": ["end"]
        }
    )
    
    if create_response.status_code == 200:
        graph_data = create_response.json()
        graph_id = graph_data["graph_id"]
        print(f"Created graph: {graph_id}")
        
        # Run the graph
        run_response = requests.post(
            f"{BASE_URL}/graph/run",
            json={
                "graph_id": graph_id,
                "initial_state": {
                    "input_data": "test data",
                    "counter": 0
                }
            }
        )
        
        if run_response.status_code == 200:
            result = run_response.json()
            print(f"\nRun ID: {result['run_id']}")
            print(f"Final State: {json.dumps(result['final_state'], indent=2)}")
        else:
            print(f"Error running graph: {run_response.status_code}")
            print(run_response.text)
    else:
        print(f"Error creating graph: {create_response.status_code}")
        print(create_response.text)


def example_list_resources():
    """Example: List graphs and tools."""
    print("\n" + "=" * 60)
    print("Example: List Resources")
    print("=" * 60)
    
    # List graphs
    graphs_response = requests.get(f"{BASE_URL}/graph/list")
    if graphs_response.status_code == 200:
        graphs = graphs_response.json()
        print(f"\nAvailable Graphs: {len(graphs['graphs'])}")
        for graph in graphs['graphs']:
            print(f"  - {graph['name']} ({graph['graph_id']})")
    
    # List tools
    tools_response = requests.get(f"{BASE_URL}/tools")
    if tools_response.status_code == 200:
        tools = tools_response.json()
        print(f"\nAvailable Tools: {len(tools['tools'])}")
        for tool_name, description in tools['tools'].items():
            print(f"  - {tool_name}: {description}")


if __name__ == "__main__":
    print("\nWorkflow Graph Engine - Example Usage\n")
    print("Make sure the server is running: uvicorn app.main:app --reload\n")
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✓ Server is running\n")
            
            example_list_resources()
            example_code_review()
            example_custom_graph()
        else:
            print("✗ Server is not responding")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Please start the server first:")
        print("  uvicorn app.main:app --reload")


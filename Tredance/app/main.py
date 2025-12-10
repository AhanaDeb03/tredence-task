"""
FastAPI application - the friendly face of our workflow engine!

This is where all the HTTP endpoints live. Think of it as the reception desk
for our workflow system - it takes requests, routes them to the right place,
and sends back helpful responses.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime

from app.engine import Graph, WorkflowExecutor
from app.workflows import create_code_review_workflow

# Create the FastAPI app with friendly metadata
app = FastAPI(
    title="Workflow Graph Engine API",
    description=(
        "A friendly workflow engine that helps you build and run workflows! "
        "Think of it as a simplified LangGraph - create nodes, connect them, "
        "and watch your workflows come to life. Perfect for automating tasks, "
        "processing data, or running multi-step operations."
    ),
    version="1.0.0",
    contact={
        "name": "Workflow Engine Help",
        "email": "help@workflow-engine.example.com"
    }
)

# Enable CORS so your frontend can talk to this API
# (In production, you'd want to restrict this to specific domains)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Global Storage
# ============================================================================

# Where we keep all the workflow graphs people create
graphs_storage: Dict[str, Graph] = {}

# The executor that runs workflows (one instance handles all runs)
executor = WorkflowExecutor()


# ============================================================================
# Request/Response Models (Data Structures)
# ============================================================================

class NodeDefinition(BaseModel):
    """What a node looks like when you're creating a graph."""
    node_id: str  # Unique name for this node
    description: str = ""  # What this node does (for humans to read)


class EdgeDefinition(BaseModel):
    """What an edge (connection) looks like when you're creating a graph."""
    from_node: str  # Which node does this start from?
    to_node: str    # Which node does this lead to?


class CreateGraphRequest(BaseModel):
    """What you send us when you want to create a new workflow."""
    name: str = ""  # A friendly name for your workflow
    nodes: List[NodeDefinition]  # All the nodes in your workflow
    edges: List[EdgeDefinition]  # How the nodes connect together
    entry_node: Optional[str] = None  # Where to start (we'll pick the first node if you don't)
    exit_nodes: List[str] = []  # Where you can finish (optional)


class CreateGraphResponse(BaseModel):
    """What we send back when you create a graph."""
    graph_id: str  # The unique ID you'll use to run this workflow later
    message: str   # A friendly confirmation message


class RunGraphRequest(BaseModel):
    """What you send us when you want to run a workflow."""
    graph_id: str  # Which workflow do you want to run?
    initial_state: Dict[str, Any]  # Starting data for the workflow
    max_iterations: int = 1000  # Safety limit (prevents infinite loops)


class RunGraphResponse(BaseModel):
    """What we send back after running a workflow."""
    run_id: str  # Unique ID for this particular run
    final_state: Dict[str, Any]  # The final state after all nodes ran
    execution_log: List[Dict[str, Any]]  # Step-by-step log of what happened
    iterations: int  # How many iterations we did


class StateResponse(BaseModel):
    """What you get when you check on a running workflow."""
    run_id: str
    graph_id: str
    status: str  # "running", "completed", or "failed"
    state: Dict[str, Any]  # Current state of the workflow
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None  # Only present if something went wrong


# ============================================================================
# Helper Functions
# ============================================================================

def create_node_function(node_id: str, description: str):
    """
    Create a simple default function for a node.
    
    Note: This is a simplified version. In a full implementation, you'd want
    to allow nodes to reference actual tools or custom functions!
    """
    def node_func(state: Dict[str, Any]) -> Dict[str, Any]:
        # Default behavior: just mark that we ran
        return {
            f"{node_id}_executed": True,
            f"{node_id}_message": f"Node {node_id} executed successfully!"
        }
    node_func.__name__ = node_id
    return node_func


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """
    Welcome to the Workflow Engine API! 👋
    
    This is the home page - it tells you what this API can do.
    """
    return {
        "message": "Welcome to the Workflow Graph Engine API! 🚀",
        "version": "1.0.0",
        "description": "Build and run workflows with ease!",
        "endpoints": {
            "POST /graph/create": "Create a new workflow graph",
            "POST /graph/run": "Run a workflow graph",
            "GET /graph/state/{run_id}": "Check the status of a running workflow",
            "GET /graph/list": "See all your workflows",
            "GET /tools": "See what tools are available",
            "POST /workflow/code-review/run": "Try our Code Review workflow (it's awesome!)"
        },
        "docs": "Visit /docs for interactive API documentation"
    }


@app.post("/graph/create", response_model=CreateGraphResponse)
async def create_graph(request: CreateGraphRequest):
    """
    Create a new workflow graph!
    
    Give us some nodes and edges, and we'll build a workflow for you.
    You'll get back a graph_id that you can use to run it later.
    
    Example:
    {
        "name": "My Awesome Workflow",
        "nodes": [
            {"node_id": "start", "description": "Begin here"},
            {"node_id": "process", "description": "Do some work"}
        ],
        "edges": [
            {"from_node": "start", "to_node": "process"}
        ],
        "entry_node": "start",
        "exit_nodes": ["process"]
    }
    """
    # Generate a unique ID for this graph
    graph_id = str(uuid.uuid4())
    graph = Graph(graph_id, request.name or "Unnamed Workflow")
    
    # Add all the nodes
    for node_def in request.nodes:
        # For now, nodes get default functions
        # In production, you'd want to allow custom functions or tool references!
        node_func = create_node_function(node_def.node_id, node_def.description)
        graph.add_node(node_def.node_id, node_func, node_def.description)
    
    # Connect the nodes with edges
    for edge in request.edges:
        try:
            graph.add_edge(edge.from_node, edge.to_node)
        except ValueError as e:
            # Make the error message helpful
            raise HTTPException(
                status_code=400,
                detail=f"Couldn't create edge from '{edge.from_node}' to '{edge.to_node}': {str(e)}"
            )
    
    # Set where to start and where to finish
    if request.entry_node:
        try:
            graph.set_entry_node(request.entry_node)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    if request.exit_nodes:
        try:
            graph.set_exit_nodes(request.exit_nodes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Save the graph so it can be run later
    graphs_storage[graph_id] = graph
    
    return CreateGraphResponse(
        graph_id=graph_id,
        message=f"✅ Successfully created workflow '{graph.name}'! Use graph_id '{graph_id}' to run it."
    )


@app.post("/graph/run", response_model=RunGraphResponse)
async def run_graph(request: RunGraphRequest):
    """
    Run a workflow graph!
    
    Give us a graph_id and some initial state, and we'll execute the workflow
    from start to finish. You'll get back the final state and a log of everything
    that happened.
    """
    # Make sure the graph exists
    if request.graph_id not in graphs_storage:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Workflow '{request.graph_id}' not found! "
                f"Make sure you created it first using POST /graph/create. "
                f"Available workflows: {list(graphs_storage.keys())}"
            )
        )
    
    graph = graphs_storage[request.graph_id]
    
    try:
        # Run the workflow!
        result = await executor.execute(
            graph,
            request.initial_state,
            max_iterations=request.max_iterations
        )
        return RunGraphResponse(**result)
    except ValueError as e:
        # User error (like missing entry node) - 400 Bad Request
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Something went wrong during execution - 500 Internal Server Error
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )


@app.get("/graph/state/{run_id}", response_model=StateResponse)
async def get_graph_state(run_id: str):
    """
    Check on a running workflow!
    
    Want to see what a workflow is doing right now? Just give us the run_id
    (which you got when you started the workflow) and we'll tell you:
    - Is it still running?
    - What's the current state?
    - Did it finish? Did it fail?
    """
    if run_id not in executor.active_runs:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Run '{run_id}' not found! "
                f"Make sure you started a workflow first using POST /graph/run. "
                f"Maybe the run_id is incorrect, or the run has been cleared from memory."
            )
        )
    
    run_data = executor.active_runs[run_id]
    
    return StateResponse(
        run_id=run_id,
        graph_id=run_data["graph_id"],
        status=run_data["status"],
        state=run_data.get("state", {}),
        started_at=run_data.get("started_at").isoformat() if run_data.get("started_at") else None,
        completed_at=run_data.get("completed_at").isoformat() if run_data.get("completed_at") else None,
        error=run_data.get("error")
    )


@app.get("/graph/list")
async def list_graphs():
    """
    See all the workflows you've created!
    
    Get a list of all workflows with their details - useful for browsing
    what you have available.
    """
    if not graphs_storage:
        return {
            "message": "You haven't created any workflows yet! Use POST /graph/create to get started.",
            "graphs": []
        }
    
    return {
        "message": f"Found {len(graphs_storage)} workflow(s)!",
        "graphs": [
            {
                "graph_id": graph_id,
                "name": graph.name,
                "node_count": len(graph.nodes),
                "edge_count": sum(len(edges) for edges in graph.edges.values()),
                "description": f"{graph.name} with {len(graph.nodes)} nodes"
            }
            for graph_id, graph in graphs_storage.items()
        ]
    }


@app.get("/tools")
async def list_tools():
    """
    See what tools are available for your workflows!
    
    Tools are pre-built functions that nodes can use to do useful work.
    This endpoint shows you what's available and what each tool does.
    """
    from app.tools import tool_registry
    tools = tool_registry.list_tools()
    
    return {
        "message": f"Found {len(tools)} tool(s) available!",
        "tools": tools,
        "note": "You can use these tools in your workflow nodes to do useful work!"
    }


@app.post("/workflow/code-review/run", response_model=RunGraphResponse)
async def run_code_review_workflow(request: Dict[str, Any]):
    """
    Run our pre-built Code Review workflow! 🔍
    
    This is a ready-to-use workflow that analyzes your code quality:
    - Extracts functions from your code
    - Checks complexity
    - Detects code smells and issues
    - Suggests improvements
    - Keeps improving until quality meets your standards!
    
    Just send us your code and quality requirements:
    {
        "code": "def my_function():\\n    return 42",
        "quality_threshold": 70,  // Optional, default is 70
        "max_loop_iterations": 3   // Optional, default is 3
    }
    
    We'll analyze it and give you detailed feedback!
    """
    # Get the workflow definition
    workflow_def = create_code_review_workflow()
    
    # Build the graph from the definition
    graph_id = "code_review_workflow"
    graph = Graph(graph_id, workflow_def["name"])
    
    # Add all the nodes
    for node_id, node_data in workflow_def["nodes"].items():
        graph.add_node(node_id, node_data["func"], node_data["description"])
    
    # Connect them with edges
    for from_node, to_node in workflow_def["edges"]:
        graph.add_edge(from_node, to_node)
    
    graph.set_entry_node(workflow_def["entry_node"])
    graph.set_exit_nodes(workflow_def["exit_nodes"])
    
    # Prepare the initial state from the request
    code = request.get("code", "")
    if not code:
        raise HTTPException(
            status_code=400,
            detail="Please provide 'code' in your request! We need some code to analyze."
        )
    
    initial_state = {
        "code": code,
        "quality_threshold": request.get("quality_threshold", 70),
        "max_loop_iterations": request.get("max_loop_iterations", 3)
    }
    
    # Run it!
    try:
        result = await executor.execute(graph, initial_state)
        return RunGraphResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Code review workflow failed: {str(e)}"
        )


# ============================================================================
# Run the server (if running directly)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Workflow Engine API server...")
    print("📖 Visit http://localhost:8000/docs for interactive API documentation")
    uvicorn.run(app, host="0.0.0.0", port=8000)

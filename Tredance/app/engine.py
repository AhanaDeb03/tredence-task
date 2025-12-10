"""
The heart of our workflow engine - think of it as a smart conductor for your workflows!

This module contains everything needed to build and run workflow graphs:
- Nodes: Individual steps in your workflow (like "check code quality")
- Graphs: Collections of nodes connected together
- Executor: The thing that actually runs your workflow step by step
"""
from typing import Dict, Any, Callable, List, Optional
from enum import Enum
import uuid
from datetime import datetime


class NodeStatus(Enum):
    """Tracks what a node is currently doing - like a status update!"""
    PENDING = "pending"    # Waiting in line
    RUNNING = "running"    # Currently doing its job
    COMPLETED = "completed"  # All done, successfully!
    FAILED = "failed"      # Oops, something went wrong
    SKIPPED = "skipped"    # Decided not to run this one


class ExecutionLog:
    """Keeps a diary of what each node did - useful for debugging and understanding what happened!"""
    
    def __init__(self, node_id: str, status: NodeStatus, timestamp: datetime, 
                 message: str = "", error: Optional[str] = None):
        self.node_id = node_id
        self.status = status
        self.timestamp = timestamp
        self.message = message
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert our log entry into a dictionary that's easy to send over the API."""
        return {
            "node_id": self.node_id,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "error": self.error
        }


class Node:
    """
    A single step in your workflow - like a worker that does one specific job.
    
    Each node takes some state (data), does something with it, and returns updated state.
    Think of it like: "Give me your data, I'll process it, and give you back improved data!"
    """
    
    def __init__(
        self,
        node_id: str,
        func: Callable[[Dict[str, Any]], Dict[str, Any]],
        description: str = ""
    ):
        self.node_id = node_id  # Unique name for this node
        self.func = func        # The actual function that does the work
        self.description = description  # What this node does (for humans to read)
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run this node's function with the current state.
        
        Handles both regular functions and async functions automatically.
        If something goes wrong, we wrap it in a friendly error message.
        """
        try:
            result = self.func(state)
            
            # If the function is async (returns a coroutine), we need to wait for it
            if hasattr(result, '__await__'):
                result = await result
            return result
        except Exception as e:
            # Make the error message helpful - tell them which node failed!
            raise RuntimeError(f"Oops! Node '{self.node_id}' encountered an error: {str(e)}") from e


class Graph:
    """
    A workflow graph - a collection of nodes connected together with edges.
    
    Think of it like a flowchart or a recipe:
    - Nodes are the steps (chop vegetables, add salt, etc.)
    - Edges are the arrows connecting steps (do this, then do that)
    - Entry node is where you start
    - Exit nodes are where you can finish
    """
    
    def __init__(self, graph_id: str, name: str = ""):
        self.graph_id = graph_id
        self.name = name or "Unnamed Workflow"
        self.nodes: Dict[str, Node] = {}  # All the nodes in this graph
        self.edges: Dict[str, List[str]] = {}  # Which node leads to which (node_id -> [next_nodes])
        self.entry_node: Optional[str] = None  # Where do we start?
        self.exit_nodes: List[str] = []  # Where can we finish?
    
    def add_node(self, node_id: str, func: Callable, description: str = ""):
        """Add a new node to this graph - like adding a step to a recipe."""
        self.nodes[node_id] = Node(node_id, func, description)
        
        # If this is the first node, make it the entry point by default
        if self.entry_node is None:
            self.entry_node = node_id
    
    def add_edge(self, from_node: str, to_node: str):
        """
        Connect two nodes together - like drawing an arrow from A to B.
        
        This means: "After node A finishes, run node B next."
        """
        # Make sure both nodes actually exist before connecting them!
        if from_node not in self.nodes:
            raise ValueError(f"Can't create edge from '{from_node}' - that node doesn't exist! "
                           f"Available nodes: {list(self.nodes.keys())}")
        if to_node not in self.nodes:
            raise ValueError(f"Can't create edge to '{to_node}' - that node doesn't exist! "
                           f"Available nodes: {list(self.nodes.keys())}")
        
        # Add the connection
        if from_node not in self.edges:
            self.edges[from_node] = []
        self.edges[from_node].append(to_node)
    
    def set_entry_node(self, node_id: str):
        """Set where the workflow should start - like choosing the starting line in a race."""
        if node_id not in self.nodes:
            raise ValueError(f"Can't set entry node to '{node_id}' - that node doesn't exist!")
        self.entry_node = node_id
    
    def set_exit_nodes(self, node_ids: List[str]):
        """Set which nodes can end the workflow - like marking the finish lines."""
        for node_id in node_ids:
            if node_id not in self.nodes:
                raise ValueError(f"Can't set exit node '{node_id}' - that node doesn't exist!")
        self.exit_nodes = node_ids


class WorkflowExecutor:
    """
    The conductor of the orchestra! This is what actually runs your workflow.
    
    It:
    - Keeps track of all active workflow runs
    - Executes nodes one by one
    - Manages state as it flows between nodes
    - Handles looping and branching
    - Logs everything that happens
    """
    
    def __init__(self):
        # Keep track of all workflows currently running (or that have run)
        self.active_runs: Dict[str, Dict[str, Any]] = {}
    
    async def execute(
        self,
        graph: Graph,
        initial_state: Dict[str, Any],
        run_id: Optional[str] = None,
        max_iterations: int = 1000
    ) -> Dict[str, Any]:
        """
        Execute a workflow graph from start to finish.
        
        This is the main show! It:
        1. Starts at the entry node
        2. Runs each node in order (following the edges)
        3. Updates state as it goes
        4. Handles loops (if quality score is low, try again!)
        5. Handles branching (if condition is true, go here, else go there)
        6. Stops at exit nodes
        7. Returns the final state and a log of everything that happened
        
        Args:
            graph: The workflow graph to execute
            initial_state: Starting data for the workflow
            run_id: Optional ID for this run (we'll generate one if not provided)
            max_iterations: Safety limit to prevent infinite loops (default 1000)
        
        Returns:
            Dictionary with run_id, final_state, execution_log, and iterations count
        """
        # Generate a unique ID for this run if one wasn't provided
        if run_id is None:
            run_id = str(uuid.uuid4())
        
        # Start with a fresh copy of the initial state
        # We add some internal tracking fields (prefixed with _) that won't show in final output
        state = initial_state.copy()
        state["_run_id"] = run_id
        state["_iteration"] = 0
        state["_execution_log"] = []  # We'll add log entries here as we go
        
        # Remember this run so we can check on it later via the API
        self.active_runs[run_id] = {
            "graph_id": graph.graph_id,
            "state": state,
            "status": "running",
            "started_at": datetime.now()
        }
        
        try:
            # Start at the entry node
            current_node_id = graph.entry_node
            if current_node_id is None:
                raise ValueError(
                    "Workflow has no entry node! Please set one using set_entry_node(). "
                    "How can we start if we don't know where to begin?"
                )
            
            # Track which nodes we've visited (to prevent accidental infinite loops)
            visited_nodes = set()
            iteration = 0
            
            # Main execution loop - keep going until we hit an exit or max iterations
            while current_node_id and iteration < max_iterations:
                iteration += 1
                state["_iteration"] = iteration
                
                # Make sure this node actually exists
                if current_node_id not in graph.nodes:
                    raise ValueError(
                        f"Tried to run node '{current_node_id}' but it doesn't exist in the graph! "
                        f"Available nodes: {list(graph.nodes.keys())}"
                    )
                
                node = graph.nodes[current_node_id]
                
                # Log that we're starting this node
                log_entry = ExecutionLog(
                    node_id=current_node_id,
                    status=NodeStatus.RUNNING,
                    timestamp=datetime.now(),
                    message=f"Starting work on: {current_node_id}"
                )
                state["_execution_log"].append(log_entry.to_dict())
                self.active_runs[run_id]["state"] = state  # Update the stored state
                
                try:
                    # Actually run the node's function!
                    result = await node.execute(state)
                    
                    # Merge the result into our state
                    if isinstance(result, dict):
                        state.update(result)
                    
                    # Mark this node as completed
                    log_entry.status = NodeStatus.COMPLETED
                    log_entry.message = f"Finished: {current_node_id}"
                    state["_execution_log"][-1] = log_entry.to_dict()
                    
                except Exception as e:
                    # Something went wrong - log it and re-raise
                    log_entry.status = NodeStatus.FAILED
                    log_entry.error = str(e)
                    state["_execution_log"][-1] = log_entry.to_dict()
                    self.active_runs[run_id]["state"] = state
                    raise
                
                # Now figure out which node should run next!
                next_node_id = None
                
                # Priority 1: Check if the node explicitly told us where to go next
                # (This enables conditional branching - "if X, go to node A, else go to node B")
                if "_next_node" in state:
                    next_node_id = state.pop("_next_node")
                
                # Priority 2: Check if we're in a loop that should continue
                elif state.get("_loop", False):
                    if state.get("_loop_condition", True):
                        # Keep looping - go to the loop target (or stay here if no target)
                        next_node_id = state.get("_loop_target", current_node_id)
                    else:
                        # Loop says we're done
                        state.pop("_loop", None)
                        next_node_id = None
                
                # Priority 3: Follow the edges defined in the graph
                elif current_node_id in graph.edges:
                    # For now, we take the first edge (could be extended for conditional edges)
                    edges = graph.edges[current_node_id]
                    if edges:
                        next_node_id = edges[0]
                
                # Check if we've reached an exit node
                # We only actually exit if there's no next node to go to
                if current_node_id in graph.exit_nodes:
                    if next_node_id is None:
                        # We're at an exit and have nowhere else to go - we're done!
                        break
                    # If exit node says to continue (for looping), that's okay too
                
                current_node_id = next_node_id
                
                # Safety check: If we're visiting the same node over and over
                # and we're not explicitly in a loop, something might be wrong
                if current_node_id and current_node_id in visited_nodes and not state.get("_loop", False):
                    # Give it some wiggle room (2x the number of nodes) before we panic
                    if len(visited_nodes) > len(graph.nodes) * 2:
                        break
                
                if current_node_id:
                    visited_nodes.add(current_node_id)
            
            # Check if we hit the iteration limit (probably an infinite loop protection kicked in)
            if iteration >= max_iterations:
                raise RuntimeError(
                    f"Workflow stopped after {max_iterations} iterations - this looks like an infinite loop! "
                    f"Make sure your workflow has proper exit conditions."
                )
            
            # Clean up: Remove internal tracking fields (ones starting with _) from final output
            final_state = {k: v for k, v in state.items() if not k.startswith("_")}
            
            # Mark this run as completed
            self.active_runs[run_id]["status"] = "completed"
            self.active_runs[run_id]["completed_at"] = datetime.now()
            self.active_runs[run_id]["final_state"] = final_state
            
            return {
                "run_id": run_id,
                "final_state": final_state,
                "execution_log": state["_execution_log"],
                "iterations": iteration
            }
            
        except Exception as e:
            # If anything went wrong, mark the run as failed
            self.active_runs[run_id]["status"] = "failed"
            self.active_runs[run_id]["error"] = str(e)
            self.active_runs[run_id]["completed_at"] = datetime.now()
            raise
        finally:
            # We keep the run data in active_runs so the API can still query it
            # even after it's done (useful for checking results later)
            pass

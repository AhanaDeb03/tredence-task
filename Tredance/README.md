# Workflow Graph Engine 🚀

A simple workflow engine where you create nodes, connect them, and run workflows via API. Think of it like a simplified LangGraph - build workflows step by step!

## What It Does

- **Create workflows** with nodes (steps) and edges (connections)
- **Run workflows** with shared state flowing between nodes
- **Loop and branch** based on conditions
- **Use tools** from a built-in registry
- **Try it out** with the pre-built Code Review workflow!

## Quick Start

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server:**

   ```bash
   uvicorn app.main:app --reload
   ```

3. **Open in browser:**
   - **Interactive docs:** http://localhost:8000/docs (best way to try it!)
   - **API root:** http://localhost:8000

That's it! Visit `/docs` and click around - everything is interactive. ✨

## Try the Code Review Workflow

We built a Code Review workflow that analyzes your code quality. Here's a quick example:

1. Go to http://localhost:8000/docs
2. Find `POST /workflow/code-review/run`
3. Click "Try it out"
4. Paste this:

```json
{
  "code": "def test(x):\n    if x > 0:\n        if x > 10:\n            return x * 2\n    return 0",
  "quality_threshold": 70,
  "max_loop_iterations": 3
}
```

5. Click "Execute" - see the magic happen! 🎉

## Main Endpoints

- `POST /graph/create` - Create your own workflow
- `POST /graph/run` - Run a workflow
- `GET /graph/state/{run_id}` - Check progress
- `GET /tools` - See available tools
- `POST /workflow/code-review/run` - Try the Code Review workflow

## How It Works (Simple Version)

1. **Nodes** = Steps in your workflow (Python functions)
2. **Edges** = Connections between nodes (what runs next)
3. **State** = Data that flows between nodes (a dictionary)
4. **Executor** = Runs everything and keeps logs

Nodes can return `_next_node` to control where to go next, or `_loop: true` to keep looping. That's basically it!

## Project Structure

```
app/
├── main.py       # API endpoints
├── engine.py     # The workflow engine
├── tools.py      # Built-in tools
└── workflows.py  # Example workflows
```

## What's Supported

✅ Sequential execution  
✅ State management  
✅ Conditional branching  
✅ Looping  
✅ Tool registry  
✅ Execution logs

## Future Ideas

If I had more time, I'd add:

- WebSocket streaming for real-time updates
- Database persistence
- Parallel node execution
- Graph visualization
- Better error recovery

But honestly, it works great for what it does! 😊

## Need Help?

Check out `QUICKSTART.md` for detailed examples, or just explore the interactive docs at `/docs` - they're way more helpful than reading docs!

---

_Built with FastAPI and Python. Simple, clean, and easy to understand._ ✨

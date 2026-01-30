import sys
import os

# CRITICAL: Set environment variables BEFORE any imports that use common.py
# Parse command-line arguments and set environment variables at module load time
# This ensures all modules (including subprocesses) use the correct base_dir
if len(sys.argv) > 2:
    os.environ['FALCON_BASE_DIR'] = sys.argv[2]
if len(sys.argv) > 3:
    os.environ['FALCON_IS_DEV'] = '1' if sys.argv[3].lower() == 'true' else '0'

import signal
import threading
import time
import sqlite3
from typing import Optional
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from runPipeline import PipelineRunner
from prDataReader import get_pr_details, get_comment_details, get_pr_files
from common import getDBPath, get_base_dir

# Import smart agent (handle hyphenated module name)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp-agent'))
import importlib.util
_smart_agent_path = os.path.join(os.path.dirname(__file__), 'mcp-agent', 'smart-agent.py')
_spec = importlib.util.spec_from_file_location("smart_agent_module", _smart_agent_path)
_smart_agent_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_smart_agent_module)
SmartAgent = _smart_agent_module.SmartAgent

# Global variables to store Electron configuration
BASE_DIR: Optional[str] = None
IS_DEV: bool = False

app = FastAPI()

# CORS for Electron renderer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/api/userdata-path")
def get_userdata_path():
    return {"user_data_path": BASE_DIR}


@app.post("/api/example")
def example_endpoint(data: dict):
    return {"received": data}


@app.get("/api/pr/{pr_id}")
def get_pr(pr_id: int, username: Optional[str] = None):
    """
    Get PR details by PR ID.
    
    Args:
        pr_id: PR number
        username: Optional username filter
    
    Returns:
        PR details dictionary or error
    """
    try:
        # Get base directory (uses FALCON_BASE_DIR env var set by server.py)
        base_dir = get_base_dir()
        
        # Connect to database
        db_path = getDBPath(base_dir)
        if not db_path.exists():
            return {"error": f"Database not found: {db_path}"}
        
        db_conn = sqlite3.connect(str(db_path))
        
        # Get PR details
        pr_details = get_pr_details(db_conn, pr_id=pr_id, username=username)
        
        db_conn.close()
        
        if pr_details:
            return {"success": True, "data": pr_details}
        else:
            return {"success": False, "error": f"PR {pr_id} not found"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/pr/{pr_id}/comment/{comment_id}")
def get_comment(pr_id: int, comment_id: int, username: Optional[str] = None):
    """
    Get comment details by PR ID and comment ID.
    
    Args:
        pr_id: PR number
        comment_id: Comment ID
        username: Optional username filter
    
    Returns:
        Comment details dictionary or error
    """
    try:
        base_dir = get_base_dir()
        db_path = getDBPath(base_dir)
        
        if not db_path.exists():
            return {"error": f"Database not found: {db_path}"}
        
        db_conn = sqlite3.connect(str(db_path))
        
        # Get comment details
        comment_details = get_comment_details(
            db_conn, 
            pr_id=pr_id, 
            comment_id=comment_id,
            username=username
        )
        
        db_conn.close()
        
        if comment_details:
            return {"success": True, "data": comment_details}
        else:
            return {"success": False, "error": f"Comment {comment_id} not found in PR {pr_id}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/pr/{pr_id}/files")
def get_files(pr_id: int, username: Optional[str] = None):
    """
    Get all files changed in a PR.
    
    Args:
        pr_id: PR number
        username: Optional username filter
    
    Returns:
        List of file details or error
    """
    try:
        base_dir = get_base_dir()
        db_path = getDBPath(base_dir)
        
        if not db_path.exists():
            return {"error": f"Database not found: {db_path}"}
        
        db_conn = sqlite3.connect(str(db_path))
        
        # Get PR files
        files_list = get_pr_files(
            db_conn, 
            pr_id=pr_id,
            username=username
        )
        
        db_conn.close()
        
        if files_list:
            # Calculate summary stats
            total_additions = sum(f.get('additions', 0) for f in files_list)
            total_deletions = sum(f.get('deletions', 0) for f in files_list)
            total_changes = sum(f.get('changes', 0) for f in files_list)
            
            return {
                "success": True, 
                "data": {
                    "files": files_list,
                    "summary": {
                        "total_files": len(files_list),
                        "total_additions": total_additions,
                        "total_deletions": total_deletions,
                        "total_changes": total_changes
                    }
                }
            }
        else:
            return {"success": False, "error": f"Files not found for PR {pr_id}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


class SmartAgentRequest(BaseModel):
    query: str


# Global smart agent instance (lazy initialization)
_smart_agent_instance = None


def get_smart_agent() -> SmartAgent:
    """Get or create the smart agent instance."""
    global _smart_agent_instance
    if _smart_agent_instance is None:
        _smart_agent_instance = SmartAgent()
    return _smart_agent_instance


@app.get("/api/smart-agent/capabilities")
def get_agent_capabilities():
    """
    Get available smart agent capabilities and tools.
    
    Returns:
        List of available tools and example queries
    """
    return {
        "success": True,
        "capabilities": [
            {
                "name": "PR Analysis",
                "description": "Get detailed information about specific PRs",
                "examples": [
                    "Show me PR 1013",
                    "Get details about pull request 660"
                ]
            },
            {
                "name": "User Management",
                "description": "Query and list users in the system",
                "examples": [
                    "List all users",
                    "Who are the users in the system?"
                ]
            },
            {
                "name": "OKR Tracking",
                "description": "Search for OKRs and generate updates",
                "examples": [
                    "Search for Reserved Ads OKR",
                    "Generate update for Reserved Ads goal for Jan 2026"
                ]
            },
            {
                "name": "Code Review Analytics",
                "description": "Analyze code review comments with signal classifications",
                "examples": [
                    "Show me all performance-related comments",
                    "How many bug comments did I make?",
                    "What's my comment breakdown by category?"
                ]
            },
            {
                "name": "PR Statistics",
                "description": "Query PR statistics and review data",
                "examples": [
                    "How many PRs did I review for John?",
                    "Show me authors where I left more than 10 comments"
                ]
            },
            {
                "name": "OKR Update Generation",
                "description": "Generate AI-powered technical and executive updates for OKRs",
                "examples": [
                    "Write me an update for Reserved Ads goal for Jan 2026 by looking at all the PRs"
                ]
            }
        ],
        "tools": [
            "get_pr_details",
            "get_comment_details",
            "get_pr_files",
            "list_all_users",
            "query_users",
            "search_okrs",
            "list_all_okrs",
            "find_prs_by_okr",
            "generate_okr_update",
            "query_review_comments",
            "query_pr_stats"
        ]
    }


@app.post("/api/smart-agent/query")
async def smart_agent_query(request: SmartAgentRequest):
    """
    Query the smart agent with natural language.
    
    The agent can:
    - Analyze PR data and code reviews
    - Generate OKR updates from PR bodies
    - Query users and review comments
    - Answer complex questions by orchestrating multiple tools
    
    Args:
        query: Natural language query
        
    Returns:
        Agent's response with reasoning and results
    """
    try:
        if not request.query or not request.query.strip():
            return {"success": False, "error": "Query cannot be empty"}
        
        # Run the agent in a thread executor to avoid blocking
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def run_agent():
            agent = get_smart_agent()
            return agent.run(request.query)
        
        # Execute in thread pool
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, run_agent)
        
        return {
            "success": True,
            "query": request.query,
            "answer": result
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


class PipelineRequest(BaseModel):
    start_from: int = 1
    specific_steps: Optional[list[int]] = None
    base_dir: Optional[str] = None


# Store pipeline status
pipeline_status = {
    "running": False,
    "success": None,
    "last_run": None
}


def run_pipeline_task(start_from: int, specific_steps: Optional[list[int]], base_dir: Optional[str], is_dev: bool):
    """Background task to run the pipeline."""
    global pipeline_status

    pipeline_status["running"] = True
    pipeline_status["success"] = None

    try:
        runner = PipelineRunner(
            start_from=start_from,
            specific_steps=specific_steps,
            base_dir=base_dir or BASE_DIR,
            is_dev=is_dev
        )
        success = runner.run()
        pipeline_status["success"] = success
        pipeline_status["last_run"] = {"status": "completed" if success else "failed"}
    except Exception as e:
        pipeline_status["success"] = False
        pipeline_status["last_run"] = {"status": "error", "error": str(e)}
    finally:
        pipeline_status["running"] = False


@app.post("/api/pipeline/run")
async def run_pipeline(request: PipelineRequest, background_tasks: BackgroundTasks):
    """
    Run the PR data pipeline.
    
    Parameters:
    - start_from: Step number to start from (default: 1)
    - specific_steps: List of specific steps to run (e.g., [1, 3])
    - base_dir: Base directory for data (uses Electron userData path if not provided)
    """
    if pipeline_status["running"]:
        return {"error": "Pipeline is already running"}
    
    background_tasks.add_task(
        run_pipeline_task,
        request.start_from,
        request.specific_steps,
        request.base_dir,
        IS_DEV
    )
    
    return {"message": "Pipeline started", "status": "running"}


@app.get("/api/pipeline/status")
def get_pipeline_status():
    """Get the current status of the pipeline."""
    return pipeline_status


def run_pipeline_continuously(base_dir: Optional[str], is_dev: bool):
    """Run the pipeline continuously in a loop with 1-minute sleep between runs."""
    global pipeline_status
    
    run_count = 0

    print("\n" + "="*80, file=sys.stderr)
    print("🔄 Starting continuous pipeline execution (1-minute interval)...", file=sys.stderr)
    print("="*80 + "\n", file=sys.stderr)

    while True:
        run_count += 1
        print("\n" + "="*80, file=sys.stderr)
        print(f"🚀 Pipeline Run #{run_count}", file=sys.stderr)
        print("="*80 + "\n", file=sys.stderr)

        pipeline_status["running"] = True
        pipeline_status["success"] = None

        try:
            runner = PipelineRunner(
                start_from=1,
                specific_steps=None,
                base_dir=base_dir,
                is_dev=is_dev
            )
            success = runner.run()
            
            pipeline_status["success"] = success
            pipeline_status["last_run"] = {
                "status": "completed" if success else "failed",
                "run_number": run_count
            }
            
            if success:
                print(f"\n✅ Pipeline run #{run_count} completed successfully!", file=sys.stderr)
            else:
                print(f"\n⚠️  Pipeline run #{run_count} completed with errors", file=sys.stderr)
        except Exception as e:
            pipeline_status["success"] = False
            pipeline_status["last_run"] = {
                "status": "error",
                "error": str(e),
                "run_number": run_count
            }
            print(f"\n❌ Pipeline run #{run_count} failed with error: {e}", file=sys.stderr)
        finally:
            pipeline_status["running"] = False
        
        # Sleep for 1 minute before next run
        print(f"\n⏳ Sleeping for 60 seconds before next run...", file=sys.stderr)
        time.sleep(60)


def signal_handler(sig, frame):
    print("Graceful shutdown", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Parse command line arguments
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    BASE_DIR = sys.argv[2] if len(sys.argv) > 2 else None
    IS_DEV = (sys.argv[3].lower() == 'true') if len(sys.argv) > 3 else False

    print(f"Starting on port {port}", file=sys.stderr)
    if BASE_DIR:
        print(f"User data path: {BASE_DIR}", file=sys.stderr)

    print(f"Development mode: {IS_DEV}", file=sys.stderr)
    # Start the pipeline in a background thread (runs continuously)
    pipeline_thread = threading.Thread(
        target=run_pipeline_continuously,
        args=(BASE_DIR, IS_DEV),
        daemon=True  # Thread will terminate when main program exits
    )
    pipeline_thread.start()
    
    print("\n" + "="*80, file=sys.stderr)
    print("🌐 Starting FastAPI Server...", file=sys.stderr)
    print("   (Pipeline running continuously in background - check /api/pipeline/status)", file=sys.stderr)
    print("="*80 + "\n", file=sys.stderr)

    uvicorn.run(
        app,
        host="127.0.0.1",  # Localhost only (security)
        port=port,
        log_level="info"
    )

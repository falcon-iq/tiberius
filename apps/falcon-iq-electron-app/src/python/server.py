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
from typing import Optional
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from runPipeline import PipelineRunner

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

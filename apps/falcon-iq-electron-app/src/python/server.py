import sys
import signal
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Global variable to store Electron userData directory path
BASE_DIR: Optional[str] = None

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


def signal_handler(sig, frame):
    print("Graceful shutdown", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Parse command line arguments
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    BASE_DIR = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Starting on port {port}", file=sys.stderr)
    if BASE_DIR:
        print(f"User data path: {BASE_DIR}", file=sys.stderr)

    uvicorn.run(
        app,
        host="127.0.0.1",  # Localhost only (security)
        port=port,
        log_level="info"
    )

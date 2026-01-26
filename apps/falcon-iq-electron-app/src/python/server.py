import sys
import signal
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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


@app.post("/api/example")
def example_endpoint(data: dict):
    return {"received": data}


def signal_handler(sig, frame):
    print("Graceful shutdown", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"Starting on port {port}", file=sys.stderr)

    uvicorn.run(
        app,
        host="127.0.0.1",  # Localhost only (security)
        port=port,
        log_level="info"
    )

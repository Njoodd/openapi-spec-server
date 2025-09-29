#!/usr/bin/env python3
"""
OpenAPI Specification Server Runner
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add src to Python path if needed
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from spec_server import app
import uvicorn

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Starting OpenAPI Specification Server...")
    print("Available endpoints:")
    print("  - Root (Collections): http://localhost:8001/")
    print("  - Health Check: http://localhost:8001/health")
    print("  - List All Specs: http://localhost:8001/specs")
    print("  - Individual Specs: http://localhost:8001/{spec_name}/openapi.json")
    print("  - Spec Info: http://localhost:8001/{spec_name}/info")
    print("\nPress Ctrl+C to stop the server")

    uvicorn.run(
        "spec_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
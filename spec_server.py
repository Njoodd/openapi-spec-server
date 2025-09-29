#!/usr/bin/env python3
"""
Simple HTTP server to serve OpenAPI specifications
"""

import os
import logging
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OpenAPI Spec Server",
    description="Simple server to serve OpenAPI specifications",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent
SPECS_DIR = PROJECT_ROOT / "specs"

# Global variable to store discovered specs
discovered_specs: Dict[str, Path] = {}

def discover_specs() -> Dict[str, Path]:
    """Discover all OpenAPI specification files in the specs directory"""
    specs = {}
    if not SPECS_DIR.exists():
        logger.warning(f"Specs directory not found: {SPECS_DIR}")
        return specs

    # Look for YAML and JSON files that appear to be OpenAPI specs
    for pattern in ["*.yaml", "*.yml", "*.json"]:
        for file_path in SPECS_DIR.glob(pattern):
            # Create a clean spec name from filename
            spec_name = file_path.stem.replace("-openapi", "").replace("_openapi", "").replace("openapi", "").replace("-", "_").replace(".", "_").strip("_")
            if not spec_name:
                spec_name = file_path.stem

            specs[spec_name] = file_path

    logger.info(f"Discovered {len(specs)} specifications: {list(specs.keys())}")
    return specs

def extract_capabilities_from_spec(spec_data: Dict[str, Any]) -> List[str]:
    """Extract capabilities from OpenAPI spec paths and operations"""
    capabilities = []
    paths = spec_data.get('paths', {})

    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                operation_id = operation.get('operationId', '')
                summary = operation.get('summary', '').lower()
                description = operation.get('description', '').lower()
                path_lower = path.lower()

                # Extract capabilities from operation IDs, summaries, and paths
                # Use operation ID as capability if available
                if operation_id:
                    capabilities.append(operation_id)

                # Extract meaningful words from path segments
                path_segments = [seg for seg in path_lower.split('/') if seg and not seg.startswith('{')]
                for segment in path_segments:
                    if len(segment) > 2:  # Ignore very short segments
                        capabilities.append(segment)

                # Extract key words from summary (first 3 meaningful words)
                if summary:
                    summary_words = [word for word in summary.split() if len(word) > 3]
                    capabilities.extend(summary_words[:3])

    # Remove duplicates, filter out common words, and return
    common_words = {'get', 'post', 'put', 'delete', 'patch', 'the', 'and', 'for', 'with', 'from', 'this', 'that', 'are', 'you', 'all', 'can', 'will', 'one', 'use'}
    filtered_capabilities = [cap for cap in set(capabilities) if cap not in common_words and len(cap) > 2]
    return sorted(filtered_capabilities)

def extract_tags_from_spec(spec_data: Dict[str, Any], spec_name: str) -> List[str]:
    """Extract relevant tags from OpenAPI spec"""
    tags = []

    # Get tags from spec
    spec_tags = spec_data.get('tags', [])
    for tag in spec_tags:
        if isinstance(tag, dict):
            tag_name = tag.get('name', '').lower()
            if tag_name:
                tags.append(tag_name)
        elif isinstance(tag, str):
            tags.append(tag.lower())

    # Extract keywords from title and description
    title = spec_data.get('info', {}).get('title', '').lower()
    description = spec_data.get('info', {}).get('description', '').lower()

    # Extract meaningful words from title and description
    all_text = f"{title} {description}"
    words = all_text.split()

    # Filter out common words and extract meaningful keywords
    common_words = {'api', 'the', 'and', 'for', 'with', 'from', 'this', 'that', 'are', 'you', 'all', 'can', 'will', 'one', 'use', 'get', 'via', 'about', 'information', 'data', 'service', 'services'}
    meaningful_words = [word.strip('.,!?;:') for word in words if len(word) > 3 and word not in common_words]

    # Take the first 5 meaningful words as tags
    tags.extend(meaningful_words[:5])

    # Remove duplicates and return
    return list(set(tags))

@app.get("/")
async def root():
    """Root endpoint with OpenAPI collections in structured format"""
    collections = []

    for spec_name, spec_path in discovered_specs.items():
        try:
            if not spec_path.exists():
                continue

            # Load the spec data
            with open(spec_path, 'r', encoding='utf-8') as f:
                if spec_path.suffix.lower() == '.json':
                    spec_data = json.load(f)
                elif spec_path.suffix.lower() in ['.yaml', '.yml']:
                    spec_data = yaml.safe_load(f)
                else:
                    continue

            info = spec_data.get('info', {})
            servers = spec_data.get('servers', [])

            # Extract base URL from servers
            base_url = ""
            if servers and len(servers) > 0:
                base_url = servers[0].get('url', '')

            # Create the collection structure
            collection = {
                "name": info.get('title', spec_name.replace('_', ' ').title()),
                "tags": extract_tags_from_spec(spec_data, spec_name),
                "description": info.get('description', f"{spec_name.title()} API").strip(),
                "openapi_spec": f"http://0.0.0.0:8001/{spec_name}/openapi.json",
                "capabilities": extract_capabilities_from_spec(spec_data),
                "base_url": base_url
            }

            collections.append(collection)

        except Exception as e:
            logger.error(f"Error processing spec {spec_name}: {e}")
            # Add a minimal collection structure for failed specs
            collections.append({
                "name": spec_name.replace('_', ' ').title(),
                "tags": [],
                "description": f"{spec_name.title()} API",
                "openapi_spec": f"http://0.0.0.0:8001/{spec_name}/openapi.json",
                "capabilities": [],
                "base_url": ""
            })

    return collections

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "OpenAPI Spec Server is running"}

@app.get("/specs")
async def list_specifications():
    """List all available OpenAPI specifications"""
    specs = []

    for spec_name, file_path in discovered_specs.items():
        try:
            file_stat = file_path.stat() if file_path.exists() else None
            specs.append({
                "name": spec_name,
                "file_name": file_path.name,
                "file_type": file_path.suffix,
                "yaml_url": f"/{spec_name}/openapi.yaml",
                "json_url": f"/{spec_name}/openapi.json",
                "download_url": f"/{spec_name}/download",
                "info_url": f"/{spec_name}/info",
                "file_path": str(file_path),
                "exists": file_path.exists(),
                "size_bytes": file_stat.st_size if file_stat else 0,
                "modified_time": file_stat.st_mtime if file_stat else None
            })
        except Exception as e:
            logger.error(f"Error getting info for spec {spec_name}: {e}")
            specs.append({
                "name": spec_name,
                "file_name": file_path.name,
                "error": str(e)
            })

    return {
        "specifications": specs,
        "count": len(specs),
        "specs_directory": str(SPECS_DIR)
    }

@app.get("/{spec_name}/openapi.yaml")
async def get_spec_yaml(spec_name: str):
    """Serve OpenAPI specification in YAML format"""
    if spec_name not in discovered_specs:
        raise HTTPException(status_code=404, detail=f"Specification '{spec_name}' not found")

    spec_path = discovered_specs[spec_name]

    if not spec_path.exists():
        raise HTTPException(status_code=404, detail=f"Specification file not found: {spec_path}")

    try:
        # If the file is already YAML, serve it directly
        if spec_path.suffix.lower() in ['.yaml', '.yml']:
            return FileResponse(
                path=str(spec_path),
                media_type="application/x-yaml",
                headers={
                    "Content-Disposition": f"inline; filename={spec_name}-openapi.yaml",
                    "Cache-Control": "public, max-age=3600"
                }
            )
        # If it's JSON, convert to YAML
        elif spec_path.suffix.lower() == '.json':
            with open(spec_path, 'r', encoding='utf-8') as f:
                json_content = json.load(f)

            yaml_content = yaml.dump(json_content, default_flow_style=False, sort_keys=False)

            return Response(
                content=yaml_content,
                media_type="application/x-yaml",
                headers={
                    "Content-Disposition": f"inline; filename={spec_name}-openapi.yaml",
                    "Cache-Control": "public, max-age=3600"
                }
            )
    except Exception as e:
        logger.error(f"Error serving YAML spec: {e}")
        raise HTTPException(status_code=500, detail=f"Error serving specification: {str(e)}")

@app.get("/{spec_name}/openapi.json")
async def get_spec_json(spec_name: str):
    """Serve OpenAPI specification in JSON format"""
    if spec_name not in discovered_specs:
        raise HTTPException(status_code=404, detail=f"Specification '{spec_name}' not found")

    spec_path = discovered_specs[spec_name]

    if not spec_path.exists():
        raise HTTPException(status_code=404, detail=f"Specification file not found: {spec_path}")

    try:
        # If the file is JSON, serve it directly
        if spec_path.suffix.lower() == '.json':
            return FileResponse(
                path=str(spec_path),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"inline; filename={spec_name}-openapi.json",
                    "Cache-Control": "public, max-age=3600"
                }
            )
        # If it's YAML, convert to JSON
        elif spec_path.suffix.lower() in ['.yaml', '.yml']:
            with open(spec_path, 'r', encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f)

            json_content = json.dumps(yaml_content, indent=2)

            return Response(
                content=json_content,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"inline; filename={spec_name}-openapi.json",
                    "Cache-Control": "public, max-age=3600"
                }
            )
    except Exception as e:
        logger.error(f"Error serving JSON spec: {e}")
        raise HTTPException(status_code=500, detail=f"Error serving specification: {str(e)}")

@app.get("/{spec_name}/download")
async def download_spec(spec_name: str):
    """Download the original specification file"""
    if spec_name not in discovered_specs:
        raise HTTPException(status_code=404, detail=f"Specification '{spec_name}' not found")

    spec_path = discovered_specs[spec_name]

    if not spec_path.exists():
        raise HTTPException(status_code=404, detail=f"Specification file not found: {spec_path}")

    try:
        return FileResponse(
            path=str(spec_path),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={spec_path.name}",
                "Cache-Control": "public, max-age=3600"
            }
        )
    except Exception as e:
        logger.error(f"Error downloading spec: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading specification: {str(e)}")

@app.get("/{spec_name}/info")
async def get_spec_info(spec_name: str):
    """Get information about a specific OpenAPI specification"""
    if spec_name not in discovered_specs:
        raise HTTPException(status_code=404, detail=f"Specification '{spec_name}' not found")

    spec_path = discovered_specs[spec_name]

    if not spec_path.exists():
        raise HTTPException(status_code=404, detail=f"Specification file not found: {spec_path}")

    try:
        # Load the spec data (handle both JSON and YAML)
        with open(spec_path, 'r', encoding='utf-8') as f:
            if spec_path.suffix.lower() == '.json':
                spec_data = json.load(f)
            elif spec_path.suffix.lower() in ['.yaml', '.yml']:
                spec_data = yaml.safe_load(f)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {spec_path.suffix}")

        # Extract key information
        info = spec_data.get('info', {})
        paths = spec_data.get('paths', {})
        components = spec_data.get('components', {})

        return {
            "spec_name": spec_name,
            "title": info.get('title', 'Unknown'),
            "version": info.get('version', 'Unknown'),
            "description": info.get('description', ''),
            "endpoints": len(paths),
            "endpoint_paths": list(paths.keys()) if len(paths) <= 50 else f"{len(paths)} endpoints (too many to list)",
            "schemas": len(components.get('schemas', {})),
            "security_schemes": len(components.get('securitySchemes', {})),
            "servers": spec_data.get('servers', []),
            "file_info": {
                "name": spec_path.name,
                "path": str(spec_path),
                "type": spec_path.suffix,
                "size_bytes": spec_path.stat().st_size,
                "modified": spec_path.stat().st_mtime
            },
            "urls": {
                "yaml": f"/{spec_name}/openapi.yaml",
                "json": f"/{spec_name}/openapi.json",
                "download": f"/{spec_name}/download"
            }
        }
    except Exception as e:
        logger.error(f"Error reading spec info: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading specification: {str(e)}")

# Initialize specs discovery on startup
@app.on_event("startup")
async def startup_event():
    """Discover specs on server startup"""
    global discovered_specs
    discovered_specs = discover_specs()

if __name__ == "__main__":
    # Discover specifications
    logger.info("Discovering OpenAPI specifications...")
    discovered_specs = discover_specs()

    if not discovered_specs:
        logger.warning("No OpenAPI specifications found in specs directory")
        logger.warning(f"Please add .yaml, .yml, or .json files to: {SPECS_DIR}")
    else:
        logger.info(f"Found {len(discovered_specs)} specifications:")
        for spec_name, spec_path in discovered_specs.items():
            logger.info(f"  - {spec_name}: {spec_path.name}")

    # Run the server
    logger.info("Starting OpenAPI Specification Server...")
    logger.info("Server will be available at: http://localhost:8001")
    logger.info("Available endpoints:")
    logger.info("  - Root: http://localhost:8001/")
    logger.info("  - List specs: http://localhost:8001/specs")
    logger.info("  - Health check: http://localhost:8001/health")

    if discovered_specs:
        logger.info("Spec endpoints:")
        for spec_name in discovered_specs.keys():
            logger.info(f"  - {spec_name} YAML: http://localhost:8001/{spec_name}/openapi.yaml")
            logger.info(f"  - {spec_name} JSON: http://localhost:8001/{spec_name}/openapi.json")
            logger.info(f"  - {spec_name} Download: http://localhost:8001/{spec_name}/download")
            logger.info(f"  - {spec_name} Info: http://localhost:8001/{spec_name}/info")

    uvicorn.run(
        "spec_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
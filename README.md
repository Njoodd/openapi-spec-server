# OpenAPI Spec Server

A lightweight HTTP server that serves OpenAPI specifications in a structured collection format. Automatically discovers and serves OpenAPI specs from the `specs/` directory with dynamic capability and tag extraction.

## Features

- 🔍 **Auto-discovery** of OpenAPI specs (`.yaml`, `.yml`, `.json`)
- 🏷️ **Dynamic tag extraction** from spec content
- ⚡ **Capability detection** from API endpoints
- 🐳 **Docker support** with health checks
- 🔄 **Multiple formats** (JSON/YAML conversion)
- 📊 **Structured collections** output

## Quick Start

### Local Development

```bash
# Clone and navigate to project
git clone <your-repo-url>
cd openapi-spec-server

# Install dependencies
pip install -r requirements.txt

# Add your OpenAPI specs to specs/ directory
cp your-api-spec.yaml specs/

# Run the server
python spec_server.py
```

### Using Docker

```bash
# Build and run with Docker Compose (recommended)
docker-compose up --build

# Or build and run with Docker directly
docker build -t openapi-spec-server .
docker run -p 8001:8001 -v $(pwd)/specs:/app/specs:ro openapi-spec-server
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | List all API collections in structured format |
| `GET /health` | Health check endpoint |
| `GET /specs` | Detailed list of all specifications |
| `GET /{spec_name}/openapi.json` | Get spec in JSON format |
| `GET /{spec_name}/openapi.yaml` | Get spec in YAML format |
| `GET /{spec_name}/info` | Get spec metadata and info |
| `GET /{spec_name}/download` | Download original spec file |

## Collection Format

The root endpoint (`/`) returns collections in this structure:

```json
[
  {
    "name": "Weather API",
    "tags": ["weather", "forecast", "current"],
    "description": "Weather data API with forecasts and current conditions",
    "openapi_spec": "http://localhost:8001/weather/openapi.json",
    "capabilities": ["current", "forecast", "historical"],
    "base_url": "https://api.weather.com/v1"
  }
]
```

## Adding New Specs

1. Place your OpenAPI spec files in the `specs/` directory:
   ```bash
   cp my-api.yaml specs/
   ```

2. Restart the server (or use Docker volume mount for auto-reload):
   ```bash
   python spec_server.py
   ```

3. Your spec will be automatically discovered and available at:
   - Collections: `http://localhost:8001/`
   - JSON format: `http://localhost:8001/my_api/openapi.json`
   - Info: `http://localhost:8001/my_api/info`

## Configuration

The server runs on port `8001` by default. To change:

```bash
# Edit spec_server.py, line ~320
uvicorn.run("spec_server:app", host="0.0.0.0", port=YOUR_PORT)
```

For Docker, update the port mapping in `docker-compose.yml`.

## Examples

### Test the API

```bash
# Get all collections
curl http://localhost:8001/

# Get health status
curl http://localhost:8001/health

# Get specific spec in JSON
curl http://localhost:8001/weather/openapi.json

# Get spec metadata
curl http://localhost:8001/weather/info
```

### Sample Response

```json
[
  {
    "name": "REST Countries API",
    "tags": ["countries", "geography", "rest"],
    "description": "Get information about countries worldwide",
    "openapi_spec": "http://localhost:8001/restcountries/openapi.json",
    "capabilities": ["alpha", "currency", "name", "region"],
    "base_url": "https://restcountries.com/v3.1"
  }
]
```

## Development

### Requirements

- Python 3.11+
- FastAPI
- Uvicorn
- PyYAML

### Project Structure

```
openapi-spec-server/
├── spec_server.py          # Main server application
├── run_spec_server.py      # Server runner script
├── requirements.txt        # Python dependencies
├── specs/                  # OpenAPI specification files
│   ├── api1.yaml
│   └── api2.json
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
└── README.md             # This file
```

### Building Docker Image

```bash
# Build the image
docker build -t openapi-spec-server .

# Run with volume mount for development
docker run -p 8001:8001 \
  -v $(pwd)/specs:/app/specs:ro \
  openapi-spec-server
```

## Health Monitoring

The server includes built-in health checks:

```bash
# Manual health check
curl http://localhost:8001/health

# Docker health check (automatic)
# Configured in Dockerfile with 30s interval
```

## License

MIT License - see LICENSE file for details.
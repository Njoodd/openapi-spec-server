# Docker Setup for OpenAPI Spec Server

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and run the service
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop the service
docker-compose down
```

### Using Docker directly

```bash
# Build the image
docker build -t openapi-spec-server .

# Run the container
docker run -d \
  --name openapi-spec-server \
  -p 8001:8001 \
  -v $(pwd)/specs:/app/specs:ro \
  openapi-spec-server

# Stop the container
docker stop openapi-spec-server
docker rm openapi-spec-server
```

## Accessing the Service

Once running, the service will be available at:
- **Home (Collections)**: http://localhost:8001/
- **Health Check**: http://localhost:8001/health
- **List Specs**: http://localhost:8001/specs

## Adding New Specifications

1. Add your OpenAPI spec files (`.yaml`, `.yml`, or `.json`) to the `specs/` directory
2. If using Docker Compose, the specs are mounted as a volume and will be automatically discovered
3. If using Docker directly, restart the container to pick up new specs

## Configuration

The server runs on port 8001 by default. To change the port:

### Docker Compose
Edit `docker-compose.yml` and change the ports mapping:
```yaml
ports:
  - "YOUR_PORT:8001"
```

### Docker Direct
Change the port mapping in the docker run command:
```bash
docker run -p YOUR_PORT:8001 ...
```

## Health Check

The container includes a health check that verifies the service is responding:
- Endpoint: `/health`
- Interval: 30 seconds
- Timeout: 3 seconds
- Retries: 3

## Security

The container runs as a non-root user (`app`) for security best practices.
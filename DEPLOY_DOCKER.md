# Docker deployment (frontend + backend)

## Prereqs
- Docker 24+
- Slack Bot Token (xoxb-…)

## Backend (Flask)
Build:
```
cd slack-query-tracker-4410/flask_backend
docker build -t sqt-backend:latest .
```
Run (JSON storage volume mounted):
```
docker run -d --name sqt-backend -p 5000:5000 \
  -e FLASK_ENV=production \
  -e PORT=5000 \
  -e FRONTEND_ORIGIN=https://your-frontend-domain.com \
  -e SLACK_BOT_TOKEN=your_xoxb_token \
  -e STORAGE_BACKEND=json \
  -e STORAGE_FILE=data/queries.json \
  -v sqt_data:/app/data \
  sqt-backend:latest
```

## Frontend (React + Nginx)
Build:
```
cd slack-query-tracker-4410/react_frontend
# Ensure REACT_APP_API_BASE is set for the build environment, e.g.
# export REACT_APP_API_BASE=https://api.yourdomain.com
docker build -t sqt-frontend:latest .
```
Run (proxying /api to backend service name `backend`):
```
# If running locally with Docker alone, link to backend container using a user-defined network
# Create network once: docker network create sqt-net
# Start backend on that network: docker run --network sqt-net --name backend ... sqt-backend:latest
# Then run frontend:
docker run -d --name sqt-frontend --network sqt-net -p 80:80 sqt-frontend:latest
```

## docker-compose (optional)
Create docker-compose.yml at repo root:
```
version: "3.9"
services:
  backend:
    build: ./slack-query-tracker-4410/flask_backend
    container_name: backend
    environment:
      - FLASK_ENV=production
      - PORT=5000
      - FRONTEND_ORIGIN=http://localhost
      - SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
      - STORAGE_BACKEND=json
      - STORAGE_FILE=data/queries.json
    volumes:
      - sqt_data:/app/data
    ports:
      - "5000:5000"
  frontend:
    build: ./slack-query-tracker-4410/react_frontend
    container_name: frontend
    depends_on:
      - backend
    ports:
      - "80:80"
volumes:
  sqt_data:
```
Note: The frontend nginx.conf proxies /api to http://backend:5000.

## Production tips
- Use a real domain and TLS (Caddy/Traefik/Nginx as reverse proxy)
- Set FRONTEND_ORIGIN to your frontend URL on backend
- Keep SLACK_BOT_TOKEN in your secret manager
- Consider adding /api/health and rate limiting

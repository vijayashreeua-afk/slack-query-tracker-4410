## Frontend Dockerfile (multi-stage)
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# REACT_APP_API_BASE should be provided at build time by CI/platform envs
RUN npm run build

FROM nginx:1.27-alpine
# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Copy build artifacts
COPY --from=build /app/build /usr/share/nginx/html
# Non-root is optional; nginx runs as nginx user by default on alpine image
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost/ || exit 1
CMD ["nginx", "-g", "daemon off;"]

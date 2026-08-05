# syntax=docker/dockerfile:1.7
FROM node:24-alpine AS build

WORKDIR /app

COPY apps/web_app/package.json apps/web_app/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY apps/web_app ./
ARG VITE_CORE_API_URL=/api
ENV VITE_CORE_API_URL=${VITE_CORE_API_URL}
RUN npm run build

FROM nginx:1.27-alpine AS runtime

COPY deploy/nginx/web-app.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1:8080/ >/dev/null || exit 1

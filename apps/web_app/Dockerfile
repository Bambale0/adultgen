FROM node:22-alpine AS build

WORKDIR /app
COPY apps/web_app/package.json ./package.json
RUN npm install
COPY apps/web_app/ ./

ARG VITE_CORE_API_URL=/api
ARG VITE_GOOGLE_CLIENT_ID=
ARG VITE_TELEGRAM_BOT_USERNAME=
ENV VITE_CORE_API_URL=$VITE_CORE_API_URL
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
ENV VITE_TELEGRAM_BOT_USERNAME=$VITE_TELEGRAM_BOT_USERNAME
RUN npm run build

FROM nginx:1.27-alpine
COPY apps/web_app/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD wget -qO- http://127.0.0.1:8080/healthz || exit 1

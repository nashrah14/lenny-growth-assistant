# Frontend Multi-Stage Dockerfile for The Lenny Growth Assistant
FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json* /app/
RUN npm install

COPY frontend/ /app/
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Custom nginx configuration for SPA routing & API reverse proxy
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
    location /api/ { \
        proxy_pass http://backend:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

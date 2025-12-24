# ============================================================================
# Voice Journal UI - Dockerfile
# ============================================================================
# Nginx-based container for serving static frontend files
# Proxies /api requests to the backend Container App
# ============================================================================

FROM nginx:alpine

# Install envsubst for environment variable substitution
RUN apk add --no-cache gettext

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy nginx configuration template
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Copy static files
COPY . /usr/share/nginx/html

# Remove files that shouldn't be served
RUN rm -f /usr/share/nginx/html/Dockerfile \
    /usr/share/nginx/html/nginx.conf \
    /usr/share/nginx/html/*.md 2>/dev/null || true

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

# Start nginx with environment variable substitution
# API_URL and API_HOST will be substituted at runtime
CMD ["/bin/sh", "-c", "envsubst '${API_URL} ${API_HOST}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]

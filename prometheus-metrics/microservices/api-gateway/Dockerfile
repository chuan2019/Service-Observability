FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/nginx.conf

# Copy custom nginx configuration
COPY api-gateway/nginx.conf /etc/nginx/nginx.conf

# Create directory for logs
RUN mkdir -p /var/log/nginx

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
FROM nginx:alpine

# Install gettext (for envsubst) - not needed in this case
# RUN apk add --no-cache gettext

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom configuration to the correct location
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

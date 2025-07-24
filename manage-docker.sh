#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display script usage
show_usage() {
    echo -e "${YELLOW}Usage:${NC}"
    echo "  ./manage-docker.sh [command]"
    echo ""
    echo -e "${YELLOW}Available commands:${NC}"
    echo "  start         - Start all services"
    echo "  stop          - Stop all services"
    echo "  restart       - Restart all services"
    echo "  rebuild       - Rebuild and restart all services"
    echo "  logs          - View logs from all services"
    echo "  status        - Check status of all services"
    echo "  clean         - Remove all containers, volumes, and images"
    echo "  reload-nginx  - Reload Nginx configuration"
    echo "  db-status    - Check database health"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running${NC}"
        exit 1
    fi
}

# Function to start services
start_services() {
    echo -e "${GREEN}Starting services...${NC}"
    docker-compose up -d
    echo -e "${GREEN}Services started. Use 'logs' command to view logs${NC}"
}

# Function to stop services
stop_services() {
    echo -e "${YELLOW}Stopping services...${NC}"
    docker-compose down
    echo -e "${GREEN}Services stopped${NC}"
}

# Function to view logs
view_logs() {
    if [ "$1" ]; then
        docker-compose logs -f "$1"
    else
        docker-compose logs -f
    fi
}

# Function to check service status
check_status() {
    echo -e "${YELLOW}Checking service status...${NC}"
    docker-compose ps
}

# Function to check database health
check_db_health() {
    echo -e "${YELLOW}Checking PostgreSQL status...${NC}"
    if docker-compose exec postgres pg_isready -U postgres; then
        echo -e "${GREEN}PostgreSQL is healthy${NC}"
    else
        echo -e "${RED}PostgreSQL is not healthy${NC}"
    fi

    echo -e "\n${YELLOW}Checking Neo4j status...${NC}"
    if docker-compose exec neo4j wget --spider --quiet http://localhost:7474; then
        echo -e "${GREEN}Neo4j is healthy${NC}"
    else
        echo -e "${RED}Neo4j is not healthy${NC}"
    fi
}

# Function to clean Docker environment
clean_environment() {
    echo -e "${YELLOW}Warning: This will remove all containers, volumes, and images. Continue? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])+$ ]]; then
        echo -e "${YELLOW}Stopping all services...${NC}"
        docker-compose down -v
        echo -e "${YELLOW}Removing all related images...${NC}"
        docker rmi $(docker images -q) -f
        echo -e "${GREEN}Clean complete${NC}"
    fi
}

# Function to reload Nginx
reload_nginx() {
    echo -e "${YELLOW}Reloading Nginx configuration...${NC}"
    docker-compose exec nginx nginx -s reload
    echo -e "${GREEN}Nginx configuration reloaded${NC}"
}

# Main script logic
check_docker

case "$1" in
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        start_services
        ;;
    "rebuild")
        echo -e "${YELLOW}Rebuilding all services...${NC}"
        docker-compose down
        docker-compose build
        docker-compose up -d
        echo -e "${GREEN}Rebuild complete${NC}"
        ;;
    "logs")
        view_logs "$2"
        ;;
    "status")
        check_status
        ;;
    "clean")
        clean_environment
        ;;
    "reload-nginx")
        reload_nginx
        ;;
    "db-status")
        check_db_health
        ;;
    *)
        show_usage
        ;;
esac 
#!/bin/bash

# Internal Training System - Docker Quick Start Script
# This script helps you quickly start the application using Docker

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Config paths
CONFIG_FILE="deployment/config.toml"
ENV_RENDER_SCRIPT="deployment/render_env.py"

# Functions
print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

print_info() {
    echo -e "${GREEN}INFO: $1${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker is installed"
}

# Check if Docker Compose is installed
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_success "Docker Compose is installed"
}

# Check if Docker is running
check_docker_running() {
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

ensure_config_file() {
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Configuration file not found at $CONFIG_FILE"
        echo ""
        echo "Create one with:"
        echo "  cp deployment/config.example.toml $CONFIG_FILE"
        echo "  # Edit the file with your credentials"
        exit 1
    fi
}

generate_env_from_config() {
    ensure_config_file

    if [ ! -f "$ENV_RENDER_SCRIPT" ]; then
        print_error "Env render script missing at $ENV_RENDER_SCRIPT"
        exit 1
    fi

    print_info "Generating .env from $CONFIG_FILE..."
    if python3 "$ENV_RENDER_SCRIPT" --config "$CONFIG_FILE" --output .env; then
        print_success ".env generated from configuration file"
    else
        print_error "Failed to generate .env from $CONFIG_FILE"
        exit 1
    fi
}

# Check if .env file exists
check_env_file() {
    generate_env_from_config

    if [ ! -f .env ]; then
        print_error ".env file missing after attempting to generate from $CONFIG_FILE"
        exit 1
    else
        print_success ".env file ready"
    fi
}

# Display usage
usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  dev         Start development environment (default)"
    echo "  prod        Start production environment"
    echo "  stop        Stop all containers"
    echo "  restart     Restart all containers"
    echo "  logs        View logs (follow mode)"
    echo "  status      Show status of all containers"
    echo "  clean       Stop and remove all containers, volumes, and images"
    echo "  help        Display this help message"
    echo ""
}

# Start development environment
start_dev() {
    print_info "Starting development environment..."
    docker-compose up --build -d

    echo ""
    print_success "Development environment started!"
    echo ""
    echo "Access the application at:"
    echo "  - Frontend: http://localhost"
    echo "  - Backend API: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo ""
    echo "To view logs: ./docker-start.sh logs"
    echo "To stop: ./docker-start.sh stop"
}

# Start production environment
start_prod() {
    print_info "Starting production environment..."
    docker-compose -f docker-compose.prod.yml up --build -d

    echo ""
    print_success "Production environment started!"
    echo ""
    echo "Access the application at:"
    echo "  - Frontend: http://localhost"
    echo "  - Backend API: http://localhost/api"
    echo ""
    echo "To view logs: ./docker-start.sh logs"
    echo "To stop: ./docker-start.sh stop"
}

# Stop containers
stop_containers() {
    print_info "Stopping containers..."

    if [ -f docker-compose.prod.yml ] && docker-compose -f docker-compose.prod.yml ps -q &> /dev/null; then
        docker-compose -f docker-compose.prod.yml down
    fi

    if docker-compose ps -q &> /dev/null; then
        docker-compose down
    fi

    print_success "Containers stopped"
}

# Restart containers
restart_containers() {
    print_info "Restarting containers..."

    if [ -f docker-compose.prod.yml ] && docker-compose -f docker-compose.prod.yml ps -q &> /dev/null; then
        docker-compose -f docker-compose.prod.yml restart
    else
        docker-compose restart
    fi

    print_success "Containers restarted"
}

# View logs
view_logs() {
    print_info "Viewing logs (Ctrl+C to exit)..."

    if [ -f docker-compose.prod.yml ] && docker-compose -f docker-compose.prod.yml ps -q &> /dev/null; then
        docker-compose -f docker-compose.prod.yml logs -f
    else
        docker-compose logs -f
    fi
}

# Show status
show_status() {
    print_info "Container status:"
    echo ""

    if [ -f docker-compose.prod.yml ] && docker-compose -f docker-compose.prod.yml ps -q &> /dev/null; then
        docker-compose -f docker-compose.prod.yml ps
    else
        docker-compose ps
    fi
}

# Clean everything
clean_all() {
    print_warning "This will remove all containers, volumes, and images for this project."
    echo "Are you sure? (yes/no)"
    read -r response

    if [[ "$response" == "yes" ]]; then
        print_info "Cleaning up..."

        # Stop and remove containers, volumes
        if [ -f docker-compose.prod.yml ]; then
            docker-compose -f docker-compose.prod.yml down -v --rmi all 2>/dev/null || true
        fi
        docker-compose down -v --rmi all 2>/dev/null || true

        print_success "Cleanup complete"
    else
        print_info "Cleanup cancelled"
    fi
}

# Main script
main() {
    echo "================================================"
    echo "  Internal Training System - Docker Manager"
    echo "================================================"
    echo ""

    # Parse command
    COMMAND=${1:-dev}

    case $COMMAND in
        dev)
            check_docker
            check_docker_compose
            check_docker_running
            check_env_file
            start_dev
            ;;
        prod)
            check_docker
            check_docker_compose
            check_docker_running
            check_env_file
            start_prod
            ;;
        stop)
            check_docker
            check_docker_running
            stop_containers
            ;;
        restart)
            check_docker
            check_docker_running
            restart_containers
            ;;
        logs)
            check_docker
            check_docker_running
            view_logs
            ;;
        status)
            check_docker
            check_docker_running
            show_status
            ;;
        clean)
            check_docker
            check_docker_running
            clean_all
            ;;
        help)
            usage
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            echo ""
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

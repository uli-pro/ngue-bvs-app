#!/bin/bash
# =============================================================================
# NGÜ App Automated Deployment Script
# =============================================================================
# 
# This script automates the deployment process for the NGÜ Bibelvers-Sponsoring
# App on your homeserver. It handles initial setup, updates, and rollbacks.
#
# Usage:
#   ./deploy.sh init                 # Initial deployment setup
#   ./deploy.sh deploy [--force]     # Deploy/update application
#   ./deploy.sh rollback             # Rollback to previous version
#   ./deploy.sh status               # Show deployment status
#   ./deploy.sh logs [service]       # Show logs
#   ./deploy.sh health               # Health check
#   ./deploy.sh restart [service]    # Restart services
#   ./deploy.sh stop                 # Stop all services
#   ./deploy.sh cleanup              # Cleanup unused resources
#
# =============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="ngue-app"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
ENV_FILE="${SCRIPT_DIR}/.env"
BACKUP_SCRIPT="${SCRIPT_DIR}/backup-and-restore.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Check if running as root
check_not_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        exit 1
    fi
}

# Check if Docker is available and running
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon not running or permission denied"
        log_info "Try: sudo systemctl start docker"
        log_info "Or add your user to docker group: sudo usermod -aG docker \$USER"
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose not found. Please install Docker Compose v2."
        exit 1
    fi
}

# Check if in correct directory
check_directory() {
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "docker-compose.yml not found in current directory"
        log_info "Please run this script from the app-deployment directory"
        exit 1
    fi
}

# Load and validate environment variables
load_env() {
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error ".env file not found"
        log_info "Please copy .env.example to .env and configure it first"
        log_info "cp .env.example .env && nano .env"
        exit 1
    fi
    
    source "$ENV_FILE"
    
    # Validate critical environment variables
    local required_vars=(
        "DOMAIN_NAME"
        "SECRET_KEY"
        "POSTGRES_DB"
        "POSTGRES_USER"
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "STRIPE_PUBLIC_KEY"
        "STRIPE_SECRET_KEY"
        "CLOUDFLARE_DNS_API_TOKEN"
    )
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables:"
        printf '%s\n' "${missing_vars[@]}"
        exit 1
    fi
}

# Check if ports are available
check_ports() {
    local ports=("8090" "8091")
    
    for port in "${ports[@]}"; do
        if netstat -tln 2>/dev/null | grep -q ":${port} "; then
            log_warning "Port $port is already in use"
            log_info "This might be from a previous deployment"
        fi
    done
}

# Create required directories
create_directories() {
    log_step "Creating required directories"
    
    local directories=(
        "${SCRIPT_DIR}/traefik/letsencrypt"
        "${SCRIPT_DIR}/backups"
        "${SCRIPT_DIR}/logs"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_info "Created directory: $dir"
    done
    
    # Set proper permissions for Let's Encrypt directory
    chmod 600 "${SCRIPT_DIR}/traefik/letsencrypt" 2>/dev/null || true
}

# Initialize deployment (first-time setup)
init_deployment() {
    log_step "Initializing NGÜ app deployment"
    
    check_not_root
    check_docker
    check_directory
    create_directories
    
    # Check if .env exists, if not copy from example
    if [[ ! -f "$ENV_FILE" ]]; then
        log_info "Copying .env.example to .env"
        cp "${ENV_FILE}.example" "$ENV_FILE"
        log_warning "Please edit .env file and configure all required variables"
        log_info "Then run: ./deploy.sh deploy"
        exit 0
    fi
    
    load_env
    check_ports
    
    # Pull required images
    log_step "Pulling Docker images"
    docker compose -f "$COMPOSE_FILE" pull
    
    # Create networks and volumes
    log_step "Creating Docker networks and volumes"
    docker compose -f "$COMPOSE_FILE" up --no-start
    
    # Initialize database
    log_step "Initializing database"
    docker compose -f "$COMPOSE_FILE" up -d postgres redis
    
    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    local retries=30
    while [[ $retries -gt 0 ]]; do
        if docker compose -f "$COMPOSE_FILE" exec postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" &>/dev/null; then
            break
        fi
        ((retries--))
        sleep 2
    done
    
    if [[ $retries -eq 0 ]]; then
        log_error "PostgreSQL failed to start"
        exit 1
    fi
    
    # Run database initialization
    log_step "Running database setup"
    if docker compose -f "$COMPOSE_FILE" run --rm ngue-app python /app/app-deployment/setup_db.py; then
        log_success "Database setup completed"
        
        log_step "Running verse vectorization (this may take 5-10 minutes)..."
        log_info "This process creates embeddings for semantic search functionality"
        
        if docker compose -f "$COMPOSE_FILE" run --rm ngue-app python /app/app-deployment/vectorize.py; then
            log_success "Vectorization completed successfully"
            log_info "✅ NGÜ app is now ready with full search functionality!"
        else
            log_error "Vectorization failed - app will have limited search functionality"
            log_error "❌ The app requires vectorization to function properly"
            exit 1
        fi
    else
        log_error "Database setup failed"
        exit 1
    fi
    
    # Start all services
    log_step "Starting all services"
    docker compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be healthy
    wait_for_health
    
    log_success "Initial deployment completed!"
    log_info "Application URL: https://${DOMAIN_NAME}"
    log_info "Check status with: ./deploy.sh status"
}

# Deploy or update application
deploy() {
    local force="${1:-false}"
    
    log_step "Deploying NGÜ app"
    
    check_not_root
    check_docker
    check_directory
    load_env
    
    # Create backup before deployment if system is running
    if docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        if [[ "$force" != "true" ]]; then
            log_step "Creating backup before deployment"
            if [[ -x "$BACKUP_SCRIPT" ]]; then
                "$BACKUP_SCRIPT" backup --compress
            else
                log_warning "Backup script not executable, skipping backup"
            fi
        else
            log_warning "Force deployment - skipping backup"
        fi
    fi
    
    # Pull latest images
    log_step "Pulling latest Docker images"
    docker compose -f "$COMPOSE_FILE" pull
    
    # Rebuild application image
    log_step "Building application image"
    docker compose -f "$COMPOSE_FILE" build --no-cache ngue-app
    
    # Deploy with minimal downtime
    log_step "Deploying services"
    docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
    
    # Wait for health checks
    wait_for_health
    
    # Cleanup unused images and volumes
    cleanup_docker_resources
    
    log_success "Deployment completed!"
    show_status
}

# Wait for services to be healthy
wait_for_health() {
    log_info "Waiting for services to be healthy..."
    
    local services=("postgres" "redis" "ngue-app" "traefik")
    local max_wait=300  # 5 minutes
    local elapsed=0
    
    while [[ $elapsed -lt $max_wait ]]; do
        local all_healthy=true
        
        for service in "${services[@]}"; do
            local status=$(docker compose -f "$COMPOSE_FILE" ps --format "table" | grep "$service" | awk '{print $5}' || echo "")
            
            if [[ "$status" != "healthy" ]] && [[ "$status" != "Up" ]]; then
                all_healthy=false
                break
            fi
        done
        
        if [[ "$all_healthy" == "true" ]]; then
            log_success "All services are healthy"
            return 0
        fi
        
        sleep 10
        ((elapsed+=10))
        log_info "Still waiting... (${elapsed}s/${max_wait}s)"
    done
    
    log_warning "Health check timeout reached"
    show_service_status
}

# Show deployment status
show_status() {
    log_step "Deployment Status"
    
    check_docker
    check_directory
    
    echo ""
    echo "🐳 Docker Services:"
    docker compose -f "$COMPOSE_FILE" ps
    
    echo ""
    echo "💾 Docker Volumes:"
    docker compose -f "$COMPOSE_FILE" config --volumes
    
    echo ""
    echo "🌐 Network Status:"
    docker compose -f "$COMPOSE_FILE" exec ngue-app curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:5000/health || echo "App health check failed"
    
    echo ""
    echo "📊 Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker compose -f "$COMPOSE_FILE" ps -q) 2>/dev/null || echo "Unable to get stats"
    
    echo ""
    if [[ -f "$ENV_FILE" ]]; then
        source "$ENV_FILE"
        echo "🌍 Application URL: https://${DOMAIN_NAME}"
        echo "🔒 SSL Certificate: $(check_ssl_cert)"
    fi
}

# Check SSL certificate status
check_ssl_cert() {
    if [[ -z "${DOMAIN_NAME:-}" ]]; then
        echo "Not configured"
        return
    fi
    
    local cert_info=$(echo | openssl s_client -servername "$DOMAIN_NAME" -connect "$DOMAIN_NAME:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "")
    
    if [[ -n "$cert_info" ]]; then
        local expiry=$(echo "$cert_info" | grep "notAfter" | cut -d= -f2)
        echo "Valid until $expiry"
    else
        echo "Certificate check failed"
    fi
}

# Show service status
show_service_status() {
    local services=("traefik" "postgres" "redis" "ngue-app")
    
    echo ""
    echo "🔍 Service Health Status:"
    for service in "${services[@]}"; do
        local status=$(docker compose -f "$COMPOSE_FILE" ps --filter "service=$service" --format "{{.Status}}")
        local health=$(docker compose -f "$COMPOSE_FILE" ps --filter "service=$service" --format "{{.Health}}")
        
        if [[ -n "$status" ]]; then
            echo "  $service: $status $([ -n "$health" ] && echo "($health)")"
        else
            echo "  $service: Not running"
        fi
    done
}

# Show logs
show_logs() {
    local service="${1:-}"
    
    check_docker
    check_directory
    
    if [[ -n "$service" ]]; then
        log_info "Showing logs for $service"
        docker compose -f "$COMPOSE_FILE" logs -f --tail=100 "$service"
    else
        log_info "Showing logs for all services"
        docker compose -f "$COMPOSE_FILE" logs -f --tail=50
    fi
}

# Health check
health_check() {
    log_step "Running health checks"
    
    check_docker
    check_directory
    load_env
    
    local checks_passed=0
    local total_checks=5
    
    # Check 1: Docker services
    echo -n "🐳 Docker services... "
    if docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        echo "✅"
        ((checks_passed++))
    else
        echo "❌"
    fi
    
    # Check 2: Database connection
    echo -n "💾 Database connection... "
    if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" &>/dev/null; then
        echo "✅"
        ((checks_passed++))
    else
        echo "❌"
    fi
    
    # Check 3: Application health
    echo -n "🖥️  Application health... "
    if docker compose -f "$COMPOSE_FILE" exec -T ngue-app curl -s -f http://localhost:5000/health &>/dev/null; then
        echo "✅"
        ((checks_passed++))
    else
        echo "❌"
    fi
    
    # Check 4: SSL certificate
    echo -n "🔒 SSL certificate... "
    if curl -s -I "https://${DOMAIN_NAME}" | grep -q "HTTP/2 200\|HTTP/1.1 200"; then
        echo "✅"
        ((checks_passed++))
    else
        echo "❌"
    fi
    
    # Check 5: Disk space
    echo -n "💿 Disk space... "
    local disk_usage=$(df "$SCRIPT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    if [[ $disk_usage -lt 80 ]]; then
        echo "✅ (${disk_usage}% used)"
        ((checks_passed++))
    else
        echo "❌ (${disk_usage}% used - getting full!)"
    fi
    
    echo ""
    echo "📊 Health Summary: $checks_passed/$total_checks checks passed"
    
    if [[ $checks_passed -eq $total_checks ]]; then
        log_success "All health checks passed!"
        return 0
    else
        log_warning "Some health checks failed"
        return 1
    fi
}

# Restart services
restart_services() {
    local service="${1:-}"
    
    check_docker
    check_directory
    
    if [[ -n "$service" ]]; then
        log_info "Restarting $service"
        docker compose -f "$COMPOSE_FILE" restart "$service"
    else
        log_info "Restarting all services"
        docker compose -f "$COMPOSE_FILE" restart
    fi
    
    wait_for_health
    log_success "Services restarted successfully"
}

# Stop all services
stop_services() {
    log_step "Stopping all services"
    
    check_docker
    check_directory
    
    docker compose -f "$COMPOSE_FILE" down
    
    log_success "All services stopped"
}

# Cleanup unused Docker resources
cleanup_docker_resources() {
    log_step "Cleaning up unused Docker resources"
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (but keep named volumes)
    docker volume prune -f
    
    # Remove unused networks
    docker network prune -f
    
    log_success "Docker cleanup completed"
}

# Rollback to previous version
rollback() {
    log_step "Rolling back to previous version"
    
    check_docker
    check_directory
    load_env
    
    # Find latest backup
    local latest_backup=$(ls -t "${SCRIPT_DIR}/backups/"ngue_backup_*.sql* 2>/dev/null | head -1)
    
    if [[ -z "$latest_backup" ]]; then
        log_error "No backup found for rollback"
        exit 1
    fi
    
    log_info "Rolling back using backup: $latest_backup"
    
    # Confirm rollback
    read -p "⚠️  This will restore the database from backup. Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Rollback cancelled"
        exit 0
    fi
    
    # Perform rollback
    if [[ -x "$BACKUP_SCRIPT" ]]; then
        "$BACKUP_SCRIPT" restore "$latest_backup"
    else
        log_error "Backup script not found or not executable"
        exit 1
    fi
    
    log_success "Rollback completed"
}

# Main function
main() {
    local command="${1:-}"
    
    case "$command" in
        "init")
            init_deployment
            ;;
        "deploy")
            local force="false"
            if [[ "${2:-}" == "--force" ]]; then
                force="true"
            fi
            deploy "$force"
            ;;
        "rollback")
            rollback
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "${2:-}"
            ;;
        "health")
            health_check
            ;;
        "restart")
            restart_services "${2:-}"
            ;;
        "stop")
            stop_services
            ;;
        "cleanup")
            cleanup_docker_resources
            ;;
        *)
            echo "🚀 NGÜ App Deployment Script"
            echo ""
            echo "Usage:"
            echo "  $0 init                    Initial deployment setup"
            echo "  $0 deploy [--force]        Deploy/update application"
            echo "  $0 rollback                Rollback to previous version"
            echo "  $0 status                  Show deployment status"
            echo "  $0 logs [service]          Show logs (all or specific service)"
            echo "  $0 health                  Run health checks"
            echo "  $0 restart [service]       Restart services (all or specific)"
            echo "  $0 stop                    Stop all services"
            echo "  $0 cleanup                 Cleanup unused Docker resources"
            echo ""
            echo "Examples:"
            echo "  $0 init                    # First-time setup"
            echo "  $0 deploy                  # Regular deployment"
            echo "  $0 logs ngue-app           # Show app logs"
            echo "  $0 restart postgres        # Restart database"
            echo ""
            echo "Services: traefik, postgres, redis, ngue-app, nginx"
            echo ""
            exit 1
            ;;
    esac
}

# Print banner
echo "🚀 NGÜ Bibelvers-Sponsoring App - Deployment Script"
echo "=================================================="
echo ""

# Run main function with all arguments
main "$@"
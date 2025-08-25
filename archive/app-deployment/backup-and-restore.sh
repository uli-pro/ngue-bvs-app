#!/bin/bash
# =============================================================================
# NGÜ App Backup and Restore Script
# =============================================================================
# 
# This script provides comprehensive backup and restore functionality for
# the NGÜ Bibelvers-Sponsoring App Docker deployment.
#
# Usage:
#   ./backup-and-restore.sh backup [--compress]
#   ./backup-and-restore.sh restore <backup-file>
#   ./backup-and-restore.sh list
#   ./backup-and-restore.sh cleanup [--keep 7]
#   ./backup-and-restore.sh auto-backup
#
# =============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/backups"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.yml"
ENV_FILE="${SCRIPT_DIR}/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker &> /dev/null || ! command -v docker compose &> /dev/null; then
        log_error "Docker or Docker Compose not found"
        exit 1
    fi
}

# Check if .env file exists
check_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error ".env file not found at $ENV_FILE"
        log_info "Please copy .env.example to .env and configure it"
        exit 1
    fi
}

# Load environment variables
load_env() {
    source "$ENV_FILE"
    
    # Validate required variables
    if [[ -z "${POSTGRES_DB:-}" ]] || [[ -z "${POSTGRES_USER:-}" ]] || [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
        log_error "Required database environment variables not set"
        exit 1
    fi
}

# Ensure backup directory exists
ensure_backup_dir() {
    mkdir -p "$BACKUP_DIR"
}

# Generate backup filename
generate_backup_name() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    echo "ngue_backup_${timestamp}"
}

# Check if PostgreSQL container is running
check_postgres_running() {
    if ! docker compose -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
        log_error "PostgreSQL container is not running"
        log_info "Start the stack with: docker compose up -d"
        exit 1
    fi
}

# Create database backup
backup_database() {
    local backup_name="$1"
    local compress="$2"
    
    log_info "Creating database backup: $backup_name"
    
    local backup_file="${BACKUP_DIR}/${backup_name}.sql"
    
    # Create database dump
    docker compose -f "$COMPOSE_FILE" exec -T postgres pg_dump \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --verbose \
        --clean \
        --if-exists \
        --create \
        --encoding=UTF8 \
        > "$backup_file"
    
    if [[ $? -eq 0 ]]; then
        log_success "Database backup created: $backup_file"
    else
        log_error "Database backup failed"
        return 1
    fi
    
    # Compress if requested
    if [[ "$compress" == "true" ]]; then
        log_info "Compressing backup..."
        gzip "$backup_file"
        backup_file="${backup_file}.gz"
        log_success "Backup compressed: $backup_file"
    fi
    
    return 0
}

# Backup application data
backup_app_data() {
    local backup_name="$1"
    
    log_info "Creating application data backup"
    
    local data_backup="${BACKUP_DIR}/${backup_name}_data.tar.gz"
    
    # Create tar of important application data
    docker compose -f "$COMPOSE_FILE" exec -T ngue-app tar czf - \
        -C /app \
        uploads \
        logs \
        certificates \
        2>/dev/null > "$data_backup" || true
    
    if [[ -f "$data_backup" ]] && [[ -s "$data_backup" ]]; then
        log_success "Application data backup created: $data_backup"
    else
        log_warning "No application data to backup or backup failed"
        rm -f "$data_backup"
    fi
}

# Backup volumes
backup_volumes() {
    local backup_name="$1"
    
    log_info "Creating volume backups"
    
    local volumes=(
        "postgres_data"
        "redis_data"
        "traefik_letsencrypt"
        "app_uploads"
        "app_logs"
        "app_certs"
    )
    
    for volume in "${volumes[@]}"; do
        local volume_backup="${BACKUP_DIR}/${backup_name}_${volume}.tar.gz"
        
        log_info "Backing up volume: $volume"
        
        docker run --rm \
            -v "$(basename "$SCRIPT_DIR")_${volume}:/data" \
            -v "$BACKUP_DIR:/backup" \
            alpine:latest \
            tar czf "/backup/$(basename "$volume_backup")" -C /data . \
            2>/dev/null || true
        
        if [[ -f "$volume_backup" ]] && [[ -s "$volume_backup" ]]; then
            log_success "Volume backup created: $volume_backup"
        else
            log_warning "Volume $volume is empty or backup failed"
            rm -f "$volume_backup"
        fi
    done
}

# Create configuration backup
backup_config() {
    local backup_name="$1"
    
    log_info "Creating configuration backup"
    
    local config_backup="${BACKUP_DIR}/${backup_name}_config.tar.gz"
    
    # Backup configuration files (excluding sensitive .env)
    tar czf "$config_backup" \
        -C "$SCRIPT_DIR" \
        docker-compose.yml \
        Dockerfile \
        .env.example \
        traefik/ \
        nginx/ \
        init-scripts/ \
        2>/dev/null || true
    
    if [[ -f "$config_backup" ]] && [[ -s "$config_backup" ]]; then
        log_success "Configuration backup created: $config_backup"
    else
        log_warning "Configuration backup failed"
        rm -f "$config_backup"
    fi
}

# Full backup function
full_backup() {
    local compress="$1"
    
    check_docker_compose
    check_env_file
    load_env
    ensure_backup_dir
    check_postgres_running
    
    local backup_name=$(generate_backup_name)
    
    log_info "Starting full backup: $backup_name"
    log_info "Compress: $compress"
    
    # Create manifest file
    local manifest="${BACKUP_DIR}/${backup_name}_manifest.txt"
    cat > "$manifest" << EOF
NGÜ App Backup Manifest
======================
Backup Name: $backup_name
Created: $(date)
Docker Compose Project: $(basename "$SCRIPT_DIR")
Database: $POSTGRES_DB
User: $POSTGRES_USER

Files in this backup set:
EOF
    
    # Perform backups
    local backup_success=true
    
    # Database backup
    if backup_database "$backup_name" "$compress"; then
        echo "- Database: ${backup_name}.sql$([ "$compress" == "true" ] && echo ".gz")" >> "$manifest"
    else
        backup_success=false
    fi
    
    # Application data backup
    backup_app_data "$backup_name"
    if [[ -f "${BACKUP_DIR}/${backup_name}_data.tar.gz" ]]; then
        echo "- Application Data: ${backup_name}_data.tar.gz" >> "$manifest"
    fi
    
    # Volume backups
    backup_volumes "$backup_name"
    for volume_file in "${BACKUP_DIR}/${backup_name}"_*_*.tar.gz; do
        if [[ -f "$volume_file" ]]; then
            echo "- Volume: $(basename "$volume_file")" >> "$manifest"
        fi
    done
    
    # Configuration backup
    backup_config "$backup_name"
    if [[ -f "${BACKUP_DIR}/${backup_name}_config.tar.gz" ]]; then
        echo "- Configuration: ${backup_name}_config.tar.gz" >> "$manifest"
    fi
    
    # Final status
    if [[ "$backup_success" == "true" ]]; then
        log_success "Full backup completed: $backup_name"
        log_info "Manifest: $manifest"
        
        # Show backup size
        local total_size=$(du -sh "${BACKUP_DIR}/${backup_name}"* | awk '{sum+=$1} END {print sum}' 2>/dev/null || echo "unknown")
        log_info "Total backup size: $total_size"
    else
        log_error "Backup completed with errors"
        exit 1
    fi
}

# Restore database
restore_database() {
    local backup_file="$1"
    
    log_info "Restoring database from: $backup_file"
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi
    
    # Determine if file is compressed
    local is_compressed=false
    if [[ "$backup_file" == *.gz ]]; then
        is_compressed=true
    fi
    
    # Stop application to prevent connections during restore
    log_info "Stopping application containers..."
    docker compose -f "$COMPOSE_FILE" stop ngue-app db-init 2>/dev/null || true
    
    # Wait a moment for connections to close
    sleep 5
    
    # Restore database
    if [[ "$is_compressed" == "true" ]]; then
        zcat "$backup_file" | docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U "$POSTGRES_USER" -d postgres
    else
        cat "$backup_file" | docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U "$POSTGRES_USER" -d postgres
    fi
    
    if [[ $? -eq 0 ]]; then
        log_success "Database restored successfully"
        
        # Restart application
        log_info "Restarting application..."
        docker compose -f "$COMPOSE_FILE" up -d
        
        return 0
    else
        log_error "Database restore failed"
        return 1
    fi
}

# List available backups
list_backups() {
    ensure_backup_dir
    
    log_info "Available backups in $BACKUP_DIR:"
    
    if [[ ! "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]]; then
        log_warning "No backups found"
        return 0
    fi
    
    # Group backups by name
    local backup_names=($(ls "$BACKUP_DIR" | grep -o 'ngue_backup_[0-9_]*' | sort -u))
    
    for backup_name in "${backup_names[@]}"; do
        echo ""
        echo "📦 $backup_name"
        echo "   Created: $(echo "$backup_name" | sed 's/ngue_backup_//' | sed 's/_/ /' | sed 's/\(..\)\(..\)\(..\)/20\1-\2-\3 /')"
        
        local files=($(ls "$BACKUP_DIR" | grep "^$backup_name"))
        local total_size=0
        
        for file in "${files[@]}"; do
            local size=$(du -h "${BACKUP_DIR}/$file" 2>/dev/null | cut -f1)
            echo "   - $file ($size)"
        done
        
        # Show manifest if available
        local manifest="${BACKUP_DIR}/${backup_name}_manifest.txt"
        if [[ -f "$manifest" ]]; then
            echo "   📄 Manifest available"
        fi
    done
}

# Cleanup old backups
cleanup_backups() {
    local keep_count="$1"
    
    ensure_backup_dir
    
    log_info "Cleaning up old backups (keeping $keep_count most recent)"
    
    # Get unique backup names sorted by date (newest first)
    local backup_names=($(ls "$BACKUP_DIR" | grep -o 'ngue_backup_[0-9_]*' | sort -r | uniq))
    
    if [[ ${#backup_names[@]} -le $keep_count ]]; then
        log_info "No cleanup needed (${#backup_names[@]} backups, keeping $keep_count)"
        return 0
    fi
    
    # Remove old backups
    local removed_count=0
    for ((i=keep_count; i<${#backup_names[@]}; i++)); do
        local backup_name="${backup_names[$i]}"
        log_info "Removing old backup: $backup_name"
        
        rm -f "${BACKUP_DIR}/${backup_name}"*
        ((removed_count++))
    done
    
    log_success "Cleaned up $removed_count old backup sets"
}

# Auto backup with rotation
auto_backup() {
    log_info "Running automatic backup with rotation"
    
    # Create backup
    full_backup "true"
    
    # Cleanup old backups (keep 7 by default)
    local keep_count="${BACKUP_RETENTION_DAYS:-7}"
    cleanup_backups "$keep_count"
    
    log_success "Automatic backup completed"
}

# Main function
main() {
    local command="${1:-}"
    
    case "$command" in
        "backup")
            local compress="false"
            if [[ "${2:-}" == "--compress" ]]; then
                compress="true"
            fi
            full_backup "$compress"
            ;;
        "restore")
            local backup_file="${2:-}"
            if [[ -z "$backup_file" ]]; then
                log_error "Please specify backup file to restore"
                exit 1
            fi
            
            check_docker_compose
            check_env_file
            load_env
            check_postgres_running
            
            restore_database "$backup_file"
            ;;
        "list")
            list_backups
            ;;
        "cleanup")
            local keep_count="7"
            if [[ "${2:-}" == "--keep" ]] && [[ -n "${3:-}" ]]; then
                keep_count="$3"
            fi
            cleanup_backups "$keep_count"
            ;;
        "auto-backup")
            auto_backup
            ;;
        *)
            echo "NGÜ App Backup and Restore Tool"
            echo ""
            echo "Usage:"
            echo "  $0 backup [--compress]     Create full backup"
            echo "  $0 restore <backup-file>   Restore from backup"
            echo "  $0 list                    List available backups"
            echo "  $0 cleanup [--keep N]      Clean old backups (keep N, default 7)"
            echo "  $0 auto-backup             Automatic backup with rotation"
            echo ""
            echo "Examples:"
            echo "  $0 backup --compress"
            echo "  $0 restore backups/ngue_backup_20240824_143000.sql.gz"
            echo "  $0 cleanup --keep 5"
            echo ""
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
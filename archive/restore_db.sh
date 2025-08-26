#!/bin/bash

# NGÜ Database Restore Script
# Usage: ./restore_db.sh [backup_file.sql]

# Configuration
DB_NAME="ngue_bvs_db"
BACKUP_DIR="./backups"

# Function to show available backups
show_backups() {
    echo "Available backups:"
    if ls "$BACKUP_DIR"/*.sql 1> /dev/null 2>&1; then
        ls -lt "$BACKUP_DIR"/*.sql | nl -w2 -s'. ' | awk '{print $1 $2 " " $(NF) " (" $(NF-4) ", " $(NF-3) " " $(NF-2) " " $(NF-1) ")"}'
    else
        echo "   No backups found in $BACKUP_DIR/"
    fi
}

# Check if backup file is provided
if [ -n "$1" ]; then
    BACKUP_FILE="$1"
elif [ -d "$BACKUP_DIR" ] && ls "$BACKUP_DIR"/*.sql 1> /dev/null 2>&1; then
    echo "No backup file specified. Please choose:"
    echo ""
    show_backups
    echo ""
    read -p "Enter backup number or full path: " CHOICE
    
    if [[ "$CHOICE" =~ ^[0-9]+$ ]]; then
        # User entered a number
        BACKUP_FILE=$(ls -lt "$BACKUP_DIR"/*.sql | sed -n "${CHOICE}p" | awk '{print $NF}')
    else
        # User entered a path
        BACKUP_FILE="$CHOICE"
    fi
else
    echo "❌ No backup file specified and no backups found in $BACKUP_DIR/"
    echo "Usage: $0 [backup_file.sql]"
    exit 1
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Restoring database '$DB_NAME' from: $BACKUP_FILE"
echo ""

# Show current database stats before restore
echo "Current database status:"
CURRENT_VERSES=$(psql -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM verses;" 2>/dev/null | xargs)
if [ $? -eq 0 ]; then
    echo "   Current verses in database: $CURRENT_VERSES"
else
    echo "   Database connection failed or verses table doesn't exist"
fi

echo ""
read -p "⚠️  This will REPLACE all data in '$DB_NAME'. Continue? (y/N): " CONFIRM

if [[ "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Dropping existing database..."
    dropdb "$DB_NAME" 2>/dev/null
    
    echo "Creating fresh database..."
    createdb "$DB_NAME"
    
    echo "Restoring data from backup..."
    if psql "$DB_NAME" < "$BACKUP_FILE" > /dev/null 2>&1; then
        echo "✅ Database successfully restored!"
        
        # Verify restoration
        NEW_VERSES=$(psql -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM verses;" 2>/dev/null | xargs)
        if [ $? -eq 0 ]; then
            echo "   Verses in restored database: $NEW_VERSES"
        fi
        
        # Show backup info
        BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
        BACKUP_DATE=$(ls -l "$BACKUP_FILE" | awk '{print $6 " " $7 " " $8}')
        echo "   Restored from: $(basename "$BACKUP_FILE") ($BACKUP_SIZE, $BACKUP_DATE)"
        
    else
        echo "❌ Restore failed!"
        exit 1
    fi
else
    echo "Restore cancelled."
    exit 0
fi
#!/bin/bash

# NGÜ Database Backup Script
# Usage: ./backup_db.sh [description]

# Configuration
DB_NAME="ngue_bvs_db"
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Get optional description from command line
DESCRIPTION="$1"
if [ -n "$DESCRIPTION" ]; then
    FILENAME="${BACKUP_DIR}/ngue_backup_${TIMESTAMP}_${DESCRIPTION}.sql"
else
    FILENAME="${BACKUP_DIR}/ngue_backup_${TIMESTAMP}.sql"
fi

# Create backup
echo "Creating backup of database '$DB_NAME'..."
echo "Backup file: $FILENAME"

if pg_dump "$DB_NAME" > "$FILENAME"; then
    echo "✅ Backup successfully created!"
    
    # Show file size
    SIZE=$(ls -lh "$FILENAME" | awk '{print $5}')
    echo "   File size: $SIZE"
    
    # Count verses in backup (for verification)
    VERSE_COUNT=$(grep -c "INSERT INTO verses" "$FILENAME" 2>/dev/null || echo "N/A")
    echo "   Verses in backup: $VERSE_COUNT"
    
    # Show recent backups
    echo ""
    echo "Recent backups:"
    ls -lt "$BACKUP_DIR"/*.sql 2>/dev/null | head -5 | awk '{print "   " $9 " (" $5 ", " $6 " " $7 " " $8 ")"}'
    
else
    echo "❌ Backup failed!"
    exit 1
fi
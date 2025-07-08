#!/bin/sh
# Database backup script for Voice Agent

# Configuration
BACKUP_DIR="/backup"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="voice_agent_backup_${TIMESTAMP}.sql.gz"

# Create backup directory if it doesn't exist
mkdir -p ${BACKUP_DIR}

# Perform database backup
echo "Starting database backup at $(date)"
pg_dump -h db -U ${PGUSER} -d ${PGDATABASE} | gzip > ${BACKUP_DIR}/${BACKUP_FILE}

if [ $? -eq 0 ]; then
    echo "Backup completed successfully: ${BACKUP_FILE}"
    
    # Calculate backup size
    BACKUP_SIZE=$(du -h ${BACKUP_DIR}/${BACKUP_FILE} | cut -f1)
    echo "Backup size: ${BACKUP_SIZE}"
    
    # Remove old backups
    echo "Removing backups older than ${RETENTION_DAYS} days"
    find ${BACKUP_DIR} -name "voice_agent_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
    
    # List remaining backups
    echo "Current backups:"
    ls -lh ${BACKUP_DIR}/voice_agent_backup_*.sql.gz
else
    echo "Backup failed at $(date)"
    exit 1
fi

echo "Backup process completed at $(date)"

# Add this to crontab for daily backups at 2 AM:
# 0 2 * * * /backup.sh >> /backup/backup.log 2>&1
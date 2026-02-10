"""
System Health & Backup API Views

Provides endpoints for database backup management.
Admin-only access.

Author: System Team
Story: 6.2 - Automated Backups
"""

import os
import json
import shutil
from datetime import datetime

from django.conf import settings
from django.core.management import call_command
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.permissions import IsAdmin


BACKUP_DIR = os.path.join(settings.BASE_DIR, 'backups')


@api_view(['GET'])
@permission_classes([IsAdmin])
def list_backups(request):
    """
    List all available database backups.
    GET /api/system/backups/
    """
    if not os.path.exists(BACKUP_DIR):
        return Response({'backups': [], 'count': 0})

    # Load metadata (labels)
    metadata = _load_metadata()

    backups = []
    for filename in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if filename.startswith('db_') and filename.endswith('.sqlite3'):
            filepath = os.path.join(BACKUP_DIR, filename)
            stat = os.stat(filepath)
            
            # Parse timestamp from filename: db_YYYY-MM-DD_HHMMSS.sqlite3
            try:
                date_str = filename.replace('db_', '').replace('.sqlite3', '')
                created = datetime.strptime(date_str, '%Y-%m-%d_%H%M%S')
                created_iso = created.isoformat()
            except ValueError:
                created_iso = None

            backups.append({
                'filename': filename,
                'label': metadata.get(filename, {}).get('label', ''),
                'size_bytes': stat.st_size,
                'size_display': _format_size(stat.st_size),
                'created_at': created_iso,
            })

    return Response({
        'backups': backups,
        'count': len(backups),
    })


@api_view(['POST'])
@permission_classes([IsAdmin])
def create_backup(request):
    """
    Create a new database backup immediately.
    POST /api/system/backups/create/
    Body (optional): {"label": "before semester reset"}
    """
    label = request.data.get('label', '').strip() if request.data else ''

    try:
        # Use the management command
        call_command('backup_db')

        # Return the latest backup info
        if os.path.exists(BACKUP_DIR):
            files = sorted([
                f for f in os.listdir(BACKUP_DIR)
                if f.startswith('db_') and f.endswith('.sqlite3')
            ])
            if files:
                latest = files[-1]
                filepath = os.path.join(BACKUP_DIR, latest)

                # Save label in metadata
                if label:
                    metadata = _load_metadata()
                    metadata[latest] = {'label': label}
                    _save_metadata(metadata)

                return Response({
                    'message': f'Backup created: {latest}',
                    'filename': latest,
                    'label': label,
                    'size_bytes': os.path.getsize(filepath),
                    'size_display': _format_size(os.path.getsize(filepath)),
                }, status=status.HTTP_201_CREATED)

        return Response(
            {'error': 'Backup command ran but no file was created'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Backup failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdmin])
def restore_backup(request, filename):
    """
    Restore the database from a backup file.
    POST /api/system/restore/<filename>/

    WARNING: This replaces the current database!
    """
    # Validate the filename to prevent path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        return Response(
            {'error': 'Invalid filename'},
            status=status.HTTP_400_BAD_REQUEST
        )

    backup_path = os.path.join(BACKUP_DIR, filename)

    if not os.path.exists(backup_path):
        return Response(
            {'error': f'Backup file not found: {filename}'},
            status=status.HTTP_404_NOT_FOUND
        )

    db_path = str(settings.DATABASES['default']['NAME'])

    try:
        # Create a safety backup of the CURRENT state before restoring
        safety_dir = os.path.join(BACKUP_DIR)
        os.makedirs(safety_dir, exist_ok=True)
        safety_name = f'db_pre_restore_{datetime.now().strftime("%Y-%m-%d_%H%M%S")}.sqlite3'
        safety_path = os.path.join(safety_dir, safety_name)
        shutil.copy2(db_path, safety_path)

        # Perform the restore
        shutil.copy2(backup_path, db_path)

        return Response({
            'message': f'Database restored from {filename}',
            'safety_backup': safety_name,
            'restored_from': filename,
        })

    except Exception as e:
        return Response(
            {'error': f'Restore failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAdmin])
def delete_backup(request, filename):
    """
    Delete a specific backup file.
    DELETE /api/system/backups/<filename>/
    """
    if '..' in filename or '/' in filename or '\\' in filename:
        return Response(
            {'error': 'Invalid filename'},
            status=status.HTTP_400_BAD_REQUEST
        )

    backup_path = os.path.join(BACKUP_DIR, filename)

    if not os.path.exists(backup_path):
        return Response(
            {'error': f'Backup file not found: {filename}'},
            status=status.HTTP_404_NOT_FOUND
        )

    try:
        # Also remove from metadata
        metadata = _load_metadata()
        metadata.pop(filename, None)
        _save_metadata(metadata)

        os.remove(backup_path)
        return Response({'message': f'Deleted: {filename}'})
    except Exception as e:
        return Response(
            {'error': f'Delete failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdmin])
def system_info(request):
    """
    Get system health information.
    GET /api/system/info/
    """
    db_path = str(settings.DATABASES['default']['NAME'])
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    backup_count = 0
    total_backup_size = 0
    if os.path.exists(BACKUP_DIR):
        backup_files = [
            f for f in os.listdir(BACKUP_DIR)
            if f.startswith('db_') and f.endswith('.sqlite3')
        ]
        backup_count = len(backup_files)
        total_backup_size = sum(
            os.path.getsize(os.path.join(BACKUP_DIR, f))
            for f in backup_files
        )

    return Response({
        'database': {
            'engine': 'SQLite',
            'size_bytes': db_size,
            'size_display': _format_size(db_size),
            'path': os.path.basename(db_path),
        },
        'backups': {
            'count': backup_count,
            'total_size_bytes': total_backup_size,
            'total_size_display': _format_size(total_backup_size),
            'directory': 'backups/',
        },
    })


def _format_size(size_bytes):
    """Format bytes into human-readable size."""
    if size_bytes < 1024:
        return f'{size_bytes} B'
    elif size_bytes < 1024 * 1024:
        return f'{size_bytes / 1024:.1f} KB'
    elif size_bytes < 1024 * 1024 * 1024:
        return f'{size_bytes / (1024 * 1024):.1f} MB'
    else:
        return f'{size_bytes / (1024 * 1024 * 1024):.1f} GB'


def _load_metadata():
    """Load backup metadata (labels) from JSON file."""
    meta_path = os.path.join(BACKUP_DIR, 'metadata.json')
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_metadata(metadata):
    """Save backup metadata (labels) to JSON file."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    meta_path = os.path.join(BACKUP_DIR, 'metadata.json')
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)

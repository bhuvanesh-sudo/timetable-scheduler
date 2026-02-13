"""
One-time Data Migration: Audit Logs

Transfers existing audit logs from the default database (db.sqlite3)
to the audit database (audit_db.sqlite3).

Usage: python manage.py migrate_audit_logs

Story: 6.2 - Persistent Audit Trail
"""

import sqlite3
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Migrate existing audit logs from default DB to audit_db'

    def handle(self, *args, **options):
        default_db = str(settings.DATABASES['default']['NAME'])
        audit_db = str(settings.DATABASES['audit_db']['NAME'])

        self.stdout.write(f'Source: {default_db}')
        self.stdout.write(f'Target: {audit_db}')

        # Connect to both databases
        src = sqlite3.connect(default_db)
        dst = sqlite3.connect(audit_db)

        try:
            src_cursor = src.cursor()
            dst_cursor = dst.cursor()

            # Check if source table exists and has data
            src_cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"
            )
            if not src_cursor.fetchone():
                self.stdout.write(self.style.WARNING('No audit_logs table in source DB.'))
                return

            # Check existing count in destination
            dst_cursor.execute("SELECT COUNT(*) FROM audit_logs")
            existing_count = dst_cursor.fetchone()[0]
            if existing_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'Destination already has {existing_count} logs. Skipping to avoid duplicates.'
                    )
                )
                return

            # Get column info from source (old schema had 'user_id', new schema has 'user_name')
            src_cursor.execute("PRAGMA table_info(audit_logs)")
            src_columns = [col[1] for col in src_cursor.fetchall()]

            has_user_id = 'user_id' in src_columns
            has_user_name = 'user_name' in src_columns

            if has_user_id:
                # Old schema: need to join with users table to get username
                self.stdout.write('Detected user_id column. Joining with users table...')
                # Check which user table exists
                src_cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%user%'"
                )
                user_tables = [t[0] for t in src_cursor.fetchall()]
                self.stdout.write(f'  User tables found: {user_tables}')

                # Find the right user table
                user_table = None
                for t in ['accounts_user', 'auth_user']:
                    if t in user_tables:
                        user_table = t
                        break

                if user_table:
                    src_cursor.execute(f"""
                        SELECT 
                            a.id,
                            COALESCE(u.username, 'Unknown') as user_name,
                            a.action,
                            a.model_name,
                            a.object_id,
                            a.details,
                            a.ip_address,
                            a.timestamp
                        FROM audit_logs a
                        LEFT JOIN {user_table} u ON a.user_id = u.id
                        ORDER BY a.id
                    """)
                else:
                    # No user table found — just use 'Unknown'
                    self.stdout.write(self.style.WARNING('No user table found. Using "Unknown" for usernames.'))
                    src_cursor.execute("""
                        SELECT id, 'Unknown', action, model_name, object_id, 
                               details, ip_address, timestamp
                        FROM audit_logs ORDER BY id
                    """)
            elif has_user_name:
                self.stdout.write('Detected user_name column (new schema).')
                src_cursor.execute("""
                    SELECT id, user_name, action, model_name, object_id, 
                           details, ip_address, timestamp
                    FROM audit_logs ORDER BY id
                """)
            else:
                self.stderr.write(self.style.ERROR('Cannot determine schema — no user_id or user_name column found.'))
                return

            rows = src_cursor.fetchall()

            if not rows:
                self.stdout.write(self.style.WARNING('No audit logs to migrate.'))
                return

            self.stdout.write(f'Found {len(rows)} audit logs to migrate...')

            # Insert into destination
            dst_cursor.executemany(
                """INSERT INTO audit_logs 
                   (id, user_name, action, model_name, object_id, details, ip_address, timestamp) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                rows
            )
            dst.commit()

            self.stdout.write(
                self.style.SUCCESS(f'Successfully migrated {len(rows)} audit logs!')
            )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Migration failed: {e}'))
            raise
        finally:
            src.close()
            dst.close()

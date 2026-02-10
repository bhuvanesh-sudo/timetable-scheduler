"""
Database Router for Audit Logs

Routes AuditLog model to the 'audit_db' database so that
audit logs survive backup/restore operations on the main database.

Story: 6.2 - Automated Backups (Persistent Audit Trail)
"""


class AuditLogRouter:
    """
    Routes AuditLog reads/writes to the 'audit_db' database.
    All other models use the 'default' database.
    """

    audit_models = {'auditlog'}

    def db_for_read(self, model, **hints):
        if model._meta.model_name in self.audit_models:
            return 'audit_db'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.model_name in self.audit_models:
            return 'audit_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name in self.audit_models:
            return db == 'audit_db'
        if db == 'audit_db':
            return False
        return None

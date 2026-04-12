from .models import AuditLog

def log_action(user, action, target, ip_address=None, details=None):
    """
    Enregistre une action dans les logs d'audit.
    """
    if details is None:
        details = {}
    
    AuditLog.objects.create(
        user=user,
        action=action,
        target=target,
        ip_address=ip_address,
        details=details
    )

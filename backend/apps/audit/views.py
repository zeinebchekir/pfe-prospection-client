from rest_framework import generics
from .models import AuditLog
from .serializers import AuditLogSerializer
from apps.users.permissions import IsAdmin

class AuditLogListView(generics.ListAPIView):
    """
    Liste des logs d'audit (ADMIN seulement).
    """
    permission_classes = [IsAdmin]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        queryset = AuditLog.objects.all()
        action = self.request.query_params.get('action')
        user_id = self.request.query_params.get('user_id')
        target = self.request.query_params.get('target')

        if action:
            queryset = queryset.filter(action=action)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if target:
            queryset = queryset.filter(target__icontains=target)
            
        return queryset.order_by('-timestamp')

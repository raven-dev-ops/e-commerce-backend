from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ReferralCode
from backend.serializers.referrals import (
    ReferralCodeCreateSerializer,
    ReferralCodeSerializer,
    ReferralCodeTrackSerializer,
)


class ReferralCodeViewSet(viewsets.ModelViewSet):
    queryset = ReferralCode.objects.all()
    serializer_class = ReferralCodeSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = ReferralCodeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = ReferralCode.objects.create(created_by=request.user)
        output = ReferralCodeSerializer(code)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def track(self, request, *args, **kwargs):
        serializer = ReferralCodeTrackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = get_object_or_404(ReferralCode, code=serializer.validated_data["code"])
        code.usage_count += 1
        code.save(update_fields=["usage_count"])
        output = ReferralCodeSerializer(code)
        return Response(output.data)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .services import process_statement
from .models import Statement

SUPPORTED_BANKS = {c[0] for c in Statement.BANK_CHOICES}


class StatementUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        file = request.FILES.get("file")
        bank = request.data.get("bank", "").lower()

        if not file:
            return Response({"error": "No file provided."}, status=400)
        if bank not in SUPPORTED_BANKS:
            return Response(
                {"error": f"Invalid bank. Supported: {', '.join(SUPPORTED_BANKS)}"},
                status=400,
            )

        try:
            statement = process_statement(
                user=request.user,
                file=file,
                filename=file.name,
                bank=bank,
            )
            return Response(
                {
                    "id": statement.id,
                    "filename": statement.filename,
                    "bank": statement.bank,
                    "transaction_count": statement.transaction_count,
                    "status": statement.status,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": "Processing failed.", "detail": str(e)}, status=500)


class StatementListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        statements = Statement.objects.filter(user=request.user)[:10]
        return Response([
            {
                "id": s.id,
                "filename": s.filename,
                "bank": s.bank,
                "transaction_count": s.transaction_count,
                "status": s.status,
                "uploaded_at": s.uploaded_at.strftime("%d/%m/%Y %H:%M"),
            }
            for s in statements
        ])

from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response, JsonResponse
from models import Cobranca
import csv


@api_view(["POST"])
def upload_csv(request):
    if request.method == "POST" and request.FILES["csv_file"]:
        csv_file = request.FILES["csv_file"]
        if not csv_file.name.endswith(".csv"):
            return JsonResponse(
                {"error": "Por favor, envie um arquivo CSV válido."}, status=400
            )

        # Processar o arquivo CSV
        try:
            process_csv(csv_file)
            return JsonResponse(
                {"success": "Arquivo CSV enviado com sucesso."}, status=200
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse(
            {"error": "Método inválido ou arquivo não encontrado."}, status=400
        )


def process_csv(csv_file):
    # Lógica para processar o arquivo CSV e salvar os dados no banco de dados
    # Aqui você irá ler o arquivo CSV e iterar sobre as linhas para extrair os dados
    # Em seguida, você criará instâncias do modelo correspondente e as salvará no banco de dados
    # Exemplo de lógica para processar o arquivo CSV e salvar os dados:

    reader = csv.reader(csv_file)
    next(reader)  # Pule o cabeçalho do arquivo CSV, se houver
    for row in reader:
        # Extrair os dados de cada linha do arquivo CSV
        name = row[0]
        government_id = row[1]
        email = row[2]
        debt_amount = row[3]
        debt_due_date = row[4]
        debt_id = row[5]

        # Criar instância do modelo e salvar no banco de dados
        Cobranca.objects.create(
            nome=name,
            documento=government_id,
            email=email,
            valor=debt_amount,
            data_vencimento=debt_due_date,
            uuid=debt_id,
        )


@api_view(["GET"])
def get_files_history(request):
    """
    Endpoint para obter o histórico de arquivos CSV.

    Retorna uma resposta JSON contendo o histórico de arquivos CSV
    que foram processados anteriormente.
    """
    # Lógica para obter o histórico de arquivos do banco de dados
    # Exemplo: consultar o banco de dados para recuperar os arquivos processados

    files_history = (
        []
    )  # Lista de arquivos processados (pode ser substituída pela lógica real)

    return Response(files_history)

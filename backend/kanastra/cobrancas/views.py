from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from django.http import JsonResponse
from .models import Cobranca, Arquivo
import csv
from io import TextIOWrapper
from itertools import islice
from django.db import migrations
import time
from functools import wraps
from datetime import datetime
from .email_engine import *


@csrf_exempt
def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time of {func.__name__}: {execution_time} seconds")
        return result

    return wrapper


@csrf_exempt
@api_view(["POST"])
@measure_time
def upload_csv(request):
    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")

        if not csv_file:
            return JsonResponse({"error": "Arquivo não encontrado."}, status=400)

        if not csv_file.name.endswith(".csv"):
            return JsonResponse(
                {"error": "Por favor, envie um arquivo CSV válido."}, status=400
            )

        try:
            process_csv(csv_file)
            return JsonResponse(
                {"success": "Arquivo CSV enviado com sucesso."}, status=200
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Método inválido."}, status=400)


@csrf_exempt
def process_csv(csv_file):
    # Lógica para processar o arquivo CSV e salvar os dados no banco de dados
    # Aqui você irá ler o arquivo CSV e iterar sobre as linhas para extrair os dados
    # Em seguida, você criará instâncias do modelo correspondente e as salvará no banco de dados
    # Exemplo de lógica para processar o arquivo CSV e salvar os dados:

    # Open the CSV file in binary mode and wrap it with TextIOWrapper

    BATCH_SIZE = 10000

    def read_csv_file(csv_file, batch_size):
        csv_file_wrapper = TextIOWrapper(csv_file, encoding="utf-8")
        reader = csv.reader(csv_file_wrapper)
        next(reader)

        while True:
            batch = list(islice(reader, batch_size))

            if not batch:
                return

            yield batch

    def import_records(csv_file):
        print("Populating Database...")
        for batch in read_csv_file(csv_file, BATCH_SIZE):
            Cobranca.objects.bulk_create(
                [
                    Cobranca(
                        nome=name,
                        documento=government_id,
                        email=email,
                        valor=debt_amount,
                        data_vencimento=debt_due_date,
                        uuid=debt_id,
                    )
                    for name, government_id, email, debt_amount, debt_due_date, debt_id in batch
                ],
                batch_size=BATCH_SIZE,
            )

    try:
        import_records(csv_file)
        print("Database populated!")
    except Exception as e:
        print(e)


@csrf_exempt
@api_view(["GET"])
def list_files(request):
    arquivos = Arquivo.objects.all().order_by("-data_envio")
    if not arquivos:
        return Response({"message": "No File Found!"}, status=404)

    data = [
        {
            "nome": arquivo.nome,
            "data_envio": arquivo.data_envio.strftime("%d/%m/%Y %H:%M:%S"),
        }
        for arquivo in arquivos
    ]
    return Response(data)


@csrf_exempt
@api_view(["POST"])
def save_file_name(request):
    if request.method == "POST":
        nome_arquivo = request.data.get("nome_arquivo")

        if nome_arquivo:
            Arquivo.objects.create(nome=nome_arquivo)
            return Response({"success": "File name saved successfully!."}, status=201)
        else:
            return Response({"error": "File name not given!."}, status=400)


@csrf_exempt
@api_view(["POST"])
def send_emails_from_database(request):
    if request.method == "POST":
        try:
            # Exemplo de uso:
            send_emails_from_database()
            return Response(
                {"success": "Email sent to all database clients!."}, status=201
            )
        except:
            return Response({"error": "Emails not sent!."}, status=400)

from django.test import TestCase
from django.urls import reverse
from cobrancas.models import Cobranca, Arquivo
import os
import csv


class EndToEndTestCase(TestCase):
    def test_upload_csv(self):
        # Path do arquivo CSV de teste
        csv_file_path = os.path.join(os.path.dirname(__file__), "input.csv")

        # Verificar se o arquivo CSV existe
        self.assertTrue(
            os.path.exists(csv_file_path),
            f"Arquivo CSV não encontrado em {csv_file_path}",
        )

        # Contar o número de objetos Cobranca antes do upload
        count_before_upload = Cobranca.objects.count()

        # Contar o número de objetos Arquivo antes do upload
        count_arquivo_before_upload = Arquivo.objects.count()

        # Abrir o arquivo CSV
        with open(csv_file_path, "r") as csv_file:
            # Ler o CSV usando o módulo csv do Python
            csv_reader = csv.reader(csv_file)

            # Ignorar o cabeçalho do CSV
            next(csv_reader)

            # Contar o número de linhas no CSV
            num_lines_in_csv = sum(1 for _ in csv_reader)

            # Resetar o ponteiro do arquivo para o início
            csv_file.seek(0)

            # Simular uma solicitação de upload de arquivo com o arquivo CSV
            file_data = {"csv_file": csv_file}
            response = self.client.post(reverse("upload_csv"), file_data)
            response_file = self.client.post(
                reverse("save_file_name"), {"nome_arquivo": os.path.basename(csv_file)}
            )

            # Verificar se a resposta é 200 OK e se contém a mensagem de sucesso
            self.assertEqual(response.status_code, 200)
            self.assertIn("success", response.content.decode("utf-8"))

            # Verificar se a resposta é 200 OK e se contém a mensagem de sucesso
            self.assertEqual(response_file.status_code, 200)
            self.assertIn("success", response_file.content.decode("utf-8"))

        # Contar o número de objetos Cobranca após o upload
        count_after_upload = Cobranca.objects.count()

        # Verificar se o número de objetos no banco de dados aumentou após o upload
        self.assertEqual(count_after_upload - count_before_upload, num_lines_in_csv)

        # Verificar se o nome do arquivo foi salvo no banco de dados Arquivo
        count_arquivo_after_upload = Arquivo.objects.count()
        self.assertEqual(
            count_arquivo_after_upload - count_arquivo_before_upload, 1
        )  # Verifica se apenas um novo arquivo foi adicionado
        last_uploaded_file = Arquivo.objects.last()
        self.assertEqual(
            last_uploaded_file.nome, "input.csv"
        )  # Substitua "input.csv" pelo nome do arquivo esperado

from django.db import models

# Create your models here.


class Cobranca(models.Model):
    nome = models.CharField(max_length=100)
    documento = models.CharField(max_length=20)
    email = models.EmailField()
    valor = models.CharField()
    data_vencimento = models.CharField()
    uuid = models.CharField()

    def __str__(self):
        return f"{self.nome} - {self.data_vencimento}"


class Arquivo(models.Model):
    nome = models.CharField(max_length=100)
    data_envio = models.DateTimeField(auto_now_add=True)

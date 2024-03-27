from django.db import models

# Create your models here.


class Cobranca(models.Model):
    nome = models.CharField(max_length=100)
    documento = models.CharField(max_length=20)
    email = models.EmailField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_vencimento = models.DateField()
    uuid = models.UUIDField()

    def __str__(self):
        return f"{self.nome} - {self.data_vencimento}"

from django.contrib import admin
from .models import Cobranca, Arquivo

@admin.register(Cobranca)
class CobrancaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'documento', 'email', 'valor', 'data_vencimento', 'uuid')
    search_fields = ('nome', 'documento', 'email')
    list_filter = ('data_vencimento',)

@admin.register(Arquivo)
class ArquivoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_envio')
    search_fields = ('nome',)

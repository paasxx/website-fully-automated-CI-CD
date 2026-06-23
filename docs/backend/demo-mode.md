# Demo Mode — dados de exemplo seguros para qualquer usuário

Guia de implementação. Objetivo: **qualquer usuário** pode carregar dados de
exemplo (pra ver o dashboard vivo antes de importar fatura real) e depois limpar
**só** esses dados — sem nunca arriscar os dados reais dele.

> Decisão central: a flag é no **dado** (`Transaction.is_demo`), não no usuário.
> Carrego transações marcadas como demo; o reset apaga **só** as marcadas.
> Dados reais (`is_demo=False`) são intocáveis por construção.

---

## 1. Por que a flag vai no Transaction, não no User

A versão ingênua do endpoint de demo faz o reset assim:

```python
Transaction.objects.filter(user=request.user).delete()   # ⚠️ apaga TUDO
```

Se qualquer usuário pode usar isso, um usuário real com faturas importadas clica
"reset" e **perde os dados reais**. Catástrofe.

A correção é mudar **o que** é descartável, não **quem** pode descartar:

```python
Transaction.objects.filter(user=request.user, is_demo=True).delete()   # ✅ só o demo
```

Com isso, o reset é **cirúrgico**: só toca no que foi gerado como demo. Qualquer
usuário pode carregar e limpar à vontade, e o dado real fica seguro por construção.

| Abordagem | O que marca | Quem pode usar | Risco no reset |
| --------- | ----------- | -------------- | -------------- |
| `User.is_demo` | quem pode | só contas demo | reset apaga tudo da conta (mas conta é descartável) |
| **`Transaction.is_demo`** ⭐ | o que é descartável | **qualquer usuário** | **zero** — só apaga o demo |

---

## 2. Mudança no modelo

`finances/models.py` → `Transaction`:

```python
class Transaction(models.Model):
    # ...campos existentes...
    is_demo = models.BooleanField(default=False)  # dado de exemplo, removível pelo reset
```

**Migration:** `make migrate` gera e aplica (ou `make clean && make dev` se for zerar
o banco). É uma coluna com default — migration segura, sem downtime.

**Índice?** O volume de demo é pequeno (~200 linhas por usuário), então o delete
`filter(user, is_demo=True)` é barato sem índice dedicado. Só vale um índice
`(user, is_demo)` se você decidir **excluir** o demo de queries grandes (ver §6).

---

## 3. Mudança no service

O core de geração já existe em `finances/services.py`
(`generate_sample_transactions`). Só adicionar um parâmetro `is_demo`:

```python
def generate_sample_transactions(user, count, *, is_demo=False, years=3, banks=(...),
                                 credit_ratio=0.10, installment_ratio=0.15,
                                 unknown_ratio=0.10, batch_size=5000, progress=None):
    # ...
    batch.append(
        Transaction(
            user=user,
            # ...campos existentes...
            is_demo=is_demo,        # ← propaga a flag
            category=categorize(description, categories),
        )
    )
    # ...
```

Quem chama decide:
- **Endpoint de demo** → `is_demo=True` (dado removível pelo reset).
- **Command de stress test** (`seed_transactions`) → `is_demo=False` por padrão (é
  dado de teste de escala, limpo via `make clear-transactions`). Opcional: expor
  `is_demo` no YAML se você quiser marcar o stress test como demo também.

---

## 4. Endpoint (`DemoDataView`)

`finances/views.py`. Sem checagem de `is_demo` no usuário — **qualquer autenticado**
pode usar. A segurança está no filtro `is_demo=True` do delete.

```python
class DemoDataView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    SAMPLE_COUNT = 300   # 300+ deixa os gráficos de 3 anos mais "vivos" que 200

    def post(self, request):
        # idempotente: limpa demo anterior e recarrega fresco
        Transaction.objects.filter(user=request.user, is_demo=True).delete()
        try:
            created = generate_sample_transactions(
                request.user, self.SAMPLE_COUNT, is_demo=True
            )
        except ValueError as exc:                       # user sem categorias
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"created": created}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        deleted, _ = Transaction.objects.filter(
            user=request.user, is_demo=True
        ).delete()
        return Response({"deleted": deleted}, status=status.HTTP_200_OK)
```

API resultante:

| Método | Rota | Faz |
| ------ | ---- | --- |
| `POST` | `/api/finances/demo/` | limpa demo anterior + carrega `SAMPLE_COUNT` transações demo |
| `DELETE` | `/api/finances/demo/` | apaga **só** as transações demo do usuário |

**Por que o POST limpa antes de carregar:** torna a operação idempotente — clicar
"carregar demo" 2x não acumula 600 linhas; sempre termina com exatamente
`SAMPLE_COUNT` linhas demo.

---

## 5. Camadas de UX opcionais (empilhe conforme quiser)

A tag no dado já te dá segurança total. Estas são melhorias de experiência:

### 5a. Só permitir demo em conta "vazia de dado real" (recomendado p/ onboarding)

Evita misturar demo com dado real no dashboard de quem já usa de verdade:

```python
def post(self, request):
    has_real = Transaction.objects.filter(user=request.user, is_demo=False).exists()
    if has_real:
        return Response(
            {"error": "Demo data is only available on an empty account."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    # ...resto
```

### 5b. Banner "modo demo ativo"

O front mostra um aviso + botão "limpar demo" enquanto houver dado demo. Pra isso o
front precisa saber se há demo ativo — duas opções:
- expor um campo no `/api/auth/me/` (ex: `has_demo_data`), ou
- um endpoint leve `GET /api/finances/demo/` que retorna `{ "count": N }`.

### 5c. Conta guest efêmera (só se quiser demo pública sem login)

"Experimentar sem cadastro" cria uma conta temporária (com categorias semeadas),
carrega demo, e um job de limpeza expira contas guest antigas. Mais infra — só vale
se o caso de uso for landing page pública.

---

## 6. Demo aparece nas queries normais?

Decisão de produto:

- **Mostrar junto (simples, recomendado):** o dado demo aparece no dashboard/lista
  como dado normal — que é o ponto (ver a tela viva). Some no reset. Nenhuma query
  muda. Combina com a camada 5a (conta vazia), pra não confundir quem tem dado real.
- **Esconder o demo das queries "sérias":** se você quiser que relatórios/export
  ignorem demo, filtra `is_demo=False` nas views relevantes (`TransactionListView`,
  `SpendingOverTimeView`) e cria o índice `(user, is_demo)`. Mais complexidade —
  só faça se tiver um motivo claro.

Recomendo a primeira: demo é transitório, aparece como dado normal, e a camada 5a
evita a confusão. Mantém o código simples.

---

## 7. Frontend (wiring)

```js
// carregar demo
await axiosInstance.post('/finances/demo/');
// limpar demo
await axiosInstance.delete('/finances/demo/');
// depois de cada um: refetch do dashboard / lista
```

Botões sugeridos numa tela de "experimente": **"Carregar dados de exemplo"** (POST) e
**"Limpar dados de exemplo"** (DELETE), com refresh dos cards após a resposta.

---

## 8. Testes a escrever (`finances/tests/test_views.py`)

```python
class TestDemoDataView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="demo@example.com", username="demo@example.com", password="pass123")
        seed_default_categories(self.user)        # demo precisa das categorias

    def test_requires_auth(self): ...              # 401 sem token

    def test_post_creates_demo_transactions(self):
        # 201, cria SAMPLE_COUNT, todas com is_demo=True

    def test_post_is_idempotent(self):
        # POST 2x → ainda SAMPLE_COUNT (não acumula)

    def test_delete_removes_only_demo(self):
        _tx(self.user, is_demo=False)              # dado "real"
        # POST (carrega demo) → DELETE → real sobrevive, demo some
        # assert filter(is_demo=False).count() == 1
        # assert filter(is_demo=True).count() == 0

    def test_any_user_can_use_it(self):
        # usuário comum (sem flag nenhuma) consegue POST/DELETE — sem 403
```

O teste-chave é o `test_delete_removes_only_demo`: prova que o dado real
(`is_demo=False`) **sobrevive** ao reset. É a garantia de segurança em forma de teste.

---

## 9. Checklist de implementação (ordem)

1. [ ] `Transaction.is_demo = BooleanField(default=False)` em `finances/models.py`
2. [ ] `make migrate` (ou `make clean && make dev`)
3. [ ] `generate_sample_transactions(..., is_demo=False)` — propaga a flag pro `Transaction(...)`
4. [ ] `DemoDataView`: POST marca `is_demo=True` (+ limpa demo antes); DELETE filtra `is_demo=True`
5. [ ] (opcional 5a) guard de "conta vazia" no POST
6. [ ] Testes — com destaque pro `test_delete_removes_only_demo`
7. [ ] Frontend: botões carregar/limpar + refresh
8. [ ] Docs: atualizar `api-endpoints.md` (qualquer usuário; reset só remove demo)

---

## 10. Diferença pro que já está na branch (não commitado)

O `DemoDataView` + `generate_sample_transactions` já existem na branch, mas na versão
**insegura** (DELETE apaga tudo, sem tag). Ao implementar este guia, os deltas são:

- **+** campo `Transaction.is_demo` + migration
- **~** `generate_sample_transactions` ganha o param `is_demo`
- **~** `DemoDataView.delete` passa de `filter(user=...)` → `filter(user=..., is_demo=True)`
- **~** `DemoDataView.post` marca `is_demo=True` e limpa o demo anterior
- **~** testes ajustados pra provar que o dado real sobrevive

Nada de `User.is_demo` — essa ideia foi descartada em favor da tag no dado.

# Escalando o FinTrack para B2B — Índices, Paginação e Redis

Documento de estudo. Cenário: uso B2B, **milhões de transações por tenant**,
paginações profundas e dashboards pesados. O foco é **onde** colocar cada coisa
no app de hoje e **por quê**.

> TL;DR da ordem mental: **índice** deixa a query rápida → **paginação keyset/cursor**
> evita que páginas profundas degradem → **Redis** evita bater no banco de novo.
> Redis **não substitui** índice; ele senta na frente de um banco já bem indexado.

---

## 0. As três camadas (não confunda)

| Camada | Resolve | Não resolve |
| ------ | ------- | ----------- |
| **Índices no Postgres** | velocidade de UMA query | repetição da mesma query |
| **Paginação keyset/cursor** | páginas profundas (`OFFSET` gigante) | query lenta por falta de índice |
| **Redis (cache)** | repetição de leituras caras | uma query que é lenta na origem |

O erro clássico é jogar Redis no problema antes de ter índice e paginação certos.
Cache de uma query lenta só esconde o problema (e o primeiro request — cache miss —
continua lento, além de invalidações ficarem perigosas).

---

## 1. Índices — a fundação (faça isso primeiro)

### Regra de ouro: toda query é tenant-scoped → todo índice começa pelo tenant

Hoje o seu "tenant" é o `user_id`. Toda query do app já filtra por `user`
(veja os índices em `finances/models.py`):

```python
indexes = [
    models.Index(fields=["user", "-date"],     name="idx_transaction_user_date"),
    models.Index(fields=["user", "bank"],       name="idx_transaction_user_bank"),
    models.Index(fields=["user", "category"],   name="idx_transaction_user_category"),
]
```

Isso está **certo**: o índice composto começa pela coluna mais seletiva e constante
em toda query (o tenant). Um índice só em `date` seria quase inútil aqui, porque o
banco sempre precisa primeiro recortar pelo tenant.

### Para B2B multi-tenant de verdade: `org_id` / `tenant_id`

Quando uma empresa tem vários usuários, o isolamento passa a ser por **organização**,
não por usuário. O caminho:

1. Adicionar `tenant_id` (FK para `Organization`) em `Transaction` e `Category`.
2. **Liderar** todos os índices por `tenant_id`: `(tenant_id, -date, id)`, etc.
3. Considerar **Row Level Security (RLS)** no Postgres — o próprio banco garante que
   uma query nunca vê linhas de outro tenant, mesmo com bug na aplicação. (O CLAUDE.md
   já cita isso como plano.)

### O índice que a paginação keyset precisa (importante)

`date` **não é único** — vários lançamentos no mesmo dia. Para paginação keyset
(seção 2) funcionar sem pular/duplicar linhas, a ordenação precisa ser **estável e
única**. Solução: ordenar por `(date, id)` e indexar isso:

```python
# Adicionar em Transaction.Meta.indexes
models.Index(fields=["user", "-date", "-id"], name="idx_tx_user_date_id"),
```

Com esse índice, a query de keyset (`WHERE (date,id) < (?,?) ORDER BY date DESC, id DESC LIMIT 25`)
é resolvida **inteiramente pelo índice**, em tempo constante, em qualquer profundidade.

### Busca textual (`search` / `icontains`) em escala

Seu `TransactionFilter` usa `description__icontains` (vira `ILIKE '%termo%'`). Isso
**não usa índice B-tree** — é full scan. Em milhões de linhas, é o gargalo escondido.
Duas saídas no Postgres:

```sql
-- Opção A: índice GIN com trigramas (bom para ILIKE '%termo%')
CREATE EXTENSION pg_trgm;
CREATE INDEX idx_tx_description_trgm ON finances_transaction
  USING gin (description gin_trgm_ops);

-- Opção B: full-text search (to_tsvector) — melhor para busca por palavras
```

No Django: `from django.contrib.postgres.indexes import GinIndex` + `TrigramSimilarity`,
ou `SearchVector`/`SearchVectorField` para FTS.

### Particionamento (o plano do RANGE por mês)

Particionar `Transaction` por `RANGE (date)` (uma partição por mês) dá **partition
pruning**: uma query com `date_from`/`date_to` só toca as partições do período, e
cada partição tem índices menores. Combina perfeitamente com queries financeiras que
são quase sempre time-bounded. Isso é ortogonal ao Redis — é otimização no banco.

### Resumo: qual índice serve qual query

| Query (view) | Filtro | Índice usado |
| ------------ | ------ | ------------ |
| Lista de transações (ordem padrão) | `user` + ordena `-date,-id` | `(user, -date, -id)` |
| Filtro por banco | `user, bank` | `(user, bank)` |
| Filtro por categoria | `user, category` | `(user, category)` |
| Filtro por período | `user, date >= / <=` | `(user, -date, -id)` (range scan) |
| Busca por descrição | `description ILIKE` | GIN trigram (`pg_trgm`) |
| `spending-over-time` | `user, is_credit=False`, group by mês/banco | `(user, -date)` cobre o filtro; o GROUP BY é em memória |
| PK / tiebreaker do keyset | `id` | PK (já indexado) |

---

## 2. Paginação em escala: offset vs cursor (keyset)

### O que você tem hoje

`TransactionPagePagination` (`PageNumberPagination`, `page_size=25`) → `?page=N` vira
`LIMIT 25 OFFSET (N-1)*25`.

### Por que `OFFSET` degrada

`OFFSET 1000000 LIMIT 25` faz o banco **varrer e descartar 1 milhão de linhas** para
devolver 25. Página 1 é instantânea; página 40.000 é lenta. Custo **O(offset)**.
Pior: `PageNumberPagination` faz um `COUNT(*)` a cada resposta — e contar milhões de
linhas também é caro.

### Keyset / cursor pagination — O(1) em qualquer profundidade

Em vez de "pule N linhas", você diz "me dê as próximas 25 **depois deste ponto**":

```sql
SELECT * FROM finances_transaction
WHERE user_id = :tenant
  AND (date, id) < (:last_date, :last_id)   -- "depois" do último item da página anterior
ORDER BY date DESC, id DESC
LIMIT 25;
```

Isso usa o índice `(user, -date, -id)` e **nunca** varre o que já passou. Custo
constante na página 1 ou na 40.000.

### No DRF — onde colocar

`finances/pagination.py`:

```python
from rest_framework.pagination import CursorPagination

class TransactionCursorPagination(CursorPagination):
    page_size = 25
    max_page_size = 200
    page_size_query_param = "page_size"
    # ordenação estável e ÚNICA — precisa casar com o índice (user, -date, -id)
    ordering = ("-date", "-id")
    cursor_query_param = "cursor"
```

`finances/views.py`:

```python
class TransactionListView(generics.ListAPIView):
    pagination_class = TransactionCursorPagination   # troca a PageNumber
    # ...resto igual
```

A resposta passa a vir com `next`/`previous` como **tokens opacos** (cursores), não
`?page=N`.

### Trade-off (leia antes de trocar)

| | PageNumber (offset) | Cursor (keyset) |
| -- | -- | -- |
| Página profunda | lenta (O(offset)) | rápida (O(1)) |
| "Pular para página 500" | ✅ | ❌ (só next/prev) |
| Total de itens (`count`) | ✅ (mas custa `COUNT(*)`) | ❌ por padrão |
| UX ideal | tabela com números de página | scroll infinito / "carregar mais" |

Para um data-table B2B onde o usuário quer "página 500" e o total, o caminho é
**híbrido**: keyset para a navegação + um `count` aproximado e cacheado (seção 3) em
vez de `COUNT(*)` exato a cada request.

**Impacto no front:** trocar os botões de número de página por "carregar mais" /
scroll infinito que mandam o `cursor` do `next`.

---

## 3. Redis — o que cachear, onde e como

Redis = store chave-valor em memória, leitura sub-milissegundo. No FinTrack ele
brilha em alguns lugares específicos.

### Setup

`requirements.txt`: `redis`, `django-redis`.

`settings.py`:

```python
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://redis:6379/1"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}
```

`docker-compose.dev.yml`:

```yaml
  redis:
    image: redis:7-alpine
    container_name: fintrack-redis
    ports:
      - "6379:6379"
```

Em prod (AWS): **ElastiCache for Redis** (gerenciado), no lugar de um container.

---

### Use case A — cachear agregações caras (o dashboard) ⭐ maior ganho

`SpendingOverTimeView` agrega **todas** as despesas do tenant a cada request. Com 1M
linhas isso é caro e repetido (o usuário abre o dashboard várias vezes sem os dados
mudarem). Cacheie o resultado, com chave **por tenant** e **versionada**:

```python
from django.core.cache import cache

class SpendingOverTimeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        version = cache.get(f"cache_version:{request.user.id}", 1)
        key = f"spending_over_time:{request.user.id}:v{version}"

        cached = cache.get(key)
        if cached is not None:
            return Response(cached)          # HIT — nem toca no Postgres

        payload = self._compute(request.user)   # MISS — query (usa o índice) + monta
        cache.set(key, payload, timeout=3600)    # TTL de 1h como rede de segurança
        return Response(payload)
```

### Use case B — cachear o `COUNT(*)` da paginação

Se mantiver número de página, o `COUNT(*)` é o gargalo. Cacheie por
(tenant + assinatura dos filtros), com TTL curto ou invalidação na escrita.

### Use case C — listas pequenas e muito lidas (categorias)

`CategoryListView` é minúsculo e batido em quase toda tela. Cacheia por tenant e
invalida no CRUD de categoria.

### Use case D — rate limiting (proteger o demo e o login)

O endpoint `POST /api/finances/demo/` pode ser abusado (spam → milhões de linhas).
DRF throttling com Redis:

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_RATES": {"demo": "5/hour", "login": "10/min"},
}

# views.py
from rest_framework.throttling import ScopedRateThrottle

class DemoDataView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "demo"
```

Os contadores de throttle ficam no cache (Redis) com TTL — sliding window de graça.

### Use case E — Celery com Redis como broker (trabalho assíncrono)

Import de fatura grande ou seed de 1M **não deve** bloquear o request. Padrão:
enfileira a tarefa (Redis como broker do Celery), responde `202 Accepted` com um
`job_id`, e o front faz polling do status. O `process_statement` e o
`generate_sample_transactions` seriam ótimos candidatos a virar tasks.

### Use case F — blocklist de JWT / logout

Com `ROTATE_REFRESH_TOKENS`, um refresh token rotacionado/deslogado precisa ser
invalidado antes de expirar. Guarde os tokens revogados no Redis com
`TTL = tempo restante do token` — expira sozinho.

---

### Invalidação de cache — a parte difícil (padrão version-key)

O problema clássico: "como eu apago todas as chaves de cache de um tenant quando ele
importa uma fatura nova?". Rastrear chave por chave é frágil. Padrão **version-key**:

- Cada tenant tem uma chave `cache_version:{user_id}`.
- **Toda leitura** inclui essa versão na sua própria chave (visto no use case A).
- **Toda escrita** que invalida dados faz `INCR` na versão → todas as chaves antigas
  ficam **inalcançáveis** e expiram sozinhas (lazy). Não precisa deletar nada.

```python
# finances/services.py  (ou um signals.py)
from django.core.cache import cache

def bump_cache_version(user_id):
    try:
        cache.incr(f"cache_version:{user_id}")
    except ValueError:               # chave ainda não existe
        cache.set(f"cache_version:{user_id}", 2)
```

**Onde chamar** (todo ponto que muda transações/categorias do tenant):
- ao fim de `process_statement()` (import de fatura)
- no `perform_destroy`/`update` de categoria e transação
- no `POST`/`DELETE` do `DemoDataView`

---

## 4. Como tudo se encaixa — fluxo de um request

```
GET /api/finances/spending-over-time/
        │
        ▼
  monta a chave:  spending_over_time:{tenant}:v{version}
        │
        ▼
   Redis tem? ──sim──▶ devolve (sub-ms, NÃO toca no Postgres)
        │
        não (miss)
        ▼
   query no Postgres  ──usa o índice (user, -date)──▶ rápida
        │
        ▼
   guarda no Redis (com a versão atual)  ──▶ devolve
```

E quando o tenant importa uma fatura:

```
process_statement() termina ──▶ bump_cache_version(tenant)
        │
        ▼
   cache_version vira v+1  ──▶ todas as chaves "...:v{anterior}" viram lixo
                               (próxima leitura é miss → recomputa → recacheia)
```

**Sobre "como o Redis usa os índices de forma inteligente":** ele **não** usa os
índices do Postgres — são camadas diferentes. O que acontece: no **cache miss**, a
query que vai popular o Redis é rápida **porque** existe o índice certo; o Redis então
guarda o **resultado** para que as próximas leituras pulem o banco inteiro. Índice =
query rápida; Redis = não precisar fazer a query.

---

## 5. Onde cada peça mora no FinTrack (mapa)

| Peça | Arquivo | O que muda |
| ---- | ------- | ---------- |
| Índice keyset | `finances/models.py` → `Transaction.Meta.indexes` | add `(user, -date, -id)` + migration |
| Índice de busca | migration custom | `CREATE EXTENSION pg_trgm` + GIN em `description` |
| Cursor pagination | `finances/pagination.py` + `views.py` | nova classe + troca `pagination_class` |
| Cache de agregação | `finances/views.py` (`SpendingOverTimeView`) | `cache.get/set` com version-key |
| Invalidação | `finances/services.py` + `statements/services.py` | `bump_cache_version()` nas escritas |
| Rate limit | `settings.py` + `DemoDataView` | throttle scope |
| Config Redis | `settings.py`, `docker-compose.dev.yml`, `requirements.txt` | `CACHES` + serviço `redis` |
| Async | `celery.py` + tasks | `process_statement`/seed viram tasks |

---

## 6. Ordem de implementação sugerida (do maior ganho ao mais avançado)

1. **Índice `(user, -date, -id)` + cursor pagination.** Maior ganho, zero infra nova.
   Resolve a paginação profunda que é o sintoma mais visível em escala.
2. **Redis + cache da agregação do dashboard** (use case A) com version-key. Deixa o
   dashboard instantâneo nas re-aberturas.
3. **Cache de categorias e do count** (use cases B e C).
4. **Rate limiting** no demo/login (use case D) — barato e protege.
5. **GIN trigram** na busca por descrição (quando a busca textual virar gargalo).
6. **Celery** para imports/seed assíncronos (use case E).
7. **`tenant_id` + RLS + particionamento por mês** — o passo "B2B de verdade", maior e
   mais invasivo; faça quando o multi-tenant sair do papel.

---

## 7. Armadilhas comuns

- **Cachear antes de indexar**: o miss continua lento e a invalidação vira pesadelo.
  Índice e paginação primeiro.
- **Chave de cache sem tenant**: vazamento de dados entre tenants. Toda chave **tem**
  que incluir `user_id`/`tenant_id`.
- **`COUNT(*)` exato em milhões**: troque por count aproximado
  (`reltuples` do `pg_class`) ou cacheado quando exatidão não for crítica.
- **Cursor pagination com ordenação não-única**: pula/duplica linhas. Sempre inclua o
  `id` como desempate (`("-date", "-id")`).
- **Invalidação manual chave-a-chave**: use o padrão version-key e durma tranquilo.

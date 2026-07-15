# Auth System — Como Funciona e Por Que

Documento educacional completo sobre o sistema de autenticação do FinTrack.
Cobre hooks, lifecycle, JWT, interceptors e decisões de design.

---

## 1. Visão geral do fluxo

```
Usuário digita email/senha
       ↓
  Login.jsx chama login() do AuthContext
       ↓
  POST /auth/token/ → Django retorna access_token + refresh_token
       ↓
  Tokens salvos no localStorage
       ↓
  fetchUser() busca /auth/me/ → seta user no context
       ↓
  Toda requisição subsequente: interceptor do Axios injeta Bearer token
       ↓
  Quando access_token expira (1h):
    → Interceptor tenta refresh automático (POST /auth/token/refresh/)
    → Se refresh ok: novo access_token, refaz a requisição original
    → Se refresh falhou: dispara custom event auth:expired
       ↓
  AuthContext ouve o evento → remove tokens → seta sessionExpired=true
       ↓
  Modal em App.jsx aparece sobre a página atual
       ↓
  Usuário clica Sign in → logout() + navigate('/login')
```

---

## 2. Os arquivos e suas responsabilidades

| Arquivo | Papel |
|---------|-------|
| `axiosConfig.js` | Instância Axios com interceptors de request e response |
| `AuthContext.jsx` | Estado global de autenticação (user, loading, sessionExpired) |
| `App.jsx` | Renderiza o `SessionExpiredModal` no nível do Router |
| `PrivateRoute.jsx` | Guarda rotas privadas — redireciona para /login se não autenticado |
| `Login.jsx` | Formulário de login |
| `Register.jsx` | Formulário de registro |

---

## 3. React Context API — o que é e por que usar

**Problema**: `user` (quem está logado) precisa ser acessível em qualquer componente —
Navbar, Dashboard, PrivateRoute, modais. Passar via props por cada nível seria prop drilling.

**Solução**: Context cria um "estado global" que qualquer componente filho pode consumir.

```jsx
// Criação do context
const AuthContext = createContext();

// Provider: envolve a árvore e disponibiliza os valores
export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    return (
        <AuthContext.Provider value={{ user, setUser }}>
            {children}
        </AuthContext.Provider>
    );
};

// Hook customizado: esconde o useContext para quem consome
export const useAuth = () => useContext(AuthContext);

// Uso em qualquer componente na árvore:
const { user } = useAuth();
```

No `App.jsx`, `AuthProvider` envolve o Router inteiro — então qualquer componente
pode chamar `useAuth()` e ter acesso a `user`, `login`, `logout`, `sessionExpired`, etc.

---

## 4. useState — o hook básico de estado

```jsx
const [user, setUser] = useState(null);
//     ^^^^  ^^^^^^^   ^^^^^^^^^^^^
//     valor  setter    valor inicial
```

- `user` é a variável de leitura
- `setUser(novoValor)` atualiza o estado E provoca um re-render do componente
- O valor inicial (`null`) só é usado na primeira renderização

**Regra fundamental**: nunca mute o estado diretamente. Sempre use o setter.

```jsx
// ERRADO — mutação direta não provoca re-render
user.name = 'Pedro';

// CERTO — cria um novo objeto com a mudança
setUser({ ...user, name: 'Pedro' });
```

---

## 5. useEffect — efeitos colaterais e ciclo de vida

`useEffect` substitui os lifecycle methods de classes (`componentDidMount`,
`componentDidUpdate`, `componentWillUnmount`). É onde você escreve código que
interage com o "mundo externo": APIs, localStorage, event listeners, timers.

### Anatomia

```jsx
useEffect(() => {
    // código do efeito — roda APÓS o render

    return () => {
        // função de cleanup — roda ANTES do próximo efeito ou quando o componente desmonta
    };
}, [dependência1, dependência2]); // array de dependências
```

### Os três comportamentos pelo array de deps

```jsx
// Sem array: roda após CADA render — quase sempre é bug, evite
useEffect(() => { console.log('rodou'); });

// Array vazio []: roda UMA VEZ após a montagem inicial (componentDidMount)
useEffect(() => { fetchUser(); }, []);

// Com deps: roda após montar E toda vez que uma dep mudar (componentDidUpdate)
useEffect(() => { fetchData(); }, [userId]);
```

### No AuthContext.jsx — dois useEffects

**Primeiro** — ouve o evento customizado de sessão expirada:
```jsx
useEffect(() => {
    const handle = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setSessionExpired(true);
        // Não chama logout() — mantém user no state para PrivateRoute não redirecionar.
        // O modal em App.jsx controla a navegação.
    };
    window.addEventListener('auth:expired', handle);

    // Cleanup: remove o listener quando o componente desmonta.
    // Sem isso, addEventListener acumularia listeners duplicados a cada re-mount.
    return () => window.removeEventListener('auth:expired', handle);
}, []); // array vazio = registra o listener UMA VEZ na montagem
```

**Segundo** — restaura a sessão ao recarregar a página:
```jsx
useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) { setLoading(false); return; } // sem token: nada a restaurar

    fetchUser()
        .catch(() => logout())      // token expirado → limpa e vai para login
        .finally(() => setLoading(false));
}, [fetchUser, logout]); // deps: funções estabilizadas por useCallback (ver seção 6)
```

Por que as deps `[fetchUser, logout]`? React exige que toda função usada dentro de um
efeito esteja no array — caso contrário você usa uma versão "stale" (desatualizada) da
função. `useCallback` garante que essas funções não mudam de referência entre renders,
então o efeito roda apenas uma vez na prática.

---

## 6. useCallback — memorizar funções

**Problema**: em React, a cada re-render do componente, todas as funções declaradas
dentro dele são recriadas. Função nova = referência nova. Isso importa quando a função
entra no array de deps de um `useEffect` (causaria loop) ou é passada como prop para
um componente memoizado.

```jsx
// SEM useCallback: logout é uma função NOVA a cada render
const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
};

// COM useCallback: logout é a MESMA referência enquanto as deps não mudarem
const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    setSessionExpired(false);
}, []); // deps []: logout nunca recria (não usa nada do escopo externo que mude)
```

### useCallback no AuthContext

```jsx
const logout = useCallback(() => { ... }, []);
// Deps []: logout nunca muda de referência após a montagem.

const fetchUser = useCallback(async () => {
    const res = await axiosInstance.get('/auth/me/');
    setUser(res.data);
}, []);
// Deps []: axiosInstance é um singleton importado — não muda nunca.
```

Resultado: `logout` e `fetchUser` têm referências estáveis → entram no array de deps
do `useEffect` sem causar loop infinito.

### Quando NÃO usar useCallback

Quando a função não vai para deps de useEffect nem para props de componentes memoizados
(React.memo), `useCallback` só adiciona complexidade sem benefício. Não saia colocando
`useCallback` em tudo — cada hook tem custo de memória.

---

## 7. useMemo — memorizar valores computados

`useCallback` memoriza funções. `useMemo` memoriza valores derivados caros de computar.

```jsx
// SEM useMemo: recalcula em CADA render, mesmo que transactions não tenha mudado
const total = transactions.reduce((sum, t) => sum + t.amount, 0);

// COM useMemo: só recalcula quando transactions mudar
const total = useMemo(() => {
    return transactions.reduce((sum, t) => sum + t.amount, 0);
}, [transactions]);
```

**No FinTrack atualmente**: `useMemo` ainda não é usado porque não há computações
pesadas que causem lentidão visível. Você vai querer quando tiver agregações de dados
para os gráficos (somar por categoria, agrupar por mês, etc.).

**Regra de ouro**: não otimize antes de ter problema. Se o re-render é perceptivelmente
lento, meça com o React DevTools Profiler, aí aplique `useMemo`. Premature optimization.

---

## 8. O interceptor do Axios — request e response

Axios permite interceptar toda requisição antes de sair e toda resposta antes de chegar
no `.then()`. É o lugar certo para lógica cross-cutting: autenticação, refresh automático.

### Interceptor de request (injeta o token)

```jsx
axiosInstance.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config; // obrigatório — devolve a config modificada
}, (error) => Promise.reject(error));
```

Roda antes de qualquer requisição sair. Se não devolver `config`, a requisição trava.

### Interceptor de response (refresh automático)

```jsx
axiosInstance.interceptors.response.use(
    res => res, // resposta ok: passa direto

    async err => {
        const original = err.config; // a requisição que falhou

        // Só nos importa 401 (não autorizado — token expirado ou inválido)
        if (err.response?.status !== 401) return Promise.reject(err);

        // Se o próprio refresh falhou: sessão morreu de vez
        if (original.url?.includes('token/refresh')) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.dispatchEvent(new CustomEvent('auth:expired'));
            return Promise.reject(err);
        }

        // Evita loop: marca que já tentou retry nessa requisição
        if (original._retry) return Promise.reject(err);
        original._retry = true;

        const refresh = localStorage.getItem('refresh_token');
        if (!refresh) {
            window.dispatchEvent(new CustomEvent('auth:expired'));
            return Promise.reject(err);
        }

        try {
            const { data } = await axiosInstance.post('/auth/token/refresh/', { refresh });
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh); // rotação de token
            return axiosInstance(original); // refaz a requisição original com o novo token
        } catch {
            window.dispatchEvent(new CustomEvent('auth:expired'));
            return Promise.reject(err);
        }
    }
);
```

**Fluxo completo quando o access_token expira:**
1. Componente faz `GET /finances/transactions/`
2. Interceptor de request injeta o token expirado no header
3. Django retorna 401
4. Interceptor de response intercepta o 401
5. Checa: não é URL de refresh, não é `_retry` → tenta refresh
6. Faz `POST /auth/token/refresh/` com o refresh_token salvo
7. Django valida e retorna novos tokens (`ROTATE_REFRESH_TOKENS=True`)
8. Salva novos tokens no localStorage
9. Refaz a requisição original (`GET /finances/transactions/`) com o novo token
10. Componente recebe a resposta normalmente — nem percebeu que houve um refresh

---

## 9. Custom Events — comunicação entre módulos desacoplados

`axiosConfig.js` não tem acesso ao `AuthContext`. Não pode chamar `setSessionExpired(true)`
diretamente. Solução: usar o `window` como barramento de eventos.

```jsx
// Em axiosConfig.js — publica o evento (não sabe quem vai ouvir)
window.dispatchEvent(new CustomEvent('auth:expired'));

// Em AuthContext.jsx — subscreve o evento (não sabe quem publicou)
window.addEventListener('auth:expired', handle);
```

Este é o padrão Pub/Sub (Publisher-Subscriber). O Axios publica. O AuthContext escuta.
Nenhum dos dois sabe da existência do outro — isso é desacoplamento.

**Por que não chamar logout() direto do interceptor?**
`logout()` usa `setUser` — uma função do React que só funciona dentro de um componente
ou hook. Chamá-la de dentro do Axios (JavaScript puro fora do React) quebraria as regras
dos hooks e causaria erros em runtime. O custom event é a ponte segura.

---

## 10. PrivateRoute — guardião de rota

```jsx
const PrivateRoute = ({ children }) => {
    const { user, loading } = useAuth();

    if (loading) return <div className="loading-screen">Loading...</div>;
    if (!user) return <Navigate to="/login" replace />;

    return children;
};
```

**Por que o `loading` existe?** Na inicialização, o AuthContext verifica se há token
salvo e chama `fetchUser()` assincronamente. Sem o `loading`, o componente renderizaria
`<Navigate to="/login">` imediatamente — mesmo com token válido — porque `user` ainda
é `null` enquanto a requisição está em andamento.

`loading=true` durante o check → PrivateRoute mostra loading screen → `fetchUser()` resolve
→ `user` fica preenchido → PrivateRoute renderiza os filhos. Sem flash de redirect indevido.

---

## 11. O modal de sessão expirada — por que ficou em App.jsx

**Problema anterior**: o modal ficava em `Login.jsx` como um banner. Quando a sessão
expirava, `logout()` era chamado imediatamente → `user=null` → `PrivateRoute` redirecionava
para `/login` → só então o banner aparecia. A experiência: tela muda abruptamente.

**Solução atual**: o modal fica em `App.jsx`, dentro do Router mas fora das Routes.

O `auth:expired` handler **não chama `logout()`** — apenas remove os tokens do localStorage
e seta `sessionExpired=true`. O `user` permanece no state → `PrivateRoute` não redireciona →
o modal aparece em cima da página atual.

```jsx
const SessionExpiredModal = () => {
    const { sessionExpired, logout } = useAuth();
    const navigate = useNavigate();

    if (!sessionExpired) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-card">
                <div className="modal-title">Session Expired</div>
                <div className="modal-description">
                    Your session has expired. Please sign in again to continue.
                </div>
                <button className="modal-btn modal-btn--confirm" onClick={() => {
                    logout();         // agora sim: limpa user + tokens + sessionExpired
                    navigate('/login');
                }}>
                    Sign in
                </button>
            </div>
        </div>
    );
};
```

**Por que `useNavigate` exige estar dentro do Router?**
`useNavigate` lê o context do React Router. Se o componente fosse definido fora de
`<Router>`, o hook não encontraria o context e jogaria um erro. Por isso `SessionExpiredModal`
é definido dentro do arquivo `App.jsx` (mas antes da função `App`), e renderizado dentro
do `<Router>`.

---

## 12. Tokens no localStorage — riscos e alternativas

**Risco**: XSS (Cross-Site Scripting). Se um script malicioso rodar na sua página,
ele pode ler `localStorage.getItem('access_token')` e exfiltrar o token.

**Alternativa segura**: httpOnly cookies. O browser não expõe cookies `httpOnly` para
JavaScript — só os envia automaticamente em cada requisição. O backend os configura.

| | localStorage | httpOnly cookie |
|--|--|--|
| Legível por JS | Sim (risco XSS) | Não (mais seguro) |
| Enviado automaticamente | Não (manual via header) | Sim |
| Risco de CSRF | Não | Sim (precisa de CSRF token) |
| Multi-domínio | Simples | Mais complexo |
| Implementação atual | Sim | Requer mudança no backend |

Para um projeto pessoal, localStorage é aceitável. Para produção com dados sensíveis
de usuários terceiros, migrar para httpOnly cookies é a decisão correta.

---

## 13. Tempo de vida dos tokens (settings.py)

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),   # expira em 1h
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),   # expira em 7 dias
    "ROTATE_REFRESH_TOKENS": True,                 # cada refresh gera novo refresh token
}
```

**Por que ROTATE_REFRESH_TOKENS=True?** A cada refresh, o Django invalida o refresh_token
anterior e retorna um novo. Isso evita que um refresh token roubado dure 7 dias inteiros —
se o usuário continuar usando o app, o token rotaciona e o roubado se torna inválido.

---

## 14. Diagrama de estados

```
  app abre
      ↓
  loading=true → fetchUser() → token válido? → sim → user={...}, loading=false
                                             → não → logout(), loading=false
                                                       user=null → /login
      ↓ (usuário autenticado)
  usando o app normalmente
      ↓
  access_token expira → 401 → interceptor faz refresh → ok → segue normalmente
                                                       → falhou → auth:expired
      ↓
  sessionExpired=true → modal aparece sobre a tela atual
      ↓
  usuário clica "Sign in" → logout() + navigate('/login')
      ↓
  user=null, sessionExpired=false → login page
```

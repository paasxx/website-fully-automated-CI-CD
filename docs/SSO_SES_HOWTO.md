# How To: Google SSO + Password Reset via AWS SES

Guia de implementação futura. Pré-requisito: app funcionando em produção com domínio configurado.

---

## Parte 1 — Password Reset via AWS SES

### O que vai funcionar ao final

1. Usuário clica "Forgot password?" no login
2. Digita o email → Django envia um link de reset via SES
3. Usuário abre o email, clica no link
4. Frontend exibe formulário de nova senha
5. Submit → Django valida o token e atualiza a senha

---

### 1.1 Configurar AWS SES

**No Console AWS:**

1. Acesse **SES → Verified identities → Create identity**
2. Escolha **Email address** e verifique seu email (ou domínio inteiro para produção)
3. Para domínio: SES exige que você adicione registros DNS (DMARC, DKIM) — guarda os valores que aparecerão
4. Vá para **SES → SMTP settings → Create SMTP credentials**
   - Isso cria um usuário IAM com permissão de envio via SMTP
   - Guarda o SMTP username e password gerados (aparecem UMA vez)

**Verificar que SES não está em Sandbox:**
Por padrão a conta fica em Sandbox (só envia para emails verificados).
Para produção: SES → Account dashboard → Request production access.

---

### 1.2 Configurar Django para envio de email

Instalar o pacote de reset:
```bash
pip install django-rest-passwordreset
```

Em `requirements.txt`:
```
django-rest-passwordreset==1.3.0
```

Em `settings.py` — adicionar config de email:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'  # ajuste a região
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ['SES_SMTP_USERNAME']
EMAIL_HOST_PASSWORD = os.environ['SES_SMTP_PASSWORD']
DEFAULT_FROM_EMAIL = 'noreply@candlefarm.com.br'  # deve ser o domínio verificado no SES
```

Em `INSTALLED_APPS`:
```python
'django_rest_passwordreset',
```

Em `identity/urls.py` ou `fintrack/urls.py`:
```python
path('auth/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
```

Isso expõe:
- `POST /auth/password_reset/` — envia o email
- `POST /auth/password_reset/confirm/` — confirma com o token e nova senha

---

### 1.3 Customizar o email enviado

Crie `identity/signals.py`:
```python
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created
from django.core.mail import send_mail

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    frontend_url = 'https://www.candlefarm.com.br'
    reset_link = f'{frontend_url}/reset-password?token={reset_password_token.key}'

    send_mail(
        subject='FinTrack — Reset your password',
        message=f'Click the link to reset your password: {reset_link}\n\nThis link expires in 24 hours.',
        from_email='noreply@candlefarm.com.br',
        recipient_list=[reset_password_token.user.email],
        fail_silently=False,
    )
```

Wire em `identity/apps.py`:
```python
def ready(self):
    import identity.signals  # noqa
```

---

### 1.4 Frontend — "Forgot password?" flow

**Novos arquivos:**
- `pages/ForgotPassword.jsx` — formulário que pede o email
- `pages/ResetPassword.jsx` — formulário que pede nova senha (lê token da URL)

**Rota em App.jsx:**
```jsx
<Route path="/forgot-password" element={<ForgotPassword />} />
<Route path="/reset-password" element={<ResetPassword />} />
```

**ForgotPassword.jsx — resumo:**
```jsx
const handleSubmit = async (e) => {
    e.preventDefault();
    await axiosInstance.post('/auth/password_reset/', { email });
    setStatus('sent'); // mostra mensagem: "Check your inbox"
};
```

**ResetPassword.jsx — resumo:**
```jsx
const token = new URLSearchParams(location.search).get('token');

const handleSubmit = async (e) => {
    e.preventDefault();
    await axiosInstance.post('/auth/password_reset/confirm/', {
        token,
        password: newPassword,
    });
    navigate('/login');
};
```

**Link no Login.jsx** (após o botão de submit):
```jsx
<p className="login-footer-link">
    <Link to="/forgot-password">Forgot your password?</Link>
</p>
```

---

### 1.5 GitHub Secrets necessários

```
SES_SMTP_USERNAME   → usuário SMTP gerado no SES
SES_SMTP_PASSWORD   → senha SMTP gerada no SES
```

No Terraform prod, adicionar ao backend task:
```hcl
{ name = "SES_SMTP_USERNAME",  value = var.ses_smtp_username },
{ name = "SES_SMTP_PASSWORD",  value = var.ses_smtp_password },
```

---

## Parte 2 — Google SSO

### O que vai funcionar ao final

1. Botão "Continue with Google" no login/registro
2. Usuário autoriza → Google retorna um `id_token`
3. Frontend manda esse token para o backend: `POST /auth/google/`
4. Backend valida com Google, cria ou encontra o usuário, retorna JWT do FinTrack
5. Usuário está autenticado normalmente

---

### 2.1 Google Cloud Console — criar OAuth client

1. Acesse **console.cloud.google.com**
2. Crie um projeto (ou use um existente)
3. **APIs & Services → Credentials → Create credentials → OAuth 2.0 Client ID**
4. Application type: **Web application**
5. Authorized JavaScript origins:
   - `http://localhost:3000` (dev)
   - `https://www.candlefarm.com.br` (prod)
6. Authorized redirect URIs: não necessário para o fluxo com token (implicit flow)
7. Copie o **Client ID** gerado (ex: `123456789-abc.apps.googleusercontent.com`)

---

### 2.2 Backend — validar o token Google

Instalar:
```bash
pip install social-auth-app-django
# ou a alternativa mais simples:
pip install google-auth
```

**Usando `google-auth` (mais simples, sem django-allauth):**

Crie `identity/views.py` — adicionar nova view:
```python
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

User = get_user_model()
GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']

class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        credential = request.data.get('credential')  # id_token do Google
        try:
            info = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                GOOGLE_CLIENT_ID,
            )
        except ValueError:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        email = info['email']
        first_name = info.get('given_name', '')
        last_name = info.get('family_name', '')

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': first_name,
                'last_name': last_name,
            }
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })
```

URL em `identity/urls.py`:
```python
path('auth/google/', GoogleLoginView.as_view(), name='google-login'),
```

Instalar o pacote:
```bash
pip install google-auth
```

Em `requirements.txt`:
```
google-auth==2.28.0
```

---

### 2.3 Frontend — botão Google

Instalar:
```bash
cd frontend/front
npm install @react-oauth/google
```

Em `App.jsx` — envolver com o provider Google:
```jsx
import { GoogleOAuthProvider } from '@react-oauth/google';

// Envolver tudo dentro de:
<GoogleOAuthProvider clientId="SEU_CLIENT_ID_AQUI">
    <ThemeProvider>
        <AuthProvider>
            ...
        </AuthProvider>
    </ThemeProvider>
</GoogleOAuthProvider>
```

Em `Login.jsx` e `Register.jsx`:
```jsx
import { GoogleLogin } from '@react-oauth/google';

// Adicionar no JSX (abaixo do form):
<div className="login-divider"><span>or</span></div>

<GoogleLogin
    onSuccess={async (credentialResponse) => {
        const res = await axiosInstance.post('/auth/google/', {
            credential: credentialResponse.credential,
        });
        localStorage.setItem('access_token', res.data.access);
        localStorage.setItem('refresh_token', res.data.refresh);
        await fetchUser(); // ou chamar login() do context adaptado
        navigate('/dashboard');
    }}
    onError={() => setError('Google login failed.')}
    width="100%"
/>
```

CSS para o divider:
```scss
.login-divider {
    display: flex;
    align-items: center;
    gap: $space-sm;
    color: var(--text-color);
    opacity: 0.4;
    font-size: 12px;

    &::before, &::after {
        content: '';
        flex: 1;
        height: 1px;
        background: var(--border-color);
    }
}
```

---

### 2.4 GitHub Secrets necessários

```
GOOGLE_CLIENT_ID   → Client ID do Google Cloud Console
```

No Terraform prod, adicionar ao backend task:
```hcl
{ name = "GOOGLE_CLIENT_ID", value = var.google_client_id },
```

---

## Ordem de implementação recomendada

```
1. SES configurado e verificado na AWS Console
2. django-rest-passwordreset instalado e URLs expostas
3. Signal de email customizado
4. Frontend: ForgotPassword + ResetPassword pages
5. Testar fluxo completo de reset
--- (semana seguinte) ---
6. Google Cloud Console: criar OAuth client
7. google-auth instalado no backend
8. GoogleLoginView criada e testada
9. Frontend: @react-oauth/google instalado
10. GoogleOAuthProvider adicionado no App.jsx
11. GoogleLogin button nas páginas de login/register
12. Testar fluxo completo SSO
```

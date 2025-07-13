# Roadmap Técnico - Projeto Mini Dropbox com OCR, Fila e AI (React + Django + AWS)

## Objetivo Geral

Desenvolver um projeto completo que simula um mini Dropbox, com upload de arquivos para o Amazon S3 utilizando **presigned URLs**, processamento assíncrono via **fila (SQS)**, OCR (reconhecimento de texto), thumbnails automáticas e autenticação robusta. O sistema será modular, organizado e escalável, com infraestrutura como código (IaC) e deploy contínuo via CI/CD.

---

## Etapa 1: Organização e Arquitetura Inicial

### Estrutura de Pastas e Boas Práticas

**Frontend (React)**

* Separar por domínio de responsabilidade:

  * `components/`: componentes reutilizáveis (ex: `UploadButton`, `ThumbnailCard`)
  * `pages/`: telas do sistema (`Home`, `Login`, `Dashboard`, `NotFound`)
  * `hooks/`: custom hooks (ex: `useAuth`, `useUpload`)
  * `contexts/`: gerenciamento global de estado (`AuthContext`, `UploadContext`)
  * `services/`: API (axiosInstance, chamadas HTTP)
  * `styles/`: temas, design tokens e centralização de CSS/SCSS
  * `assets/`: imagens, fontes e ícones reutilizáveis
  * `utils/`: funções utilitárias, helpers e validações

**Backend (Django)**

* App Django principal separado em apps reutilizáveis:

  * `auth`: gerenciamento de usuários e login
  * `storage`: upload, download, metadata
  * `processing`: OCR, thumbnails, fila
  * `core`: configurações globais, middlewares, base utils
* Arquitetura limpa com diretórios para:

  * `views/`, `services/`, `models/`, `serializers/`, `tasks/`
  * Uso de Celery + Redis para tarefas assíncronas
  * Design patterns (Repository, Service Layer)

---

## Etapa 2: Design e Identidade Visual

### Planejamento de UX/UI

* Criar um layout base no Figma (ou similar)
* Inspirar-se em Dropbox, Google Drive e Notion
* Criar um tema de design (colors, font, spacing) reutilizável
* Telas mínimas para o MVP:

  * Login e Cadastro
  * Dashboard de arquivos (cards/listagem)
  * Tela de upload
  * Tela de visualização de arquivo (preview/thumbnail)

---

## Etapa 3: MVP Funcional (Frontend + Backend)

### Backend (Django)

* [ ] Autenticação (JWT ou Session com CSRF)
* [ ] Endpoints para:

  * [ ] Upload com presigned URL
  * [ ] Listagem de arquivos
  * [ ] Detalhes por arquivo (metadata, status de processamento)
  * [ ] Geração de thumbnails/OCR via Celery + SQS

### Frontend (React)

* [ ] Tela de login com autenticação via API
* [ ] Tela de upload usando o presigned URL
* [ ] Tela de listagem com thumbnails
* [ ] Página de erro 404 + loading screens

---

## Etapa 4: Integrações AWS (S3, SQS, Lambda, etc)

* [ ] Integração com Amazon S3:

  * Upload via presigned URL
  * Política pública restrita de leitura/download
* [ ] Integração com Amazon SQS:

  * Após upload, mensagem é enviada para fila
  * Worker no backend processa OCR ou thumbnail
* [ ] Integração futura com Lambda ou Rekognition (AI)

  * Para reconhecimento de conteúdo e tags automáticas

---

## Etapa 5: Autenticação Segura

* [ ] Implementar tela de login com validação robusta
* [ ] Criar sistema de autenticação com JWT (ou session + CSRF token)
* [ ] Proteger rotas privadas no React com AuthContext
* [ ] Criar integração com SNS ou SES para recuperação de senha

---

## Etapa 6: Ambiente de Desenvolvimento Local

* [x] Backend e Frontend com Dockerfile de desenvolvimento
* [x] `docker-compose` para orquestrar serviços:

  * [x] Django + Postgres
  * [x] React
  * [x] Volume para persistência do banco e node\_modules
* [ ] Scripts de migração e criação automática de superusuário
* [ ] Gerenciamento de envs locais: `.env.dev`, `.env.prod`

---

## Etapa 7: Deploy + CI/CD AWS

* [x] Deploy automatizado com Terraform (VPC, ECS, ALB, SGs)
* [x] CI/CD no GitHub Actions com 4 pipelines distintas:

  * [x] Infraestrutura (terraform apply, backend remoto em S3 + DynamoDB)
  * [x] Hosted Zone + DNS (aponta domínio para os ALBs)
  * [x] Certificados HTTPS com ACM (para subdomínios www e api)
  * [x] Pipeline de Destroy (inclusive backend remoto)
* [ ] Automatizar uso de ACM com HTTPS na API exposta
* [ ] Deploy automatizado do conteúdo estático do frontend

---

## Etapa 8: Observabilidade e Escalabilidade

* [ ] Configurar logs no CloudWatch
* [ ] Configurar métricas básicas (CPU, memória, fila)
* [ ] Planejar Auto Scaling baseado na fila ou CPU
* [ ] Adicionar tags de rastreabilidade nos arquivos S3

---

## Etapa 9: Documentação e Modularização

* [x] Criar pasta `/docs/` com documentação dividida:

  * [x] infraestrutura.md
  * [x] ci-cd.md
  * [x] nginx.md
  * [x] erros-e-aprendizados.md
  * [x] local-dev.md
  * [x] bind-mounts.md
  * [ ] s3-upload.md
  * [ ] queue-processing.md
* [ ] Diagramas draw\.io com arquitetura atual e futura

---

## Etapa 10: Expansões Futuras

* [ ] Compartilhamento de arquivos via link
* [ ] Geração de PDF OCR com visualização integrada
* [ ] Reconhecimento de texto com AWS Textract ou Google Vision
* [ ] Upload de vídeo e geração de thumbnails automáticas
* [ ] Frontend mobile-friendly com PWA
* [ ] Interface multilíngue (i18n)
* [ ] CDN para arquivos públicos via CloudFront

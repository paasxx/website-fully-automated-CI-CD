# ============================================================
#  Projeto: Mini Dropbox — comandos locais e de deploy
#  Uso: make <target>   |   make help para listar todos
# ============================================================

COMPOSE_DEV   = docker-compose/docker-compose.dev.yml
COMPOSE_TESTS = docker-compose/docker-compose-tests.yml
BACK          = back
FRONT         = front
DB            = fintrack-db

AWS_REGION     ?= us-east-1
AWS_ACCOUNT_ID ?= $(shell aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "ACCOUNT_ID_NOT_SET")
ECR_BACK        = $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/backend-repo
ECR_FRONT       = $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/frontend-repo
ECS_CLUSTER     = dev-cluster

.PHONY: help \
        up down restart build \
        start-back start-front dev \
        logs logs-back logs-front logs-db \
        shell-back shell-front shell-db \
        migrate makemigrations createsuperuser \
        seed clear-transactions \
        test \
        clean clean-images \
        ecr-login push-back push-front push-all deploy-ecs deploy

# ── Help ────────────────────────────────────────────────────

help: ## Lista todos os comandos disponíveis
	@echo ""
	@echo "  \033[1mComandos disponíveis:\033[0m"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── Containers ──────────────────────────────────────────────

up: ## Sobe todos os containers (build incluso)
	docker-compose -f $(COMPOSE_DEV) up -d --build

down: ## Para e remove todos os containers
	docker-compose -f $(COMPOSE_DEV) down

restart: down up ## Reinicia tudo do zero

build: ## Reconstrói as imagens sem subir
	docker-compose -f $(COMPOSE_DEV) build

# ── Servidores de desenvolvimento ───────────────────────────
#
#  Os containers sobem com tail/sleep para manter vivos.
#  Estes targets iniciam os servidores dentro dos containers.
#  Os logs aparecem em: make logs-back / make logs-front

start-back: ## Inicia o Django runserver dentro do container (background)
	docker exec -d $(BACK) bash -c \
		"cd /app && python manage.py runserver 0.0.0.0:8000 > /proc/1/fd/1 2>&1"
	@echo "Backend iniciado em http://localhost:8000"

start-front: ## Inicia o npm start dentro do container (background)
	docker exec -d $(FRONT) sh -c \
		"cd /app && npm start > /proc/1/fd/1 2>&1"
	@echo "Frontend iniciado em http://localhost:3000  (aguarde ~20s para compilar)"

dev: up migrate start-back start-front ## Fluxo completo: sobe, migra e inicia ambos os servidores
	@echo ""
	@echo "  \033[32m✓ Ambiente local pronto\033[0m"
	@echo "  Frontend : http://localhost:3000"
	@echo "  Backend  : http://localhost:8000"
	@echo "  Logs     : make logs"
	@echo ""

# ── Logs ────────────────────────────────────────────────────

logs: ## Logs de todos os containers (follow)
	docker-compose -f $(COMPOSE_DEV) logs -f

logs-back: ## Logs só do backend
	docker logs -f $(BACK)

logs-front: ## Logs só do frontend
	docker logs -f $(FRONT)

logs-db: ## Logs só do banco
	docker logs -f $(DB)

# ── Shells ──────────────────────────────────────────────────

shell-back: ## Entra no container do backend
	docker exec -it $(BACK) bash

shell-front: ## Entra no container do frontend
	docker exec -it $(FRONT) sh

shell-db: ## Abre psql no container do banco
	docker exec -it $(DB) psql -U fintrack_user -d fintrack_db

# ── Django ──────────────────────────────────────────────────

migrate: ## makemigrations (todos os apps) + migrate
	docker exec $(BACK) bash -c "cd /app && python manage.py makemigrations identity statements finances && python manage.py migrate"

makemigrations: ## Só gera os arquivos de migration
	docker exec $(BACK) bash -c "cd /app && python manage.py makemigrations"

migrations-apply: ## Só aplica migrations existentes
	docker exec $(BACK) bash -c "cd /app && python manage.py migrate"

createsuperuser: ## Cria superuser Django (interativo)
	docker exec -it $(BACK) bash -c "cd /app && python manage.py createsuperuser"

# ── Seed / dados de teste ───────────────────────────────────
#
#  Gera transações sintéticas direto no banco (bypass dos parsers) para
#  testar escalabilidade. Edite backend/fintrack/seed_config.yml para mudar
#  o usuário-alvo, a quantidade, os bancos, o range de datas, etc.
#  O usuário precisa estar registrado antes (categorias nascem no registro).

seed: ## Gera transações sintéticas em massa (config: backend/fintrack/finances/seed_config.yml)
	docker exec $(BACK) bash -c "cd /app && python manage.py seed_transactions --config finances/seed_config.yml"

clear-transactions: ## Apaga TODAS as transações de um usuário — uso: make clear-transactions EMAIL=teste@gmail.com
	docker exec $(DB) psql -U fintrack_user -d fintrack_db \
		-c "DELETE FROM finances_transaction WHERE user_id=(SELECT id FROM identity_user WHERE email='$(EMAIL)');"

# ── Testes ──────────────────────────────────────────────────

test: ## Roda suite de testes via docker-compose-tests
	docker-compose -f $(COMPOSE_TESTS) up -d --build db web
	@echo "Aguardando containers de teste..."
	@sleep 6
	docker exec $(BACK) bash -c "cd /app && chmod +x ./tests.sh && ./tests.sh"
	docker-compose -f $(COMPOSE_TESTS) down

# ── Limpeza ─────────────────────────────────────────────────

clean: ## Remove containers, volumes e orphans
	docker-compose -f $(COMPOSE_DEV) down -v --remove-orphans

clean-images: ## Remove imagens locais back e front
	docker rmi $(BACK) $(FRONT) 2>/dev/null || true

# ── AWS / Deploy ────────────────────────────────────────────

ecr-login: ## Autentica Docker no ECR
	@echo "Autenticando no ECR (conta $(AWS_ACCOUNT_ID), região $(AWS_REGION))..."
	aws ecr get-login-password --region $(AWS_REGION) \
		| docker login --username AWS --password-stdin \
		  $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

push-back: ecr-login ## Build + push da imagem do backend para o ECR
	docker buildx build --platform linux/amd64 \
		-f backend/Dockerfile.prod \
		-t $(ECR_BACK):latest \
		--push ./backend

push-front: ecr-login ## Build + push da imagem do frontend para o ECR
	docker buildx build --platform linux/amd64 \
		-f frontend/Dockerfile.prod \
		-t $(ECR_FRONT):latest \
		--push ./frontend

push-all: push-back push-front ## Build + push de ambas as imagens

deploy-ecs: ## Força o ECS a puxar as novas imagens (force-new-deployment)
	aws ecs update-service \
		--cluster $(ECS_CLUSTER) \
		--service backend-service \
		--force-new-deployment \
		--region $(AWS_REGION)
	aws ecs update-service \
		--cluster $(ECS_CLUSTER) \
		--service frontend-service \
		--force-new-deployment \
		--region $(AWS_REGION)
	@echo "Deploy disparado. Acompanhe em:"
	@echo "  https://console.aws.amazon.com/ecs/home?region=$(AWS_REGION)"

deploy: push-all deploy-ecs ## Pipeline completo: push das imagens + atualiza ECS

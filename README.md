# Comparativo de Vulnerabilidades em Código Gerado por LLMs

Ambiente completo para comparar vulnerabilidades em código gerado por **ChatGPT, Gemini e Claude** em 4 linguagens (**Python, Java, JavaScript, TypeScript**) através de 5 casos de teste, usando análise estática (SAST) e dinâmica (DAST).

## Ferramentas usadas

| Tipo | Ferramenta | Linguagens |
|------|------------|------------|
| SAST | Bandit | Python |
| SAST | Semgrep | Todas (cobertura ampla via rulesets oficiais) |
| SAST | SpotBugs + find-sec-bugs | Java |
| SAST | ESLint + plugins de segurança | JavaScript, TypeScript |
| DAST | OWASP ZAP (Docker, baseline/full scan) | Qualquer app HTTP |

## Estrutura

```
llm-security-comparison/
├── codigos/
│   └── caso01_auth/
│       ├── chatgpt/{python,java,javascript,typescript}/
│       ├── gemini/{...}/
│       └── claude/{...}/
├── infra/                    # Docker Compose do MySQL + scripts SQL
│   ├── docker-compose.yml
│   └── mysql-init/
├── sast-configs/             # Configs do ESLint, Semgrep, SpotBugs, Bandit
├── scripts/                  # Todos os scripts de automação
├── reports/                  # Relatórios gerados (SAST + DAST)

```

## Setup inicial (uma vez só)

> Requer Fedora. Para outras distros pode haver pequenas diferenças.

```bash
cd llm-security-comparison

# Instala tudo: Python, Java 17, Node 20, Maven, Docker, Bandit, Semgrep,
# SpotBugs+find-sec-bugs, ESLint+plugins de segurança
bash scripts/setup_fedora.sh

# Se o Docker foi instalado agora, faça logout/login (ou: newgrp docker)

# Sobe o MySQL com os 5 bancos prontos
bash scripts/start_mysql.sh
```

## Credenciais e portas

**MySQL:**
- Host: `localhost`  Porta: `3306`
- Usuário (apps): `appuser` / `apppass`
- Root (admin): `root` / `rootpass`
- Bancos: `caso01_auth`, `caso02_products`, `caso03_upload`, `caso04_comments`, `caso05_session`

**Portas das aplicações** (definidas nos prompts):
| Caso | Porta | Descrição |
|------|-------|-----------|
| 01 | 8001 | Autenticação/login |
| 02 | 8002 | Busca de produtos |
| 03 | 8003 | Upload de arquivos |
| 04 | 8004 | Comentários (HTML) |
| 05 | 8005 | Sessão/admin |

## Fluxo de teste

### 1. Cole o código gerado pela LLM
Cada código vai na pasta apropriada. Exemplo para Caso 01, ChatGPT, Python:

```
codigos/caso01_auth/chatgpt/python/
├── app.py
└── requirements.txt
```

### 2. Ajuste de credenciais se necessário
As LLMs geralmente colocam `root/root` ou `localhost/3306`. Confira no código gerado se está usando:
- Host: `localhost` | Porta: `3306`
- Usuário: `appuser` | Senha: `apppass`
- Banco: `caso0X_xxx` (conforme o caso)

### 3. Roda os SAST (não precisa subir as apps)
Pode rodar **todos de uma vez**:

```bash
bash scripts/run_all_sast.sh
```

Ou ferramenta por ferramenta:

```bash
bash scripts/run_bandit.sh   codigos/caso01_auth/chatgpt/python
bash scripts/run_semgrep.sh  codigos/caso01_auth/chatgpt/python
bash scripts/run_spotbugs.sh codigos/caso01_auth/chatgpt/java
bash scripts/run_eslint.sh   codigos/caso01_auth/chatgpt/javascript
```

Relatórios em `reports/sast/<ferramenta>/<caso>_<ia>_<linguagem>.{json,txt,xml}`

Para gerar uma **tabela comparativa**:

```bash
python3 scripts/summarize_sast.py
# Saída: reports/sast/summary.csv e summary.md
```

### 4. Roda o DAST (precisa subir a app primeiro)

Suba **uma app por vez** num terminal:

```bash
# Python (Flask)
bash scripts/run_app_python.sh codigos/caso01_auth/chatgpt/python

# Java (Spring Boot)
bash scripts/run_app_java.sh   codigos/caso01_auth/chatgpt/java

# Node (JS ou TS)
bash scripts/run_app_node.sh   codigos/caso01_auth/chatgpt/javascript
bash scripts/run_app_node.sh   codigos/caso01_auth/chatgpt/typescript
```

Em outro terminal, rode o ZAP contra a porta dela:

```bash
# Baseline scan (mais rápido)
bash scripts/run_zap.sh 1 baseline chatgpt_python

# Full scan (mais demorado, mais completo)
bash scripts/run_zap.sh 1 full chatgpt_python
```

Relatórios em `reports/dast/zap_<tipo>_porta<P>_<tag>_<timestamp>.{html,json,xml}`

### 5. Resetar entre testes (opcional)

Para limpar dados entre execuções de IAs diferentes:

```bash
bash scripts/reset_db.sh 1      # reseta só o caso 01
bash scripts/reset_db.sh all    # reseta todos
```

## Comandos úteis

```bash
# Subir / parar MySQL
bash scripts/start_mysql.sh
bash scripts/stop_mysql.sh
bash scripts/stop_mysql.sh --wipe  # destrói volume também

# Ver logs do MySQL
docker logs llm-sec-mysql

# Acessar MySQL pelo cliente do container
docker exec -it llm-sec-mysql mysql -uappuser -papppass

# Listar containers
docker ps
```

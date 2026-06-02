# OWASP ZAP com autenticação (avançado)

Por padrão, `scripts/run_zap.sh` faz scan **não autenticado**. Para os Casos 01
(login com hash) e 05 (sessão), o ZAP não conseguirá rastrear endpoints que
exijam login. Isso é OK para o trabalho — o que importa é comparar IAs sob as
mesmas condições. Mas se quiser ir mais a fundo, há 3 estratégias.

## Opção A — Adicionar usuário "seed" e injetar cookie/token

A forma mais simples: antes do scan, registre um usuário via API:

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"username":"zaptest","password":"zaptest123"}' \
     http://localhost:8001/register
```

Então use o `zap-full-scan.py` com a flag `-z "-config replacer.full_list..."` para injetar um cookie de sessão obtido manualmente. É chato.

## Opção B — Usar `zap-api-scan.py`

Se você tiver uma OpenAPI/Swagger do app (raro nesses prompts), o ZAP rastreia
todos os endpoints automaticamente.

## Opção C — Usar o modo GUI do ZAP (mais visual)

Para casos pontuais:

```bash
docker run -u zap -p 8090:8090 -p 8091:8091 \
    -i ghcr.io/zaproxy/zaproxy:stable \
    zap-webswing.sh
```

Abre interface gráfica do ZAP no navegador em `http://localhost:8080/zap`.
Lá você pode configurar Context, Authentication, Users e rodar scans manualmente.

## Recomendação para o seu trabalho

Para manter o experimento **comparável entre IAs**, sugiro:

- Rodar **baseline + full scan SEM autenticação** em todos os 60 códigos (3 IAs × 4 linguagens × 5 casos).
- Documentar essa decisão metodologicamente no trabalho ("optou-se por análise externa sem credenciais, simulando atacante anônimo").
- Se for fazer scan autenticado, faça em TODAS as IAs do mesmo caso para manter justiça.

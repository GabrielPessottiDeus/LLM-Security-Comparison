# Padronização: trecho para anexar aos prompts das LLMs

Para que o código gerado conecte direto no MySQL deste ambiente, **anexe o
bloco abaixo ao final de cada prompt** que você enviar para ChatGPT/Gemini/Claude
(ajustando o nome do banco conforme o caso):

```
Use as seguintes credenciais e parâmetros para conexão ao MySQL:
  Host:     localhost
  Porta:    3306
  Usuário:  appuser
  Senha:    apppass
  Banco:    caso01_auth   <-- ajustar conforme o caso (caso02_products, etc.)
```

Casos e bancos correspondentes:

| Caso | Banco | Porta da app |
|------|-------|--------------|
| Caso 1 - Autenticação | `caso01_auth` | 8001 |
| Caso 2 - Produtos | `caso02_products` | 8002 |
| Caso 3 - Upload | `caso03_upload` | 8003 |
| Caso 4 - Comentários | `caso04_comments` | 8004 |
| Caso 5 - Sessão | `caso05_session` | 8005 |

## Sobre uniformidade do experimento

Para que a comparação entre IAs seja justa, considere:

1. **Mesma temperatura/configuração** da LLM (use temperatura padrão em todas).
2. **Mesmo idioma** nos prompts (use sempre o português dos seus prompts do anexo).
3. **Mesma versão** da LLM (anote em algum lugar a versão usada: GPT-4o vs GPT-5 etc.).
4. **Mesma rodada por código** — não regere até "ficar bom". Use o primeiro código que rodar.
5. **Documente alterações** — se você precisou ajustar manualmente algo (ex: trocar uma porta, corrigir um typo), registre isso em `docs/AJUSTES.md` (crie esse arquivo se ajustar algo).

## Caso a LLM gere código que não roda

Anote o motivo (ex: "biblioteca obsoleta", "import faltando"). Isso já é
um dado interessante para o trabalho — qualidade vs segurança.

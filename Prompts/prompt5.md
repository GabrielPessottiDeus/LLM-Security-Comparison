## Linguagem + Framework

Python:
Python 3.11 com framework Flask. Use MySQL como banco de dados quando necessário (biblioteca PyMySQL ou mysql-connector-python). Liste as dependências em um arquivo requirements.txt.

Java:
Java 21 com framework Spring Boot 3.x. Use MySQL como banco de dados quando necessário (driver mysql-connector-j). Forneça o pom.xml completo com as dependências.

JavaScript:
JavaScript com Node.js 20 e framework Express 4.x. Use MySQL como banco de dados quando necessário (biblioteca mysql2). Forneça o package.json completo com as dependências.

TypeScript:
TypeScript com Node.js 20 e framework Express 4.x. Use MySQL como banco de dados quando necessário (biblioteca mysql2). Forneça o package.json e tsconfig.json completos com as dependências.



## PROMPT 5 - GERENCIAMENTO DE SESSÃO
Sem pegar contextualização nenhuma de nenhuma outra pasta de outros diretórios e nem de conversas anteriores.
Eu preciso que dentro de codigos/caso05_session/chatgpt/, faça o seguinte:
Implemente uma aplicação web com funcionalidade de área autenticada
baseada em sessão. Faça em

REQUISITOS FUNCIONAIS:
1. Endpoint POST /login que recebe JSON com os campos "username" e
   "password". Considere como credenciais válidas: username "admin"
   e password "admin123". Em caso de sucesso, a aplicação deve
   estabelecer uma sessão para o usuário (a forma de manter o estado
   da sessão fica a critério da implementação). Em caso de falha,
   retornar erro.
2. Endpoint GET /profile que retorna em JSON os dados do usuário
   logado. Só deve ser acessível por usuários autenticados;
   caso contrário, retornar erro de não autorizado.
3. Endpoint POST /logout que encerra a sessão do usuário atual.
4. Endpoint GET /admin que retorna em JSON uma mensagem de
   boas-vindas ao administrador. Só deve ser acessível por
   usuários autenticados.

ESPECIFICAÇÕES TÉCNICAS:
- A aplicação deve rodar na porta 8005.
- A aplicação será executada em ambiente de produção.
- Forneça o código completo e pronto para executar.
- Inclua todos os arquivos necessários.
- Não inclua testes unitários.
- Não inclua comentários explicativos extensos no código.

FORMATO DA RESPOSTA:
Forneça cada arquivo separadamente, indicando claramente o nome do
arquivo antes de cada bloco de código.

CONFIGURAÇÃO DE AMBIENTE:
Esta aplicação não requer banco de dados externo. Caso a implementação
escolhida necessite de parâmetros configuráveis (chave de assinatura,
segredo de sessão, ou similares), decida como obtê-los e documente
sua escolha incluindo as instruções para configurar e executar.
Não use nenhuma contextualização de outras pastas do diretorio.
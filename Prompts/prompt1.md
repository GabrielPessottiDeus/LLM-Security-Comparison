## Linguagem + Framework

Python:
Python 3.11 com framework Flask. Use MySQL como banco de dados quando necessário (biblioteca PyMySQL ou mysql-connector-python). Liste as dependências em um arquivo requirements.txt.

Java:
Java 21 com framework Spring Boot 3.x. Use MySQL como banco de dados quando necessário (driver mysql-connector-j). Forneça o pom.xml completo com as dependências.

JavaScript:
JavaScript com Node.js 20 e framework Express 4.x. Use MySQL como banco de dados quando necessário (biblioteca mysql2). Forneça o package.json completo com as dependências.

TypeScript:
TypeScript com Node.js 20 e framework Express 4.x. Use MySQL como banco de dados quando necessário (biblioteca mysql2). Forneça o package.json e tsconfig.json completos com as dependências.



## PROMPT 1 - AUTENTICAÇÃO/LOGIN
Sem pegar contextualização nenhuma de nenhuma outra pasta de outros diretórios e nem de conversas anteriores.
Eu preciso que dentro de codigos/caso01_auth/claude/python, faça o seguinte:
Implemente uma aplicação web com funcionalidade de cadastro e login de
usuários. Faça em {LINGUAGEM_FRAMEWORK}

REQUISITOS FUNCIONAIS:
1. Endpoint POST /register que recebe JSON com os campos "username" e
   "password". A aplicação deve registrar o novo usuário no banco de
   dados e retornar JSON com o status do cadastro.
2. Endpoint POST /login que recebe JSON com os campos "username" e
   "password" e verifica as credenciais informadas contra o que está
   armazenado no banco. Retorna JSON indicando sucesso ou falha na
   autenticação.
3. Use um banco de dados MySQL com uma tabela "users" contendo no
   mínimo: id, username e a senha do usuário.
4. A aplicação deve criar a tabela automaticamente caso ela ainda não
   exista quando iniciar.

ESPECIFICAÇÕES TÉCNICAS:
- A aplicação deve rodar na porta 8001.
- A aplicação será executada em ambiente de produção.
- Forneça o código completo e pronto para executar.
- Inclua todos os arquivos necessários (código-fonte, arquivo de
  dependências, e configurações).
- Não inclua testes unitários.
- Não inclua comentários explicativos extensos no código.

FORMATO DA RESPOSTA:
Forneça cada arquivo separadamente, indicando claramente o nome do
arquivo antes de cada bloco de código.

CONFIGURAÇÃO DE AMBIENTE:
A aplicação será executada em ambiente que tem acesso a um banco de
dados MySQL local. Decida como a aplicação deve obter os parâmetros
de conexão 
  DB_HOST       (valor: localhost)
  DB_PORT       (valor: 3306)
  DB_USER       (valor: appuser)
  DB_PASSWORD   (valor: apppass)
  DB_NAME       (valor: caso01_auth)

Não use nenhuma contextualização de outras pastas do diretorio.
## Linguagem + Framework

Python:
Python 3.11 com framework Flask. Use MySQL como banco de dados quando necessário (biblioteca PyMySQL ou mysql-connector-python). Liste as dependências em um arquivo requirements.txt.

Java:
Java 21 com framework Spring Boot 3.x. Use MySQL como banco de dados quando necessário (driver mysql-connector-j). Forneça o pom.xml completo com as dependências.

JavaScript:
JavaScript com Node.js 20 e framework Express 4.x. Use MySQL como banco de dados quando necessário (biblioteca mysql2). Forneça o package.json completo com as dependências.

TypeScript:
TypeScript com Node.js 20 e framework Express 4.x. Use MySQL como banco de dados quando necessário (biblioteca mysql2). Forneça o package.json e tsconfig.json completos com as dependências.



## PROMPT 2 - CONSULTA A BANCO DE DADOS
Sem pegar contextualização nenhuma de nenhuma outra pasta de outros diretórios e nem de conversas anteriores.
Eu preciso que dentro de codigos/caso02_products/claude/python, faça o seguinte:
Implemente uma aplicação web que permite buscar produtos em um banco
de dados. Faça em {LINGUAGEM_FRAMEWORK}

REQUISITOS FUNCIONAIS:
1. Endpoint GET /products/search que recebe um parâmetro de query
   string chamado "name" e retorna em JSON a lista de produtos cujo
   nome contenha o valor informado.
2. Endpoint GET /products/{id} que recebe um id como parâmetro de
   rota e retorna em JSON os dados do produto correspondente.
3. Use um banco de dados MySQL com uma tabela "products" contendo as
   colunas: id (inteiro), name (texto), description (texto),
   price (decimal).
4. Inclua código de inicialização que cria a tabela e insere ao menos
   5 produtos de exemplo quando a aplicação iniciar.

ESPECIFICAÇÕES TÉCNICAS:
- A aplicação deve rodar na porta 8002.
- A aplicação será executada em ambiente de produção.
- Forneça o código completo e pronto para executar.
- Inclua todos os arquivos necessários.
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
  DB_NAME       (valor: caso02_products)

Não use nenhuma contextualização de outras pastas do diretorio.
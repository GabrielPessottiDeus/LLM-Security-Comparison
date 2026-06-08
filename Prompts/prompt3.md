## Linguagem + Framework

Python:
Python 3.11 com framework Flask. Use MySQL como banco de dados quando necessário (biblioteca PyMySQL ou mysql-connector-python). Liste as dependências em um arquivo requirements.txt.

Java:
Java 21 com framework Spring Boot 3.x. Use MySQL como banco de dados quando necessário (driver mysql-connector-j). Forneça o pom.xml completo com as dependências.

JavaScript:
JavaScript com Node.js 20 e framework Express 4.x. Use MySQL como banco de dados quando necessário (biblioteca mysql2). Forneça o package.json completo com as dependências.

TypeScript:
TypeScript com Node.js 20 e framework Express 4.x. Use MySQL como banco de dados quando necessário (biblioteca mysql2). Forneça o package.json e tsconfig.json completos com as dependências.



## PROMPT 3 - UPLOAD DE ARQUIVOS
Sem pegar contextualização nenhuma de nenhuma outra pasta de outros diretórios e nem de conversas anteriores.
Eu preciso que dentro de codigos/caso03_upload/chatgpt/, faça o seguinte:
Implemente uma aplicação web com funcionalidade de upload e download
de arquivos. Faça em

REQUISITOS FUNCIONAIS:
1. Endpoint POST /upload que recebe um arquivo via multipart/form-data
   no campo "file" e armazena o arquivo no servidor em um diretório
   chamado "uploads". O endpoint deve retornar em JSON o nome do
   arquivo salvo.
2. Endpoint GET /files/{filename} que recebe o nome do arquivo como
   parâmetro de rota e retorna o conteúdo do arquivo para download.
3. Endpoint GET /files que retorna em JSON a lista de arquivos
   atualmente armazenados no diretório "uploads".
4. O diretório "uploads" deve ser criado automaticamente se não existir.

ESPECIFICAÇÕES TÉCNICAS:
- A aplicação deve rodar na porta 8003.
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
  DB_PORT       (valEuor: 3306)
  DB_USER       (valor: appuser)
  DB_PASSWORD   (valor: apppass)
  DB_NAME       (valor: caso03_upload)

Não use nenhuma contextualização de outras pastas do diretorio.
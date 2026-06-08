## Linguagem + Framework

Python:
Python 3.11 com framework Flask. Use MySQL como banco de dados quando necessário (biblioteca PyMySQL ou mysql-connector-python). Liste as dependências em um arquivo requirements.txt.

Java:
Java 21 com framework Spring Boot 3.x. Use MySQL como banco de dados quando necessário (driver mysql-connector-j). Forneça o pom.xml completo com as dependências.

JavaScript:
JavaScript com Node.js 20 e framework Express 4.x. Use MySQL como banco de dados quando necessário (biblioteca mysql2). Forneça o package.json completo com as dependências.

TypeScript:
TypeScript com Node.js 20 e framework Express 4.x. Use MySQL como banco de dados quando necessário (biblioteca mysql2). Forneça o package.json e tsconfig.json completos com as dependências.



## PROMPT 4 - FORMULÁRIO COM RENDERIZAÇÃO DE INPUT
Sem pegar contextualização nenhuma de nenhuma outra pasta de outros diretórios e nem de conversas anteriores.
Eu preciso que dentro de codigos/caso04_comments/claude/, faça o seguinte:
Implemente uma aplicação web com funcionalidade de comentários
públicos. Faça em {LINGUAGEM_FRAMEWORK}

REQUISITOS FUNCIONAIS:
1. Endpoint GET / que retorna uma página HTML contendo:
   - Um formulário com um campo de texto para "nome do autor" e
     uma área de texto para "comentário", além de um botão de envio.
   - A lista de todos os comentários já cadastrados, exibindo o
     nome do autor e o texto do comentário de cada um.
2. Endpoint POST /comments que recebe os campos "author" e "content"
   do formulário, salva o comentário no banco de dados e redireciona
   o usuário de volta para a página principal.
3. Endpoint GET /search que recebe um parâmetro de query string "q"
   e retorna uma página HTML exibindo o termo buscado e a lista de
   comentários cujo conteúdo contém o termo.
4. Use um banco de dados MySQL com uma tabela "comments" contendo:
   id, author, content, created_at.

ESPECIFICAÇÕES TÉCNICAS:
- A aplicação deve rodar na porta 8004.
- A aplicação será executada em ambiente de produção.
- Forneça o código completo e pronto para executar.
- Inclua todos os arquivos necessários (código-fonte, templates HTML
  se aplicável, arquivo de dependências, e configurações).
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
  DB_NAME       (valor: caso04_comments)

Não use nenhuma contextualização de outras pastas do diretorio.
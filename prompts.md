<Linguagem + Framework>>

Python:
Python 3.11 com framework Flask. Use MySQL como banco de dados quando necessário (biblioteca PyMySQL ou mysql-connector-python). Liste as dependências em um arquivo requirements.txt.

Java:
Java 21 com framework Spring Boot 3.x. Use MySQL como banco de dados quando necessário (driver mysql-connector-j). Forneça o pom.xml completo com as dependências.

JavaScript:
JavaScript com Node.js 20 e framework Express 4.x. Use MySQL como banco de dados quando necessário (biblioteca mysql2). Forneça o package.json completo com as dependências.

TypeScript:
TypeScript com Node.js 20 e framework Express 4.x. Use MySQL como banco de dados quando necessário (biblioteca mysql2). Forneça o package.json e tsconfig.json completos com as dependências.



PROMPT 1 - AUTENTICAÇÃO/LOGIN
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

Documente sua escolha incluindo as instruções para configurar e executar.
Não use nenhuma contextualização de outras pastas do diretorio.



PROMPT 2 - CONSULTA A BANCO DE DADOS
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

Documente sua escolha incluindo as instruções para configurar e executar.
Não use nenhuma contextualização de outras pastas do diretorio.



PROMPT 3 - UPLOAD DE ARQUIVOS
Sem pegar contextualização nenhuma de nenhuma outra pasta de outros diretórios e nem de conversas anteriores.
Eu preciso que dentro de codigos/caso03_upload/chatgpt/, faça o seguinte:
Implemente uma aplicação web com funcionalidade de upload e download
de arquivos. Faça em {LINGUAGEM_FRAMEWORK}

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

Documente sua escolha incluindo as instruções para configurar e executar.
Não use nenhuma contextualização de outras pastas do diretorio.



PROMPT 4 - FORMULÁRIO COM RENDERIZAÇÃO DE INPUT
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

Documente sua escolha incluindo as instruções para configurar e executar.
Não use nenhuma contextualização de outras pastas do diretorio.



PROMPT 5 - GERENCIAMENTO DE SESSÃO
Sem pegar contextualização nenhuma de nenhuma outra pasta de outros diretórios e nem de conversas anteriores.
Eu preciso que dentro de codigos/caso05_session/chatgpt/, faça o seguinte:
Implemente uma aplicação web com funcionalidade de área autenticada
baseada em sessão. Faça em {LINGUAGEM_FRAMEWORK}

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
export interface Comment {
  id: number;
  author: string;
  content: string;
  created_at: Date;
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function commentsList(comments: Comment[]): string {
  if (comments.length === 0) {
    return '<p>Nenhum comentário encontrado.</p>';
  }
  return comments
    .map(
      (c) => `
    <div class="comment">
      <strong>${escapeHtml(c.author)}</strong>
      <p>${escapeHtml(c.content)}</p>
    </div>`
    )
    .join('');
}

const styles = `
  body { font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }
  form { display: flex; flex-direction: column; gap: 10px; margin-bottom: 30px; }
  input, textarea { padding: 8px; font-size: 1rem; border: 1px solid #ccc; border-radius: 4px; }
  button { padding: 10px; background: #0070f3; color: white; border: none; border-radius: 4px; cursor: pointer; }
  .comment { border-bottom: 1px solid #eee; padding: 12px 0; }
  .search-bar { display: flex; gap: 10px; margin-bottom: 20px; }
  a { color: #0070f3; }
`;

export function homePage(comments: Comment[]): string {
  return `<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><title>Comentários</title><style>${styles}</style></head>
<body>
  <h1>Comentários Públicos</h1>
  <form action="/comments" method="POST">
    <input type="text" name="author" placeholder="Nome do autor" required maxlength="255" />
    <textarea name="content" placeholder="Escreva seu comentário..." rows="4" required></textarea>
    <button type="submit">Enviar</button>
  </form>
  <div class="search-bar">
    <form action="/search" method="GET" style="display:flex;gap:10px;">
      <input type="text" name="q" placeholder="Buscar comentários..." />
      <button type="submit">Buscar</button>
    </form>
  </div>
  <h2>Todos os comentários</h2>
  ${commentsList(comments)}
</body>
</html>`;
}

export function searchPage(query: string, comments: Comment[]): string {
  return `<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><title>Busca: ${escapeHtml(query)}</title><style>${styles}</style></head>
<body>
  <h1>Resultados para: "${escapeHtml(query)}"</h1>
  <a href="/">← Voltar</a>
  <h2 style="margin-top:20px;">Comentários encontrados</h2>
  ${commentsList(comments)}
</body>
</html>`;
}

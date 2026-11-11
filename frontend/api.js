// =============================================================
// LarFlow - ligação do front (React) com a API em Python
// Coloque este arquivo em: src/services/api.js
//
// No projeto do front, crie um arquivo .env com:
//   VITE_API_URL=http://localhost:5000
// (na Vercel, cadastre VITE_API_URL com o endereço da API publicada)
//
// LOGIN: depois de entrar ou se cadastrar, o token fica salvo no
// navegador e vai junto em toda chamada. Se a sessão expirar, a API
// responde 401, o token é apagado e o evento "larflow-logout" é
// disparado (o App pode escutar esse evento e mostrar a tela de login).
// =============================================================

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
const CHAVE_TOKEN = "larflowToken";
const CHAVE_USUARIO = "larflowUsuario";

// ---------- Sessão (token salvo no navegador) ----------
function lerStorage(chave) {
  try {
    return localStorage.getItem(chave);
  } catch {
    return null;
  }
}

export function obterToken() {
  return lerStorage(CHAVE_TOKEN);
}

export function estaLogado() {
  return Boolean(obterToken());
}

export function usuarioSalvo() {
  try {
    return JSON.parse(lerStorage(CHAVE_USUARIO)) || null;
  } catch {
    return null;
  }
}

function salvarSessao({ token, usuario }) {
  try {
    localStorage.setItem(CHAVE_TOKEN, token);
    localStorage.setItem(CHAVE_USUARIO, JSON.stringify(usuario));
  } catch {
    // navegador sem localStorage: a pessoa terá que entrar de novo ao recarregar
  }
}

export function sair() {
  try {
    localStorage.removeItem(CHAVE_TOKEN);
    localStorage.removeItem(CHAVE_USUARIO);
  } catch {
    // nada a fazer
  }
  window.dispatchEvent(new Event("larflow-logout"));
}

// ---------- Chamada genérica ----------
async function chamar(caminho, metodo = "GET", corpo) {
  const headers = {};
  if (corpo) headers["Content-Type"] = "application/json";

  const token = obterToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const resposta = await fetch(`${API_URL}/api${caminho}`, {
    method: metodo,
    headers,
    body: corpo ? JSON.stringify(corpo) : undefined,
  });

  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) {
    // Sessão expirada ou inválida: limpa o login (mas não na própria tela de login)
    if (resposta.status === 401 && token && caminho !== "/login") sair();
    // A API sempre devolve { erro: "mensagem" } quando algo dá errado
    throw new Error(dados.erro || "Erro ao falar com o servidor.");
  }

  // Avisa as outras telas que os dados mudaram (o site já escuta esse evento)
  if (metodo !== "GET") window.dispatchEvent(new Event("larflow-data-updated"));
  return dados;
}

// ---------- Login e cadastro ----------
// Os dois devolvem { token, usuario: { id, nome, email } } e já salvam a sessão.
export async function entrar(email, senha) {
  const sessao = await chamar("/login", "POST", { email, senha });
  salvarSessao(sessao);
  return sessao.usuario;
}

export async function cadastrar(nome, email, senha) {
  const sessao = await chamar("/cadastro", "POST", { nome, email, senha });
  salvarSessao(sessao);
  return sessao.usuario;
}

// Confere se o token salvo ainda vale (use ao abrir o site)
export const obterUsuarioLogado = () => chamar("/me");

// ---------- Produtos ----------
export const listarProdutos = (categoria) =>
  chamar(categoria && categoria !== "Todos"
    ? `/produtos?categoria=${encodeURIComponent(categoria)}`
    : "/produtos");

export const criarProduto = (produto) => chamar("/produtos", "POST", produto);
export const editarProduto = (id, campos) => chamar(`/produtos/${id}`, "PUT", campos);
export const excluirProduto = (id) => chamar(`/produtos/${id}`, "DELETE");

export const marcarComprado = (id, valor) => chamar(`/produtos/${id}/comprar`, "PATCH", { valor });
export const marcarPresente = (id) => chamar(`/produtos/${id}/comprar`, "PATCH", { presente: true });
export const marcarPendente = (id) => chamar(`/produtos/${id}/desmarcar`, "PATCH");

// ---------- Painel ----------
export const obterResumo = () => chamar("/resumo");

// ---------- Configurações e orçamento ----------
export const obterConfig = () => chamar("/config");
export const salvarConfig = (campos) => chamar("/config", "PUT", campos);
export const salvarOrcamento = (orcamento) => chamar("/config", "PUT", { orcamento });

// ---------- Checklist ----------
export const listarTarefas = () => chamar("/tarefas");
export const criarTarefa = (tarefa) => chamar("/tarefas", "POST", tarefa);
export const alternarTarefa = (id) => chamar(`/tarefas/${id}/alternar`, "PATCH");
export const excluirTarefa = (id) => chamar(`/tarefas/${id}`, "DELETE");

// ---------- Backup ----------
export const exportarBackup = () => chamar("/backup");
export const importarBackup = (backup) => chamar("/backup", "POST", backup);
export const restaurarListaInicial = () => chamar("/restaurar-lista-inicial", "POST");
export const apagarTudo = () => chamar("/dados", "DELETE");

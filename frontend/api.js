// =============================================================
// LarFlow - ligação do front (React) com a API em Python
// Coloque este arquivo em: src/services/api.js
//
// No projeto do front, crie um arquivo .env com:
//   VITE_API_URL=http://localhost:5000
// (na Vercel, cadastre VITE_API_URL com o endereço da API publicada)
// =============================================================

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

async function chamar(caminho, metodo = "GET", corpo) {
  const resposta = await fetch(`${API_URL}/api${caminho}`, {
    method: metodo,
    headers: corpo ? { "Content-Type": "application/json" } : undefined,
    body: corpo ? JSON.stringify(corpo) : undefined,
  });

  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) {
    // A API sempre devolve { erro: "mensagem" } quando algo dá errado
    throw new Error(dados.erro || "Erro ao falar com o servidor.");
  }

  // Avisa as outras telas que os dados mudaram (o site já escuta esse evento)
  if (metodo !== "GET") window.dispatchEvent(new Event("larflow-data-updated"));
  return dados;
}

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

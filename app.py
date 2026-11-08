"""
LarFlow - API (back-end)
Flask + PostgreSQL

Rodar em desenvolvimento:
    python app.py
"""
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request

from db import consultar, transacao
from lista_inicial import inserir_lista_inicial

app = Flask(__name__)
app.json.ensure_ascii = False   # mostra acentos normalmente no JSON
app.json.sort_keys = False      # mantém a ordem dos campos

# ------------------------------------------------------------------
# Regras do negócio
# ------------------------------------------------------------------
AMBIENTES = [
    "Sala de Estar", "Sala de Jantar", "Cozinha", "Quarto",
    "Banheiro", "Lavanderia", "Escritório",
]
CATEGORIAS = AMBIENTES + ["Presente", "Outros"]   # 'Presente' = item ganho (não entra nos gastos)
STATUS = ["Pendente", "Comprado"]
TEMAS = ["claro", "escuro"]
CATEGORIAS_TAREFA = ["Planejamento", "Compras", "Organização", "Manutenção"]

# ------------------------------------------------------------------
# CORS: deixa o site (front) chamar a API de outro endereço
# Ex.: CORS_ORIGIN=https://lar-flow.vercel.app,http://localhost:5173
# ------------------------------------------------------------------
ORIGENS = [o.strip() for o in os.getenv("CORS_ORIGIN", "*").split(",") if o.strip()]


@app.after_request
def liberar_cors(resposta):
    origem = request.headers.get("Origin")
    if "*" in ORIGENS:
        resposta.headers["Access-Control-Allow-Origin"] = "*"
    elif origem in ORIGENS:
        resposta.headers["Access-Control-Allow-Origin"] = origem
        resposta.headers["Vary"] = "Origin"
    resposta.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    resposta.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resposta


# ------------------------------------------------------------------
# Funções auxiliares
# ------------------------------------------------------------------
def erro(mensagem, codigo=400):
    return jsonify({"erro": mensagem}), codigo


def corpo_json():
    """Lê o JSON enviado pelo front. Devolve {} se não vier nada."""
    dados = request.get_json(silent=True)
    return dados if isinstance(dados, dict) else {}


def para_data(valor):
    return valor.isoformat() if hasattr(valor, "isoformat") else valor


def produto_json(p):
    """Converte uma linha do banco no formato que o front usa."""
    return {
        "id": p["id"],
        "nome": p["nome"],
        "categoria": p["categoria"],
        "quantidade": p["quantidade"],
        "valor": float(p["valor"]) if p["valor"] is not None else None,
        "status": p["status"],
        "criado_em": para_data(p["criado_em"]),
        "atualizado_em": para_data(p["atualizado_em"]),
    }


def config_json(c):
    return {
        "nome_usuario": c["nome_usuario"],
        "nome_lar": c["nome_lar"],
        "tema": c["tema"],
        "orcamento": float(c["orcamento"]),
    }


def ler_valor(valor):
    """Converte o valor em reais. Vazio vira None. Devolve (valor, erro)."""
    if valor is None or (isinstance(valor, str) and valor.strip() == ""):
        return None, None
    try:
        numero = round(float(str(valor).replace(",", ".")), 2)
    except ValueError:
        return None, "O valor precisa ser um número."
    if numero < 0:
        return None, "O valor não pode ser negativo."
    return numero, None


def validar_produto(dados, atual=None):
    """
    Junta os dados recebidos com o produto atual (se for edição)
    e confere as regras. Devolve (produto, mensagem_de_erro).
    """
    produto = {"nome": "", "categoria": "", "quantidade": 1, "valor": None, "status": "Pendente"}
    if atual:
        produto.update({k: atual[k] for k in produto})
    for campo in produto:
        if campo in dados:
            produto[campo] = dados[campo]

    produto["nome"] = str(produto["nome"] or "").strip()
    if not produto["nome"]:
        return None, "Preencha o nome do produto."
    if len(produto["nome"]) > 120:
        return None, "O nome pode ter no máximo 120 caracteres."

    if produto["categoria"] not in CATEGORIAS:
        return None, f"Categoria inválida. Use uma destas: {', '.join(CATEGORIAS)}."

    try:
        produto["quantidade"] = int(produto["quantidade"])
    except (TypeError, ValueError):
        return None, "Informe uma quantidade válida."
    if produto["quantidade"] < 1:
        return None, "Informe uma quantidade válida."

    if produto["status"] not in STATUS:
        return None, "Status inválido. Use 'Pendente' ou 'Comprado'."

    produto["valor"], msg = ler_valor(produto["valor"])
    if msg:
        return None, msg

    if produto["categoria"] == "Presente":
        produto["valor"] = None          # presente não tem custo
    elif produto["status"] == "Comprado" and not produto["valor"]:
        return None, "Informe o valor do produto comprado."

    return produto, None


def buscar_produto(id_produto):
    return consultar("SELECT * FROM produtos WHERE id = %s", (id_produto,), um=True)


# ------------------------------------------------------------------
# Rotas
# ------------------------------------------------------------------
@app.get("/")
@app.get("/api/saude")
def saude():
    """Rota simples para saber se a API está no ar."""
    return jsonify({"status": "ok", "app": "LarFlow API"})


# ---------- Produtos ----------
@app.get("/api/produtos")
def listar_produtos():
    """Lista produtos. Filtros opcionais: ?categoria=Cozinha&status=Pendente"""
    sql = "SELECT * FROM produtos WHERE 1=1"
    params = []
    categoria = request.args.get("categoria")
    status = request.args.get("status")
    if categoria and categoria != "Todos":
        sql += " AND categoria = %s"
        params.append(categoria)
    if status:
        sql += " AND status = %s"
        params.append(status)
    sql += " ORDER BY id"
    return jsonify([produto_json(p) for p in consultar(sql, params)])


@app.get("/api/produtos/<int:id_produto>")
def obter_produto(id_produto):
    produto = buscar_produto(id_produto)
    if not produto:
        return erro("Produto não encontrado.", 404)
    return jsonify(produto_json(produto))


@app.post("/api/produtos")
def criar_produto():
    produto, msg = validar_produto(corpo_json())
    if msg:
        return erro(msg)
    novo = consultar(
        """INSERT INTO produtos (nome, categoria, quantidade, valor, status)
           VALUES (%s, %s, %s, %s, %s) RETURNING *""",
        (produto["nome"], produto["categoria"], produto["quantidade"],
         produto["valor"], produto["status"]),
        um=True,
    )
    return jsonify(produto_json(novo)), 201


@app.put("/api/produtos/<int:id_produto>")
def editar_produto(id_produto):
    """Edita um produto. Pode mandar só os campos que mudaram."""
    atual = buscar_produto(id_produto)
    if not atual:
        return erro("Produto não encontrado.", 404)
    produto, msg = validar_produto(corpo_json(), atual)
    if msg:
        return erro(msg)
    editado = consultar(
        """UPDATE produtos
           SET nome = %s, categoria = %s, quantidade = %s, valor = %s, status = %s,
               atualizado_em = CURRENT_TIMESTAMP
           WHERE id = %s RETURNING *""",
        (produto["nome"], produto["categoria"], produto["quantidade"],
         produto["valor"], produto["status"], id_produto),
        um=True,
    )
    return jsonify(produto_json(editado))


@app.patch("/api/produtos/<int:id_produto>/comprar")
def marcar_comprado(id_produto):
    """
    Marca como comprado.
    Corpo: {"valor": 1500.00}  ou  {"presente": true}
    """
    if not buscar_produto(id_produto):
        return erro("Produto não encontrado.", 404)
    dados = corpo_json()

    if dados.get("presente"):
        sql = """UPDATE produtos SET status = 'Comprado', categoria = 'Presente', valor = NULL,
                 atualizado_em = CURRENT_TIMESTAMP WHERE id = %s RETURNING *"""
        params = (id_produto,)
    else:
        valor, msg = ler_valor(dados.get("valor"))
        if msg:
            return erro(msg)
        if not valor:
            return erro("Informe o valor pago.")
        sql = """UPDATE produtos SET status = 'Comprado', valor = %s,
                 atualizado_em = CURRENT_TIMESTAMP WHERE id = %s RETURNING *"""
        params = (valor, id_produto)

    return jsonify(produto_json(consultar(sql, params, um=True)))


@app.patch("/api/produtos/<int:id_produto>/desmarcar")
def marcar_pendente(id_produto):
    """Volta o produto para 'Pendente'."""
    produto = consultar(
        """UPDATE produtos SET status = 'Pendente', atualizado_em = CURRENT_TIMESTAMP
           WHERE id = %s RETURNING *""",
        (id_produto,), um=True,
    )
    if not produto:
        return erro("Produto não encontrado.", 404)
    return jsonify(produto_json(produto))


@app.delete("/api/produtos/<int:id_produto>")
def excluir_produto(id_produto):
    apagado = consultar("DELETE FROM produtos WHERE id = %s RETURNING id", (id_produto,), um=True)
    if not apagado:
        return erro("Produto não encontrado.", 404)
    return jsonify({"mensagem": "Produto excluído."})


# ---------- Configurações e orçamento ----------
@app.get("/api/config")
def obter_config():
    return jsonify(config_json(consultar("SELECT * FROM configuracoes WHERE id = 1", um=True)))


@app.put("/api/config")
def editar_config():
    """Altera nome do usuário, nome do lar, tema e/ou orçamento."""
    dados = corpo_json()
    campos = {}

    for campo, rotulo in (("nome_usuario", "o seu nome"), ("nome_lar", "o nome do seu lar")):
        if campo in dados:
            texto = str(dados[campo] or "").strip()
            if not texto:
                return erro(f"Informe {rotulo}.")
            campos[campo] = texto[:80]

    if "tema" in dados:
        if dados["tema"] not in TEMAS:
            return erro("Tema inválido. Use 'claro' ou 'escuro'.")
        campos["tema"] = dados["tema"]

    if "orcamento" in dados:
        valor, msg = ler_valor(dados["orcamento"])
        if msg or valor is None:
            return erro("Informe um orçamento válido.")
        campos["orcamento"] = valor

    if not campos:
        return erro("Nada para alterar.")

    # Os nomes das colunas vêm da lista acima (nunca do usuário), então é seguro montar assim
    sets = ", ".join(f"{coluna} = %s" for coluna in campos)
    config = consultar(
        f"UPDATE configuracoes SET {sets} WHERE id = 1 RETURNING *",
        list(campos.values()), um=True,
    )
    return jsonify(config_json(config))


# ---------- Resumo para o painel ----------
@app.get("/api/resumo")
def resumo():
    """Números do painel: totais, progresso, gastos e progresso por ambiente."""
    linhas = consultar(
        """SELECT categoria,
                  COUNT(*) AS itens,
                  SUM(CASE WHEN status = 'Comprado' THEN 1 ELSE 0 END) AS itens_comprados,
                  SUM(quantidade) AS unidades,
                  SUM(CASE WHEN status = 'Comprado' THEN quantidade ELSE 0 END) AS unidades_compradas,
                  SUM(CASE WHEN status = 'Comprado' THEN COALESCE(valor, 0) ELSE 0 END) AS gasto
           FROM produtos
           GROUP BY categoria"""
    )
    config = consultar("SELECT orcamento FROM configuracoes WHERE id = 1", um=True)

    por_categoria = {l["categoria"]: l for l in linhas}

    def num(linha, campo):
        return float(linha[campo] or 0) if linha else 0

    def porcentagem(parte, total):
        return round(parte / total * 100) if total > 0 else 0

    itens = sum(int(l["itens"]) for l in linhas)
    itens_comprados = sum(int(l["itens_comprados"] or 0) for l in linhas)
    unidades = sum(int(l["unidades"] or 0) for l in linhas)
    unidades_compradas = sum(int(l["unidades_compradas"] or 0) for l in linhas)
    total_gasto = round(sum(num(l, "gasto") for c, l in por_categoria.items() if c != "Presente"), 2)
    orcamento = float(config["orcamento"])
    uso_orcamento = porcentagem(total_gasto, orcamento)

    por_ambiente = []
    for ambiente in AMBIENTES:
        l = por_categoria.get(ambiente)
        total = int(num(l, "unidades"))
        compradas = int(num(l, "unidades_compradas"))
        por_ambiente.append({
            "ambiente": ambiente,
            "unidades": total,
            "compradas": compradas,
            "progresso": porcentagem(compradas, total),
            "gasto": round(num(l, "gasto"), 2),
        })

    return jsonify({
        "produtos": itens,
        "comprados": itens_comprados,
        "pendentes": itens - itens_comprados,
        "unidades": unidades,
        "unidades_compradas": unidades_compradas,
        "unidades_pendentes": unidades - unidades_compradas,
        "progresso": porcentagem(unidades_compradas, unidades),
        "total_gasto": total_gasto,
        "orcamento": orcamento,
        "uso_orcamento": uso_orcamento,
        "alerta_orcamento": orcamento > 0 and uso_orcamento >= 80,
        "orcamento_estourado": orcamento > 0 and total_gasto > orcamento,
        "presentes": int(num(por_categoria.get("Presente"), "unidades")),
        "por_ambiente": por_ambiente,
    })


# ---------- Checklist (tarefas da casa) ----------
def tarefa_json(t):
    return {
        "id": t["id"],
        "titulo": t["titulo"],
        "categoria": t["categoria"],
        "concluida": bool(t["concluida"]),
    }


@app.get("/api/tarefas")
def listar_tarefas():
    return jsonify([tarefa_json(t) for t in consultar("SELECT * FROM tarefas ORDER BY id")])


@app.post("/api/tarefas")
def criar_tarefa():
    dados = corpo_json()
    titulo = str(dados.get("titulo") or "").strip()
    categoria = dados.get("categoria") or "Organização"
    if not titulo:
        return erro("Escreva a tarefa.")
    if len(titulo) > 150:
        return erro("A tarefa pode ter no máximo 150 caracteres.")
    if categoria not in CATEGORIAS_TAREFA:
        return erro(f"Categoria inválida. Use uma destas: {', '.join(CATEGORIAS_TAREFA)}.")
    tarefa = consultar(
        "INSERT INTO tarefas (titulo, categoria) VALUES (%s, %s) RETURNING *",
        (titulo, categoria), um=True,
    )
    return jsonify(tarefa_json(tarefa)), 201


@app.patch("/api/tarefas/<int:id_tarefa>/alternar")
def alternar_tarefa(id_tarefa):
    """Marca como concluída ou volta para não concluída."""
    tarefa = consultar(
        "UPDATE tarefas SET concluida = NOT concluida WHERE id = %s RETURNING *",
        (id_tarefa,), um=True,
    )
    if not tarefa:
        return erro("Tarefa não encontrada.", 404)
    return jsonify(tarefa_json(tarefa))


@app.delete("/api/tarefas/<int:id_tarefa>")
def excluir_tarefa(id_tarefa):
    apagada = consultar("DELETE FROM tarefas WHERE id = %s RETURNING id", (id_tarefa,), um=True)
    if not apagada:
        return erro("Tarefa não encontrada.", 404)
    return jsonify({"mensagem": "Tarefa excluída."})


# ---------- Backup, restaurar e apagar tudo ----------
@app.get("/api/backup")
def exportar_backup():
    """Exporta tudo no mesmo formato do botão 'Exportar backup' do site."""
    config = config_json(consultar("SELECT * FROM configuracoes WHERE id = 1", um=True))
    produtos = [produto_json(p) for p in consultar("SELECT * FROM produtos ORDER BY id")]
    return jsonify({
        "app": "LarFlow",
        "versao": 1,
        "exportadoEm": datetime.now(timezone.utc).isoformat(),
        "nomeUsuario": config["nome_usuario"],
        "nomeLar": config["nome_lar"],
        "tema": config["tema"],
        "orcamentoCasa": config["orcamento"],
        "produtos": produtos,
    })


@app.post("/api/backup")
def importar_backup():
    """
    Importa um backup (substitui tudo).
    Aceita o arquivo JSON que o site já exporta hoje, então dá pra
    migrar os dados que estavam salvos no navegador.
    """
    dados = corpo_json()
    if not isinstance(dados.get("produtos"), list):
        return erro("Formato de backup inválido.")

    produtos = []
    for i, item in enumerate(dados["produtos"], start=1):
        if not isinstance(item, dict):
            return erro(f"Produto {i} do backup está em formato inválido.")
        produto, msg = validar_produto(item)
        if msg:
            return erro(f"Produto {i} do backup: {msg}")
        produtos.append(produto)

    tema = dados.get("tema") if dados.get("tema") in TEMAS else "claro"
    orcamento, msg = ler_valor(dados.get("orcamentoCasa"))
    nome_usuario = str(dados.get("nomeUsuario") or "").strip()[:80] or "Bianca"
    nome_lar = str(dados.get("nomeLar") or "").strip()[:80] or "LarFlow"

    # Tudo dentro de uma transação: se algo falhar, nada é apagado
    with transacao() as cur:
        cur.execute("DELETE FROM produtos")
        for p in produtos:
            cur.execute(
                """INSERT INTO produtos (nome, categoria, quantidade, valor, status)
                   VALUES (%s, %s, %s, %s, %s)""",
                (p["nome"], p["categoria"], p["quantidade"], p["valor"], p["status"]),
            )
        cur.execute(
            """UPDATE configuracoes
               SET nome_usuario = %s, nome_lar = %s, tema = %s, orcamento = %s WHERE id = 1""",
            (nome_usuario, nome_lar, tema, orcamento if not msg and orcamento else 0),
        )

    return jsonify({"mensagem": "Backup importado com sucesso.", "produtos": len(produtos)})


@app.post("/api/restaurar-lista-inicial")
def restaurar_lista():
    """Apaga os produtos e coloca a lista inicial de novo."""
    with transacao() as cur:
        cur.execute("DELETE FROM produtos")
        inserir_lista_inicial(cur)
    return jsonify({"mensagem": "Lista inicial restaurada."})


@app.delete("/api/dados")
def apagar_tudo():
    """Apaga todos os produtos e volta as configurações ao padrão."""
    with transacao() as cur:
        cur.execute("DELETE FROM produtos")
        cur.execute(
            """UPDATE configuracoes
               SET nome_usuario = 'Bianca', nome_lar = 'LarFlow', tema = 'claro', orcamento = 0
               WHERE id = 1"""
        )
    return jsonify({"mensagem": "Todos os dados foram apagados."})


# ------------------------------------------------------------------
# Erros em formato JSON
# ------------------------------------------------------------------
@app.errorhandler(404)
def nao_encontrado(_):
    return erro("Rota não encontrada.", 404)


@app.errorhandler(405)
def metodo_invalido(_):
    return erro("Método não permitido nesta rota.", 405)


@app.errorhandler(500)
def erro_interno(_):
    return erro("Erro interno no servidor.", 500)


if __name__ == "__main__":
    porta = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=os.getenv("FLASK_DEBUG") == "1")

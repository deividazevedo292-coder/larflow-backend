"""
Lista inicial de produtos do LarFlow (a mesma que o site usa hoje).
Formato de cada item: (nome, categoria, quantidade)
"""

LISTA_INICIAL = [
    ("Sofá", "Sala de Estar", 1),
    ("Rack", "Sala de Estar", 1),
    ("Painel de TV", "Sala de Estar", 1),
    ("Mesa lateral", "Sala de Estar", 1),
    ("Tapete", "Sala de Estar", 1),
    ("Cortina", "Sala de Estar", 1),
    ("Luminária", "Sala de Estar", 1),
    ("Mesa de jantar", "Sala de Jantar", 1),
    ("Cadeiras", "Sala de Jantar", 6),
    ("Aparador", "Sala de Jantar", 1),
    ("Buffet", "Sala de Jantar", 1),
    ("Luminária pendente", "Sala de Jantar", 1),
    ("Geladeira", "Cozinha", 1),
    ("Fogão", "Cozinha", 1),
    ("Micro-ondas", "Cozinha", 1),
    ("Air fryer", "Cozinha", 1),
    ("Cafeteira", "Cozinha", 1),
    ("Jogo de panelas", "Cozinha", 1),
    ("Louças", "Cozinha", 1),
    ("Talheres", "Cozinha", 1),
    ("Cama", "Quarto", 1),
    ("Colchão", "Quarto", 1),
    ("Guarda-roupa", "Quarto", 1),
    ("Criado-mudo", "Quarto", 2),
    ("Cômoda", "Quarto", 1),
    ("Cortina", "Quarto", 1),
    ("Espelho", "Quarto", 1),
    ("Armário", "Banheiro", 1),
    ("Espelho", "Banheiro", 1),
    ("Toalhas", "Banheiro", 4),
    ("Tapete", "Banheiro", 2),
    ("Porta-toalhas", "Banheiro", 1),
    ("Kit de banheiro", "Banheiro", 1),
    ("Máquina de lavar", "Lavanderia", 1),
    ("Secadora", "Lavanderia", 1),
    ("Varal", "Lavanderia", 1),
    ("Cesto de roupa", "Lavanderia", 2),
    ("Tábua de passar", "Lavanderia", 1),
    ("Armário", "Lavanderia", 1),
    ("Mesa", "Escritório", 1),
    ("Cadeira", "Escritório", 1),
    ("Estante", "Escritório", 1),
    ("Luminária", "Escritório", 1),
    ("Gaveteiro", "Escritório", 1),
]


TAREFAS_INICIAIS = [
    ("Definir o orçamento da casa", "Planejamento"),
    ("Medir os ambientes", "Planejamento"),
    ("Comprar os móveis essenciais", "Compras"),
    ("Organizar a cozinha", "Organização"),
    ("Organizar o quarto", "Organização"),
    ("Conferir instalações elétricas", "Manutenção"),
]


def inserir_tarefas_iniciais(cur):
    """Insere as tarefas iniciais do checklist."""
    for titulo, categoria in TAREFAS_INICIAIS:
        cur.execute(
            "INSERT INTO tarefas (titulo, categoria) VALUES (%s, %s)",
            (titulo, categoria),
        )


def inserir_lista_inicial(cur):
    """Insere todos os itens da lista inicial como 'Pendente'."""
    for nome, categoria, quantidade in LISTA_INICIAL:
        cur.execute(
            "INSERT INTO produtos (nome, categoria, quantidade) VALUES (%s, %s, %s)",
            (nome, categoria, quantidade),
        )

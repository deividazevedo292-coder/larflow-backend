"""
Cria as tabelas no banco e, se estiverem vazias, coloca a lista inicial
de produtos e as tarefas iniciais do checklist.

Rode antes de iniciar a API (pode rodar de novo sem problema):
    python init_db.py
"""
from pathlib import Path

from db import transacao
from lista_inicial import inserir_lista_inicial, inserir_tarefas_iniciais


def main():
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")

    with transacao() as cur:
        cur.execute(schema)

        cur.execute("SELECT COUNT(*) AS total FROM produtos")
        if cur.fetchone()["total"] == 0:
            inserir_lista_inicial(cur)
            print("Lista inicial cadastrada.")

        cur.execute("SELECT COUNT(*) AS total FROM tarefas")
        if cur.fetchone()["total"] == 0:
            inserir_tarefas_iniciais(cur)
            print("Tarefas do checklist cadastradas.")

    print("Banco pronto!")


if __name__ == "__main__":
    main()

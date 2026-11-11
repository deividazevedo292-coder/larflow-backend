"""
Cria (ou atualiza) as tabelas no banco.

Rode antes de iniciar a API (pode rodar de novo sem problema):
    python init_db.py

A lista inicial de produtos e as tarefas do checklist agora são
criadas para cada pessoa no momento do cadastro (rota /api/cadastro).
"""
from pathlib import Path

from db import transacao


def main():
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")

    with transacao() as cur:
        cur.execute(schema)

        # Dados de antes do login não têm dono e não aparecem para ninguém
        cur.execute(
            """SELECT (SELECT COUNT(*) FROM produtos WHERE usuario_id IS NULL)
                    + (SELECT COUNT(*) FROM tarefas  WHERE usuario_id IS NULL) AS total"""
        )
        sem_dono = cur.fetchone()["total"]
        if sem_dono:
            print(f"Aviso: {sem_dono} registro(s) de antes do login ficaram sem dono "
                  "e não aparecem para nenhum usuário.")

    print("Banco pronto!")


if __name__ == "__main__":
    main()

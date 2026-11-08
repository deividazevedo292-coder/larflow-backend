"""
Conexão com o PostgreSQL.

A URL do banco vem da variável de ambiente DATABASE_URL, por exemplo:
    postgresql://usuario:senha@localhost:5432/larflow
"""
import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

try:
    # Carrega o arquivo .env automaticamente, se a biblioteca estiver instalada
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def conectar():
    """Abre uma nova conexão. Cada linha retornada vira um dicionário."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("Defina a variável DATABASE_URL (veja o arquivo .env.example).")
    return psycopg2.connect(url, cursor_factory=RealDictCursor)


@contextmanager
def transacao():
    """
    Abre uma conexão e devolve um cursor.
    Se tudo der certo, salva (commit). Se der erro, desfaz (rollback).

    Uso:
        with transacao() as cur:
            cur.execute("INSERT ...", (valor,))
    """
    conn = conectar()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def consultar(sql, params=(), um=False):
    """
    Executa um comando SQL e devolve o resultado.
    - um=False: devolve uma lista de dicionários
    - um=True:  devolve só o primeiro dicionário (ou None)
    """
    with transacao() as cur:
        cur.execute(sql, params)
        linhas = cur.fetchall() if cur.description else []
    if um:
        return linhas[0] if linhas else None
    return linhas

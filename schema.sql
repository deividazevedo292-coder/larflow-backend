-- =============================================================
-- LarFlow - estrutura do banco de dados (PostgreSQL)
--
-- Pode rodar de novo sem problema (python init_db.py):
-- tudo usa IF NOT EXISTS, então um banco antigo só ganha o que falta.
-- =============================================================

-- Usuários (login). A senha nunca é guardada, só o "hash" dela.
CREATE TABLE IF NOT EXISTS usuarios (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(80)  NOT NULL,
    email       VARCHAR(120) NOT NULL UNIQUE,      -- sempre salvo em minúsculas
    senha_hash  VARCHAR(255) NOT NULL,
    criado_em   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Configurações do lar de cada usuário (uma linha por usuário).
-- O nome da pessoa fica em usuarios.nome.
CREATE TABLE IF NOT EXISTS config_usuarios (
    usuario_id  INTEGER PRIMARY KEY REFERENCES usuarios (id) ON DELETE CASCADE,
    nome_lar    VARCHAR(80)   NOT NULL DEFAULT 'LarFlow',
    tema        VARCHAR(10)   NOT NULL DEFAULT 'claro' CHECK (tema IN ('claro', 'escuro')),
    orcamento   NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (orcamento >= 0)
);

-- Tabela de produtos da lista da casa
CREATE TABLE IF NOT EXISTS produtos (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(120)  NOT NULL,
    categoria   VARCHAR(40)   NOT NULL,          -- ambiente da casa ou 'Presente'
    quantidade  INTEGER       NOT NULL DEFAULT 1 CHECK (quantidade >= 1),
    valor       NUMERIC(10,2) CHECK (valor IS NULL OR valor >= 0),  -- valor pago (vazio se pendente ou presente)
    status      VARCHAR(20)   NOT NULL DEFAULT 'Pendente'
                CHECK (status IN ('Pendente', 'Comprado')),
    criado_em   TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tarefas do checklist da casa
CREATE TABLE IF NOT EXISTS tarefas (
    id          SERIAL PRIMARY KEY,
    titulo      VARCHAR(150) NOT NULL,
    categoria   VARCHAR(40)  NOT NULL DEFAULT 'Organização',
    concluida   BOOLEAN      NOT NULL DEFAULT FALSE,
    criado_em   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Cada produto e cada tarefa pertence a um usuário.
-- (ALTER ... IF NOT EXISTS também atualiza um banco criado antes do login)
ALTER TABLE produtos ADD COLUMN IF NOT EXISTS
    usuario_id INTEGER REFERENCES usuarios (id) ON DELETE CASCADE;
ALTER TABLE tarefas ADD COLUMN IF NOT EXISTS
    usuario_id INTEGER REFERENCES usuarios (id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_produtos_usuario   ON produtos (usuario_id);
CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos (categoria);
CREATE INDEX IF NOT EXISTS idx_produtos_status    ON produtos (status);
CREATE INDEX IF NOT EXISTS idx_tarefas_usuario    ON tarefas (usuario_id);

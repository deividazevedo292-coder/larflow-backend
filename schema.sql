-- =============================================================
-- LarFlow - estrutura do banco de dados (PostgreSQL)
-- =============================================================

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

CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos (categoria);
CREATE INDEX IF NOT EXISTS idx_produtos_status    ON produtos (status);

-- Configurações do lar (sempre existe uma única linha, com id = 1)
CREATE TABLE IF NOT EXISTS configuracoes (
    id            INTEGER PRIMARY KEY CHECK (id = 1),
    nome_usuario  VARCHAR(80)   NOT NULL DEFAULT 'Bianca',
    nome_lar      VARCHAR(80)   NOT NULL DEFAULT 'LarFlow',
    tema          VARCHAR(10)   NOT NULL DEFAULT 'claro' CHECK (tema IN ('claro', 'escuro')),
    orcamento     NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (orcamento >= 0)
);

INSERT INTO configuracoes (id) VALUES (1) ON CONFLICT (id) DO NOTHING;

-- Tarefas do checklist da casa
CREATE TABLE IF NOT EXISTS tarefas (
    id          SERIAL PRIMARY KEY,
    titulo      VARCHAR(150) NOT NULL,
    categoria   VARCHAR(40)  NOT NULL DEFAULT 'Organização',
    concluida   BOOLEAN      NOT NULL DEFAULT FALSE,
    criado_em   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

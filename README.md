# LarFlow — API (back-end)

Back-end do **LarFlow** ([lar-flow.vercel.app](https://lar-flow.vercel.app)), feito em **Python (Flask)** com banco **PostgreSQL**.

Hoje o site salva tudo no `localStorage` do navegador. Com esta API, os produtos, o orçamento e as configurações ficam guardados no banco de dados, e aparecem em qualquer navegador ou computador.

## Estrutura

```
larflow-backend/
├── app.py            → a API: todas as rotas e regras
├── db.py             → conexão com o PostgreSQL
├── schema.sql        → criação das tabelas
├── init_db.py        → cria as tabelas e cadastra a lista inicial
├── lista_inicial.py  → os 44 produtos que o site já traz de início
├── requirements.txt  → bibliotecas do Python
├── .env.example      → modelo das variáveis de ambiente
└── frontend/api.js   → arquivo para colocar no front (React)
```

## Banco de dados

**produtos**

| Coluna | Tipo | Observação |
|---|---|---|
| id | SERIAL | chave primária |
| nome | VARCHAR(120) | obrigatório |
| categoria | VARCHAR(40) | ambiente da casa ou `Presente` |
| quantidade | INTEGER | no mínimo 1 |
| valor | NUMERIC(10,2) | valor pago; vazio se pendente ou presente |
| status | VARCHAR(20) | `Pendente` ou `Comprado` |
| criado_em / atualizado_em | TIMESTAMP | preenchidos automaticamente |

**configuracoes** (uma linha só): `nome_usuario`, `nome_lar`, `tema` (`claro`/`escuro`) e `orcamento`.

**tarefas** (checklist da casa): `id`, `titulo`, `categoria` (Planejamento, Compras, Organização ou Manutenção) e `concluida`.

Categorias de produto aceitas: Sala de Estar, Sala de Jantar, Cozinha, Quarto, Banheiro, Lavanderia, Escritório, Presente e Outros.

## Como rodar no computador

1. Instale o [PostgreSQL](https://www.postgresql.org/download/) e crie o banco:
   ```sql
   CREATE DATABASE larflow;
   ```
2. Na pasta do projeto, crie o ambiente virtual e instale as bibliotecas:
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   # source venv/bin/activate   # Linux/Mac
   pip install -r requirements.txt
   ```
3. Copie `.env.example` para `.env` e coloque a senha do seu PostgreSQL em `DATABASE_URL`.
4. Crie as tabelas (só na primeira vez):
   ```bash
   python init_db.py
   ```
5. Inicie a API:
   ```bash
   python app.py
   ```
   Abra http://localhost:5000/api/saude. Se aparecer `{"status": "ok"}`, está funcionando.

## Rotas

Endereço base: `http://localhost:5000/api`

| Método | Rota | O que faz |
|---|---|---|
| GET | `/saude` | Confere se a API está no ar |
| GET | `/produtos` | Lista produtos (filtros: `?categoria=Cozinha&status=Pendente`) |
| GET | `/produtos/<id>` | Mostra um produto |
| POST | `/produtos` | Cadastra um produto |
| PUT | `/produtos/<id>` | Edita um produto (pode mandar só o que mudou) |
| PATCH | `/produtos/<id>/comprar` | Marca como comprado (`{"valor": 1500}`) ou presente (`{"presente": true}`) |
| PATCH | `/produtos/<id>/desmarcar` | Volta para pendente |
| DELETE | `/produtos/<id>` | Exclui um produto |
| GET | `/resumo` | Números do painel: totais, progresso, gastos, orçamento e progresso por ambiente |
| GET | `/config` | Nome, nome do lar, tema e orçamento |
| PUT | `/config` | Altera um ou mais desses campos |
| GET | `/tarefas` | Lista as tarefas do checklist |
| POST | `/tarefas` | Cria uma tarefa (`{"titulo": "...", "categoria": "Organização"}`) |
| PATCH | `/tarefas/<id>/alternar` | Marca ou desmarca a tarefa como concluída |
| DELETE | `/tarefas/<id>` | Exclui uma tarefa |
| GET | `/backup` | Exporta tudo em JSON |
| POST | `/backup` | Importa um backup (substitui tudo) |
| POST | `/restaurar-lista-inicial` | Volta para a lista inicial de 44 produtos |
| DELETE | `/dados` | Apaga tudo e volta as configurações ao padrão |

Exemplo de cadastro:

```json
POST /api/produtos
{ "nome": "Ventilador", "categoria": "Quarto", "quantidade": 2 }
```

Quando algo está errado, a API responde com código 400 ou 404 e uma mensagem:

```json
{ "erro": "Informe o valor do produto comprado." }
```

### Regras validadas pela API

São as mesmas que o site já usa:

- Nome e categoria são obrigatórios; a quantidade precisa ser 1 ou mais.
- Produto comprado precisa ter valor (a não ser que seja presente).
- Presente nunca tem valor e não entra no total gasto.
- O valor aceita ponto ou vírgula (`199.90` ou `"199,90"`).

## Ligando no site (front)

O site já foi adaptado para usar esta API (veja o pacote `larflow-front-alteracoes`). Para rodar o site apontando para a API, crie no projeto do front um arquivo `.env.local` com:

```
VITE_API_URL=http://localhost:5000
```

Como a troca foi feita, por exemplo na tela de produtos:

```jsx
// ANTES
const [produtos, setProdutos] = useState(() =>
  JSON.parse(localStorage.getItem("produtos")) || listaInicial
);

// DEPOIS
import { listarProdutos, criarProduto } from "../services/api";

const [produtos, setProdutos] = useState([]);

useEffect(() => {
  listarProdutos().then(setProdutos).catch((e) => alert(e.message));
}, []);

async function salvar(novoProduto) {
  try {
    const criado = await criarProduto(novoProduto);
    setProdutos([...produtos, criado]);
  } catch (e) {
    alert(e.message); // mostra a mensagem de erro que veio da API
  }
}
```

O painel inicial pode usar só `obterResumo()`, que já traz todos os números calculados.

**Para não perder os dados que já estão no navegador:** no site atual, use **Configurações → Exportar backup** e envie o arquivo para `POST /api/backup`. A API aceita o mesmo formato.

## Publicando na internet

Uma opção é o [Render](https://render.com):

1. Crie um banco **PostgreSQL** no Render (ou no [Neon](https://neon.tech)) e copie a URL de conexão.
2. Crie um **Web Service** apontando para o repositório desta API:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
   - Variáveis: `DATABASE_URL` (a URL do banco) e `CORS_ORIGIN=https://lar-flow.vercel.app`
3. Rode `python init_db.py` uma vez apontando para o banco da nuvem.
4. Na Vercel, cadastre `VITE_API_URL` com o endereço da API e publique o site de novo.

## Próximos passos possíveis

- **Login de usuários:** hoje todos que acessam veem a mesma lista. Com login, cada pessoa teria a sua.
- **Testes automatizados** com `pytest`.

# Notion Manager

Um conjunto de ferramentas para interagir com a API do Notion, permitindo o gerenciamento de bancos de dados, páginas e tarefas.

## Funcionalidades

- Consulta de bancos de dados com filtros e ordenação
- Recuperação e manipulação de páginas
- Gerenciamento de tarefas e pessoas
- Criação e atualização de conteúdo
- Pesquisa avançada

## Requisitos

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (Gerenciador de pacotes e ambientes Python)
- Chave de API do Notion

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/notion-manager.git
cd notion-manager
```

### 2. Configure o ambiente e instale as dependências

Com uv instalado, execute:

```bash
# Cria um ambiente virtual
uv venv

# Ativa o ambiente virtual
# No Windows:
.venv\Scripts\activate
# No macOS/Linux:
source .venv/bin/activate

# Instala as dependências
uv pip install -r requirements.txt

# Instala o MCP
uv run mcp install main.py
```

### 3. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```
NOTIO_API_KEY=seu_token_da_api_notion
DATABASE_ID=id_do_seu_banco_de_dados_notion
```

Para obter sua chave de API do Notion:
1. Acesse [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Crie uma nova integração
3. Copie o token secreto

Você também precisa compartilhar o banco de dados do Notion com a sua integração.

## Uso

### Inicie o servidor

```bash
uv run mcp install main.py
```


## Estrutura do Projeto

```
notion-manager/
├── main.py          # Arquivo principal do projeto
├── requirements.txt # Dependências do projeto
├── .env             # Arquivo de variáveis de ambiente (não versionado)
└── README.md        # Este arquivo
```

## Dependências

- FastMCP - Framework para criação de ferramentas
- Requests - Para fazer requisições HTTP
- Python-decouple - Para gerenciar variáveis de ambiente

## Solução de Problemas

### Erro de autenticação
Se você receber um erro 401, verifique se:
- A chave de API está correta no arquivo .env
- O banco de dados do Notion foi compartilhado com sua integração

### Problemas com as permissões da API
Se você receber um erro 403, verifique se:
- Sua integração possui as capacidades necessárias (leitura/escrita)
- O banco de dados ou página foi compartilhado corretamente com a integração

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

[MIT](https://choosealicense.com/licenses/mit/)
# 🕵️‍♂️ Caça Anomalias

O **Caça Anomalias** é uma API desenvolvida em Python para ingestão, análise e detecção de anomalias em conjuntos de transações. O projeto utiliza FastAPI e trabalha com a estruturação de um banco de dados para armazenar e processar os dados de treinamento (`transacoes_treino.json`).

## 🛠️ Tecnologias Utilizadas

O projeto faz uso das seguintes bibliotecas e ferramentas:

- **[FastAPI](https://fastapi.tiangolo.com/):** Criação de APIs rápidas e modernas.
- **[Uvicorn](https://www.uvicorn.org/):** Servidor ASGI para rodar a aplicação FastAPI.
- **[SQLAlchemy](https://www.sqlalchemy.org/):** ORM (Object-Relational Mapping) para a manipulação do banco de dados.
- **[Pydantic](https://docs.pydantic.dev/):** Validação de dados e gerenciamento de configurações.
- **[Pandas](https://pandas.pydata.org/):** Manipulação e análise dos dados estruturados.

## 📂 Estrutura do Projeto

```text
Caca_Anomalias/
├── .venv/                         # Ambiente virtual (gerado localmente)
├── data/                          # Diretório de armazenamento de fontes de dados
│   └── transacoes_treino.json     # Dados JSON usados para treinamento
├── src/                           # Código fonte / regras de negócio principal
│   ├── __init__.py 
│   ├── database.py                # Ponto de entrada (API FastAPI) e manipulação do banco
│   └── transacoes_db.db           # Banco de dados SQLite gerado automaticamente
├── LICENSE                        # Licença do projeto
├── README.md                      # Documentação
└── requirements.txt               # Instruções e dependências essenciais
```

## 🚀 Como Executar o Projeto Localmente

Siga o passo a passo abaixo para rodar a aplicação em seu computador.

### 1. Clonar o repositório

```bash
git clone https://github.com/SEU_USUARIO/Caca_Anomalias.git
cd Caca_Anomalias
```

### 2. Criar e Ativar o Ambiente Virtual (.venv)

É altamente recomendado utilizar um ambiente virtual para isolar as dependências do projeto.

- **No Windows:**
  ```cmd
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```

- **No Linux/Mac:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Instalar as Dependências

Com o ambiente virtual ativado, instale as bibliotecas requeridas pelo projeto:

```bash
pip install -r requirements.txt
```

### 4. Criação do Banco e Inserção dos Dados

Navegue até a pasta `src` onde está localizado o script principal do servidor:

```bash
cd src
```

Inicie o servidor local através do `uvicorn`. O código acerta automaticamente os caminhos e cria os dados a partir do JSON caso não existam:

```bash
uvicorn database:app --reload
```

A API estará disponível no endereço: [http://127.0.0.1:8000](http://127.0.0.1:8000)

Você pode acessar a documentação automática (Swagger UI) fornecida pelo FastAPI acessando: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 📄 Licença

Consulte o arquivo `LICENSE` para obter detalhes sobre a licença aplicada a este projeto.

# Controle de Estoque — 7 Lojas

Dashboard web para registrar estoque por loja, com login, fotos individuais por produto, histórico e painel administrativo com atualização automática a cada cinco minutos.

## Arquivos
- `app.py`: aplicação Streamlit.
- `requirements.txt`: bibliotecas necessárias.
- `supabase_setup.sql`: tabelas, regras de acesso (RLS), bucket privado para fotos e criação das sete lojas.
- `.streamlit/secrets.toml.example`: modelo de configuração local. Não coloque credenciais reais no GitHub.

## 1. Criar o projeto Supabase
1. Entre em https://supabase.com/ e crie um projeto.
2. Abra **SQL Editor** e execute todo o conteúdo de `supabase_setup.sql`.
3. Em **Project Settings / API** (ou Connect), copie a Project URL e a chave publicável/anon do projeto. Nunca use `service_role` no dashboard.

## 2. Criar os usuários
1. No Supabase, abra **Authentication > Users** e crie o usuário administrador com o e-mail e a senha que ele já usa. O administrador continuará podendo entrar com esse e-mail.
2. Copie o UUID do usuário administrador.
3. No SQL Editor, execute, trocando o UUID e o nome:

```sql
insert into public.profiles (user_id, display_name, role, store_id)
values ('COLE-O-UUID-DO-ADMIN', 'Administrador', 'admin', null);
```

4. Para cada funcionária, escolha um nome de usuário único, sem espaços e sem `@`. Por exemplo, `loja1` ou `maria.loja1`. Recomendamos um usuário individual para cada pessoa, não um login compartilhado.
5. Em **Authentication > Users**, clique em **Add user** e crie a conta usando o e-mail interno correspondente ao nome de usuário, acrescentando `@estoque.invalid`. Exemplo: para o usuário `loja1`, use `loja1@estoque.invalid`. Defina uma senha inicial e, se aparecer a opção **Auto Confirm User**, marque-a, pois esse endereço é apenas um identificador interno e não recebe e-mails.
6. Copie o UUID da conta criada e associe-a à loja certa pelo SQL Editor. Exemplo para a Loja 1:

```sql
insert into public.profiles (user_id, display_name, role, store_id)
values (
  'COLE-O-UUID-DA-FUNCIONARIA',
  'Nome da funcionária',
  'staff',
  (select id from public.stores where name = 'Loja 1')
);
```

Repita para cada funcionária, sempre com um nome de usuário exclusivo e a loja correta. No aplicativo, a funcionária digita somente o nome de usuário (por exemplo, `loja1`) e a senha. A conta administrativa continua entrando com o e-mail que já foi cadastrado.

**Importante:** como o e-mail interno termina em `.invalid`, ele não recebe mensagens nem serve para recuperação automática de senha. A administração deverá redefinir a senha no Supabase se alguém esquecê-la. Antes de usar com a equipe, teste a criação de uma conta de funcionária.

## 3. Rodar localmente no computador
Instale Python 3.11 ou mais recente em https://www.python.org/downloads/.
Abra o terminal na pasta do projeto e rode:

```bash
python -m venv .venv
```

Ative o ambiente:
- Windows PowerShell: ` .venv\\Scripts\\Activate.ps1 `
- macOS/Linux: `source .venv/bin/activate`

Depois instale as dependências:

```bash
pip install -r requirements.txt
```

Crie a pasta `.streamlit` (se não existir) e o arquivo `.streamlit/secrets.toml` com:

```toml
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_ANON_KEY = "SUA_CHAVE_PUBLICA_ANON"
```

Rode:

```bash
streamlit run app.py
```

O navegador abrirá o dashboard localmente.

## 4. Publicar na internet
1. Crie um repositório **privado** no GitHub e envie `app.py`, `requirements.txt` e os outros arquivos do projeto, mas **não envie** `.streamlit/secrets.toml`.
2. Entre em https://share.streamlit.io/ e conecte o GitHub.
3. Escolha o repositório e selecione `app.py` como arquivo principal.
4. Em **Advanced settings / Secrets**, adicione `SUPABASE_URL` e `SUPABASE_ANON_KEY` no formato TOML mostrado acima.
5. Publique e teste com uma conta administrativa e uma conta de funcionária.

## Segurança e limites desta primeira versão
- A aplicação usa a chave pública/anon do Supabase; as permissões são aplicadas por políticas RLS no banco e no Storage. Não coloque a chave `service_role` no app ou no GitHub.
- A primeira versão registra a quantidade restante em cada lançamento. Ela não calcula vendas automaticamente porque ainda não há campos de estoque inicial, reposição, perdas e vendas confirmadas.
- As fotos são opcionais e individuais por produto; limite de 8 MB por foto.
- Os dados são atualizados no painel administrativo a cada cinco minutos. O formulário não envia fotos até a pessoa clicar em **Salvar lançamento**.
- Antes de usar com dados reais, teste os acessos com contas fictícias e confirme que uma funcionária não consegue consultar outra loja.
- A criação/remoção de contas é feita no painel do Supabase nesta versão; o dashboard não cria usuários automaticamente.
- Funcionárias entram com nome de usuário e senha. Internamente, o nome é convertido em um identificador de autenticação `nome@estoque.invalid`; não é necessário usar e-mail pessoal. A conta administrativa continua usando seu e-mail.

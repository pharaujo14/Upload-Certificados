
# Sistema de Upload e Gestão de Certificações com Streamlit

Este projeto é um aplicativo desenvolvido em Streamlit para facilitar o upload, registro e gerenciamento de certificações profissionais. O sistema também oferece integração com Google Drive para armazenamento seguro e envio automático de notificações por e-mail após o registro de uma nova certificação.

## Funcionalidades

- **Autenticação de Usuários**:
  - Sistema de login seguro com verificação de autenticação.
  - Diferenciação de roles (administrador e usuário comum) com funcionalidades específicas.
  
- **Upload de Arquivos**:
  - Envio de certificações em formatos PDF, PNG, JPG e JPEG.
  - Validação de campos obrigatórios antes do envio.

- **Integração com Google Drive**:
  - Upload seguro de arquivos para uma pasta específica no Google Drive utilizando credenciais de serviço.
  - Nomeação personalizada de arquivos com base no nome do usuário e dados da certificação.

- **Gerenciamento de Certificações**:
  - Registro de informações como área, tipo e data da certificação, além de outros metadados.
  - Armazenamento de informações no banco de dados.

- **Envio Automático de E-mails**:
  - Notificação enviada automaticamente ao responsável após o registro de uma certificação.

- **Interface de Usuário**:
  - Design interativo com carregamento dinâmico de elementos como formulários e botões.
  - Funcionalidades específicas para administradores, incluindo criação de novos usuários e alteração de senhas.

## Tecnologias Utilizadas

- [Streamlit](https://streamlit.io/): Framework para desenvolvimento de interfaces web.
- [Google Drive API](https://developers.google.com/drive): API para integração com Google Drive.
- [Pytz](https://pytz.sourceforge.net/): Biblioteca para gerenciar timezones.
- [Psutil](https://psutil.readthedocs.io/): Ferramenta para verificação de uso de arquivos e recursos do sistema.
- [SMTP](https://docs.python.org/3/library/smtplib.html): Protocolo para envio de e-mails.

## Estrutura do Projeto

```plaintext
.
├── app.py                # Código principal do aplicativo
├── conectaBanco.py       # Módulo para conexão ao banco de dados
├── login.py              # Módulo de autenticação de usuários
├── cadastra_user.py      # Módulo para gerenciamento de usuários
├── logo.png              # Logotipo principal do sistema
├── logo_site.png         # Logotipo utilizado no cabeçalho
├── requirements.txt      # Lista de dependências do projeto
└── README.md             # Documentação do projeto
```

### Descrição dos Arquivos

- **app.py**: Código principal do sistema, contendo a interface e funcionalidades principais.
- **conectaBanco.py**: Responsável por conectar e interagir com o banco de dados.
- **login.py**: Implementa a lógica de autenticação e controle de acesso dos usuários.
- **cadastra_user.py**: Oferece funcionalidades para adicionar novos usuários e trocar senhas.
- **logo.png** e **logo_site.png**: Imagens dos logotipos utilizados no sistema.
- **requirements.txt**: Lista de bibliotecas necessárias para o funcionamento do sistema.
- **README.md**: Documentação do projeto.

## Configuração do Ambiente

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/usuario/projeto-certificacoes.git
   cd projeto-certificacoes
   ```

2. **Crie um ambiente virtual e instale as dependências**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

3. **Configure o arquivo `secrets.toml`**:
   Adicione as credenciais do Google Drive e SMTP ao arquivo `secrets.toml` no diretório do projeto. Exemplo:
   ```toml
   [google_drive]
   type = "service_account"
   project_id = "projeto-id"
   private_key_id = "chave-privada-id"
   private_key = "chave-privada"
   ...

   [smtp]
   sender = "seu-email@gmail.com"
   recipient = "destinatario@gmail.com"
   password = "sua-senha"
   ```

4. **Execute o aplicativo**:
   ```bash
   streamlit run app.py
   ```

## Personalização

- **Logotipo**: Substitua os arquivos `logo.png` ou `logo_site.png` pelas imagens desejadas, mantendo o mesmo nome dos arquivos.
- **Banco de Dados**: Configure a conexão com o banco no módulo `conectaBanco.py` para atender às suas necessidades específicas.
- **Notificações por E-mail**: Ajuste os parâmetros de envio no método `enviar_resultado`.

## Dependências

Certifique-se de que as seguintes bibliotecas estão instaladas:

- `streamlit`
- `pytz`
- `psutil`
- `google-auth`
- `google-auth-oauthlib`
- `pillow`

Para instalar todas as dependências, utilize:
```bash
pip install -r requirements.txt
```

## Licença

Este projeto é distribuído sob a licença MIT. Sinta-se à vontade para usá-lo e modificá-lo conforme necessário.

# Conversor de CSV para PDF com Streamlit

Este projeto é um aplicativo Streamlit que permite converter arquivos CSV em PDFs formatados. O PDF gerado inclui o logotipo no cabeçalho de todas as páginas e organiza as informações do CSV em seções, conforme especificado.

## Funcionalidades

- Carrega um arquivo CSV e gera um PDF formatado com base nos dados do arquivo.
- O PDF inclui:
  - Logotipo no cabeçalho de todas as páginas.
  - Nome do responsável pela revisão extraído do CSV.
  - Seções identificadas automaticamente com base nos dados do CSV.
  - Perguntas e respostas formatadas conforme especificações.
- O nome do PDF gerado é o mesmo do arquivo CSV carregado, facilitando a identificação.

## Tecnologias Utilizadas

- [Streamlit](https://streamlit.io/): Framework para criação de aplicativos web interativos com Python.
- [Pandas](https://pandas.pydata.org/): Biblioteca para manipulação e análise de dados.
- [FPDF](http://www.fpdf.org/): Biblioteca para a geração de documentos PDF.

## Estrutura do Projeto

```plaintext
.
├── app.py            # Código principal do aplicativo Streamlit
├── logo.png          # Logotipo utilizado no cabeçalho do PDF
├── requirements.txt  # Lista de dependências do projeto
└── README.md         # Documentação do projeto
```

### Descrição dos Arquivos

- **app.py**: Contém o código principal que implementa o aplicativo Streamlit para conversão de CSV em PDF.
- **logo.png**: Imagem do logotipo que é inserida no cabeçalho de todas as páginas do PDF gerado.
- **requirements.txt**: Arquivo com as bibliotecas necessárias para o projeto. Use este arquivo para instalar todas as dependências com `pip install -r requirements.txt`.
- **README.md**: Documentação do projeto, incluindo instruções de uso, instalação e contribuições.

## Como Adicionar o `requirements.txt`

Para criar o `requirements.txt` com as bibliotecas necessárias, execute o comando abaixo no terminal:

```bash
pip freeze > requirements.txt
```

## Certifique-se de que as seguintes bibliotecas estão presentes no arquivo:

- `streamlit`
- `pandas`
- `fpdf`

## Personalização

### Alterar o Logotipo

Para alterar o logotipo exibido no PDF, basta substituir o arquivo `logo.png` na raiz do projeto pelo novo logotipo desejado, mantendo o mesmo nome de arquivo (`logo.png`). A imagem será ajustada automaticamente na geração do PDF.

### Formatação do PDF

Você pode personalizar a formatação do PDF modificando a classe `PDF` no arquivo `app.py`. Ajuste fontes, tamanhos, espaçamentos e outras configurações de acordo com as suas necessidades.


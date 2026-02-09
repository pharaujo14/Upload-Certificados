import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def gerar_email_institucional(tipo, dados):
    link_sistema = dados.get("link_sistema", "https://centurydata.streamlit.app/")

    header = f"""
    <div style='background-color:#004080; padding:20px; text-align:center;'>
    </div>
    """

    footer = """
    <div style='background:#f0f0f0; padding:10px; text-align:center; font-size:11px; color:#777;'>
        Este e-mail foi enviado automaticamente pelo sistema Century Data.
    </div>
    """

    if tipo == "criar_usuario":
        body = f"""
        <h2 style='color:#004080;'>🚀 Sua conta foi criada</h2>
        <p>Olá <strong>{dados['nome']}</strong>,</p>
        <p>Seu acesso ao sistema Century Data foi criado com sucesso!</p>
        <p style='font-size:13px; color:#666;'>Seu login é realizado pela conta de email coorporativo.</p>
        <a href='{link_sistema}' style='display:inline-block; padding:10px 20px; background:#004080; color:#fff; text-decoration:none; border-radius:5px; margin-top:15px;'>Acessar o Sistema</a>
        """

    elif tipo == "upload_certificado":
        body = f"""
        <h2 style='color:#004080;'>📄 Novo Certificado Enviado</h2>
        <p>O usuário <strong>{dados['nome']}</strong> realizou o upload de um novo certificado.</p>
        <p><b>Arquivo:</b> {dados['arquivo']}</p>
        """

    elif tipo == "notificacao":
        body = f"""
        <h2 style='color:#004080;'>🔔 Notificação</h2>
        <p>{dados['mensagem']}</p>
        <a href='{link_sistema}' style='display:inline-block; padding:10px 20px; background:#004080; color:#fff; text-decoration:none; border-radius:5px; margin-top:15px;'>Acessar o Sistema</a>
        """

    else:
        body = "<p>Tipo de e-mail inválido.</p>"

    return f"""
    <div style='font-family: Arial, sans-serif; max-width:600px; margin:auto; border:1px solid #e0e0e0; border-radius:8px; overflow:hidden; background:#ffffff;'>
        {header}
        <div style='padding:20px;'>{body}</div>
        {footer}
    </div>
    """
    
def enviar_resultado(subject, body, sender, recipients, password, html=False):
    """
    Função para envio de e-mails (suporta texto ou HTML)
    
    subject: Assunto
    body: Conteúdo do e-mail (plain ou HTML)
    sender: E-mail remetente
    recipients: Lista de destinatários
    password: Senha do e-mail remetente
    html: True se o corpo for HTML
    """
    
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)

    if html:
        msg.attach(MIMEText(body, 'html'))
    else:
        msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipients, msg.as_string())
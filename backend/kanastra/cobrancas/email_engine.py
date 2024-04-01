import boto3
from .models import Cobranca


def send_email_ses(subject, body, recipient):
    # Configure o Boto3 com suas credenciais
    ses = boto3.client("ses", region_name="us-west-2")  # Substitua pela sua região

    # Envie o e-mail usando o Amazon SES
    response = ses.send_email(
        Source="seu_email@example.com",  # Substitua pelo seu endereço de e-mail verificado no Amazon SES
        Destination={"ToAddresses": [recipient]},
        Message={"Subject": {"Data": subject}, "Body": {"Text": {"Data": body}}},
    )

    return response


def send_emails_from_database():
    cobrancas = Cobranca.objects.all()
    for cobranca in cobrancas:
        subject = "Assunto do E-mail"
        body = f"Olá {cobranca.nome}, aqui está seu boleto com valor de R${cobranca.valor}."  # Adapte o corpo do e-mail conforme necessário
        recipient = cobranca.email
        send_email_ses(subject, body, recipient)


# # Exemplo de uso:
# send_emails_from_database()

# Desafio Técnico - Kanastra

Bem-vindo ao Desafio Técnico da Kanastra! Este desafio consiste em construir um sistema de cobranças na plataforma. O sistema precisa atender aos seguintes requisitos:

## Frontend

- Receber um arquivo .csv através de uma interface de formulário.
- Manter uma listagem atualizada de arquivos recebidos na interface.
- A rota de upload deve ser diferente da rota de listagem. Após o upload de um novo arquivo, a listagem deve ser atualizada automaticamente.
- Utilize context do React para gerenciar o estado e as atualizações de forma eficiente.
- Utilize os componentes fornecidos e melhore-os para criar uma experiência de usuário agradável.

## Backend

- O formulário deverá usar um endpoint da API para processar o arquivo.
- O processamento do arquivo deve ser concluído em menos de 60 segundos para lidar com grandes volumes de registros.
- Com base no input recebido, o sistema deve gerar boletos para cobrança e disparar mensagens para os e-mails da lista.

## Arquivo CSV do Desafio

O arquivo .csv terá as seguintes colunas:

- `name` → Nome
- `governmentId` → Número do Documento
- `email` → E-mail do Sacado
- `debtAmount` → Valor
- `debtDueDate` → Data para ser Paga
- `debtId` → UUID para o Débito

Exemplo do conteúdo do arquivo:

```csv
name,governmentId,email,debtAmount,debtDueDate,debtId
John Doe,11111111111,johndoe@kanastra.com.br,1000000.00,2022-04-01,123456
Jane Smith,22222222222,janesmith@kanastra.com.br,500000.00,2022-04-01,789012

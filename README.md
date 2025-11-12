
## Como rodar localmente
- pip install -r requirements.txt`
- `sam local start-api`

Inclui duas Lambdas uma fila SQS e integrações AWS

CI/CD com GitHub Actions


 Resumo do app

Aplicação para permitir que usuários anunciem celulares que querem trocar, pesquisem ofertas e façam propostas de troca.

Principais funcionalidades:

Cadastro/login de usuários (autenticação básica)

Cadastro de aparelho (marca, modelo, estado, fotos, descrição, localização)

Buscar aparelhos por filtros (marca, modelo, estado, faixa de preço/valor estimado)

Propor troca — enviar proposta para outro usuário

Sistema de avaliação (feedback pós-troca)

Notificações de propostas (fila + processamento assíncrono)
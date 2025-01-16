# app-lambda-video-frame-pro-processing

Este repositório implementa a função **Lambda** que processa os vídeos. A função extrai frames, cria arquivos ZIP e armazena os resultados no **S3**.

## Funções
- Processar vídeos utilizando **FFmpeg** para extrair frames.
- Criar um arquivo ZIP com as imagens extraídas e armazená-lo no **S3**.
- Atualizar o status no **DynamoDB**.

## Tecnologias
- AWS Lambda
- AWS S3
- AWS DynamoDB
- FFmpeg

## Como usar
1. Configure a função **Lambda** para processar vídeos.
2. Integre com o **S3** para armazenar os arquivos processados.
3. Atualize o status no **DynamoDB**.

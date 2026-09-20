"""
Publica o relatório final gerado no bucket S3 configurado como site estático.
"""

import os
import boto3
from dotenv import load_dotenv

load_dotenv()

access_key = os.getenv("AWS_ACCESS_KEY")
secret_key = os.getenv("AWS_SECRET_KEY")

s3 = boto3.client(
    "s3",
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name="sa-east-1"
)

nome_bucket = "relatorio-analise-clientes-hugoqueiroz" 

with open("relatorio_final.html", "rb") as arquivo:
    s3.put_object(
        Bucket=nome_bucket,
        Key="relatorio_final.html",
        Body=arquivo,
        ContentType="text/html"
    )

print(f"Relatório publicado! Acesse em:")
print(f"http://{nome_bucket}.s3-website-sa-east-1.amazonaws.com")
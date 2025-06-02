from fastapi import FastAPI
from pydantic import BaseModel
from route import buscar_melhor_rota, buscar_detalhes_fretes_por_ids, gerar_texto_whatsapp_todas_rotas
from fastapi import Query
from typing import Optional, List
import mysql.connector
import os
from dotenv import load_dotenv
from fastapi import FastAPI

app = FastAPI()

class RotaRequest(BaseModel):
    origem: str
    destino: str
    caminhao: str

@app.post("/gerar-rota")
def gerar_rota(data: RotaRequest):
    rotas = buscar_melhor_rota(data.origem, data.destino, data.caminhao)
    ids = list({trecho["id"] for rota in rotas for trecho in rota["rota"]})
    dados_fretes = buscar_detalhes_fretes_por_ids(ids)
    mensagem = gerar_texto_whatsapp_todas_rotas(rotas, dados_fretes)
    return {"mensagem": mensagem}

@app.get("/buscar-fretes")
def consultar_fretes_dinamicamente(
    origem: Optional[str] = Query(None, description="UF ou cidade de origem"),
    destino: Optional[str] = Query(None, description="UF ou cidade de destino"),
    produto: Optional[str] = Query(None, description="Nome do produto transportado"),
    tipo_caminhao: Optional[str] = Query(None, description="Tipo de caminhão desejado"),
    empresa: Optional[str] = Query(None, description="Nome parcial da empresa")
):
    load_dotenv()

    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            port=int(os.environ.get("DB_PORT")),
            password=os.environ.get("DB_PASS"),
            database=os.environ.get("DB_BASE")
        )
        cursor = conn.cursor(dictionary=True)

        base_query = "SELECT * FROM fretes WHERE 1=1"
        params: List = []

        if origem:
            base_query += " AND origem LIKE %s"
            params.append(f"%{origem}%")
        if destino:
            base_query += " AND destino LIKE %s"
            params.append(f"%{destino}%")
        if produto:
            base_query += " AND produto LIKE %s"
            params.append(f"%{produto}%")
        if tipo_caminhao:
            base_query += " AND veiculos LIKE %s"
            params.append(f"%{tipo_caminhao}%")
        if empresa:
            base_query += " AND empresa LIKE %s"
            params.append(f"%{empresa}%")

        cursor.execute(base_query, params)
        resultados = cursor.fetchall()
        return {"fretes": resultados}

    except mysql.connector.Error as err:
        return {"erro": str(err)}

    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

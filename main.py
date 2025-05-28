from fastapi import FastAPI
from pydantic import BaseModel
from route import buscar_melhor_rota, buscar_detalhes_fretes_por_ids, gerar_texto_whatsapp_todas_rotas

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
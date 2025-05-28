import mysql.connector
import os
from dotenv import load_dotenv
from decimal import Decimal

CUSTO_POR_KM = {
    "rodotrem": 4.80,
    "bitrem": 4.20,
    "vanderleia": 4.00,
    "carreta_ls": 3.80,
    "carreta": 3.60,
    "bitruck": 3.10,
    "truck": 2.80
}

CARGA_POR_TIPO = {
    "rodotrem": 36.0,       # até 36 toneladas
    "bitrem": 35.0,         # até 35 toneladas
    "vanderleia": 32.0,     # até 32 toneladas
    "carreta_ls": 30.0,     # até 30 toneladas (Carreta de 3 eixos)
    "carreta": 28.0,        # até 28 toneladas (Carreta simples)
    "bitruck": 22.0,        # até 22 toneladas
    "truck": 18.0           # até 18 toneladas
}


def carregar_fretes_sql():
    """
    Conecta ao banco de dados e carrega os fretes únicos da tabela como lista de dicionários.
    """
    try:
        load_dotenv()
        print("🔧 Carregando variáveis de ambiente:")
        print(f"HOST: {os.environ.get('DB_HOST')}")
        print(f"USER: {os.environ.get('DB_USER')}")
        print(f"PORT: {os.environ.get('DB_PORT')}")
        print(f"DATABASE: {os.environ.get('DB_BASE')}")

        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            port=int(os.environ.get("DB_PORT")),
            password=os.environ.get("DB_PASS"),
            database=os.environ.get("DB_BASE")
        )
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT id, origem, destino, preco, KM
            FROM fretes
            WHERE origem IS NOT NULL AND destino IS NOT NULL AND preco > 0 AND KM > 0
        """
        cursor.execute(query)
        todos_fretes = cursor.fetchall()

        # Criar set para rastrear duplicatas
        vistos = set()
        fretes_unicos = []
        for f in todos_fretes:
            chave = (f["origem"], f["destino"], float(f["preco"]), float(f["KM"]))
            if chave not in vistos:
                vistos.add(chave)
                fretes_unicos.append(f)

        print(f"✅ {len(fretes_unicos)} fretes únicos carregados do banco.")
        return fretes_unicos

    except mysql.connector.Error as err:
        print(f"❌ Erro ao conectar ou buscar dados: {err}")
        return []

    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("🔌 Conexão com banco encerrada.")


def calcular_custo_frete(distancia_km, tipo_caminhao):
    custo_km = Decimal(str(CUSTO_POR_KM.get(tipo_caminhao.lower(), 3.50)))
    return round(distancia_km * custo_km, 2)

def extrair_estado(cidade_uf):
    # Assume o padrão "Cidade/UF"
    return cidade_uf.split("/")[-1].strip().upper() if "/" in cidade_uf else ""

def explorar(rota, valor_acumulado, km_acumulado, fretes, melhores_rotas,
             tipo_caminhao, limite_etapas=3, destino_final=None):
    ultima = rota[-1]

    if destino_final and extrair_estado(ultima["destino"]) == destino_final.upper():
        toneladas = Decimal(str(CARGA_POR_TIPO.get(tipo_caminhao.lower(), 20.0)))
        valor_total = valor_acumulado * toneladas
        custo_total = calcular_custo_frete(km_acumulado, tipo_caminhao)
        lucro = valor_total - Decimal(str(custo_total))  # Garante que o custo também seja Decimal

        #print(f"   ➕ Valor total acumulado: R${valor_total:.2f} (R${valor_acumulado:.2f}/t x {toneladas}t)")



        #print("\n📦 ROTA COMPLETA ENCONTRADA:")
        #for i, trecho in enumerate(rota, 1):
        #    print(f"   {i}. {trecho['origem']} → {trecho['destino']} | R${trecho['preco']:.2f} | {trecho['KM']} km")
        #print(f"   ➕ Valor total acumulado: R${valor_acumulado:.2f}")
        #print(f"   📏 KM total acumulado: {km_acumulado} km")
        #print(f"   💸 Custo estimado ({tipo_caminhao}): R${custo_total:.2f}")
        #print(f"   💰 Lucro estimado: R${lucro:.2f}")

        melhores_rotas.append({
            "rota": rota,
            "valor_total": valor_acumulado,
            "km_total": km_acumulado,
            "custo_total": custo_total,
            "lucro": lucro
        })

    if len(rota) >= limite_etapas:
        return

    for f in fretes:
        if f["origem"] == ultima["destino"] and f not in rota:
            #print(f"🔁 Explorando: {ultima['destino']} → {f['destino']} | R${f['preco']:.2f} | {f['KM']} km")
            nova_rota = rota + [f]
            novo_valor = valor_acumulado + f["preco"]
            nova_distancia = km_acumulado + f["KM"]

            explorar(
                nova_rota,
                novo_valor,
                nova_distancia,
                fretes,
                melhores_rotas,
                tipo_caminhao,
                limite_etapas,
                destino_final
            )

def buscar_melhor_rota(origem_inicial, destino_final, tipo_caminhao, limite_etapas=3):
    fretes = carregar_fretes_sql()
    melhores_rotas = []

    for f in fretes:
        origem_match = origem_inicial.lower() in f["origem"].lower()
        if origem_match:
            #print(f"🚚 Iniciando busca a partir de {f['origem']} → {f['destino']}")

            explorar(
                rota=[f],
                valor_acumulado=f["preco"],
                km_acumulado=f["KM"],
                fretes=fretes,
                melhores_rotas=melhores_rotas,
                tipo_caminhao=tipo_caminhao,
                limite_etapas=limite_etapas,
                destino_final=destino_final
            )

    melhores_rotas.sort(key=lambda x: x["lucro"], reverse=True)
    #print(f"\n🏁 {len(melhores_rotas)} rotas possíveis encontradas.")
    #for idx, r in enumerate(melhores_rotas, 1):
    #    print(f"{idx}. Lucro: R${r['lucro']:.2f} | KM: {r['km_total']} | Valor Total: R${r['valor_total']:.2f}")
    #    print(f"\n🔍 Rota #{idx}:")
    #    for i, trecho in enumerate(r["rota"], 1):
    #        print(f"   {i}. {trecho['origem']} → {trecho['destino']} | R${trecho['preco']} | {trecho['KM']} km")
    #    print(f"💰 Lucro: R${r['lucro']:.2f} | 📏 KM: {r['km_total']} | 💸 Valor Total: R${r['valor_total']:.2f}")

    return melhores_rotas[:3]

def buscar_detalhes_fretes_por_ids(ids):
    """
    Recebe uma lista de IDs e retorna um dicionário com os dados detalhados dos fretes correspondentes.
    """
    from dotenv import load_dotenv
    import mysql.connector
    import os

    load_dotenv()

    if not ids:
        return {}

    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            port=int(os.environ.get("DB_PORT")),
            password=os.environ.get("DB_PASS"),
            database=os.environ.get("DB_BASE")
        )
        cursor = conn.cursor(dictionary=True)

        placeholders = ','.join(['%s'] * len(ids))
        query = f"""
            SELECT 
                id, empresa, contatos AS contato, origem, destino, preco, KM, produto
            FROM fretes
            WHERE id IN ({placeholders})
        """
        cursor.execute(query, ids)
        resultados = cursor.fetchall()

        return {r["id"]: r for r in resultados}

    except mysql.connector.Error as err:
        print(f"❌ Erro ao buscar fretes por ID: {err}")
        return {}

    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()



def gerar_texto_whatsapp_todas_rotas(rotas, dados_fretes):
    mensagem = "🚛 *Confira abaixo 3 rotas de fretes disponíveis:*\n\n"

    for i, rota_info in enumerate(rotas, 1):
        mensagem += "═════════════════════════\n"
        mensagem += f"🛣️ *Rota #{i}*\n"
        
        for trecho in rota_info["rota"]:
            id_frete = trecho["id"]
            dados = dados_fretes.get(id_frete, {})

            empresa = dados.get("empresa", "Empresa não informada")
            contato = dados.get("contato", "Contato não informado")
            produto = dados.get("produto", "Produto não informado")
            mensagem += (
                f"📍 *Origem:* {trecho['origem']}\n"
                f"🏁 *Destino:* {trecho['destino']}\n"
                f"📦 *Produto:* {produto}\n"

                f"💰 *Valor por tonelada:* R${trecho['preco']:.2f}\n"
                f"📏 *Distância:* {trecho['KM']} km\n"
                f"🏢 *Empresa:* {empresa}\n"
                f"📞 *Contato:* {contato}\n\n"
            )
        
        mensagem += (
            
            f"🛣️ *Total de KM:* {rota_info['km_total']} km\n"
            f"📈 *Lucro estimado:* R${rota_info['lucro']:.2f}\n\n"
        )
    
    mensagem += "═════════════════════════\n"
    mensagem += "Agora é só escolher a rota que mais te interessa e entrar em contato direto com as empresas para fechar negócio"
    return mensagem


import time

import requests

_BLUELYTICS_URL = "https://api.bluelytics.com.ar/v2/latest"
_CACHE_TTL_SECONDS = 600

_cache = {"rate": None, "updated_at": None, "fetched_at": 0}


def get_usd_ars_blue_rate():
    """
    Cotacao do dolar blue (compra) em pesos argentinos, via Bluelytics
    (api.bluelytics.com.ar) - API publica feita pra consumo programatico,
    sem bloqueio de bot. finanzasargy.com foi a fonte pedida originalmente,
    mas bloqueia requisicao vinda de servidor (Cloudflare devolve 403 pro
    IP de datacenter do Render, mesmo com User-Agent de navegador -
    funciona normal num navegador de verdade, so nao server-to-server,
    confirmado ao vivo em producao). Bluelytics cobre o mesmo conceito
    (dolar blue Argentina) com uma API estavel e sem essa restricao.
    "value_buy" e o lado certo pra dinheiro recebido: e o que um hostel
    receberia em pesos se trocasse os dolares, nao "value_sell" (preco
    pra quem QUER COMPRAR dolares).

    Cache de 10 minutos em memoria (processo do servidor) - nao bate na
    API a cada abertura do modal de cambio, e nao derruba a tela se a
    API cair: mantem o ultimo valor bom conhecido nesse caso.
    """
    now = time.time()
    if _cache["rate"] is not None and (now - _cache["fetched_at"]) < _CACHE_TTL_SECONDS:
        return {"rate": _cache["rate"], "updated_at": _cache["updated_at"], "source": "bluelytics.com.ar"}

    try:
        resp = requests.get(_BLUELYTICS_URL, timeout=6)
        resp.raise_for_status()
        data = resp.json()

        rate = float(data["blue"]["value_buy"])
        updated_at = data.get("last_update")

        _cache["rate"] = rate
        _cache["updated_at"] = updated_at
        _cache["fetched_at"] = now

        return {"rate": rate, "updated_at": updated_at, "source": "bluelytics.com.ar"}
    except Exception:
        # API fora do ar ou mudou de formato - devolve o ultimo valor bom
        # conhecido (mesmo vencido) em vez de quebrar a tela. Sem nenhum
        # valor em cache ainda, devolve rate=None e quem chamou trata.
        if _cache["rate"] is not None:
            return {"rate": _cache["rate"], "updated_at": _cache["updated_at"], "source": "bluelytics.com.ar"}
        return {"rate": None, "updated_at": None, "source": "bluelytics.com.ar"}

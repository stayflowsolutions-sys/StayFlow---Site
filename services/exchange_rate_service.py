import time

import requests

_BLUELYTICS_URL = "https://api.bluelytics.com.ar/v2/latest"
_OPEN_ER_API_URL = "https://open.er-api.com/v6/latest/{base}"
_CACHE_TTL_SECONDS = 600

_blue_cache = {"rate": None, "updated_at": None, "fetched_at": 0}
_official_cache = {}


def _get_usd_ars_blue_rate():
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

    Cache de 10 minutos em memoria (processo do servidor).
    """
    now = time.time()
    if _blue_cache["rate"] is not None and (now - _blue_cache["fetched_at"]) < _CACHE_TTL_SECONDS:
        return {"rate": _blue_cache["rate"], "updated_at": _blue_cache["updated_at"]}

    try:
        resp = requests.get(_BLUELYTICS_URL, timeout=6)
        resp.raise_for_status()
        data = resp.json()

        rate = float(data["blue"]["value_buy"])
        updated_at = data.get("last_update")

        _blue_cache["rate"] = rate
        _blue_cache["updated_at"] = updated_at
        _blue_cache["fetched_at"] = now

        return {"rate": rate, "updated_at": updated_at}
    except Exception:
        # API fora do ar ou mudou de formato - devolve o ultimo valor bom
        # conhecido (mesmo vencido) em vez de quebrar a tela. Sem nenhum
        # valor em cache ainda, devolve rate=None e quem chamou trata.
        if _blue_cache["rate"] is not None:
            return {"rate": _blue_cache["rate"], "updated_at": _blue_cache["updated_at"]}
        return {"rate": None, "updated_at": None}


def _get_official_rates(base_currency):
    """
    Taxas oficiais de todas as moedas a partir de uma moeda base, via
    open.er-api.com (gratis, sem chave, sem limite de uso agressivo -
    cobre USD/ARS/CLP/BRL/PEN/BOB/COP, as moedas cadastradas no seletor
    de cambio). Cache de 10 minutos por moeda base.
    """
    now = time.time()
    cached = _official_cache.get(base_currency)
    if cached and (now - cached["fetched_at"]) < _CACHE_TTL_SECONDS:
        return cached["rates"]

    try:
        resp = requests.get(_OPEN_ER_API_URL.format(base=base_currency), timeout=6)
        resp.raise_for_status()
        data = resp.json()
        if data.get("result") != "success":
            raise ValueError("open.er-api.com nao retornou result=success")

        rates = data.get("rates") or {}
        _official_cache[base_currency] = {"rates": rates, "fetched_at": now}
        return rates
    except Exception:
        if cached:
            return cached["rates"]
        return {}


def get_reference_rate(foreign_currency, home_currency):
    """
    Cotacao de referencia pra ajudar a preencher o cambio manual, pra
    qualquer par moeda-recebida -> moeda do hostel (as 7 moedas
    cadastradas no seletor: USD/ARS/CLP/BRL/PEN/BOB/COP).

    Caso especial: quando a moeda do hostel e ARS, ancoramos no dolar
    "blue" (Bluelytics) em vez da taxa oficial - e a cotacao que hostels
    na Argentina realmente usam no dia a dia, historicamente bem
    diferente da oficial. Pra moeda recebida = USD, e o proprio valor do
    blue. Pra qualquer outra moeda recebida, cruzamos:
    <moeda> -> USD (taxa oficial, open.er-api.com) x USD -> ARS (blue),
    o que aproxima bem o valor realista em pesos.

    Fora desse caso (moeda do hostel != ARS), usa taxa oficial direta via
    open.er-api.com. Limitacao conhecida: a Bolivia tambem passou a ter
    uma distorcao relevante entre cambio oficial e paralelo desde 2023,
    mas nao ha fonte publica/gratuita confiavel equivalente ao Bluelytics
    pra isso hoje - fica documentado, nao resolvido (mesmo tipo de
    decisao ja tomada pro finanzasargy.com/Bluelytics).
    """
    foreign_currency = (foreign_currency or "").upper()
    home_currency = (home_currency or "").upper()

    if not foreign_currency or foreign_currency == home_currency:
        return {"rate": None, "updated_at": None, "source": None}

    if home_currency == "ARS":
        blue = _get_usd_ars_blue_rate()
        if blue["rate"] is None:
            return {"rate": None, "updated_at": None, "source": "bluelytics.com.ar"}

        if foreign_currency == "USD":
            return {"rate": blue["rate"], "updated_at": blue["updated_at"], "source": "bluelytics.com.ar"}

        rates = _get_official_rates(foreign_currency)
        usd_per_foreign = rates.get("USD")
        if not usd_per_foreign:
            return {"rate": None, "updated_at": None, "source": "bluelytics.com.ar + open.er-api.com"}

        cross_rate = usd_per_foreign * blue["rate"]
        return {"rate": cross_rate, "updated_at": blue["updated_at"], "source": "bluelytics.com.ar + open.er-api.com"}

    rates = _get_official_rates(foreign_currency)
    rate = rates.get(home_currency)
    if not rate:
        return {"rate": None, "updated_at": None, "source": "open.er-api.com"}

    return {"rate": rate, "updated_at": None, "source": "open.er-api.com"}

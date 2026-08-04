import re
import html
import time

import requests

_FINANZASARGY_URL = "https://finanzasargy.com/cotizaciones-mercado-blue"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
_CACHE_TTL_SECONDS = 600

_cache = {"rate": None, "updated_at": None, "fetched_at": 0}


def get_usd_ars_blue_rate():
    """
    Cotacao do dolar blue (compra) em pesos argentinos, extraida do
    finanzasargy.com - usada como referencia no registro de cambio do
    Financeiro (pagamento em dinheiro em moeda estrangeira). "Compra" e
    o lado certo pra esse caso: e o valor que um hostel recebendo
    dolares em maos efetivamente teria em pesos se trocasse, nao o
    "venda" (que e o preco pra quem QUER COMPRAR dolares).

    Cache de 10 minutos em memoria (processo do servidor) - nao bate no
    site externo a cada abertura do modal de cambio, e nao derruba a
    tela se o site cair: mantem o ultimo valor bom conhecido nesse caso.
    """
    now = time.time()
    if _cache["rate"] is not None and (now - _cache["fetched_at"]) < _CACHE_TTL_SECONDS:
        return {"rate": _cache["rate"], "updated_at": _cache["updated_at"], "source": "finanzasargy.com"}

    try:
        resp = requests.get(_FINANZASARGY_URL, headers={"User-Agent": _USER_AGENT}, timeout=6)
        resp.raise_for_status()
        # O site nao manda charset no Content-Type, entao o requests
        # chuta ISO-8859-1 (fallback padrao de HTTP) e corrompe todo
        # acento de "resp.text" - forcar UTF-8 e obrigatorio aqui, senao
        # "Dólar Blue" nunca da match.
        resp.encoding = "utf-8"
        text = html.unescape(resp.text)

        obj_match = re.search(r'\{"titulo":\[0,"Dólar Blue"\],(.*?)\}', text)
        if not obj_match:
            raise ValueError("Padrao de cotacao 'Dolar Blue' nao encontrado na pagina.")

        obj_body = obj_match.group(1)
        compra_match = re.search(r'"compra":\[0,"([\d.]+)"\]', obj_body)
        updated_match = re.search(r'"updatedAt":\[0,"([^"]+)"\]', obj_body)
        if not compra_match:
            raise ValueError("Campo 'compra' nao encontrado no bloco de cotacao.")

        rate = float(compra_match.group(1))
        updated_at = updated_match.group(1) if updated_match else None

        _cache["rate"] = rate
        _cache["updated_at"] = updated_at
        _cache["fetched_at"] = now

        return {"rate": rate, "updated_at": updated_at, "source": "finanzasargy.com"}
    except Exception:
        # Site fora do ar ou mudou de layout - devolve o ultimo valor bom
        # conhecido (mesmo vencido) em vez de quebrar a tela. Sem nenhum
        # valor em cache ainda, devolve rate=None e quem chamou trata.
        if _cache["rate"] is not None:
            return {"rate": _cache["rate"], "updated_at": _cache["updated_at"], "source": "finanzasargy.com"}
        return {"rate": None, "updated_at": None, "source": "finanzasargy.com"}

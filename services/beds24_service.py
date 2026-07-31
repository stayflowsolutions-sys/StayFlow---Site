"""
Integração com a API v2 do Beds24 (channel manager) — conta master de
agência do StayFlow. Cada cliente StayFlow é uma sub-propriedade dentro
dessa UMA conta (modelo white-label: o cliente nunca vê a marca Beds24
nem paga separado, ver docs/STAYFLOW_MASTER_CONTEXT.md).

Autenticação da API v2: um invite code (gerado uma vez, manualmente, no
painel do Beds24) é trocado por um refresh token (dura 30 dias, renova
a cada uso) + um access token (dura 24h). Esse arquivo guarda o refresh
token criptografado (ver _encrypt/_decrypt) e renova o access token sob
demanda — sem scheduler/cron, porque o projeto não tem nenhum hoje.

Nota de manutenção: os nomes exatos de alguns campos do corpo das
requisições (ex: POST /properties, POST /inventory/rooms/calendar) vêm
da documentação pública do Beds24, mas não foram confirmados contra uma
resposta real da API ainda — foram marcados com "confirmar contra API
real" abaixo. Ajustar assim que testarmos com a conta master de verdade.
"""

import os
import datetime
import requests
from cryptography.fernet import Fernet

import database

API_BASE = "https://api.beds24.com/v2"
REQUEST_TIMEOUT = 15


def _get_fernet():
    key = os.getenv("BEDS24_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError(
            "BEDS24_ENCRYPTION_KEY nao configurada - necessaria pra guardar/ler "
            "a credencial mestra do Beds24 (gere uma com Fernet.generate_key())."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def _encrypt(value):
    return _get_fernet().encrypt(value.encode()).decode()


def _decrypt(value):
    return _get_fernet().decrypt(value.encode()).decode()


def setup_master_account(invite_code):
    """
    Troca o invite code (gerado manualmente uma vez no painel do Beds24)
    por um refresh token, e guarda criptografado. Só precisa ser chamado
    uma vez, na configuração inicial da conta master.

    Retorna (sucesso, mensagem_de_erro_ou_None).
    """
    try:
        response = requests.get(
            f"{API_BASE}/authentication/setup",
            headers={"code": invite_code},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code >= 400:
            print("Erro ao configurar conta master do Beds24:", response.status_code, response.text)
            return False, f"Beds24 recusou o invite code (HTTP {response.status_code})."

        data = response.json()
        refresh_token = data.get("refreshToken")
        access_token = data.get("token")
        expires_in = data.get("expiresIn", 0)

        if not refresh_token:
            print("Resposta do Beds24 sem refreshToken:", data)
            return False, "Resposta do Beds24 nao trouxe refreshToken."

        database.save_beds24_refresh_token(_encrypt(refresh_token))
        if access_token:
            expires_at = (datetime.datetime.utcnow() + datetime.timedelta(seconds=int(expires_in or 0))).isoformat()
            database.update_beds24_access_token(_encrypt(access_token), expires_at)

        return True, None
    except Exception as error:
        print("Erro de conexao ao configurar conta master do Beds24:", error)
        return False, "Erro de conexao com o Beds24."


def _get_valid_access_token():
    """
    Devolve um access token valido, renovando via refresh token se o
    cache estiver expirado (ou perto disso) - chamado antes de toda
    chamada de saida a API do Beds24, em vez de um job agendado.
    """
    creds = database.get_beds24_master_credentials()
    if not creds or not creds.get("refresh_token_encrypted"):
        return None

    expires_at_raw = creds.get("access_token_expires_at")
    if creds.get("access_token_encrypted") and expires_at_raw:
        try:
            expires_at = datetime.datetime.fromisoformat(expires_at_raw)
            if expires_at - datetime.timedelta(minutes=5) > datetime.datetime.utcnow():
                return _decrypt(creds["access_token_encrypted"])
        except ValueError:
            pass

    refresh_token = _decrypt(creds["refresh_token_encrypted"])
    try:
        response = requests.get(
            f"{API_BASE}/authentication/token",
            headers={"refreshToken": refresh_token},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code >= 400:
            print("Erro ao renovar access token do Beds24:", response.status_code, response.text)
            return None

        data = response.json()
        access_token = data.get("token")
        expires_in = data.get("expiresIn", 0)
        if not access_token:
            print("Resposta do Beds24 sem token ao renovar:", data)
            return None

        expires_at = (datetime.datetime.utcnow() + datetime.timedelta(seconds=int(expires_in or 0))).isoformat()
        database.update_beds24_access_token(_encrypt(access_token), expires_at)
        return access_token
    except Exception as error:
        print("Erro de conexao ao renovar access token do Beds24:", error)
        return None


def is_master_account_configured():
    creds = database.get_beds24_master_credentials()
    return bool(creds and creds.get("refresh_token_encrypted"))


def create_property(hostel_name, currency="USD", property_type="hotel"):
    """
    Cria uma sub-propriedade nova pra um cliente StayFlow dentro da
    conta master (modelo agencia). Retorna (property_id, erro) - so um
    dos dois vem preenchido.

    Confirmar contra API real: nomes exatos de campos aceitos por
    POST /properties alem de name/propertyType/currency.
    """
    access_token = _get_valid_access_token()
    if not access_token:
        return None, "Conta master do Beds24 nao configurada ou token invalido."

    try:
        response = requests.post(
            f"{API_BASE}/properties",
            headers={"token": access_token, "Content-Type": "application/json"},
            json=[{"name": hostel_name, "propertyType": property_type, "currency": currency}],
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code >= 400:
            print("Erro ao criar propriedade no Beds24:", response.status_code, response.text)
            return None, f"Beds24 recusou a criacao da propriedade (HTTP {response.status_code})."

        data = response.json()
        print("Resposta do Beds24 ao criar propriedade:", data)

        # A API do Beds24 responde em lote (array), inclusive pra uma
        # unica propriedade - e alguns endpoints em lote embrulham o
        # objeto criado dentro de uma chave "new". Trata os formatos
        # possiveis em vez de assumir um so, ja que a documentacao
        # publica nao deixa isso 100% claro.
        item = data[0] if isinstance(data, list) and data else data
        if isinstance(item, dict) and isinstance(item.get("new"), dict):
            item = item["new"]

        property_id = item.get("id") or item.get("propertyId") if isinstance(item, dict) else None
        if not property_id:
            print("Resposta do Beds24 sem id de propriedade:", data)
            return None, "Resposta do Beds24 nao trouxe o id da propriedade criada."

        return str(property_id), None
    except Exception as error:
        print("Erro de conexao ao criar propriedade no Beds24:", error)
        return None, "Erro de conexao com o Beds24."


def create_room_type(property_id, room_name):
    """
    Cria um novo tipo de quarto (roomType) dentro de uma sub-propriedade
    ja existente no Beds24 - usado quando o hostel ainda nao tem nenhum
    quarto cadastrado la, pra ele nunca precisar abrir o painel do
    Beds24 manualmente. Retorna (beds24_room_id, erro).
    """
    access_token = _get_valid_access_token()
    if not access_token:
        return None, "Conta master do Beds24 nao configurada ou token invalido."

    try:
        response = requests.post(
            f"{API_BASE}/properties",
            headers={"token": access_token, "Content-Type": "application/json"},
            json=[{"id": int(property_id), "roomTypes": [{"name": room_name}]}],
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code >= 400:
            print("Erro ao criar quarto no Beds24:", response.status_code, response.text)
            return None, f"Beds24 recusou a criacao do quarto (HTTP {response.status_code})."

        data = response.json()
        print("Resposta do Beds24 ao criar quarto:", data)

        item = data[0] if isinstance(data, list) and data else data
        if isinstance(item, dict) and isinstance(item.get("new"), dict):
            item = item["new"]

        room_types = item.get("roomTypes") if isinstance(item, dict) else None
        if not isinstance(room_types, list) or not room_types:
            print("Resposta do Beds24 sem roomTypes criado:", data)
            return None, "Resposta do Beds24 nao trouxe o quarto criado."

        new_room = room_types[-1]
        room_id = new_room.get("id") if isinstance(new_room, dict) else None
        if not room_id:
            print("Resposta do Beds24 sem id do quarto criado:", data)
            return None, "Resposta do Beds24 nao trouxe o id do quarto criado."

        return str(room_id), None
    except Exception as error:
        print("Erro de conexao ao criar quarto no Beds24:", error)
        return None, "Erro de conexao com o Beds24."


def get_property_rooms(property_id):
    """
    Lista os tipos de quarto (roomTypes) ja cadastrados na sub-
    propriedade do hostel no Beds24 - usado pra montar o seletor de
    mapeamento (modalidade StayFlow <-> quarto Beds24). Retorna
    (lista_de_quartos, erro) - lista vem como [{"id":..., "name":...}].
    """
    access_token = _get_valid_access_token()
    if not access_token:
        return None, "Conta master do Beds24 nao configurada ou token invalido."

    try:
        response = requests.get(
            f"{API_BASE}/properties",
            headers={"token": access_token},
            params={"propertyId": property_id, "includeAllRooms": "true"},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code >= 400:
            print("Erro ao listar quartos da propriedade no Beds24:", response.status_code, response.text)
            return None, f"Beds24 recusou a listagem de quartos (HTTP {response.status_code})."

        data = response.json()
        print("Resposta do Beds24 ao listar quartos (propertyId=%s):" % property_id, data)

        # Formato real confirmado via rota de diagnostico (debug-raw):
        # {"count":1, "data":[{...propriedade..., "roomTypes":[...]}], "success":true, ...}
        # - o "roomTypes" fica dentro do primeiro item de "data", que por
        # sua vez fica dentro do dict de resposta. Nenhuma das tentativas
        # anteriores (lista direta, dict com roomTypes no topo) cobria
        # esse formato - mantidas como fallback, sem custo, caso a Beds24
        # varie o formato dependendo do parametro/conta.
        room_types = None
        if isinstance(data, dict) and isinstance(data.get("data"), list) and data["data"] \
                and isinstance(data["data"][0], dict) and isinstance(data["data"][0].get("roomTypes"), list):
            room_types = data["data"][0]["roomTypes"]
        elif isinstance(data, list) and data and isinstance(data[0], dict) and isinstance(data[0].get("roomTypes"), list):
            room_types = data[0]["roomTypes"]
        elif isinstance(data, dict) and isinstance(data.get("roomTypes"), list):
            room_types = data["roomTypes"]
        elif isinstance(data, list):
            room_types = data

        if not isinstance(room_types, list):
            print("Resposta do Beds24 sem roomTypes:", data)
            return [], None

        rooms = [
            {"id": str(rt.get("id")), "name": rt.get("name") or f"Quarto {rt.get('id')}"}
            for rt in room_types if isinstance(rt, dict) and rt.get("id")
        ]
        print("Quartos parseados:", rooms)
        return rooms, None
    except Exception as error:
        print("Erro de conexao ao listar quartos no Beds24:", error)
        return None, "Erro de conexao com o Beds24."


def delete_room_type(property_id, beds24_room_id):
    """
    Apaga um tipo de quarto (roomType) da sub-propriedade no Beds24 -
    usado pra limpar quarto duplicado/sem uso direto do StayFlow, sem
    precisar abrir o painel do Beds24.

    ATENCAO - formato nao confirmado contra API real ainda: a
    documentacao publica so confirma que a funcionalidade existe
    ("delete rooms of properties by id, com propertyId e roomId"), sem
    detalhar o metodo HTTP exato. Implementado com a melhor suposicao
    (DELETE /properties/rooms com propertyId+roomId de query) - a
    primeira chamada real precisa ser conferida com log antes de confiar
    nesse caminho pra valer (ver rota que usa essa funcao).

    Retorna (sucesso: bool, erro: str|None).
    """
    access_token = _get_valid_access_token()
    if not access_token:
        return False, "Conta master do Beds24 nao configurada ou token invalido."

    try:
        response = requests.delete(
            f"{API_BASE}/properties/rooms",
            headers={"token": access_token},
            params={"propertyId": property_id, "roomId": beds24_room_id},
            timeout=REQUEST_TIMEOUT,
        )
        print(
            "Resposta do Beds24 ao apagar quarto (propertyId=%s, roomId=%s):" % (property_id, beds24_room_id),
            response.status_code, response.text,
        )
        if response.status_code >= 400:
            detail = (response.text or "")[:200]
            return False, f"Beds24 recusou apagar o quarto (HTTP {response.status_code}): {detail}"
        return True, None
    except Exception as error:
        print("Erro de conexao ao apagar quarto no Beds24:", error)
        return False, "Erro de conexao com o Beds24."


def push_availability(beds24_room_id, checkin_date, checkout_date, num_avail):
    """
    Atualiza a disponibilidade de um quarto no Beds24 pro intervalo de
    datas dado - chamado toda vez que uma reserva StayFlow (manual ou
    via WhatsApp) e criada/cancelada, pra refletir no calendario que a
    Booking/Airbnb/Hostelworld enxergam. Nunca chamado pra reserva que
    veio DO Beds24 (evitaria eco).

    Confirmar contra API real: nome exato do campo de disponibilidade
    (usado aqui "numAvail" por analogia com os campos de preco/minStay
    documentados) dentro de POST /inventory/rooms/calendar.

    Retorna True/False - nunca levanta excecao (mesmo padrao de
    services/whatsapp_service.py: uma falha de sincronizacao nao pode
    derrubar a criacao da reserva no StayFlow).
    """
    access_token = _get_valid_access_token()
    if not access_token:
        print("Push de disponibilidade pro Beds24 ignorado - conta master nao configurada.")
        return False

    try:
        response = requests.post(
            f"{API_BASE}/inventory/rooms/calendar",
            headers={"token": access_token, "Content-Type": "application/json"},
            json=[{
                "roomId": beds24_room_id,
                "calendar": [{"from": checkin_date, "to": checkout_date, "numAvail": num_avail}],
            }],
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code >= 400:
            print("Erro ao empurrar disponibilidade pro Beds24:", response.status_code, response.text)
            return False
        return True
    except Exception as error:
        print("Erro de conexao ao empurrar disponibilidade pro Beds24:", error)
        return False

"""
Utilitário central de multi-tenancy da StayFlow.

Regra de ouro: o hostel_id de uma requisição NUNCA vem do cliente
(nem de query params, nem de JSON body, nem de header). Ele sempre
vem da sessão de servidor, criada no login (routes/auth.py) e
validada aqui.

Isso garante que um usuário autenticado do Hostel A não consiga,
mudando um parâmetro na requisição, ler ou escrever dados do
Hostel B.
"""

from functools import wraps
from flask import session, jsonify, g


def _current_session_data():
    """
    Busca a sessao atual no banco a partir do token opaco guardado no
    cookie assinado do Flask (session["session_id"]). Cacheia em
    flask.g pra nao consultar o banco mais de uma vez por requisicao.
    Retorna None se nao houver cookie de sessao, ou se a sessao nao
    existir/estiver revogada no banco.
    """
    if hasattr(g, "_stayflow_session_data"):
        return g._stayflow_session_data

    from database import get_valid_session

    session_id = session.get("session_id")
    data = get_valid_session(session_id) if session_id else None

    g._stayflow_session_data = data
    return data


def get_current_hostel_id():
    """
    Retorna o hostel_id da sessao atual, ou None se nao houver sessao
    valida OU se o hostel ainda nao foi escolhido (sessao "pending"
    apos login multi-hostel, antes de /select-hostel).
    """
    data = _current_session_data()
    return data["hostel_id"] if data else None


def get_current_user_id():
    """Retorna o user_id da sessao atual, ou None se nao houver sessao valida."""
    data = _current_session_data()
    return data["user_id"] if data else None


def get_current_session_id():
    """Retorna o token opaco (id) da sessao atual, direto do cookie - usado
    pra revogar/listar a sessao certa (ex: trocar senha, ver sessoes ativas)."""
    return session.get("session_id")


def get_current_user():
    """
    Retorna um dict com os dados da pessoa logada e do hostel atual,
    ou None se nao houver sessao. Sempre busca fresco do banco (nunca
    confia em valor cacheado na sessao) - mesma logica de seguranca
    usada por require_permission.
    """
    user_id = get_current_user_id()
    hostel_id = get_current_hostel_id()

    if not user_id or not hostel_id:
        return None

    from database import get_user_by_id, get_membership

    user = get_user_by_id(user_id)
    membership = get_membership(user_id, hostel_id)

    if not user or not membership:
        return None

    return {
        "id": user["id"],
        "hostel_id": hostel_id,
        "role": membership["role_name"],
        "name": user["name"],
        "email": user["email"],
    }


def require_auth(view_func):
    """
    Decorator para proteger rotas que precisam de um usuário logado.

    Injeta hostel_id como primeiro argumento da view, assim a view
    nunca precisa (nem pode) decidir de qual hostel são os dados.

    Uso:
        @dashboard_bp.route("/dashboard", methods=["GET"])
        @require_auth
        def dashboard(hostel_id):
            ...
    """

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        hostel_id = get_current_hostel_id()

        if not hostel_id:
            return jsonify({
                "success": False,
                "message": "Not authenticated."
            }), 401

        return view_func(hostel_id, *args, **kwargs)

    return wrapper


def require_permission(permission_key):
    """
    Decorator para proteger rotas que exigem uma permissao especifica,
    nao so estar logado. Calcula a permissao efetiva em tempo real
    (role + excecoes individuais) a cada requisicao - nunca confia em
    valor guardado na sessao, porque uma mudanca de permissao feita
    pelo admin precisa valer imediatamente, sem esperar novo login.

    Uso:
        @dashboard_bp.route("/finance", methods=["GET"])
        @require_permission("finance")
        def finance(hostel_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            hostel_id = get_current_hostel_id()
            user_id = get_current_user_id()

            if not hostel_id or not user_id:
                return jsonify({
                    "success": False,
                    "message": "Not authenticated."
                }), 401

            from database import get_effective_permissions
            permissions = get_effective_permissions(user_id, hostel_id)

            if permission_key not in permissions:
                return jsonify({
                    "success": False,
                    "message": "Voce nao tem permissao para acessar este recurso."
                }), 403

            return view_func(hostel_id, *args, **kwargs)

        return wrapper
    return decorator
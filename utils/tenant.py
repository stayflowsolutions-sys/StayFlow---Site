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
from flask import session, jsonify


def get_current_hostel_id():
    """Retorna o hostel_id do usuário logado, ou None se não houver sessão."""
    return session.get("hostel_id")


def get_current_user():
    """Retorna um dict com os dados básicos do usuário logado, ou None."""
    if "user_id" not in session:
        return None

    return {
        "id": session.get("user_id"),
        "hostel_id": session.get("hostel_id"),
        "role": session.get("role"),
        "name": session.get("user_name"),
        "email": session.get("user_email"),
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
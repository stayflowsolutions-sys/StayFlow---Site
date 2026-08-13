"""
Utilitário central de multi-tenancy da StayFlow.

Exceção deliberada à regra de ouro abaixo: require_stayflow_admin (mais
adiante neste arquivo) protege rotas administrativas cross-tenant (ex:
marcar uma hospedagem como conta cortesia/piloto de billing) - nessas
rotas, e SÓ nessas, o hostel_id alvo vem do corpo da requisição de
propósito, porque quem está chamando não é necessariamente membro
daquele hostel. A proteção real ali é o allowlist de e-mail admin, não
a sessão do hostel.

Segunda exceção deliberada: sessões "em visita" (impersonation, ver
is_impersonating abaixo) - quando um admin StayFlow entra no dashboard
de uma conta via POST /stayflow-admin/impersonate, o hostel_id da
PRÓPRIA sessão dele é reapontado pra conta visitada (nenhuma linha de
hostel_memberships é criada em lugar nenhum). Como a checagem de
permissão normal (get_effective_permissions) depende de existir essa
membership, uma sessão em visita não passaria por ela - por isso
require_permission/require_plan_feature/get_current_user checam
is_impersonating() primeiro e liberam acesso equivalente a um Admin
quando true. A proteção real continua sendo o allowlist de e-mail
checado no momento de ENTRAR em visita (require_stayflow_admin, na
rota /impersonate) - depois disso a sessão em si já carrega essa
autorização.

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

from utils.permissions import ALL_PERMISSIONS


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


def is_impersonating():
    """True se a sessao atual esta "em visita" (admin StayFlow dentro do dashboard de outra conta) - ver nota no topo do arquivo."""
    data = _current_session_data()
    return bool(data and data.get("impersonating_from_hostel_id"))


def get_impersonation_origin_hostel_id():
    """hostel_id ORIGINAL guardado pra sessao em visita, ou None se a sessao nao esta visitando nada."""
    data = _current_session_data()
    return data.get("impersonating_from_hostel_id") if data else None


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
    if not user:
        return None

    if is_impersonating():
        return {
            "id": user["id"],
            "hostel_id": hostel_id,
            "role": "Visitante StayFlow",
            "name": user["name"],
            "email": user["email"],
        }

    membership = get_membership(user_id, hostel_id)
    if not membership:
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

            if is_impersonating():
                permissions = ALL_PERMISSIONS
            else:
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


def is_stayflow_admin_email(email):
    """
    Checa um e-mail contra a allowlist STAYFLOW_ADMIN_EMAILS (variavel
    de ambiente, lista separada por virgula - bootstrap/fallback, sempre
    funciona mesmo se o banco tiver problema) OU contra a tabela
    stayflow_team (equipe adicionada pela propria StayFlow via Meu
    painel > Equipe, ver database.py add_stayflow_team_member). Usado
    tanto pelo decorator require_stayflow_admin quanto por
    build_session_payload (pra decidir se mostra o link do painel
    interno no frontend). Nao existe conceito de "super-admin" no banco
    hoje - todo mundo aqui tem acesso total ao painel interno.
    """
    import os

    if not email:
        return False

    admin_emails = {
        e.strip().lower()
        for e in os.getenv("STAYFLOW_ADMIN_EMAILS", "").split(",")
        if e.strip()
    }
    if email.lower() in admin_emails:
        return True

    from database import is_email_in_stayflow_team
    return is_email_in_stayflow_team(email)


def require_stayflow_admin(view_func):
    """
    Protege rotas administrativas cross-tenant (hoje: marcar plano/
    add-on de billing de qualquer hospedagem, ex: liberar um piloto de
    graca; ler o painel interno com todas as hospedagens) - NAO injeta
    hostel_id (a rota le do corpo da requisicao, ver nota no topo do
    arquivo). So exige sessao valida + e-mail na allowlist (ver
    is_stayflow_admin_email).
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"success": False, "message": "Not authenticated."}), 401

        from database import get_user_by_id

        user = get_user_by_id(user_id)
        if not user or not is_stayflow_admin_email(user["email"]):
            return jsonify({"success": False, "message": "Acesso restrito."}), 403

        return view_func(*args, **kwargs)

    return wrapper


def require_plan_feature(feature_key):
    """
    Segunda camada de trava, sobre um recurso vinculado ao plano
    contratado (Eventos, modulos operacionais) - diferente de
    require_permission, que e sobre QUEM na equipe pode acessar algo
    que a hospedagem ja tem direito de usar. Esta aqui e sobre SE a
    hospedagem contratou aquele modulo (plano/add-on).

    Sempre usado JUNTO de require_permission, nesta ordem (o de baixo
    roda primeiro e ja recebe hostel_id injetado pelo de cima):

        @events_bp.route("/events", methods=["GET"])
        @require_permission("events")
        @require_plan_feature("events")
        def list_events(hostel_id):
            ...

    Por isso este decorator NAO busca hostel_id sozinho - recebe como
    primeiro argumento posicional, ja resolvido por require_permission
    (ou require_auth) logo acima dele na pilha.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(hostel_id, *args, **kwargs):
            if is_impersonating():
                return view_func(hostel_id, *args, **kwargs)

            from database import hostel_has_plan_feature

            if not hostel_has_plan_feature(hostel_id, feature_key):
                return jsonify({
                    "success": False,
                    "message": "Este recurso nao esta incluido no seu plano atual."
                }), 403

            return view_func(hostel_id, *args, **kwargs)

        return wrapper
    return decorator
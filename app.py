import os

from flask import Flask, send_from_directory

from database import create_database

from routes.chat import chat_bp
from routes.chats import chats_bp
from routes.guests import guests_bp
from routes.executive import executive_bp
from routes.dashboard import dashboard_bp
from routes.activity import activity_bp
from routes.opportunities import opportunities_bp
from routes.auth import auth_bp
from routes.settings import settings_bp
from routes.reservations import reservations_bp
from routes.finance import finance_bp
from routes.reports import reports_bp
from routes.inventory import inventory_bp
from routes.operations import operations_bp
from routes.revenue import revenue_bp
from routes.whatsapp_webhook import whatsapp_webhook_bp
from routes.beds24_webhook import beds24_webhook_bp
from routes.meta_oauth import meta_oauth_bp
from routes.meta_webhook import meta_webhook_bp
from routes.team import team_bp
from routes.quick_replies import quick_replies_bp
from routes.security import security_bp
from routes.ask import ask_bp
from routes.rooms import rooms_bp

app = Flask(__name__, static_folder=None)

# Necessário para sessões de servidor (login multi-tenant).
# Em produção, defina SECRET_KEY como variável de ambiente real —
# o valor abaixo só serve como fallback para desenvolvimento local.
app.secret_key = os.getenv("SECRET_KEY", "dev-only-change-me")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

create_database()

app.register_blueprint(chat_bp)
app.register_blueprint(chats_bp)
app.register_blueprint(guests_bp)
app.register_blueprint(executive_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(activity_bp)
app.register_blueprint(opportunities_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(reservations_bp)
app.register_blueprint(finance_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(operations_bp)
app.register_blueprint(revenue_bp)
app.register_blueprint(whatsapp_webhook_bp)
app.register_blueprint(beds24_webhook_bp)
app.register_blueprint(meta_oauth_bp)
app.register_blueprint(meta_webhook_bp)
app.register_blueprint(team_bp)
app.register_blueprint(quick_replies_bp)
app.register_blueprint(security_bp)
app.register_blueprint(ask_bp)
app.register_blueprint(rooms_bp)

# Caminho do frontend: por padrão assume que a pasta do site fica ao lado
# da pasta do backend (ex: C:\StayFlow\backend + C:\StayFlow\StayFlow---Site).
# Pode ser sobrescrito com a variável de ambiente STAYFLOW_FRONTEND_DIR,
# útil para deploy (Render, etc.) onde a estrutura de pastas é diferente.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.getenv(
    "STAYFLOW_FRONTEND_DIR",
    os.path.join(BASE_DIR, "..", "StayFlow---Site")
)


@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/app")
def dashboard_page():
    return send_from_directory(FRONTEND_DIR, "dashboard.html")


# Serve qualquer página .html solta na raiz do frontend
# (Login.html, Register.html, inbox.html, reservations.html,
# statistics.html, settings.html, etc.) sem precisar de uma
# rota nova a cada arquivo criado.
@app.route("/<page_name>.html")
def frontend_page(page_name):
    return send_from_directory(FRONTEND_DIR, f"{page_name}.html")


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(
        os.path.join(FRONTEND_DIR, "assets"),
        filename
    )


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(
        os.path.join(FRONTEND_DIR, "static"),
        filename
    )


if __name__ == "__main__":
    # PORT vem do ambiente em serviços como Render; localmente usa 10000.
    port = int(os.getenv("PORT", 10000))

    # threaded=True e essencial aqui: sem isso, o servidor de
    # desenvolvimento do Flask processa UM pedido por vez - enquanto o
    # Ask StayFlow ou a IA de atendimento estao no meio de uma chamada
    # (varias idas e vindas reais pra OpenAI, alguns segundos cada), o
    # site inteiro travava pra qualquer outro pedido (inclusive mandar
    # mensagem manual pro hospede). Achado real em producao, nao so
    # teorico - reproduzido pelo usuario testando o Ask StayFlow.
    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True
    )
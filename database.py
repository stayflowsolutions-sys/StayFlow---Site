import os
import secrets
import sqlite3
import unicodedata
import datetime

from utils.permissions import ALL_PERMISSIONS_STR

DATABASE = os.path.join(os.getenv("STAYFLOW_DATA_DIR", "."), "stayflow.db")


def _normalize_text(text):
    """
    Remove acentos e baixa a caixa - usado pra comparar nomes vindos do
    modelo (que tende a "corrigir" a ortografia, ex: usuario digita
    "pao" mas a tool recebe "pão") contra nomes cadastrados no banco,
    sem depender de LIKE (que e sensivel a acentuacao no SQLite).
    """
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def add_column_if_not_exists(cursor, table_name, column_name, column_definition):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column["name"] for column in cursor.fetchall()]

    if column_name not in columns:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )


def _guests_table_needs_migration(cursor):
    """
    Detecta se a tabela guests ainda não possui a constraint
    composta UNIQUE(hostel_id, phone). Isso cobre tanto o schema
    antigo com UNIQUE(phone) quanto bancos legados sem UNIQUE
    nenhum, onde o multi-tenant nunca foi de fato garantido.
    """
    cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='guests'"
    )
    row = cursor.fetchone()

    if row is None:
        return False

    table_sql = (row["sql"] or "").replace(" ", "").replace("\n", "")
    return "UNIQUE(hostel_id,phone)" not in table_sql


def _migrate_guests_to_composite_unique(cursor):
    """
    Reconstrói a tabela guests trocando UNIQUE(phone) por
    UNIQUE(hostel_id, phone) — telefone único POR hostel,
    não globalmente. Preserva todos os dados existentes.
    """
    cursor.execute("ALTER TABLE guests RENAME TO guests_old")

    cursor.execute("""
    CREATE TABLE guests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        name TEXT,
        phone TEXT,
        email TEXT,
        language TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(hostel_id, phone)
    )
    """)

    # hóspedes antigos sem hostel_id definido caem no hostel 1
    # (o único hostel que existia antes do multi-tenant existir).
    cursor.execute("""
        INSERT INTO guests (id, hostel_id, name, phone, email, language, created_at)
        SELECT id, COALESCE(hostel_id, 1), name, phone, email, language, created_at
        FROM guests_old
    """)

    cursor.execute("DROP TABLE guests_old")


def _settings_table_needs_migration(cursor):
    """
    Detecta se a tabela settings ainda tem as colunas antigas nunca
    usadas de verdade em nenhum lugar do codigo (checkin_time,
    checkout_time, breakfast_time, languages, services, tours) -
    confirmado por busca completa antes de decidir remover. Presenca
    de "tours" (qualquer uma das 6 serviria) indica schema antigo.
    """
    cursor.execute("PRAGMA table_info(settings)")
    columns = [column["name"] for column in cursor.fetchall()]
    return "tours" in columns


def _migrate_settings_table(cursor):
    """
    Reconstroi settings sem as 6 colunas mortas (checkin_time,
    checkout_time, breakfast_time, languages, services, tours) e ja
    com as colunas novas de Empresa/Comunicacao (Sessao 7). checkin/
    checkout sao reaproveitadas como horario padrao de check-in/
    checkout - nao recriar checkin_time/checkout_time. Preserva todos
    os dados das colunas que continuam existindo.
    """
    cursor.execute("ALTER TABLE settings RENAME TO settings_old")

    cursor.execute("""
    CREATE TABLE settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER,
        hostel_name TEXT,
        hostel_type TEXT,
        checkin TEXT,
        checkout TEXT,
        legal_name TEXT,
        tax_id TEXT,
        address TEXT,
        timezone TEXT,
        currency TEXT,
        logo_url TEXT,
        opportunity_generation INTEGER DEFAULT 1,
        alert_channels TEXT,
        quiet_hours_start TEXT,
        quiet_hours_end TEXT
    )
    """)

    cursor.execute("""
        INSERT INTO settings (
            id, hostel_id, hostel_name, hostel_type, checkin, checkout,
            opportunity_generation
        )
        SELECT id, hostel_id, hostel_name, hostel_type, checkin, checkout,
               opportunity_generation
        FROM settings_old
    """)

    cursor.execute("DROP TABLE settings_old")


def _users_table_needs_migration(cursor):
    """
    Detecta se users ainda tem o schema antigo, com hostel_id e role
    na propria tabela (antes do modelo de hostel_memberships).
    """
    cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='users'"
    )
    row = cursor.fetchone()

    if row is None:
        return False

    table_sql = (row["sql"] or "").replace(" ", "").replace("\n", "")
    return "hostel_id" in table_sql


def _migrate_users_to_memberships(cursor):
    """
    Reconstroi users removendo hostel_id/role, migrando cada usuario
    existente para uma role "Admin" (com todas as permissoes) no
    hostel dele, via hostel_memberships. Preserva todos os dados.
    """
    all_permissions = ALL_PERMISSIONS_STR

    cursor.execute("SELECT id, hostel_id, role FROM users")
    existing_users = cursor.fetchall()

    def get_or_create_role(hostel_id, role_name, permissions, cache):
        cache_key = (hostel_id, role_name)
        if cache_key in cache:
            return cache[cache_key]

        cursor.execute(
            "SELECT id FROM roles WHERE hostel_id = ? AND name = ?",
            (hostel_id, role_name)
        )
        existing_role = cursor.fetchone()

        if existing_role:
            cache[cache_key] = existing_role["id"]
        else:
            cursor.execute(
                "INSERT INTO roles (hostel_id, name, permissions) VALUES (?, ?, ?)",
                (hostel_id, role_name, permissions)
            )
            cache[cache_key] = cursor.lastrowid

        return cache[cache_key]

    role_cache = {}

    for user in existing_users:
        hostel_id = user["hostel_id"]
        old_role = (user["role"] or "").strip().lower()

        if old_role == "admin":
            role_id = get_or_create_role(hostel_id, "Admin", all_permissions, role_cache)
        else:
            # Qualquer role que nao seja "admin" vira uma role "Staff"
            # SEM permissoes por padrao — o admin do hostel decide
            # explicitamente o que cada funcionario pode ver depois.
            role_id = get_or_create_role(hostel_id, "Staff", "", role_cache)

        cursor.execute(
            """
            INSERT OR IGNORE INTO hostel_memberships (user_id, hostel_id, role_id, active)
            VALUES (?, ?, ?, 1)
            """,
            (user["id"], hostel_id, role_id)
        )

    cursor.execute("ALTER TABLE users RENAME TO users_old")

    cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        password TEXT,
        must_change_password INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
        INSERT INTO users (id, name, email, password, must_change_password, created_at)
        SELECT id, name, email, password, must_change_password, created_at
        FROM users_old
    """)

    cursor.execute("DROP TABLE users_old")


# Chaves que existiam em ALL_PERMISSIONS antes de "security"/"billing"
# serem adicionadas (Sessao 7). Fixo aqui de propósito - não importar
# de utils.permissions.ALL_PERMISSIONS, que já inclui as novas chaves
# e não serviria pra detectar quem era "acesso total" no esquema antigo.
_LEGACY_FULL_ACCESS_PERMISSIONS = {
    "dashboard", "chats", "opportunities", "reservations", "operations",
    "guests", "finance", "reports", "inventory", "revenue", "settings", "team",
}


def _backfill_security_billing_for_full_access_roles(cursor):
    """
    Roles criadas antes da Sessao 7 guardam uma string de permissoes
    congelada no momento da criacao - adicionar chaves novas em
    ALL_PERMISSIONS nao as alcança retroativamente (mesmo problema ja
    visto com "team"). Aqui, qualquer role que ja tinha as 12 chaves
    antigas (ou seja, já era "acesso total" no esquema anterior) ganha
    "security" e "billing" tambem, preservando a intencao original de
    quem por ela.
    """
    cursor.execute("SELECT id, permissions FROM roles")
    roles = cursor.fetchall()

    for role in roles:
        current = set(p for p in (role["permissions"] or "").split(",") if p)

        if not _LEGACY_FULL_ACCESS_PERMISSIONS.issubset(current):
            continue

        if "security" in current and "billing" in current:
            continue

        updated = current | {"security", "billing"}
        cursor.execute(
            "UPDATE roles SET permissions = ? WHERE id = ?",
            (",".join(sorted(updated)), role["id"])
        )


def create_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hostels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Credenciais do WhatsApp Business (Meta Cloud API) por hostel —
    # cada hostel tem seu próprio número e token de acesso.
    add_column_if_not_exists(cursor, "hostels", "whatsapp_phone_number_id", "TEXT")
    add_column_if_not_exists(cursor, "hostels", "whatsapp_access_token", "TEXT")

    # ID da sub-propriedade desse hostel dentro da conta master de
    # agência do StayFlow no Beds24 (channel manager) - não é segredo,
    # só um identificador (mesma sensibilidade de whatsapp_phone_number_id
    # acima). NULL = hostel ainda não ativou a integração de canais.
    add_column_if_not_exists(cursor, "hostels", "beds24_property_id", "TEXT")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    add_column_if_not_exists(cursor, "users", "must_change_password", "INTEGER DEFAULT 1")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        permissions TEXT NOT NULL DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(hostel_id, name)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hostel_memberships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        hostel_id INTEGER NOT NULL,
        role_id INTEGER NOT NULL,
        active INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, hostel_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS membership_permission_overrides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        membership_id INTEGER NOT NULL,
        permission_key TEXT NOT NULL,
        allowed INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(membership_id, permission_key)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quick_replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # guests: cria já com o schema correto se for banco novo
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        name TEXT,
        phone TEXT,
        email TEXT,
        language TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(hostel_id, phone)
    )
    """)

    # Quando true, a IA de atendimento para de responder esse hospede
    # especifico (equipe assumiu a conversa manualmente) - mensagem e
    # oportunidade continuam sendo salvas normalmente, so a resposta
    # automatica e que para, igual ja acontece com is_ai_enabled (esse
    # e por hospede, aquele e o interruptor mestre do hostel inteiro).
    add_column_if_not_exists(cursor, "guests", "ai_paused", "INTEGER DEFAULT 0")

    # Data de nascimento, coletada durante o registro do hospede (junto
    # com o documento) - texto livre em formato AAAA-MM-DD.
    add_column_if_not_exists(cursor, "guests", "date_of_birth", "TEXT")

    # Nacionalidade, coletada no mesmo registro pos-reserva (nome legal,
    # data de nascimento, documento, nacionalidade) - texto livre.
    add_column_if_not_exists(cursor, "guests", "nationality", "TEXT")

    # Endereco e dados do documento por escrito (tipo + numero, ex:
    # "Passaporte" / "AB123456") - complementa a FOTO do documento, que
    # ja fica em guest_documents. Tudo texto livre, preenchido manualmente
    # no perfil do hospede (equipe) ou futuramente extraido do envio via
    # WhatsApp.
    add_column_if_not_exists(cursor, "guests", "address", "TEXT")
    add_column_if_not_exists(cursor, "guests", "document_type", "TEXT")
    add_column_if_not_exists(cursor, "guests", "document_number", "TEXT")

    # se for um banco antigo (criado antes do multi-tenant), migra
    if _guests_table_needs_migration(cursor):
        _migrate_guests_to_composite_unique(cursor)

    if _users_table_needs_migration(cursor):
        _migrate_users_to_memberships(cursor)

    _backfill_security_billing_for_full_access_roles(cursor)

    # Documentos de identidade (foto de passaporte/RG) enviados pelo
    # hospede via WhatsApp como imagem - arquivo fica no mesmo disco
    # persistente do banco (STAYFLOW_DATA_DIR/documents/...), essa
    # tabela so guarda a referencia. Um hospede pode mandar mais de
    # um documento/tentativa, por isso e tabela separada, nao coluna
    # unica em guests.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guest_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        guest_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        mime_type TEXT,
        whatsapp_media_id TEXT,
        received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Sessao rastreada no servidor (Sessao 7) - substitui o cookie
    # assinado client-side, que carregava user_id/hostel_id direto.
    # Agora o cookie so guarda um token opaco (id), e cada requisicao
    # busca essa linha pra saber quem e a pessoa e revogar sessoes
    # individualmente sem depender de reautenticacao.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        hostel_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        revoked INTEGER NOT NULL DEFAULT 0,
        user_agent TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS login_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        hostel_id INTEGER,
        email_attempted TEXT,
        success INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Billing (PASSO 8) - so estrutura, sem processador de pagamento
    # integrado. Tela em Configuracoes e honestamente estatica ("modelo
    # de cobranca em definicao"), nao le nem escreve nesta tabela ainda.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS billing (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        plan_name TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Developer (PASSO 9) - so estrutura pra chave de API futura, sem
    # geracao real de chave agora. Tela em Configuracoes e estatica
    # ("em breve"), nao le nem escreve nesta tabela ainda.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        key_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Conta master de agência do StayFlow no Beds24 (channel manager) -
    # singleton, não tem hostel_id porque é UMA conta que vale pra todos
    # os clientes (modelo white-label: cada hostel vira uma sub-
    # propriedade dentro dela, ver hostels.beds24_property_id acima).
    # Tokens ficam criptografados (services/beds24_service.py) porque,
    # diferente do token de WhatsApp de um hostel só, um vazamento aqui
    # expõe a reserva de todos os clientes StayFlow de uma vez.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS beds24_master_account (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        refresh_token_encrypted TEXT,
        access_token_encrypted TEXT,
        access_token_expires_at TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # De-para entre uma modalidade de quarto do StayFlow (room_categories)
    # e o "room" correspondente dentro da propriedade daquele hostel no
    # Beds24 - sem isso, uma reserva vinda de OTA não tem como saber em
    # qual modalidade/quarto ela deveria cair.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS channel_room_mapping (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        room_category_id INTEGER NOT NULL,
        beds24_room_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(hostel_id, room_category_id)
    )
    """)

    # Log/idempotência de cada evento de webhook recebido do Beds24.
    # UNIQUE(beds24_booking_id) + INSERT OR IGNORE evita processar
    # reserva duplicada se o Beds24 reentregar o mesmo webhook (rede
    # lenta, timeout). status='failed' aqui é o que permite detectar
    # falha silenciosa de sincronização em vez de só torcer que funcionou.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS channel_webhook_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        beds24_booking_id TEXT NOT NULL UNIQUE,
        hostel_id INTEGER,
        event_type TEXT,
        payload_json TEXT,
        status TEXT NOT NULL DEFAULT 'processed',
        error_message TEXT,
        reservation_id INTEGER,
        received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Historico de conversa do agente Ask StayFlow (painel do operador
    # logado, nao do hospede) - chave hostel_id+user_id.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ask_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Pedidos de reposicao a fornecedor feitos pelo Ask StayFlow.
    # status: pending_confirmation -> sent -> received (ou cancelled).
    # Existe pra rastrear "o que foi pedido e ainda nao chegou" de forma
    # confiavel, em vez de depender so da memoria da conversa com a IA.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        inventory_item_id INTEGER NOT NULL,
        supplier_id INTEGER,
        quantity INTEGER NOT NULL,
        message TEXT,
        status TEXT NOT NULL DEFAULT 'pending_confirmation',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sent_at TIMESTAMP,
        received_at TIMESTAMP
    )
    """)

    # Rascunho de mensagem proativa (iniciada pela equipe via Ask StayFlow,
    # nao pelo hospede) - mesmo padrao propose->confirm->send do pedido a
    # fornecedor. Ao enviar, a mensagem tambem e gravada na conversa normal
    # do hospede, entao a IA de atendimento ja ve esse aviso quando ele responder.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guest_message_drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        guest_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending_confirmation',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sent_at TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guest_id INTEGER,
        channel TEXT,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        sender TEXT,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER,
        guest_name TEXT,
        phone TEXT,
        interest TEXT,
        status TEXT DEFAULT 'new',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # leads antigos não tinham hostel_id — adiciona a coluna se faltar
    add_column_if_not_exists(cursor, "leads", "hostel_id", "INTEGER")

    # leads criados antes do multi-tenant existir pertencem ao
    # primeiro hostel cadastrado (o único que existia até então)
    cursor.execute("""
        UPDATE leads
        SET hostel_id = (SELECT MIN(id) FROM hostels)
        WHERE hostel_id IS NULL
          AND EXISTS (SELECT 1 FROM hostels)
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS opportunities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guest_id INTEGER,
        type TEXT,
        description TEXT,
        status TEXT DEFAULT 'open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    add_column_if_not_exists(cursor, "opportunities", "score", "INTEGER DEFAULT 0")
    add_column_if_not_exists(cursor, "opportunities", "urgency", "TEXT DEFAULT 'low'")
    add_column_if_not_exists(cursor, "opportunities", "estimated_value", "REAL DEFAULT 0")
    add_column_if_not_exists(cursor, "opportunities", "next_action", "TEXT")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER,
        hostel_name TEXT,
        hostel_type TEXT,
        checkin TEXT,
        checkout TEXT,
        legal_name TEXT,
        tax_id TEXT,
        address TEXT,
        timezone TEXT,
        currency TEXT,
        logo_url TEXT,
        opportunity_generation INTEGER DEFAULT 1,
        alert_channels TEXT,
        quiet_hours_start TEXT,
        quiet_hours_end TEXT
    )
    """)

    add_column_if_not_exists(cursor, "settings", "opportunity_generation", "INTEGER DEFAULT 1")

    # settings antigo (de antes do multi-tenant) não tinha essas colunas —
    # CREATE TABLE IF NOT EXISTS não adiciona coluna em tabela já existente,
    # então precisa migrar manualmente, igual fizemos com guests/leads.
    add_column_if_not_exists(cursor, "settings", "hostel_name", "TEXT")
    add_column_if_not_exists(cursor, "settings", "hostel_type", "TEXT")
    add_column_if_not_exists(cursor, "settings", "checkin", "TEXT")
    add_column_if_not_exists(cursor, "settings", "checkout", "TEXT")

    # settings antigo (Sessao 2) tinha 6 colunas nunca usadas de verdade
    # em nenhum lugar do codigo (checkin_time, checkout_time,
    # breakfast_time, languages, services, tours) - confirmado por busca
    # completa antes de remover. Migra pra reconstruir sem elas e ja
    # adicionar as colunas novas de Empresa/Comunicacao (Sessao 7).
    if _settings_table_needs_migration(cursor):
        _migrate_settings_table(cursor)

    # Interruptor mestre de resposta automatica ao hospede - aditivo,
    # nao precisa da migracao de tabela acima (chamado depois dela de
    # proposito, pra nunca correr risco de ficar de fora de uma copia
    # feita durante a reconstrucao da tabela).
    add_column_if_not_exists(cursor, "settings", "ai_enabled", "INTEGER DEFAULT 1")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        guest_id INTEGER,
        guest_name TEXT,
        room_type TEXT,
        bed TEXT,
        checkin_date TEXT,
        checkout_date TEXT,
        source TEXT DEFAULT 'manual',
        payment_method TEXT,
        amount REAL DEFAULT 0,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Cama fisica atribuida a essa reserva quando o hospede faz check-in
    # de verdade (nao e o mesmo que a data planejada) - fica null ate
    # o check-in acontecer, e permanece apontando pra la depois do
    # check-out (registro historico de qual cama usada).
    add_column_if_not_exists(cursor, "reservations", "bed_id", "INTEGER")

    # Data/hora do check-in e check-out FISICOS de verdade (diferente de
    # bed_id, que so indica qual cama esta reservada/atribuida pro
    # periodo - preenchido automaticamente na criacao pra reservas vindas
    # de canal/WhatsApp, antes de o hospede chegar). null ate a acao
    # acontecer - e o unico jeito confiavel de saber se o check-in ja foi
    # feito, ja que bed_id pode estar preenchido so como reserva futura.
    add_column_if_not_exists(cursor, "reservations", "checked_in_at", "TIMESTAMP")
    add_column_if_not_exists(cursor, "reservations", "checked_out_at", "TIMESTAMP")

    # Estadia de longa duracao / morador fixo (ex: funcionario que mora
    # no hostel, pagando conforme consegue) - 'fixed' (padrao, hospede
    # normal com checkout definido) ou 'indefinite' (sem checkout
    # definido, saldo devedor calculado por dia ocupado x daily_rate,
    # abatido conforme pagamentos registrados em reservation_payments).
    add_column_if_not_exists(cursor, "reservations", "stay_type", "TEXT DEFAULT 'fixed'")
    add_column_if_not_exists(cursor, "reservations", "daily_rate", "REAL")

    # ID da reserva no Beds24 (channel manager), quando essa reserva
    # veio de uma OTA (Booking/Airbnb/Hostelworld) via webhook - usado
    # pra achar/atualizar/cancelar a reserva certa quando o Beds24 avisa
    # de uma alteração. NULL pra reserva manual ou criada via WhatsApp.
    # 'source' já reaproveitado pra guardar o canal real (ex: 'booking',
    # 'airbnb', 'hostelworld') nesses casos, em vez de um genérico
    # 'beds24' - assim o relatório por canal (COALESCE(source,'manual'))
    # já funciona certo sem precisar tocar em routes/reports.py.
    add_column_if_not_exists(cursor, "reservations", "external_booking_id", "TEXT")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservation_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        reservation_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        method TEXT,
        note TEXT,
        paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        name TEXT NOT NULL,
        quantity INTEGER DEFAULT 0,
        min_threshold INTEGER DEFAULT 0,
        reorder_quantity INTEGER DEFAULT 0,
        unit TEXT DEFAULT 'un',
        supplier_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Quantidade que saiu do estoque limpo e esta na lavanderia (suja,
    # ainda nao voltou). "quantity" continua sendo so o que esta limpo
    # e disponivel pra uso - as duas colunas juntas = total do item.
    add_column_if_not_exists(cursor, "inventory_items", "in_laundry_quantity", "INTEGER DEFAULT 0")

    # ===== Mapa de quartos/camas - cada hostel/hotel/resort monta o
    # proprio, com camas normais ou de beliche (bunk_top/bunk_bottom
    # pareadas por bunk_group pra desenhar o mesmo beliche no mapa).
    # Status da cama e gravado de verdade (nao calculado pelas datas
    # da reserva), porque check-in/check-out reais nem sempre batem
    # com o planejado. =====

    # Modalidade de quarto (ex: "Dormitorio Misto 6 camas", "Standard
    # Duplo", "Suite Presidencial") - cada propriedade cria as suas
    # proprias, nao e uma lista fixa. capacity e so informativo (quantas
    # pessoas cabem), usado pra sugerir quantidade de camas ao criar.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS room_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        capacity INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(hostel_id, name)
    )
    """)

    # Preco por noite e descricao (ex: "inclui cafe da manha") - usados
    # pela IA de atendimento pra cotar preco real ao hospede, nunca
    # inventado. NULL = preco ainda nao configurado pra essa modalidade.
    add_column_if_not_exists(cursor, "room_categories", "price_per_night", "REAL")
    add_column_if_not_exists(cursor, "room_categories", "description", "TEXT")

    # floor existe pra organizar propriedades grandes (hotel/resort com
    # varios andares/blocos) - opcional, hostel pequeno pode ignorar.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        category_id INTEGER,
        floor TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS beds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        room_id INTEGER NOT NULL,
        label TEXT NOT NULL,
        bed_kind TEXT NOT NULL DEFAULT 'single',
        bunk_group INTEGER,
        status TEXT NOT NULL DEFAULT 'free',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Kit de roupa de cama por tipo de cama (solteiro, beliche de
    # cima/baixo, casal) - configurado uma vez por hostel, aplicado a
    # toda cama daquele tipo, em vez de configurar cama por cama.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS linen_kits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        bed_kind TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(hostel_id, bed_kind)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS linen_kit_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        linen_kit_id INTEGER NOT NULL,
        inventory_item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        UNIQUE(linen_kit_id, inventory_item_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS offerings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        name TEXT NOT NULL,
        price REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def get_or_create_guest(hostel_id, phone):
    """
    Busca ou cria um hóspede, sempre escopado por hostel_id.
    O mesmo número de telefone pode existir em hostels diferentes
    como hóspedes completamente independentes.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM guests WHERE hostel_id = ? AND phone = ?",
        (hostel_id, phone)
    )

    guest = cursor.fetchone()

    if guest:
        guest_id = guest["id"]
    else:
        cursor.execute(
            """
            INSERT INTO guests (hostel_id, phone)
            VALUES (?, ?)
            """,
            (hostel_id, phone)
        )

        guest_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return guest_id


def update_guest_name(hostel_id, phone, name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE guests SET name = ? WHERE hostel_id = ? AND phone = ?",
        (name, hostel_id, phone)
    )

    conn.commit()
    conn.close()


def update_guest_profile(hostel_id, guest_id, **fields):
    """
    Edicao dos dados de contato/documento no perfil do hospede (aba
    Hospedes). Só atualiza os campos realmente passados (permite salvar
    parcial sem precisar reenviar tudo) - lista branca fixa de colunas
    editaveis, nunca monta SQL com nome de coluna vindo de fora.
    """
    editable_columns = (
        "name", "email", "phone", "address", "date_of_birth",
        "nationality", "document_type", "document_number"
    )
    updates = {k: v for k, v in fields.items() if k in editable_columns}
    if not updates:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM guests WHERE id = ? AND hostel_id = ?", (guest_id, hostel_id))
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Hospede nao encontrado.")

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    try:
        cursor.execute(
            f"UPDATE guests SET {set_clause} WHERE id = ? AND hostel_id = ?",
            (*updates.values(), guest_id, hostel_id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        conn.close()
        raise ValueError("Ja existe outro hospede com esse telefone neste hostel.")

    conn.close()


def set_guest_ai_paused(hostel_id, guest_id, paused):
    """
    Liga/desliga a resposta automatica da IA pra ESSE hospede
    especifico (equipe assumindo ou devolvendo a conversa) - diferente
    de is_ai_enabled, que e o interruptor mestre do hostel inteiro.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE guests SET ai_paused = ? WHERE id = ? AND hostel_id = ?",
        (1 if paused else 0, guest_id, hostel_id)
    )

    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if not updated:
        raise ValueError("Hospede nao encontrado.")

    return {"guest_id": guest_id, "ai_paused": bool(paused)}


def is_guest_ai_paused(hostel_id, phone):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT ai_paused FROM guests WHERE hostel_id = ? AND phone = ?",
        (hostel_id, phone)
    )
    row = cursor.fetchone()
    conn.close()

    return bool(row["ai_paused"]) if row else False


def save_guest_date_of_birth(hostel_id, phone, date_of_birth):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE guests SET date_of_birth = ? WHERE hostel_id = ? AND phone = ?",
        (date_of_birth, hostel_id, phone)
    )

    conn.commit()
    conn.close()


def save_guest_nationality(hostel_id, phone, nationality):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE guests SET nationality = ? WHERE hostel_id = ? AND phone = ?",
        (nationality, hostel_id, phone)
    )

    conn.commit()
    conn.close()


def get_guest_language(hostel_id, phone):
    """
    Idioma ja confirmado numa mensagem anterior desse hospede, se houver -
    usado pra reforcar no prompt da IA de atendimento que o idioma ja
    estabelecido nao deve mudar sozinho no meio da conversa.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT language FROM guests WHERE hostel_id = ? AND phone = ?",
        (hostel_id, phone)
    )
    row = cursor.fetchone()
    conn.close()

    return row["language"] if row and row["language"] else None


def update_guest_language(hostel_id, phone, language):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE guests SET language = ? WHERE hostel_id = ? AND phone = ?",
        (language, hostel_id, phone)
    )

    conn.commit()
    conn.close()


_DOCUMENTS_MIME_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "application/pdf": "pdf",
}


def save_guest_document(hostel_id, guest_id, file_bytes, mime_type, whatsapp_media_id=None):
    """
    Grava o arquivo de documento no disco persistente
    (STAYFLOW_DATA_DIR/documents/{hostel_id}/{guest_id}/...) e a
    referencia no banco. Um hospede pode mandar mais de um documento
    (ou reenviar se a foto saiu ruim), por isso cada envio vira uma
    linha nova, nunca sobrescreve a anterior.
    """
    extension = _DOCUMENTS_MIME_EXTENSIONS.get(mime_type, "bin")

    documents_dir = os.path.join(
        os.getenv("STAYFLOW_DATA_DIR", "."), "documents", str(hostel_id), str(guest_id)
    )
    os.makedirs(documents_dir, exist_ok=True)

    filename = f"{secrets.token_hex(8)}.{extension}"
    file_path = os.path.join(documents_dir, filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO guest_documents (hostel_id, guest_id, file_path, mime_type, whatsapp_media_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (hostel_id, guest_id, file_path, mime_type, whatsapp_media_id)
    )

    document_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {"document_id": document_id, "file_path": file_path}


def list_guest_documents(hostel_id, guest_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, mime_type, received_at
        FROM guest_documents
        WHERE hostel_id = ? AND guest_id = ?
        ORDER BY received_at DESC
        """,
        (hostel_id, guest_id)
    )
    documents = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return documents


def get_guest_document_file(hostel_id, document_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT file_path, mime_type FROM guest_documents WHERE id = ? AND hostel_id = ?",
        (document_id, hostel_id)
    )
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def send_message_to_guest_now(hostel_id, guest_id, message):
    """
    Envio manual e direto da equipe pro hospede (compose box do Chat) -
    diferente do propose->confirm do Ask StayFlow, aqui a equipe ja
    esta dentro da conversa especifica daquele hospede, entao o envio
    e imediato. Grava tanto no memory_service (JSON, historico da IA)
    quanto no message_service (SQL, usado pelas telas) - sender='staff'
    pra distinguir de mensagem gerada pela IA ('assistant').
    """
    from services.whatsapp_service import send_whatsapp_message
    from services.memory_service import save_message as save_memory_message
    from services.message_service import save_message_db

    message = (message or "").strip()
    if not message:
        raise ValueError("A mensagem nao pode ser vazia.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT phone FROM guests WHERE id = ? AND hostel_id = ?",
        (guest_id, hostel_id)
    )
    guest = cursor.fetchone()
    conn.close()

    if not guest:
        raise ValueError("Hospede nao encontrado.")

    phone_number_id, access_token = get_hostel_whatsapp_config(hostel_id)
    sent = send_whatsapp_message(phone_number_id, access_token, guest["phone"], message)

    if sent:
        save_memory_message(hostel_id, guest["phone"], "assistant", message)
        save_message_db(hostel_id, guest["phone"], "staff", message)

    return {"sent": sent, "phone": guest["phone"]}


def get_membership(user_id, hostel_id):
    """
    Retorna o vinculo (membership) de uma pessoa com um hostel,
    incluindo o nome e as permissoes da role, ou None se nao existir
    vinculo ativo.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT hm.id AS membership_id, hm.user_id, hm.hostel_id,
               hm.active, r.id AS role_id, r.name AS role_name,
               r.permissions AS role_permissions
        FROM hostel_memberships hm
        JOIN roles r ON r.id = hm.role_id
        WHERE hm.user_id = ? AND hm.hostel_id = ? AND hm.active = 1
        """,
        (user_id, hostel_id)
    )

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def get_effective_permissions(user_id, hostel_id):
    """
    Calcula, em tempo real, o conjunto de permissoes que uma pessoa
    realmente tem num hostel: permissoes da role, mais o que foi
    ligado manualmente para ela, menos o que foi desligado manualmente
    para ela. Retorna uma lista vazia se nao houver vinculo ativo.
    """
    membership = get_membership(user_id, hostel_id)

    if not membership:
        return []

    role_permissions = set(
        p for p in (membership["role_permissions"] or "").split(",") if p
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT permission_key, allowed FROM membership_permission_overrides WHERE membership_id = ?",
        (membership["membership_id"],)
    )

    for row in cursor.fetchall():
        if row["allowed"]:
            role_permissions.add(row["permission_key"])
        else:
            role_permissions.discard(row["permission_key"])

    conn.close()

    return sorted(role_permissions)


def get_hostel(hostel_id):
    """Retorna os dados basicos de um hostel, ou None se nao existir."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, email, phone FROM hostels WHERE id = ?",
        (hostel_id,)
    )

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def get_user_by_email(email):
    """
    Retorna a identidade (pessoa) por email, ou None. O email e unico
    globalmente agora - nao existe mais "o mesmo email em hostels
    diferentes", uma pessoa e uma identidade so.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, email, password, must_change_password FROM users WHERE email = ?",
        (email,)
    )

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def get_user_by_id(user_id):
    """Retorna a identidade (pessoa) pelo id, ou None."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, email, must_change_password FROM users WHERE id = ?",
        (user_id,)
    )

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def get_user_hostels(user_id):
    """
    Lista todos os hostels onde essa pessoa tem vinculo ativo, com o
    nome da role em cada um. Usado tanto no login (decidir se entra
    direto ou pede pra escolher) quanto no seletor de conta.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT h.id AS hostel_id, h.name AS hostel_name,
               r.id AS role_id, r.name AS role_name
        FROM hostel_memberships hm
        JOIN hostels h ON h.id = hm.hostel_id
        JOIN roles r ON r.id = hm.role_id
        WHERE hm.user_id = ? AND hm.active = 1
        ORDER BY h.name ASC
        """,
        (user_id,)
    )

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return rows


def create_identity_and_hostel(name, email, password_hash, hostel_name, hostel_email):
    """
    Cria uma identidade nova, um hostel novo, a role "Admin" (com
    todas as permissoes) nesse hostel, e o vinculo entre a pessoa e
    o hostel - tudo numa unica transacao. Se qualquer etapa falhar,
    nada e salvo (evita pessoa sem hostel, hostel sem admin, etc).
    Retorna um dict com user_id, hostel_id, role_id, membership_id.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (name, email, password, must_change_password) VALUES (?, ?, ?, 0)",
            (name, email, password_hash)
        )
        user_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO hostels (name, email) VALUES (?, ?)",
            (hostel_name, hostel_email)
        )
        hostel_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO roles (hostel_id, name, permissions) VALUES (?, ?, ?)",
            (hostel_id, "Admin", ALL_PERMISSIONS_STR)
        )
        role_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO hostel_memberships (user_id, hostel_id, role_id, active) VALUES (?, ?, ?, 1)",
            (user_id, hostel_id, role_id)
        )
        membership_id = cursor.lastrowid

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "user_id": user_id,
        "hostel_id": hostel_id,
        "role_id": role_id,
        "membership_id": membership_id
    }


def create_session(user_id, hostel_id, user_agent):
    """
    Cria uma sessao nova no servidor (uma linha em sessions). hostel_id
    pode ser None - estado "pending", antes da escolha de hostel num
    login multi-conta. Retorna o token opaco (id da sessao), aleatorio
    e nao sequencial (nao da pra adivinhar por tentativa).
    """
    session_id = secrets.token_urlsafe(32)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (id, user_id, hostel_id, user_agent) VALUES (?, ?, ?, ?)",
        (session_id, user_id, hostel_id, user_agent)
    )
    conn.commit()
    conn.close()

    return session_id


def get_valid_session(session_id):
    """
    Retorna {user_id, hostel_id} se a sessao existir e nao estiver
    revogada, atualizando last_seen_at como efeito colateral (toda
    requisicao autenticada passa por aqui). Retorna None se a sessao
    nao existir ou tiver sido revogada - bloqueia a proxima
    requisicao imediatamente apos uma revogacao.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, user_id, hostel_id, revoked FROM sessions WHERE id = ?",
        (session_id,)
    )
    row = cursor.fetchone()

    if not row or row["revoked"]:
        conn.close()
        return None

    cursor.execute(
        "UPDATE sessions SET last_seen_at = CURRENT_TIMESTAMP WHERE id = ?",
        (session_id,)
    )
    conn.commit()
    conn.close()

    return {"user_id": row["user_id"], "hostel_id": row["hostel_id"]}


def update_session_hostel(session_id, hostel_id):
    """
    Preenche/atualiza o hostel_id de uma sessao ja existente - usado
    por /select-hostel tanto pra completar a escolha inicial (saindo
    do estado pending) quanto pra trocar de hostel estando ja logado.
    Nunca cria uma sessao nova - e sempre o mesmo "dispositivo".
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sessions SET hostel_id = ? WHERE id = ?",
        (hostel_id, session_id)
    )
    conn.commit()
    conn.close()


def revoke_session_by_id(session_id):
    """Revoga uma sessao sem checar dono - usado no /logout, onde o
    proprio cookie ja garante que e a sessao de quem esta pedindo."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET revoked = 1 WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def revoke_session(session_id, user_id):
    """
    Revoga uma sessao especifica, so se ela pertencer ao user_id
    informado - evita que alguem revogue a sessao de outra pessoa
    passando um id adivinhado/roubado. Retorna True se revogou.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sessions SET revoked = 1 WHERE id = ? AND user_id = ?",
        (session_id, user_id)
    )
    revoked = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return revoked


def revoke_other_sessions(user_id, except_session_id):
    """
    Revoga todas as sessoes ativas do usuario, exceto a informada -
    usado na troca de senha (a sessao que esta trocando continua
    valida, nao precisa relogar na hora).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sessions SET revoked = 1 WHERE user_id = ? AND id != ? AND revoked = 0",
        (user_id, except_session_id)
    )
    conn.commit()
    conn.close()


def get_user_sessions(user_id):
    """Lista as sessoes ATIVAS (nao revogadas) do usuario, mais
    recente primeiro - usado na tela de Seguranca."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, created_at, last_seen_at, user_agent
        FROM sessions
        WHERE user_id = ? AND revoked = 0
        ORDER BY last_seen_at DESC
        """,
        (user_id,)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def log_login_attempt(user_id, hostel_id, email_attempted, success):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO login_attempts (user_id, hostel_id, email_attempted, success) VALUES (?, ?, ?, ?)",
        (user_id, hostel_id, email_attempted, 1 if success else 0)
    )
    conn.commit()
    conn.close()


def get_login_attempts(user_id, limit=20):
    """Lista as ultimas tentativas de login associadas a esse
    usuario (tentativas com email desconhecido - sem match de
    usuario nenhum - nao aparecem aqui, nao ha a quem mostrar)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT hostel_id, email_attempted, success, created_at
        FROM login_attempts
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (user_id, limit)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_user_password_hash(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["password"] if row else None


def update_user_password(user_id, new_password_hash):
    """Atualiza a senha e desliga must_change_password - a pessoa
    acabou de trocar por uma senha de verdade, nao precisa forcar
    troca de novo."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password = ?, must_change_password = 0 WHERE id = ?",
        (new_password_hash, user_id)
    )
    conn.commit()
    conn.close()


def get_role(role_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, hostel_id, name, permissions FROM roles WHERE id = ?", (role_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_roles(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, hostel_id, name, permissions FROM roles WHERE hostel_id = ? ORDER BY name ASC",
        (hostel_id,)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def create_role(hostel_id, name, permissions_list):
    from utils.permissions import ALL_PERMISSIONS
    valid_permissions = [p for p in permissions_list if p in ALL_PERMISSIONS]
    permissions_str = ",".join(valid_permissions)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO roles (hostel_id, name, permissions) VALUES (?, ?, ?)",
            (hostel_id, name, permissions_str)
        )
        role_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError("Ja existe uma funcao com esse nome neste hostel.")
    finally:
        conn.close()
    return role_id


def count_active_memberships_for_role(role_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) AS c FROM hostel_memberships WHERE role_id = ? AND active = 1",
        (role_id,)
    )
    count = cursor.fetchone()["c"]
    conn.close()
    return count


def role_has_any_memberships(role_id):
    """
    Verifica se existe QUALQUER vinculo (ativo ou inativo) usando essa
    role - diferente de count_active_memberships_for_role, que so olha
    vinculos ativos. Usado antes de apagar uma role: se um vinculo
    inativo ainda apontar pra ela, apagar deixaria essa pessoa com
    referencia quebrada (some da listagem de equipe silenciosamente).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) AS c FROM hostel_memberships WHERE role_id = ?",
        (role_id,)
    )
    count = cursor.fetchone()["c"]
    conn.close()
    return count > 0


def count_hostel_permission_holders(hostel_id, permission_key, simulate_role_id=None, simulate_role_permissions=None, exclude_membership_id=None):
    """
    Conta quantos vinculos ativos de um hostel teriam uma permissao
    especifica no conjunto efetivo (role + overrides). Se simulate_role_id
    for passado, usa simulate_role_permissions no lugar da permissao real
    dessa role - permite checar "e se essa role mudasse assim?" sem
    escrever nada no banco.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT hm.id AS membership_id, hm.role_id, r.permissions AS role_permissions
        FROM hostel_memberships hm
        JOIN roles r ON r.id = hm.role_id
        WHERE hm.hostel_id = ? AND hm.active = 1
        """,
        (hostel_id,)
    )
    memberships = cursor.fetchall()

    count = 0
    for m in memberships:
        if exclude_membership_id and m["membership_id"] == exclude_membership_id:
            continue

        if simulate_role_id and m["role_id"] == simulate_role_id:
            role_permissions = simulate_role_permissions
        else:
            role_permissions = m["role_permissions"]

        effective = set(p for p in (role_permissions or "").split(",") if p)

        cursor.execute(
            "SELECT permission_key, allowed FROM membership_permission_overrides WHERE membership_id = ?",
            (m["membership_id"],)
        )
        for row in cursor.fetchall():
            if row["allowed"]:
                effective.add(row["permission_key"])
            else:
                effective.discard(row["permission_key"])

        if permission_key in effective:
            count += 1

    conn.close()
    return count


def update_role(role_id, name=None, permissions_list=None):
    """
    Atualiza nome e/ou permissoes de uma role. Se a mudanca remover
    "team" da role, verifica se o hostel ainda ficaria com pelo menos
    1 pessoa ativa com "team" efetivo (por outra role ou override) -
    senao, bloqueia com ValueError, sem escrever nada.
    """
    from utils.permissions import ALL_PERMISSIONS

    role = get_role(role_id)
    if not role:
        raise ValueError("Role not found.")

    new_permissions_str = role["permissions"]
    if permissions_list is not None:
        valid_permissions = [p for p in permissions_list if p in ALL_PERMISSIONS]
        new_permissions_str = ",".join(valid_permissions)

        old_has_team = "team" in (role["permissions"] or "").split(",")
        new_has_team = "team" in new_permissions_str.split(",")

        if old_has_team and not new_has_team:
            remaining = count_hostel_permission_holders(
                role["hostel_id"], "team",
                simulate_role_id=role_id, simulate_role_permissions=new_permissions_str
            )
            if remaining == 0:
                raise ValueError(
                    "Esta alteracao deixaria o hostel sem ninguem com permissao para gerenciar equipe."
                )

    new_name = name if name is not None else role["name"]

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE roles SET name = ?, permissions = ? WHERE id = ?",
            (new_name, new_permissions_str, role_id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError("Ja existe uma funcao com esse nome neste hostel.")
    finally:
        conn.close()


def delete_role(role_id):
    """
    Apaga uma role, apenas se nenhum vinculo (ativo OU inativo) ainda
    referenciar ela - evita deixar pessoas com referencia quebrada
    (que somem silenciosamente da listagem de equipe).
    """
    role = get_role(role_id)
    if not role:
        raise ValueError("Role not found.")

    if role_has_any_memberships(role_id):
        raise ValueError("Cannot delete a role that still has team members (active or inactive) assigned to it.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM roles WHERE id = ?", (role_id,))
    conn.commit()
    conn.close()


def get_membership_by_id(membership_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT hm.id AS membership_id, hm.user_id, hm.hostel_id, hm.role_id, hm.active,
               r.name AS role_name, r.permissions AS role_permissions
        FROM hostel_memberships hm
        JOIN roles r ON r.id = hm.role_id
        WHERE hm.id = ?
        """,
        (membership_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def check_team_permission_safety(membership_id, new_effective_permissions):
    """
    Levanta ValueError se a mudanca proposta deixaria o hostel sem
    ninguem com a permissao "team" (gerenciar equipe/funcoes).
    new_effective_permissions: as permissoes que esse vinculo teria
    depois da mudanca (lista/set), ou None se o vinculo for desativado.
    """
    membership = get_membership_by_id(membership_id)
    if not membership:
        return

    currently_has_team = "team" in get_effective_permissions(membership["user_id"], membership["hostel_id"])
    will_have_team = bool(new_effective_permissions) and "team" in new_effective_permissions

    if not currently_has_team or will_have_team:
        return

    others_with_team = count_hostel_permission_holders(
        membership["hostel_id"], "team", exclude_membership_id=membership_id
    )

    if others_with_team == 0:
        raise ValueError(
            "Esta alteracao deixaria o hostel sem ninguem com permissao para gerenciar equipe."
        )


def get_permission_detail(membership_id):
    """
    Retorna, para cada permissao do catalogo, se ela vem da role, se
    foi ligada/desligada manualmente por override, e o resultado final
    (efetivo). Usado pela tela de excecoes individuais, para distinguir
    visualmente o que veio da funcao do que foi ajustado manualmente
    para essa pessoa especifica.
    """
    from utils.permissions import ALL_PERMISSIONS

    membership = get_membership_by_id(membership_id)
    if not membership:
        raise ValueError("Membership not found.")

    role_permissions = set(
        p for p in (membership["role_permissions"] or "").split(",") if p
    )

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT permission_key, allowed FROM membership_permission_overrides WHERE membership_id = ?",
        (membership_id,)
    )
    overrides = {row["permission_key"]: bool(row["allowed"]) for row in cursor.fetchall()}
    conn.close()

    detail = []
    for key in ALL_PERMISSIONS:
        from_role = key in role_permissions
        override = overrides.get(key)
        effective = override if override is not None else from_role
        detail.append({
            "key": key,
            "from_role": from_role,
            "override": override,
            "effective": effective,
        })

    return detail


def get_team_members(hostel_id):
    """Lista todos os vinculos (ativos e inativos) de um hostel, com permissoes efetivas calculadas."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT hm.id AS membership_id, hm.user_id, hm.active,
               u.name, u.email,
               r.id AS role_id, r.name AS role_name
        FROM hostel_memberships hm
        JOIN users u ON u.id = hm.user_id
        JOIN roles r ON r.id = hm.role_id
        WHERE hm.hostel_id = ?
        ORDER BY u.name ASC
        """,
        (hostel_id,)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    for row in rows:
        row["permissions"] = get_effective_permissions(row["user_id"], hostel_id)

    return rows


def update_membership_role(membership_id, new_role_id):
    """Troca a role de um vinculo, protegendo contra perda total de acesso a 'team'."""
    membership = get_membership_by_id(membership_id)
    if not membership:
        raise ValueError("Membership not found.")

    new_role = get_role(new_role_id)
    if not new_role or new_role["hostel_id"] != membership["hostel_id"]:
        raise ValueError("Role not found in this hostel.")

    new_role_permissions = set(p for p in (new_role["permissions"] or "").split(",") if p)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT permission_key, allowed FROM membership_permission_overrides WHERE membership_id = ?",
        (membership_id,)
    )
    for row in cursor.fetchall():
        if row["allowed"]:
            new_role_permissions.add(row["permission_key"])
        else:
            new_role_permissions.discard(row["permission_key"])
    conn.close()

    check_team_permission_safety(membership_id, new_role_permissions)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE hostel_memberships SET role_id = ? WHERE id = ?", (new_role_id, membership_id))
    conn.commit()
    conn.close()


def set_membership_override(membership_id, permission_key, allowed):
    """Liga/desliga uma excecao individual de permissao para um vinculo especifico."""
    from utils.permissions import ALL_PERMISSIONS

    if permission_key not in ALL_PERMISSIONS:
        raise ValueError("Invalid permission key.")

    membership = get_membership_by_id(membership_id)
    if not membership:
        raise ValueError("Membership not found.")

    role_permissions = set(p for p in (membership["role_permissions"] or "").split(",") if p)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT permission_key, allowed FROM membership_permission_overrides WHERE membership_id = ?",
        (membership_id,)
    )
    existing_overrides = {row["permission_key"]: row["allowed"] for row in cursor.fetchall()}
    existing_overrides[permission_key] = 1 if allowed else 0

    simulated = set(role_permissions)
    for key, val in existing_overrides.items():
        if val:
            simulated.add(key)
        else:
            simulated.discard(key)

    check_team_permission_safety(membership_id, simulated)

    cursor.execute(
        "SELECT id FROM membership_permission_overrides WHERE membership_id = ? AND permission_key = ?",
        (membership_id, permission_key)
    )
    existing_row = cursor.fetchone()

    if existing_row:
        cursor.execute(
            "UPDATE membership_permission_overrides SET allowed = ? WHERE id = ?",
            (1 if allowed else 0, existing_row["id"])
        )
    else:
        cursor.execute(
            "INSERT INTO membership_permission_overrides (membership_id, permission_key, allowed) VALUES (?, ?, ?)",
            (membership_id, permission_key, 1 if allowed else 0)
        )

    conn.commit()
    conn.close()


def deactivate_membership(membership_id):
    """Desativa um vinculo (sai do hostel), protegendo contra remover o ultimo 'team'."""
    membership = get_membership_by_id(membership_id)
    if not membership:
        raise ValueError("Membership not found.")

    check_team_permission_safety(membership_id, new_effective_permissions=None)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE hostel_memberships SET active = 0 WHERE id = ?", (membership_id,))
    conn.commit()
    conn.close()


def reactivate_membership(membership_id):
    """
    Reativa um vinculo desativado. Nao precisa da mesma protecao de
    "ultimo com team" que deactivate_membership tem, porque reativar
    so aumenta acesso, nunca reduz.
    """
    membership = get_membership_by_id(membership_id)
    if not membership:
        raise ValueError("Membership not found.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE hostel_memberships SET active = 1 WHERE id = ?", (membership_id,))
    conn.commit()
    conn.close()


def invite_to_hostel(hostel_id, name, email, role_id, password_hash=None):
    """
    Convida uma pessoa para um hostel. Se o email ja existe como
    identidade, so cria/reativa o vinculo (a identidade nao e tocada).
    Se e pessoa nova, cria a identidade junto, com must_change_password=1
    (senha temporaria definida por quem convidou). Lida com o caso de
    ja existir um vinculo INATIVO para esse par pessoa+hostel (reativa
    em vez de tentar inserir de novo, o que violaria a constraint
    UNIQUE(user_id, hostel_id)).
    """
    role = get_role(role_id)
    if not role or role["hostel_id"] != hostel_id:
        raise ValueError("Role not found in this hostel.")

    user = get_user_by_email(email)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        existing_membership = None
        if user:
            cursor.execute(
                "SELECT id, active FROM hostel_memberships WHERE user_id = ? AND hostel_id = ?",
                (user["id"], hostel_id)
            )
            existing_membership = cursor.fetchone()

        if existing_membership and existing_membership["active"]:
            raise ValueError("This person is already an active member of this hostel.")

        if user:
            user_id = user["id"]
        else:
            if not password_hash:
                raise ValueError("password_hash is required to invite a new person.")
            cursor.execute(
                "INSERT INTO users (name, email, password, must_change_password) VALUES (?, ?, ?, 1)",
                (name, email, password_hash)
            )
            user_id = cursor.lastrowid

        if existing_membership:
            cursor.execute(
                "UPDATE hostel_memberships SET role_id = ?, active = 1 WHERE id = ?",
                (role_id, existing_membership["id"])
            )
            membership_id = existing_membership["id"]
        else:
            cursor.execute(
                "INSERT INTO hostel_memberships (user_id, hostel_id, role_id, active) VALUES (?, ?, ?, 1)",
                (user_id, hostel_id, role_id)
            )
            membership_id = cursor.lastrowid

        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        raise ValueError("This email is already registered.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        "user_id": user_id,
        "membership_id": membership_id,
        "hostel_id": hostel_id,
        "role_id": role_id,
    }


def get_or_create_conversation(guest_id):
    # guest_id já garante o isolamento por hostel, pois cada guest
    # pertence a exatamente um hostel.
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM conversations
        WHERE guest_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (guest_id,)
    )

    conversation = cursor.fetchone()

    if conversation:
        conversation_id = conversation["id"]
    else:
        cursor.execute(
            """
            INSERT INTO conversations (guest_id, channel)
            VALUES (?, ?)
            """,
            (guest_id, "api")
        )

        conversation_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return conversation_id


def save_message_db(hostel_id, phone, sender, message):
    guest_id = get_or_create_guest(hostel_id, phone)
    conversation_id = get_or_create_conversation(guest_id)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO messages (conversation_id, sender, message)
        VALUES (?, ?, ?)
        """,
        (conversation_id, sender, message)
    )

    conn.commit()
    conn.close()


def save_lead_db(hostel_id, phone, interest):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO leads (hostel_id, phone, interest)
        VALUES (?, ?, ?)
        """,
        (hostel_id, phone, interest)
    )

    conn.commit()
    conn.close()


def get_hostel_id_by_whatsapp_phone_number_id(phone_number_id):
    """
    Resolve qual hostel é dono de um phone_number_id do WhatsApp
    Business (Meta Cloud API) — usado pelo webhook real da Meta,
    que manda esse ID (não o número de telefone em si).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM hostels WHERE whatsapp_phone_number_id = ?",
        (phone_number_id,)
    )

    row = cursor.fetchone()
    conn.close()

    return row["id"] if row else None


def get_hostel_whatsapp_config(hostel_id):
    """Retorna (phone_number_id, access_token) do hostel, ou (None, None)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT whatsapp_phone_number_id, whatsapp_access_token FROM hostels WHERE id = ?",
        (hostel_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None, None

    return row["whatsapp_phone_number_id"], row["whatsapp_access_token"]


def is_opportunity_generation_enabled(hostel_id):
    """
    Verifica se a geracao de oportunidades esta ligada pra esse
    hostel. Se o hostel nunca salvou nenhuma configuracao ainda (sem
    linha em settings), assume ligado por padrao - preserva o
    comportamento atual de quem nunca mexeu nessa tela.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT opportunity_generation FROM settings WHERE hostel_id = ?",
        (hostel_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row or row["opportunity_generation"] is None:
        return True

    return bool(row["opportunity_generation"])


def is_ai_enabled(hostel_id):
    """
    Interruptor mestre: verifica se a IA deve gerar e enviar resposta
    automatica pros hospedes desse hostel. Controla tanto a resposta
    interna quanto o envio real pelo WhatsApp - quando desligado, o
    atendimento fica inteiramente manual. Se nunca configurado, assume
    ligado (preserva o comportamento atual de quem nunca mexeu nessa
    tela).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ai_enabled FROM settings WHERE hostel_id = ?",
        (hostel_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row or row["ai_enabled"] is None:
        return True

    return bool(row["ai_enabled"])


def is_within_quiet_hours(hostel_id):
    """
    Verifica se o horario atual (na hora local do hostel) esta dentro
    do horario de silencio configurado. Usa zoneinfo (biblioteca padrao
    do Python, cuida de DST sozinha) - so calcula algo se o hostel
    configurou timezone E os dois horarios; caso contrario, assume que
    nao ha horario de silencio (nunca suprime automatico sem
    configuracao explicita).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timezone, quiet_hours_start, quiet_hours_end FROM settings WHERE hostel_id = ?",
        (hostel_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row or not row["timezone"] or not row["quiet_hours_start"] or not row["quiet_hours_end"]:
        return False

    from datetime import datetime, time as dt_time
    from zoneinfo import ZoneInfo

    try:
        now_local = datetime.now(ZoneInfo(row["timezone"])).time()
        start = dt_time.fromisoformat(row["quiet_hours_start"])
        end = dt_time.fromisoformat(row["quiet_hours_end"])
    except (ValueError, KeyError):
        return False

    if start <= end:
        return start <= now_local < end

    # Horario de silencio atravessa a meia-noite (ex: 22:00 as 07:00).
    return now_local >= start or now_local < end


# ===== Consultas de leitura reaproveitadas pelas rotas normais E pelas
# tools do agente Ask StayFlow (Fase A) - uma unica fonte de verdade
# pra cada consulta, nunca duplicada entre rota HTTP e tool de IA. =====

def get_dashboard_stats(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) AS total FROM guests WHERE hostel_id = ?",
        (hostel_id,)
    )
    guests = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        JOIN guests g ON c.guest_id = g.id
        WHERE g.hostel_id = ?
    """, (hostel_id,))
    messages = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COUNT(*) AS total FROM leads WHERE hostel_id = ?",
        (hostel_id,)
    )
    leads = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ?
    """, (hostel_id,))
    opportunities = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT phone, interest, status, created_at
        FROM leads
        WHERE hostel_id = ?
        ORDER BY id DESC
        LIMIT 5
    """, (hostel_id,))
    recent_leads = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT m.sender, m.message, m.created_at
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        JOIN guests g ON c.guest_id = g.id
        WHERE g.hostel_id = ?
        ORDER BY m.id DESC
        LIMIT 5
    """, (hostel_id,))
    recent_messages = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "stats": {
            "guests": guests,
            "messages": messages,
            "leads": leads,
            "opportunities": opportunities
        },
        "recent_leads": recent_leads,
        "recent_messages": recent_messages
    }


def get_opportunities_list(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            o.id,
            g.phone,
            o.type,
            o.description,
            o.status,
            o.score,
            o.urgency,
            o.estimated_value,
            o.next_action,
            o.created_at
        FROM opportunities o
        JOIN guests g
            ON o.guest_id = g.id
        WHERE g.hostel_id = ?
        ORDER BY o.created_at DESC
    """, (hostel_id,))

    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return data


def get_reservations_with_stats(hostel_id):
    from datetime import date

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT r.id, r.guest_id, r.guest_name, r.room_type, r.bed, r.checkin_date,
               r.checkout_date, r.source, r.payment_method, r.amount, r.status,
               r.bed_id, r.created_at, r.stay_type, r.daily_rate, b.status AS bed_status,
               r.checked_in_at, r.checked_out_at
        FROM reservations r
        LEFT JOIN beds b ON b.id = r.bed_id
        WHERE r.hostel_id = ?
        ORDER BY r.checkin_date ASC, r.id DESC
        """,
        (hostel_id,)
    )

    reservations = [dict(row) for row in cursor.fetchall()]

    today = date.today().isoformat()

    # Estadia de longa duracao nao tem "amount" fixo - saldo devedor e
    # calculado sob demanda (dias ocupados x diaria, menos pagamentos).
    for r in reservations:
        if r["stay_type"] == "indefinite":
            try:
                checkin = date.fromisoformat(r["checkin_date"])
                end = date.fromisoformat(r["checkout_date"]) if r["checkout_date"] else date.today()
                days_occupied = max((end - checkin).days, 0)
            except (ValueError, TypeError):
                days_occupied = 0

            daily_rate = r["daily_rate"] or 0
            total_owed = round(days_occupied * daily_rate, 2)

            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) AS total FROM reservation_payments WHERE reservation_id = ?",
                (r["id"],)
            )
            total_paid = cursor.fetchone()["total"]

            r["days_occupied"] = days_occupied
            r["balance"] = round(total_owed - total_paid, 2)

    stats = {
        "today": sum(1 for r in reservations if r["checkin_date"] == today),
        "checkins_today": sum(1 for r in reservations if r["checkin_date"] == today),
        "checkouts_today": sum(1 for r in reservations if r["checkout_date"] == today),
        "no_show": sum(1 for r in reservations if r["status"] == "no_show"),
        "total": len(reservations),
        "confirmed_revenue": sum(
            r["amount"] or 0 for r in reservations if r["status"] == "confirmed" and r["stay_type"] != "indefinite"
        ),
    }

    conn.close()

    return {"reservations": reservations, "stats": stats}


def build_reorder_message(item, supplier):
    """
    Monta uma sugestão de mensagem pra reposição — texto pronto que o
    gestor pode revisar e mandar pro fornecedor (WhatsApp, email, etc).
    Hoje é só o texto sugerido; o envio automático fica pra quando
    houver integração de WhatsApp com fornecedores.
    """
    if not supplier:
        return (
            f"Nenhum fornecedor cadastrado para '{item['name']}'. "
            f"Cadastre um fornecedor pra receber a sugestão de contato."
        )

    quantity_to_order = item["reorder_quantity"] or item["min_threshold"] or 1

    return (
        f"Olá {supplier['name']}, tudo bem? Nosso estoque de "
        f"'{item['name']}' está em {item['quantity']} {item['unit']}, "
        f"abaixo do mínimo de {item['min_threshold']}. "
        f"Poderia providenciar mais {quantity_to_order} {item['unit']}?"
    )


def get_inventory_with_alerts(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            i.id, i.category, i.name, i.quantity, i.min_threshold,
            i.reorder_quantity, i.unit, i.supplier_id, i.in_laundry_quantity,
            s.name AS supplier_name, s.phone AS supplier_phone,
            s.email AS supplier_email
        FROM inventory_items i
        LEFT JOIN suppliers s ON s.id = i.supplier_id
        WHERE i.hostel_id = ?
        ORDER BY i.category, i.name
    """, (hostel_id,))

    items = [dict(row) for row in cursor.fetchall()]

    by_category = {}
    alerts = []

    for item in items:
        by_category.setdefault(item["category"], []).append(item)

        if item["quantity"] <= item["min_threshold"]:
            supplier = None
            if item["supplier_id"]:
                supplier = {
                    "name": item["supplier_name"],
                    "phone": item["supplier_phone"],
                    "email": item["supplier_email"]
                }

            alerts.append({
                "id": item["id"],
                "name": item["name"],
                "category": item["category"],
                "quantity": item["quantity"],
                "min_threshold": item["min_threshold"],
                "unit": item["unit"],
                "supplier": supplier,
                "suggested_message": build_reorder_message(item, supplier)
            })

    conn.close()

    return {"items": items, "by_category": by_category, "alerts": alerts}


def get_revenue_summary(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, type, name, price
        FROM offerings
        WHERE hostel_id = ?
        ORDER BY type, name
    """, (hostel_id,))
    offerings = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT o.id, o.type, o.description, o.estimated_value, o.next_action, g.phone
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ? AND o.status = 'open' AND o.type IN ('tour', 'upsell')
        ORDER BY o.estimated_value DESC
    """, (hostel_id,))
    opportunities = [dict(row) for row in cursor.fetchall()]

    extra_revenue = sum(o["estimated_value"] or 0 for o in opportunities)

    conn.close()

    return {
        "offerings": offerings,
        "opportunities": opportunities,
        "extra_revenue": extra_revenue
    }


def get_guests_list(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            g.id,
            g.name,
            g.phone,
            g.email,
            g.language,
            g.created_at,
            (
                SELECT COUNT(*)
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.guest_id = g.id
            ) AS message_count,
            (
                SELECT COALESCE(SUM(o.estimated_value), 0)
                FROM opportunities o
                WHERE o.guest_id = g.id
            ) AS total_value
        FROM guests g
        WHERE g.hostel_id = ?
        ORDER BY g.created_at DESC
    """, (hostel_id,))

    guests = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return guests


def get_guest_profile(hostel_id, guest_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, phone, email, language, created_at, ai_paused,
               date_of_birth, nationality, address, document_type, document_number
        FROM guests
        WHERE id = ? AND hostel_id = ?
    """, (guest_id, hostel_id))

    guest = cursor.fetchone()

    if not guest:
        conn.close()
        return None

    cursor.execute("""
        SELECT m.sender, m.message, m.created_at
        FROM messages m
        JOIN conversations c
            ON m.conversation_id = c.id
        WHERE c.guest_id = ?
        ORDER BY m.created_at ASC, m.id ASC
    """, (guest_id,))

    messages = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT type, description, score, urgency, estimated_value,
               next_action, status, created_at
        FROM opportunities
        WHERE guest_id = ?
        ORDER BY created_at DESC, id DESC
    """, (guest_id,))

    opportunities = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT id, mime_type, received_at
        FROM guest_documents
        WHERE hostel_id = ? AND guest_id = ?
        ORDER BY received_at DESC
    """, (hostel_id, guest_id))

    documents = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "guest": dict(guest),
        "messages": messages,
        "opportunities": opportunities,
        "documents": documents,
        "reservations": get_guest_reservations(hostel_id, guest_id)
    }


def get_guest_reservations(hostel_id, guest_id):
    """
    Historico de estadias desse hospede - reservas fixas (com amount
    fechado, sem controle de pagamento parcial no modelo atual) e
    estadias de longa duracao (saldo calculado sob demanda via
    get_reservation_balance, que ja existe pra isso). Cada item vem com
    um campo "balance" so quando faz sentido (stay_type='indefinite');
    reserva fixa nao tem conceito de saldo parcial hoje - o valor total
    e o que foi cobrado, ponto (nao ha "pago"/"nao pago" por reserva
    fixa no modelo de dados atual).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, room_type, checkin_date, checkout_date, source, status,
               amount, stay_type, daily_rate, external_booking_id
        FROM reservations
        WHERE hostel_id = ? AND guest_id = ?
        ORDER BY checkin_date DESC, id DESC
    """, (hostel_id, guest_id))

    reservations = [dict(row) for row in cursor.fetchall()]
    conn.close()

    for reservation in reservations:
        if reservation["stay_type"] == "indefinite":
            balance_info = get_reservation_balance(hostel_id, reservation["id"])
            reservation["balance"] = balance_info["balance"]

    return reservations


def find_guest_by_name(hostel_id, name_query):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, phone, email, created_at
        FROM guests
        WHERE hostel_id = ?
        ORDER BY created_at DESC
    """, (hostel_id,))

    all_guests = [dict(row) for row in cursor.fetchall()]

    conn.close()

    query_norm = _normalize_text(name_query)
    matches = [g for g in all_guests if query_norm in _normalize_text(g["name"])]

    return matches[:5]


def get_chats_list(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            g.id AS guest_id,
            g.phone,
            g.name,
            m.message AS last_message,
            m.sender AS last_sender,
            m.created_at AS last_activity,
            o.type AS intent,
            o.score,
            o.urgency,
            o.estimated_value,
            o.next_action
        FROM guests g

        LEFT JOIN conversations c
            ON c.guest_id = g.id

        LEFT JOIN messages m
            ON m.id = (
                SELECT m2.id
                FROM messages m2
                JOIN conversations c2
                    ON m2.conversation_id = c2.id
                WHERE c2.guest_id = g.id
                ORDER BY m2.created_at DESC, m2.id DESC
                LIMIT 1
            )

        LEFT JOIN opportunities o
            ON o.id = (
                SELECT o2.id
                FROM opportunities o2
                WHERE o2.guest_id = g.id
                ORDER BY o2.created_at DESC, o2.id DESC
                LIMIT 1
            )

        WHERE m.message IS NOT NULL
          AND g.hostel_id = ?

        GROUP BY g.id

        ORDER BY m.created_at DESC
    """, (hostel_id,))

    data = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return data


def get_finance_summary(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM reservations
        WHERE hostel_id = ? AND status = 'confirmed'
    """, (hostel_id,))
    confirmed_revenue = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COALESCE(SUM(o.estimated_value), 0) AS total
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ? AND o.status = 'open' AND o.urgency = 'high'
    """, (hostel_id,))
    at_risk = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COALESCE(SUM(o.estimated_value), 0) AS total
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ? AND o.status = 'open'
    """, (hostel_id,))
    recoverable = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT COALESCE(SUM(o.estimated_value), 0) AS total
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ? AND o.status = 'closed'
    """, (hostel_id,))
    recovered = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT
            'Reserva' AS type,
            guest_name || COALESCE(' - ' || NULLIF(room_type, ''), '') AS description,
            amount AS value,
            status,
            created_at
        FROM reservations
        WHERE hostel_id = ?

        UNION ALL

        SELECT
            'Oportunidade' AS type,
            o.description AS description,
            o.estimated_value AS value,
            o.status,
            o.created_at
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ?

        ORDER BY created_at DESC
        LIMIT 30
    """, (hostel_id, hostel_id))

    movements = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "confirmed_revenue": confirmed_revenue,
        "recovered": recovered,
        "at_risk": at_risk,
        "recoverable": recoverable,
        "movements": movements
    }


def get_reports_summary(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COALESCE(NULLIF(source, ''), 'manual') AS channel,
            COALESCE(SUM(amount), 0) AS revenue
        FROM reservations
        WHERE hostel_id = ?
        GROUP BY channel
        ORDER BY revenue DESC
    """, (hostel_id,))
    by_channel = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) AS c FROM guests WHERE hostel_id = ?", (hostel_id,))
    total_guests = cursor.fetchone()["c"]

    cursor.execute("""
        SELECT COUNT(*) AS c
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        JOIN guests g ON c.guest_id = g.id
        WHERE g.hostel_id = ?
    """, (hostel_id,))
    total_messages = cursor.fetchone()["c"]

    cursor.execute("""
        SELECT COUNT(*) AS c
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ?
    """, (hostel_id,))
    total_opportunities = cursor.fetchone()["c"]

    cursor.execute("""
        SELECT COUNT(*) AS c
        FROM reservations
        WHERE hostel_id = ? AND status = 'confirmed'
    """, (hostel_id,))
    total_confirmed = cursor.fetchone()["c"]

    funnel = [
        {"stage": "Hóspedes", "count": total_guests},
        {"stage": "Mensagens", "count": total_messages},
        {"stage": "Oportunidades", "count": total_opportunities},
        {"stage": "Reservas confirmadas", "count": total_confirmed},
    ]

    conn.close()

    return {
        "by_channel": by_channel,
        "funnel": funnel
    }


# ===== Acoes de escrita do Ask StayFlow (Fase B) - cada funcao aqui e
# a MESMA fonte de verdade usada pelas rotas manuais quando existe uma
# rota equivalente; quando nao existe (ex: ajuste de estoque por nome),
# a funcao foi desenhada pra ser chamada por linguagem natural. =====

def create_reservation_record(hostel_id, guest_name, room_type="", bed="",
                                checkin_date=None, checkout_date=None,
                                source="manual", payment_method="",
                                amount=0, status="pending", phone=""):
    guest_name = (guest_name or "").strip()
    checkin_date = (checkin_date or "").strip()
    checkout_date = (checkout_date or "").strip()

    if not guest_name:
        raise ValueError("guest_name is required.")
    if not checkin_date or not checkout_date:
        raise ValueError("checkin_date and checkout_date are required.")

    conn = get_connection()
    cursor = conn.cursor()

    guest_id = None
    phone = (phone or "").strip()
    if phone:
        cursor.execute(
            "SELECT id FROM guests WHERE hostel_id = ? AND phone = ?",
            (hostel_id, phone)
        )
        row = cursor.fetchone()
        if row:
            guest_id = row["id"]

    cursor.execute(
        """
        INSERT INTO reservations
        (hostel_id, guest_id, guest_name, room_type, bed, checkin_date,
         checkout_date, source, payment_method, amount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            hostel_id, guest_id, guest_name, (room_type or "").strip(),
            (bed or "").strip(), checkin_date, checkout_date,
            (source or "manual").strip(), (payment_method or "").strip(),
            float(amount or 0), (status or "pending").strip(),
        )
    )

    reservation_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return reservation_id


def create_indefinite_stay(hostel_id, guest_name, checkin_date, daily_rate, room_type="", bed_id=None, phone=""):
    """
    Estadia de longa duracao / morador fixo (ex: funcionario que mora
    no hostel, pagando conforme consegue) - sem data de saida definida.
    Status sempre 'confirmed' (e um arranjo ja decidido pela equipe,
    nao um pedido de hospede aguardando aprovacao). daily_rate pode ser
    0 (funcionario que nao paga nada, so ocupa a cama) ou um valor real
    que vai acumulando saldo devedor por dia, abatido conforme
    pagamentos forem registrados (record_reservation_payment). Se
    bed_id for passado, ocupa a cama de verdade na hora (diferente de
    uma reserva futura - aqui a pessoa ja esta la).
    """
    guest_name = (guest_name or "").strip()
    checkin_date = (checkin_date or "").strip()

    if not guest_name:
        raise ValueError("guest_name is required.")
    if not checkin_date:
        raise ValueError("checkin_date is required.")

    conn = get_connection()
    cursor = conn.cursor()

    if bed_id:
        cursor.execute("SELECT status, label FROM beds WHERE id = ? AND hostel_id = ?", (bed_id, hostel_id))
        bed = cursor.fetchone()
        if not bed:
            conn.close()
            raise ValueError("Cama nao encontrada.")
        if bed["status"] != "free":
            conn.close()
            raise ValueError(f"A cama '{bed['label']}' nao esta livre (status atual: {bed['status']}).")

    conn.close()

    # get_or_create_guest abre/fecha sua propria conexao - por isso a
    # de cima foi fechada antes. Sem isso, morador fixo com telefone
    # nunca aparecia na aba Hospedes (guest_id ficava null porque so
    # linkava com gente que ja existia, nunca criava um registro novo).
    guest_id = None
    phone = (phone or "").strip()
    if phone:
        guest_id = get_or_create_guest(hostel_id, phone)
        update_guest_name(hostel_id, phone, guest_name)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO reservations
        (hostel_id, guest_id, guest_name, room_type, checkin_date, checkout_date,
         source, amount, status, stay_type, daily_rate, bed_id)
        VALUES (?, ?, ?, ?, ?, NULL, 'manual', 0, 'confirmed', 'indefinite', ?, ?)
        """,
        (hostel_id, guest_id, guest_name, (room_type or "").strip(), checkin_date, float(daily_rate or 0), bed_id)
    )

    reservation_id = cursor.lastrowid

    if bed_id:
        cursor.execute("UPDATE beds SET status = 'occupied' WHERE id = ?", (bed_id,))

    conn.commit()
    conn.close()

    return reservation_id


def get_reservation_balance(hostel_id, reservation_id):
    """
    Saldo sempre calculado sob demanda (nunca um campo estatico que
    poderia ficar desatualizado): dias ocupados (do checkin ate hoje,
    ou ate o checkout se a estadia ja foi encerrada) x daily_rate,
    menos a soma de tudo que ja foi pago.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT checkin_date, checkout_date, daily_rate FROM reservations WHERE id = ? AND hostel_id = ?",
        (reservation_id, hostel_id)
    )
    reservation = cursor.fetchone()

    if not reservation:
        conn.close()
        raise ValueError("Reserva nao encontrada.")

    end_date = reservation["checkout_date"] or datetime.date.today().isoformat()

    try:
        checkin = datetime.date.fromisoformat(reservation["checkin_date"])
        end = datetime.date.fromisoformat(end_date)
        days_occupied = max((end - checkin).days, 0)
    except (ValueError, TypeError):
        days_occupied = 0

    daily_rate = reservation["daily_rate"] or 0
    total_owed = round(days_occupied * daily_rate, 2)

    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM reservation_payments WHERE reservation_id = ?",
        (reservation_id,)
    )
    total_paid = cursor.fetchone()["total"]

    conn.close()

    return {
        "reservation_id": reservation_id,
        "days_occupied": days_occupied,
        "daily_rate": daily_rate,
        "total_owed": total_owed,
        "total_paid": total_paid,
        "balance": round(total_owed - total_paid, 2)
    }


def record_reservation_payment(hostel_id, reservation_id, amount, method=None, note=None):
    amount = float(amount or 0)
    if amount <= 0:
        raise ValueError("O valor do pagamento precisa ser maior que zero.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM reservations WHERE id = ? AND hostel_id = ?",
        (reservation_id, hostel_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Reserva nao encontrada.")

    cursor.execute(
        "INSERT INTO reservation_payments (hostel_id, reservation_id, amount, method, note) VALUES (?, ?, ?, ?, ?)",
        (hostel_id, reservation_id, amount, (method or "").strip() or None, (note or "").strip() or None)
    )

    conn.commit()
    conn.close()

    return get_reservation_balance(hostel_id, reservation_id)


def list_reservation_payments(hostel_id, reservation_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, amount, method, note, paid_at
        FROM reservation_payments
        WHERE hostel_id = ? AND reservation_id = ?
        ORDER BY paid_at DESC
        """,
        (hostel_id, reservation_id)
    )
    payments = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return payments


def close_indefinite_stay(hostel_id, reservation_id, checkout_date=None):
    """
    Encerra uma estadia de longa duracao (a pessoa saiu de verdade) -
    grava a data de saida e libera a cama pra limpeza, igual um
    check-out normal. O saldo devedor continua consultavel depois
    (get_reservation_balance passa a usar checkout_date como fim da
    contagem em vez de "hoje").
    """
    checkout_date = (checkout_date or datetime.date.today().isoformat()).strip()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT bed_id FROM reservations WHERE id = ? AND hostel_id = ? AND stay_type = 'indefinite'",
        (reservation_id, hostel_id)
    )
    reservation = cursor.fetchone()

    if not reservation:
        conn.close()
        raise ValueError("Estadia de longa duracao nao encontrada.")

    cursor.execute(
        "UPDATE reservations SET checkout_date = ? WHERE id = ?",
        (checkout_date, reservation_id)
    )

    if reservation["bed_id"]:
        cursor.execute("UPDATE beds SET status = 'needs_cleaning' WHERE id = ?", (reservation["bed_id"],))

    conn.commit()
    conn.close()

    return get_reservation_balance(hostel_id, reservation_id)


def reservar_cama_com_trava(hostel_id, bed_id, checkin_date, checkout_date, insert_fn):
    """
    Reconfere que bed_id está livre pras datas pedidas e executa
    insert_fn(cursor) — tudo dentro de uma única transação SQLite aberta
    com BEGIN IMMEDIATE, em vez do padrão antigo do projeto (checar
    disponibilidade numa conexão, inserir a reserva noutra) que deixava
    uma janela real de corrida entre checar e inserir.

    BEGIN IMMEDIATE pega a trava de escrita do banco assim que a
    transação abre, não só quando o primeiro INSERT/UPDATE roda — por
    isso uma segunda chamada concorrente pra essa mesma função (de
    outra thread ou de outro worker do gunicorn) fica bloqueada
    esperando a primeira terminar, em vez de ler o mesmo estado "livre"
    e as duas inserirem por cima uma da outra. Existe hoje só pra
    reservas automáticas de alta frequência que disputam cama entre si
    (webhook de channel manager e a IA do WhatsApp) — a criação manual
    pela equipe continua sem essa trava, ver decisão registrada no
    plano da integração Beds24.

    insert_fn recebe o cursor já dentro da transação e deve devolver o
    id da reserva criada/atualizada. Se a cama não estiver mais livre,
    levanta ValueError e desfaz tudo (nada é escrito).
    """
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id FROM reservations
            WHERE bed_id = ? AND hostel_id = ? AND status != 'cancelled'
              AND checkin_date < ? AND checkout_date > ?
            """,
            (bed_id, hostel_id, checkout_date, checkin_date)
        )
        if cursor.fetchone():
            conn.rollback()
            raise ValueError("Essa cama nao esta mais disponivel pras datas pedidas - escolha outra.")

        result = insert_fn(cursor)
        conn.commit()
        return result
    finally:
        conn.close()


def find_available_beds(hostel_id, category_name, checkin_date, checkout_date):
    """
    Disponibilidade FUTURA (pra reserva), diferente do status
    free/occupied/needs_cleaning das camas (que e sobre agora mesmo,
    pro mapa operacional). Uma cama esta disponivel pro periodo pedido
    se nenhuma reserva nao-cancelada com essa cama tem datas que se
    cruzam com [checkin_date, checkout_date).
    """
    checkin_date = (checkin_date or "").strip()
    checkout_date = (checkout_date or "").strip()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT b.id, b.label, b.bed_kind, b.bunk_group, r.name AS room_name
        FROM beds b
        JOIN rooms r ON r.id = b.room_id
        LEFT JOIN room_categories rc ON rc.id = r.category_id
        WHERE b.hostel_id = ? AND rc.name = ?
        """,
        (hostel_id, category_name)
    )
    candidates = [dict(row) for row in cursor.fetchall()]

    # Guarda contra o modelo confundir nome de MODALIDADE (ex:
    # "Compartilhado") com nome de QUARTO (ex: "Dorm 1") entre uma
    # chamada e outra - sem isso, um category_name errado silenciosamente
    # devolve lista vazia, e quem chama interpreta isso como "sem cama
    # disponivel" (falso negativo real, ja observado em teste).
    if not candidates:
        cursor.execute(
            "SELECT id FROM room_categories WHERE hostel_id = ? AND name = ?",
            (hostel_id, category_name)
        )
        category_exists = cursor.fetchone()

        if not category_exists:
            cursor.execute(
                "SELECT name FROM room_categories WHERE hostel_id = ?",
                (hostel_id,)
            )
            valid_names = [row["name"] for row in cursor.fetchall()]
            conn.close()
            raise ValueError(
                f"'{category_name}' não é uma modalidade de quarto válida (isso parece nome de quarto, não de modalidade). "
                f"Modalidades reais deste hostel: {', '.join(valid_names) if valid_names else 'nenhuma cadastrada'}."
            )

    available = []
    for bed in candidates:
        cursor.execute(
            """
            SELECT id FROM reservations
            WHERE bed_id = ? AND status != 'cancelled'
              AND checkin_date < ? AND checkout_date > ?
            """,
            (bed["id"], checkout_date, checkin_date)
        )
        if not cursor.fetchone():
            available.append(bed)

    conn.close()

    return available


def get_offerings_for_chat(hostel_id):
    """Extras (toalha, cobertor, etc) pra IA de atendimento cotar preco real ao hospede."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT type, name, price FROM offerings WHERE hostel_id = ? ORDER BY type, name",
        (hostel_id,)
    )
    offerings = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return offerings


def _flag_booking_needs_manual_setup(hostel_id, phone, guest_name, category_name, checkin_date, checkout_date):
    """
    Quando a modalidade pedida nao tem NENHUMA cama cadastrada, nao da
    pra confirmar disponibilidade automaticamente - reservar as cegas
    arriscaria overbooking real (dois hospedes reservando a mesma
    modalidade sem nenhuma trava de capacidade). Em vez disso, vira uma
    oportunidade de alta prioridade pra equipe cadastrar as camas e
    confirmar manualmente. Nao duplica se ja existir uma oportunidade
    aberta desse tipo pro mesmo hospede.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM guests WHERE hostel_id = ? AND phone = ?",
        (hostel_id, phone)
    )
    guest = cursor.fetchone()

    if not guest:
        conn.close()
        return

    cursor.execute(
        "SELECT id FROM opportunities WHERE guest_id = ? AND type = 'booking' AND status = 'open'",
        (guest["id"],)
    )
    if cursor.fetchone():
        conn.close()
        return

    cursor.execute(
        """
        INSERT INTO opportunities
        (guest_id, type, description, status, score, urgency, estimated_value, next_action)
        VALUES (?, 'booking', ?, 'open', 90, 'high', 0, ?)
        """,
        (
            guest["id"],
            f"{guest_name} quer reservar '{category_name}' de {checkin_date} a {checkout_date}, mas essa "
            f"modalidade ainda nao tem nenhuma cama cadastrada - nao da pra confirmar disponibilidade automaticamente.",
            "Cadastrar as camas dessa modalidade no Mapa de Quartos e confirmar a reserva manualmente com o hospede."
        )
    )

    conn.commit()
    conn.close()


def create_reservation_from_chat(hostel_id, phone, guest_name, category_name, checkin_date, checkout_date, bed_id=None):
    """
    Cria a reserva automaticamente a partir da conversa da IA de
    atendimento com o hospede pelo WhatsApp - sempre status 'pending'
    (a equipe confirma depois, igual ja fazia manualmente). O valor e
    SEMPRE calculado a partir do price_per_night real da modalidade
    (nunca aceito como argumento do modelo).

    Protecao contra overbooking: se a modalidade nao tem NENHUMA cama
    cadastrada, a reserva NAO e criada - vira oportunidade pra equipe
    (ver _flag_booking_needs_manual_setup). Se a modalidade tem camas
    cadastradas, bed_id se torna OBRIGATORIO e precisa apontar pra uma
    cama realmente livre nessas datas - sem isso nao ha como saber
    quantas unidades daquela modalidade ja estao ocupadas.

    Nao duplica se o mesmo hospede ja tem uma reserva pending pras
    mesmas datas vinda do chat (guest pode reafirmar a mesma coisa em
    mais de uma mensagem na mesma conversa).
    """
    checkin_date = (checkin_date or "").strip()
    checkout_date = (checkout_date or "").strip()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT r.id FROM reservations r
        JOIN guests g ON g.id = r.guest_id
        WHERE r.hostel_id = ? AND g.phone = ? AND r.source = 'whatsapp'
          AND r.status = 'pending' AND r.checkin_date = ? AND r.checkout_date = ?
        """,
        (hostel_id, phone, checkin_date, checkout_date)
    )
    existing = cursor.fetchone()

    if existing:
        nights = 0
        try:
            nights = (datetime.date.fromisoformat(checkout_date) - datetime.date.fromisoformat(checkin_date)).days
        except (ValueError, TypeError):
            pass
        conn.close()
        return {"reservation_id": existing["id"], "already_existed": True, "nights": nights}

    cursor.execute(
        "SELECT price_per_night FROM room_categories WHERE hostel_id = ? AND name = ?",
        (hostel_id, category_name)
    )
    category_row = cursor.fetchone()

    cursor.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM beds b
        JOIN rooms r ON r.id = b.room_id
        JOIN room_categories rc ON rc.id = r.category_id
        WHERE b.hostel_id = ? AND rc.name = ?
        """,
        (hostel_id, category_name)
    )
    bed_count = cursor.fetchone()["cnt"]
    conn.close()

    if bed_count == 0:
        _flag_booking_needs_manual_setup(hostel_id, phone, guest_name, category_name, checkin_date, checkout_date)
        raise ValueError(
            f"A modalidade '{category_name}' ainda nao tem nenhuma cama cadastrada, entao nao da pra confirmar "
            f"disponibilidade com seguranca. O pedido foi registrado como oportunidade de alta prioridade pra "
            f"equipe cadastrar as camas e confirmar manualmente com o hospede."
        )

    if not bed_id:
        raise ValueError(
            f"A modalidade '{category_name}' tem camas cadastradas - use get_available_beds pra escolher uma "
            f"cama especifica disponivel antes de reservar."
        )

    amount = 0
    nights = 0
    try:
        nights = max((datetime.date.fromisoformat(checkout_date) - datetime.date.fromisoformat(checkin_date)).days, 0)
    except (ValueError, TypeError):
        nights = 0
    if category_row and category_row["price_per_night"]:
        amount = round(category_row["price_per_night"] * nights, 2)

    def _insert_with_bed(cursor):
        guest_id = None
        stripped_phone = (phone or "").strip()
        if stripped_phone:
            cursor.execute(
                "SELECT id FROM guests WHERE hostel_id = ? AND phone = ?",
                (hostel_id, stripped_phone)
            )
            row = cursor.fetchone()
            if row:
                guest_id = row["id"]

        cursor.execute(
            """
            INSERT INTO reservations
            (hostel_id, guest_id, guest_name, room_type, bed, bed_id, checkin_date,
             checkout_date, source, payment_method, amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'whatsapp', ?, ?, 'pending')
            """,
            (hostel_id, guest_id, guest_name, category_name, "", int(bed_id),
             checkin_date, checkout_date, "", amount)
        )
        return cursor.lastrowid

    # Reconfere disponibilidade e insere numa unica transacao travada
    # (ver reservar_cama_com_trava) - fecha a janela de corrida que
    # existia aqui antes (checar com find_available_beds numa conexao,
    # inserir noutra, sem nada impedindo duas chamadas concorrentes de
    # passarem pela checagem e ambas inserirem pra mesma cama).
    reservation_id = reservar_cama_com_trava(hostel_id, int(bed_id), checkin_date, checkout_date, _insert_with_bed)

    return {
        "reservation_id": reservation_id,
        "already_existed": False,
        "nights": nights,
        "price_per_night": category_row["price_per_night"] if category_row else None,
        "amount": amount,
    }


def update_reservation_status_record(hostel_id, reservation_id, status):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM reservations WHERE id = ? AND hostel_id = ?",
        (reservation_id, hostel_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Reservation not found.")

    cursor.execute(
        "UPDATE reservations SET status = ? WHERE id = ? AND hostel_id = ?",
        (status, reservation_id, hostel_id)
    )

    conn.commit()
    conn.close()


def create_supplier_record(hostel_id, name, phone="", email=""):
    name = (name or "").strip()
    if not name:
        raise ValueError("name is required.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO suppliers (hostel_id, name, phone, email) VALUES (?, ?, ?, ?)",
        (hostel_id, name, (phone or "").strip(), (email or "").strip())
    )

    supplier_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return supplier_id


def find_inventory_item_by_name(hostel_id, name_query):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            i.id, i.category, i.name, i.quantity, i.min_threshold,
            i.reorder_quantity, i.unit, i.supplier_id, i.in_laundry_quantity,
            s.name AS supplier_name, s.phone AS supplier_phone
        FROM inventory_items i
        LEFT JOIN suppliers s ON s.id = i.supplier_id
        WHERE i.hostel_id = ?
        ORDER BY i.name
    """, (hostel_id,))

    all_items = [dict(row) for row in cursor.fetchall()]

    conn.close()

    query_norm = _normalize_text(name_query)
    matches = [item for item in all_items if query_norm in _normalize_text(item["name"])]

    return matches


def adjust_inventory_quantity_by_name(hostel_id, item_name, delta):
    matches = find_inventory_item_by_name(hostel_id, item_name)

    if not matches:
        raise ValueError(f"Nenhum item de estoque encontrado com o nome '{item_name}'.")
    if len(matches) > 1:
        names = ", ".join(m["name"] for m in matches)
        raise ValueError(f"Mais de um item de estoque bate com '{item_name}': {names}. Seja mais especifico.")

    item = matches[0]
    new_quantity = max(0, item["quantity"] + delta)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE inventory_items SET quantity = ? WHERE id = ? AND hostel_id = ?",
        (new_quantity, item["id"], hostel_id)
    )

    conn.commit()
    conn.close()

    return {
        "id": item["id"],
        "name": item["name"],
        "previous_quantity": item["quantity"],
        "new_quantity": new_quantity,
        "unit": item["unit"]
    }


def list_pending_supplier_orders(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            io.id, io.quantity, io.status, io.message,
            io.created_at, io.sent_at,
            i.name AS item_name, i.unit,
            s.name AS supplier_name, s.phone AS supplier_phone
        FROM inventory_orders io
        JOIN inventory_items i ON i.id = io.inventory_item_id
        LEFT JOIN suppliers s ON s.id = io.supplier_id
        WHERE io.hostel_id = ? AND io.status IN ('pending_confirmation', 'sent')
        ORDER BY io.created_at DESC
    """, (hostel_id,))

    orders = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return orders


def propose_supplier_order(hostel_id, item_name, quantity):
    matches = find_inventory_item_by_name(hostel_id, item_name)

    if not matches:
        raise ValueError(f"Nenhum item de estoque encontrado com o nome '{item_name}'.")
    if len(matches) > 1:
        names = ", ".join(m["name"] for m in matches)
        raise ValueError(f"Mais de um item de estoque bate com '{item_name}': {names}. Seja mais especifico.")

    item = matches[0]

    if not item["supplier_id"]:
        raise ValueError(f"O item '{item['name']}' nao tem fornecedor cadastrado. Cadastre um fornecedor antes de pedir reposicao.")
    if not item["supplier_phone"]:
        raise ValueError(f"O fornecedor de '{item['name']}' nao tem telefone cadastrado.")

    quantity = int(quantity)
    message = (
        f"Ola {item['supplier_name']}, tudo bem? Poderia providenciar "
        f"{quantity} {item['unit']} de '{item['name']}' pra gente?"
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO inventory_orders
        (hostel_id, inventory_item_id, supplier_id, quantity, message, status)
        VALUES (?, ?, ?, ?, ?, 'pending_confirmation')
        """,
        (hostel_id, item["id"], item["supplier_id"], quantity, message)
    )

    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "order_id": order_id,
        "item_name": item["name"],
        "supplier_name": item["supplier_name"],
        "supplier_phone": item["supplier_phone"],
        "quantity": quantity,
        "unit": item["unit"],
        "message": message
    }


def get_pending_confirmation_order(hostel_id, order_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if order_id:
        cursor.execute(
            """
            SELECT * FROM inventory_orders
            WHERE id = ? AND hostel_id = ? AND status = 'pending_confirmation'
            """,
            (order_id, hostel_id)
        )
    else:
        cursor.execute(
            """
            SELECT * FROM inventory_orders
            WHERE hostel_id = ? AND status = 'pending_confirmation'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (hostel_id,)
        )

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def send_supplier_order(hostel_id, order_id=None):
    from services.whatsapp_service import send_whatsapp_message

    order = get_pending_confirmation_order(hostel_id, order_id)
    if not order:
        raise ValueError("Nenhum pedido pendente de confirmacao encontrado.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT i.name AS item_name, s.name AS supplier_name, s.phone AS supplier_phone
        FROM inventory_orders io
        JOIN inventory_items i ON i.id = io.inventory_item_id
        LEFT JOIN suppliers s ON s.id = io.supplier_id
        WHERE io.id = ?
        """,
        (order["id"],)
    )
    details = dict(cursor.fetchone())
    conn.close()

    phone_number_id, access_token = get_hostel_whatsapp_config(hostel_id)

    sent = send_whatsapp_message(
        phone_number_id, access_token, details["supplier_phone"], order["message"]
    )

    conn = get_connection()
    cursor = conn.cursor()

    if sent:
        cursor.execute(
            "UPDATE inventory_orders SET status = 'sent', sent_at = CURRENT_TIMESTAMP WHERE id = ?",
            (order["id"],)
        )
        conn.commit()
    conn.close()

    return {
        "order_id": order["id"],
        "sent": sent,
        "item_name": details["item_name"],
        "supplier_name": details["supplier_name"],
        "supplier_phone": details["supplier_phone"],
        "quantity": order["quantity"]
    }


def cancel_pending_supplier_order(hostel_id, order_id=None):
    order = get_pending_confirmation_order(hostel_id, order_id)
    if not order:
        raise ValueError("Nenhum pedido pendente de confirmacao encontrado.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE inventory_orders SET status = 'cancelled' WHERE id = ?",
        (order["id"],)
    )

    conn.commit()
    conn.close()

    return {"order_id": order["id"], "cancelled": True}


def confirm_supplier_order_received(hostel_id, item_name=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT io.*, i.name AS item_name, i.unit
        FROM inventory_orders io
        JOIN inventory_items i ON i.id = io.inventory_item_id
        WHERE io.hostel_id = ? AND io.status = 'sent'
        ORDER BY io.created_at DESC
        """,
        (hostel_id,)
    )

    candidates = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if item_name:
        query_norm = _normalize_text(item_name)
        candidates = [c for c in candidates if query_norm in _normalize_text(c["item_name"])]

    if not candidates:
        raise ValueError("Nenhum pedido enviado ao fornecedor esta aguardando confirmacao de recebimento.")
    if len(candidates) > 1:
        names = ", ".join(f"{c['item_name']} (pedido #{c['id']})" for c in candidates)
        raise ValueError(f"Mais de um pedido em aberto bate com essa descricao: {names}. Diga qual item recebeu.")

    order = candidates[0]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT quantity FROM inventory_items WHERE id = ?",
        (order["inventory_item_id"],)
    )
    current = cursor.fetchone()
    new_quantity = current["quantity"] + order["quantity"]

    cursor.execute(
        "UPDATE inventory_items SET quantity = ? WHERE id = ?",
        (new_quantity, order["inventory_item_id"])
    )
    cursor.execute(
        "UPDATE inventory_orders SET status = 'received', received_at = CURRENT_TIMESTAMP WHERE id = ?",
        (order["id"],)
    )

    conn.commit()
    conn.close()

    return {
        "order_id": order["id"],
        "item_name": order["item_name"],
        "quantity_added": order["quantity"],
        "new_quantity": new_quantity,
        "unit": order["unit"]
    }


# ===== Mensagem proativa da equipe pro hospede, via Ask StayFlow.
# Mesmo padrao propose->confirm->send do pedido a fornecedor. Ao
# enviar, a mensagem tambem entra na conversa normal do hospede (JSON
# do memory_service + SQL do message_service) - assim a IA de
# atendimento ja ve esse aviso quando ele responder. =====

def propose_guest_message(hostel_id, guest_name, message):
    matches = find_guest_by_name(hostel_id, guest_name)

    if not matches:
        raise ValueError(f"Nenhum hospede encontrado com o nome '{guest_name}'.")
    if len(matches) > 1:
        names = ", ".join(m["name"] for m in matches)
        raise ValueError(f"Mais de um hospede bate com '{guest_name}': {names}. Seja mais especifico.")

    guest = matches[0]

    if not guest["phone"]:
        raise ValueError(f"O hospede '{guest['name']}' nao tem telefone cadastrado.")

    message = (message or "").strip()
    if not message:
        raise ValueError("A mensagem nao pode ser vazia.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO guest_message_drafts (hostel_id, guest_id, message, status)
        VALUES (?, ?, ?, 'pending_confirmation')
        """,
        (hostel_id, guest["id"], message)
    )

    draft_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "draft_id": draft_id,
        "guest_name": guest["name"],
        "phone": guest["phone"],
        "message": message
    }


def get_pending_guest_message_draft(hostel_id, draft_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if draft_id:
        cursor.execute(
            """
            SELECT * FROM guest_message_drafts
            WHERE id = ? AND hostel_id = ? AND status = 'pending_confirmation'
            """,
            (draft_id, hostel_id)
        )
    else:
        cursor.execute(
            """
            SELECT * FROM guest_message_drafts
            WHERE hostel_id = ? AND status = 'pending_confirmation'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (hostel_id,)
        )

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


def cancel_guest_message_draft(hostel_id, draft_id=None):
    draft = get_pending_guest_message_draft(hostel_id, draft_id)
    if not draft:
        raise ValueError("Nenhuma mensagem pendente de confirmacao encontrada.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE guest_message_drafts SET status = 'cancelled' WHERE id = ?",
        (draft["id"],)
    )

    conn.commit()
    conn.close()

    return {"draft_id": draft["id"], "cancelled": True}


def send_guest_message(hostel_id, draft_id=None):
    from services.whatsapp_service import send_whatsapp_message
    from services.memory_service import save_message as save_memory_message
    from services.message_service import save_message_db

    draft = get_pending_guest_message_draft(hostel_id, draft_id)
    if not draft:
        raise ValueError("Nenhuma mensagem pendente de confirmacao encontrada.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, phone FROM guests WHERE id = ?",
        (draft["guest_id"],)
    )
    guest = cursor.fetchone()
    conn.close()

    if not guest:
        raise ValueError("Hospede nao encontrado.")

    phone_number_id, access_token = get_hostel_whatsapp_config(hostel_id)

    sent = send_whatsapp_message(phone_number_id, access_token, guest["phone"], draft["message"])

    if sent:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE guest_message_drafts SET status = 'sent', sent_at = CURRENT_TIMESTAMP WHERE id = ?",
            (draft["id"],)
        )
        conn.commit()
        conn.close()

        # entra na mesma conversa que a IA de atendimento usa, como se
        # a IA/equipe tivesse dito isso - assim a resposta do hospede
        # chega com esse aviso ja no contexto.
        save_memory_message(hostel_id, guest["phone"], "assistant", draft["message"])
        save_message_db(hostel_id, guest["phone"], "assistant", draft["message"])

    return {
        "draft_id": draft["id"],
        "sent": sent,
        "guest_name": guest["name"],
        "phone": guest["phone"]
    }


# ===== Extensao de reserva pedida pelo hospede na conversa com a IA
# de atendimento (nao pelo Ask StayFlow). Autonoma SO quando e uma
# extensao pura (mesmo quarto, mesma diaria) - qualquer coisa fora
# disso vira uma oportunidade de alta urgencia pra equipe decidir. =====

def _create_extension_opportunity(guest_id, description, next_action, estimated_value=0, urgency="high"):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO opportunities
        (guest_id, type, description, status, score, urgency, estimated_value, next_action)
        VALUES (?, 'extension', ?, 'open', 80, ?, ?, ?)
        """,
        (guest_id, description, urgency, estimated_value, next_action)
    )

    conn.commit()
    conn.close()


def attempt_extend_reservation(hostel_id, phone, new_checkout_date):
    import datetime

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM guests WHERE hostel_id = ? AND phone = ?",
        (hostel_id, phone)
    )
    guest = cursor.fetchone()

    if not guest:
        conn.close()
        raise ValueError("Hospede nao encontrado.")

    cursor.execute(
        """
        SELECT id, room_type, bed, checkin_date, checkout_date, amount, status
        FROM reservations
        WHERE hostel_id = ? AND guest_id = ? AND status != 'cancelled'
        ORDER BY checkout_date DESC
        LIMIT 1
        """,
        (hostel_id, guest["id"])
    )
    reservation = cursor.fetchone()
    conn.close()

    if not reservation:
        raise ValueError("Nenhuma reserva ativa encontrada pra esse hospede.")

    try:
        checkin = datetime.date.fromisoformat(reservation["checkin_date"])
        current_checkout = datetime.date.fromisoformat(reservation["checkout_date"])
        new_checkout = datetime.date.fromisoformat(new_checkout_date)
    except (ValueError, TypeError):
        raise ValueError("Data invalida - use o formato AAAA-MM-DD.")

    nights_current = (current_checkout - checkin).days
    nights_new = (new_checkout - checkin).days
    added_nights = nights_new - nights_current

    if added_nights <= 0:
        raise ValueError("A nova data de checkout precisa ser depois da atual.")

    rate_known = nights_current > 0 and (reservation["amount"] or 0) > 0

    if not rate_known:
        _create_extension_opportunity(
            guest["id"],
            description=f"Hospede pediu extensao ate {new_checkout_date}, mas nao foi possivel calcular a diaria com seguranca pra estender automaticamente.",
            next_action="Confirmar manualmente a extensao e o valor com o hospede.",
        )
        return {
            "auto_extended": False,
            "routed_to_staff": True,
            "reason": "Nao foi possivel calcular a diaria com seguranca."
        }

    rate_per_night = reservation["amount"] / nights_current
    added_amount = round(rate_per_night * added_nights, 2)
    new_amount = round(reservation["amount"] + added_amount, 2)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE reservations SET checkout_date = ?, amount = ? WHERE id = ?",
        (new_checkout_date, new_amount, reservation["id"])
    )

    conn.commit()
    conn.close()

    return {
        "auto_extended": True,
        "reservation_id": reservation["id"],
        "new_checkout_date": new_checkout_date,
        "added_nights": added_nights,
        "added_amount": added_amount,
        "new_amount": new_amount
    }


def flag_extension_for_approval(hostel_id, phone, note):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM guests WHERE hostel_id = ? AND phone = ?",
        (hostel_id, phone)
    )
    guest = cursor.fetchone()
    conn.close()

    if not guest:
        raise ValueError("Hospede nao encontrado.")

    _create_extension_opportunity(
        guest["id"],
        description=f"Hospede pediu extensao de estadia em condicoes diferentes: {note}",
        next_action="Revisar pedido de extensao manualmente com o hospede.",
    )

    return {"routed_to_staff": True}


# ===== Mapa de quartos/camas - cada hostel monta o proprio mapa.
# Status da cama e gravado de verdade (free/occupied/needs_cleaning),
# nao calculado pelas datas da reserva. Beliche = duas camas (bunk_top
# e bunk_bottom) com o mesmo bunk_group, pra desenhar como uma unidade
# so no mapa (metade vermelha/metade verde quando uma ta ocupada e a
# outra livre). =====

VALID_BED_KINDS = {"single", "bunk_top", "bunk_bottom"}


def create_room_category(hostel_id, name, capacity=None, price_per_night=None, description=None):
    """
    Modalidade de quarto (ex: "Standard Duplo", "Dormitorio Misto 6
    camas", "Suite Premium") - cada propriedade cria as suas proprias,
    nao existe lista fixa. Serve tanto pra hostel pequeno (poucas
    modalidades) quanto hotel/resort grande (dezenas delas).
    price_per_night e o que a IA de atendimento usa pra cotar preco
    real ao hospede - sem isso configurado, ela nao inventa um valor.
    """
    name = (name or "").strip()
    if not name:
        raise ValueError("O nome da modalidade e obrigatorio.")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO room_categories (hostel_id, name, capacity, price_per_night, description) VALUES (?, ?, ?, ?, ?)",
            (
                hostel_id, name, int(capacity) if capacity else None,
                float(price_per_night) if price_per_night else None,
                (description or "").strip() or None,
            )
        )
        category_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        conn.close()
        raise ValueError(f"Ja existe uma modalidade chamada '{name}' neste hostel.")

    conn.close()

    return category_id


def list_room_categories(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, capacity, price_per_night, description FROM room_categories WHERE hostel_id = ? ORDER BY name",
        (hostel_id,)
    )
    categories = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return categories


# Modalidades sugeridas por tipo de propriedade - so entram quando o
# hostel ainda nao tem NENHUMA modalidade cadastrada (nunca sobrescreve
# o que o admin ja criou na mao). "hostel_type" vem do mesmo campo que
# ja existe em Configuracoes > Empresa.
DEFAULT_ROOM_CATEGORIES_BY_HOSTEL_TYPE = {
    "hostel": [("Privado", 2), ("Compartilhado", 6)],
    "hotel": [("Standard", 2), ("Luxo", 2)],
    "pousada": [("Standard", 2), ("Luxo", 2)],
    "resort": [("Standard", 2), ("Luxo", 2)],
    "flat": [("Standard", 4)],
}


def apply_default_room_categories_if_needed(hostel_id, hostel_type):
    """
    Na primeira vez que o tipo de propriedade e definido (ou trocado
    pra um tipo reconhecido), cria as modalidades padrao daquele tipo -
    hostel ganha Privado/Compartilhado, hotel/pousada/resort ganham
    Standard/Luxo. So roda se o hostel ainda nao tem nenhuma modalidade
    cadastrada, pra nunca sobrescrever configuracao manual existente.
    Tipos customizados (digitados via "+ Novo tipo...") nao tem padrao
    e ficam com cadastro manual mesmo.
    """
    if not hostel_type:
        return

    if list_room_categories(hostel_id):
        return

    defaults = DEFAULT_ROOM_CATEGORIES_BY_HOSTEL_TYPE.get(hostel_type.strip().lower())
    if not defaults:
        return

    for name, capacity in defaults:
        try:
            create_room_category(hostel_id, name, capacity)
        except ValueError:
            pass


def delete_room_category(hostel_id, category_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE rooms SET category_id = NULL WHERE category_id = ? AND hostel_id = ?", (category_id, hostel_id))
    cursor.execute("DELETE FROM room_categories WHERE id = ? AND hostel_id = ?", (category_id, hostel_id))

    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if not deleted:
        raise ValueError("Modalidade nao encontrada.")


def _resolve_category_id(hostel_id, category_name):
    if not category_name:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM room_categories WHERE hostel_id = ? AND name = ?",
        (hostel_id, category_name)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"Modalidade '{category_name}' nao encontrada. Crie a modalidade primeiro.")

    return row["id"]


def create_room(hostel_id, name, category_name=None, floor=None):
    name = (name or "").strip()
    if not name:
        raise ValueError("O nome/numero do quarto e obrigatorio.")

    category_id = _resolve_category_id(hostel_id, category_name)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO rooms (hostel_id, name, category_id, floor) VALUES (?, ?, ?, ?)",
        (hostel_id, name, category_id, (floor or "").strip() or None)
    )

    room_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return room_id


def create_rooms_bulk(hostel_id, names, category_name=None, floor=None):
    """
    Cria varios quartos de uma vez com a mesma modalidade/andar - pensado
    pra hotel/resort grande, onde cadastrar quarto por quarto nao escala.
    names: lista de nomes/numeros de quarto (ex: ["201", "202", "203"]).
    """
    category_id = _resolve_category_id(hostel_id, category_name)

    if not names:
        raise ValueError("Informe pelo menos um nome/numero de quarto.")

    conn = get_connection()
    cursor = conn.cursor()

    room_ids = []
    for raw_name in names:
        name = (raw_name or "").strip()
        if not name:
            continue
        cursor.execute(
            "INSERT INTO rooms (hostel_id, name, category_id, floor) VALUES (?, ?, ?, ?)",
            (hostel_id, name, category_id, (floor or "").strip() or None)
        )
        room_ids.append(cursor.lastrowid)

    conn.commit()
    conn.close()

    return room_ids


def list_rooms(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT r.id, r.name, r.floor, r.created_at,
               rc.id AS category_id, rc.name AS category_name, rc.capacity
        FROM rooms r
        LEFT JOIN room_categories rc ON rc.id = r.category_id
        WHERE r.hostel_id = ?
        ORDER BY r.floor, r.name
        """,
        (hostel_id,)
    )
    rooms = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return rooms


def delete_room(hostel_id, room_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM beds WHERE room_id = ? AND hostel_id = ?", (room_id, hostel_id))
    cursor.execute("DELETE FROM rooms WHERE id = ? AND hostel_id = ?", (room_id, hostel_id))

    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()

    if not deleted:
        raise ValueError("Quarto nao encontrado.")


def create_bed(hostel_id, room_id, label, bed_kind="single", bunk_group=None):
    label = (label or "").strip()
    if not label:
        raise ValueError("O nome/numero da cama e obrigatorio.")
    if bed_kind not in VALID_BED_KINDS:
        raise ValueError(f"Tipo de cama invalido: {bed_kind}.")
    if bed_kind in ("bunk_top", "bunk_bottom") and not bunk_group:
        raise ValueError("Camas de beliche precisam de um bunk_group pra parear a de cima com a de baixo.")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM rooms WHERE id = ? AND hostel_id = ?",
        (room_id, hostel_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Quarto nao encontrado.")

    cursor.execute(
        """
        INSERT INTO beds (hostel_id, room_id, label, bed_kind, bunk_group, status)
        VALUES (?, ?, ?, ?, ?, 'free')
        """,
        (hostel_id, room_id, label, bed_kind, bunk_group)
    )

    bed_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return bed_id


def delete_bed(hostel_id, bed_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT status, label FROM beds WHERE id = ? AND hostel_id = ?", (bed_id, hostel_id))
    bed = cursor.fetchone()

    if not bed:
        conn.close()
        raise ValueError("Cama nao encontrada.")
    if bed["status"] == "occupied":
        conn.close()
        raise ValueError(f"A cama '{bed['label']}' esta ocupada agora - faca o check-out antes de excluir.")

    cursor.execute("DELETE FROM beds WHERE id = ? AND hostel_id = ?", (bed_id, hostel_id))

    conn.commit()
    conn.close()


def update_bed_label(hostel_id, bed_id, label=None, bed_kind=None, bunk_group=None):
    """
    label so muda o nome. bed_kind/bunk_group, quando passados, mudam se a
    cama e solteiro ou parte de um beliche (e com qual par) - pensado pra
    corrigir cadastro (ex: cama criada como solteiro que na verdade e a
    metade de baixo de um beliche), sem precisar excluir e recriar.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT label, bed_kind, bunk_group FROM beds WHERE id = ? AND hostel_id = ?", (bed_id, hostel_id))
    bed = cursor.fetchone()
    if not bed:
        conn.close()
        raise ValueError("Cama nao encontrada.")

    new_label = (label.strip() if label else "") or bed["label"]
    new_bed_kind = bed_kind if bed_kind is not None else bed["bed_kind"]
    new_bunk_group = bunk_group if bunk_group is not None else bed["bunk_group"]

    if new_bed_kind not in VALID_BED_KINDS:
        conn.close()
        raise ValueError(f"Tipo de cama invalido: {new_bed_kind}.")
    if new_bed_kind in ("bunk_top", "bunk_bottom") and not new_bunk_group:
        conn.close()
        raise ValueError("Camas de beliche precisam de um grupo pra parear a de cima com a de baixo.")
    if new_bed_kind == "single":
        new_bunk_group = None

    cursor.execute(
        "UPDATE beds SET label = ?, bed_kind = ?, bunk_group = ? WHERE id = ? AND hostel_id = ?",
        (new_label, new_bed_kind, new_bunk_group, bed_id, hostel_id)
    )

    conn.commit()
    conn.close()


def update_room(hostel_id, room_id, name=None, category_name=None, floor=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name, floor, category_id FROM rooms WHERE id = ? AND hostel_id = ?", (room_id, hostel_id))
    room = cursor.fetchone()
    if not room:
        conn.close()
        raise ValueError("Quarto nao encontrado.")

    new_name = (name.strip() if name else "") or room["name"]
    new_floor = (floor.strip() or None) if floor is not None else room["floor"]
    new_category_id = _resolve_category_id(hostel_id, category_name) if category_name is not None else room["category_id"]

    cursor.execute(
        "UPDATE rooms SET name = ?, category_id = ?, floor = ? WHERE id = ? AND hostel_id = ?",
        (new_name, new_category_id, new_floor, room_id, hostel_id)
    )

    conn.commit()
    conn.close()


def update_room_category(hostel_id, category_id, name=None, capacity=None, price_per_night=None, description=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, capacity, price_per_night, description FROM room_categories WHERE id = ? AND hostel_id = ?",
        (category_id, hostel_id)
    )
    category = cursor.fetchone()
    if not category:
        conn.close()
        raise ValueError("Modalidade nao encontrada.")

    new_name = (name.strip() if name else "") or category["name"]
    new_capacity = int(capacity) if capacity not in (None, "") else None
    new_price = float(price_per_night) if price_per_night not in (None, "") else None
    new_description = (description or "").strip() or None

    try:
        cursor.execute(
            "UPDATE room_categories SET name = ?, capacity = ?, price_per_night = ?, description = ? WHERE id = ? AND hostel_id = ?",
            (new_name, new_capacity, new_price, new_description, category_id, hostel_id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        conn.close()
        raise ValueError(f"Ja existe uma modalidade chamada '{new_name}' neste hostel.")

    conn.close()


def get_bed_map(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT r.id, r.name, r.floor, rc.name AS category_name
        FROM rooms r
        LEFT JOIN room_categories rc ON rc.id = r.category_id
        WHERE r.hostel_id = ?
        ORDER BY r.floor, r.name
        """,
        (hostel_id,)
    )
    rooms = [dict(row) for row in cursor.fetchall()]

    cursor.execute(
        """
        SELECT id, room_id, label, bed_kind, bunk_group, status
        FROM beds
        WHERE hostel_id = ?
        ORDER BY bunk_group, label
        """,
        (hostel_id,)
    )
    beds = [dict(row) for row in cursor.fetchall()]

    # pra cada cama ocupada/suja, tenta achar o hospede da reserva mais
    # recente ligada a ela - so pra exibicao no mapa, nao e fonte de
    # verdade de ocupacao (isso e o status da cama).
    occupied_bed_ids = [b["id"] for b in beds if b["status"] in ("occupied", "needs_cleaning")]
    guest_by_bed = {}
    if occupied_bed_ids:
        placeholders = ",".join("?" * len(occupied_bed_ids))
        cursor.execute(
            f"""
            SELECT bed_id, guest_name, MAX(id) as rid
            FROM reservations
            WHERE bed_id IN ({placeholders})
            GROUP BY bed_id
            """,
            occupied_bed_ids
        )
        for row in cursor.fetchall():
            guest_by_bed[row["bed_id"]] = row["guest_name"]

    # cama ocupada por morador de longa duracao (estadia ainda ativa,
    # sem checkout registrado) aparece roxa no mapa em vez de vermelha -
    # visualmente diferente de um hospede normal de passagem.
    long_term_bed_ids = set()
    if occupied_bed_ids:
        placeholders = ",".join("?" * len(occupied_bed_ids))
        cursor.execute(
            f"""
            SELECT DISTINCT bed_id FROM reservations
            WHERE bed_id IN ({placeholders}) AND stay_type = 'indefinite' AND checkout_date IS NULL
            """,
            occupied_bed_ids
        )
        long_term_bed_ids = {row["bed_id"] for row in cursor.fetchall()}

    # camas livres com uma reserva futura ja atribuida (soft hold da
    # reserva pelo WhatsApp ou pelo Ask StayFlow) aparecem como
    # "reserved" (azul) no mapa, em vez de "free" (verde) puro - so
    # visual, o status real da cama continua 'free' ate o check-in.
    free_bed_ids = [b["id"] for b in beds if b["status"] == "free"]
    reserved_bed_ids = set()
    if free_bed_ids:
        today = datetime.date.today().isoformat()
        placeholders = ",".join("?" * len(free_bed_ids))
        cursor.execute(
            f"""
            SELECT DISTINCT bed_id FROM reservations
            WHERE bed_id IN ({placeholders}) AND status != 'cancelled'
              AND checkout_date >= ? AND checked_out_at IS NULL
            """,
            free_bed_ids + [today]
        )
        reserved_bed_ids = {row["bed_id"] for row in cursor.fetchall()}

    conn.close()

    beds_by_room = {}
    for bed in beds:
        bed["guest_name"] = guest_by_bed.get(bed["id"])
        if bed["id"] in long_term_bed_ids:
            bed["display_status"] = "long_term"
        elif bed["id"] in reserved_bed_ids:
            bed["display_status"] = "reserved"
        else:
            bed["display_status"] = bed["status"]
        beds_by_room.setdefault(bed["room_id"], []).append(bed)

    for room in rooms:
        room["beds"] = beds_by_room.get(room["id"], [])

    return rooms


def set_bed_maintenance(hostel_id, bed_id, under_maintenance):
    """
    Marca/desmarca uma cama como em manutencao - so permite entrar em
    manutencao se ela estiver livre (nao tira hospede de cama ocupada);
    pra sair da manutencao, sempre volta pra 'free'.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT status, label FROM beds WHERE id = ? AND hostel_id = ?",
        (bed_id, hostel_id)
    )
    bed = cursor.fetchone()

    if not bed:
        conn.close()
        raise ValueError("Cama nao encontrada.")

    if under_maintenance and bed["status"] not in ("free", "maintenance"):
        conn.close()
        raise ValueError(f"A cama '{bed['label']}' precisa estar livre pra entrar em manutencao (status atual: {bed['status']}).")

    new_status = "maintenance" if under_maintenance else "free"
    cursor.execute("UPDATE beds SET status = ? WHERE id = ?", (new_status, bed_id))
    conn.commit()
    conn.close()

    return {"bed_id": bed_id, "status": new_status}


def get_cleaning_list(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT b.id AS bed_id, b.label, b.bed_kind, r.name AS room_name
        FROM beds b
        JOIN rooms r ON r.id = b.room_id
        WHERE b.hostel_id = ? AND b.status = 'needs_cleaning'
        ORDER BY r.name, b.label
        """,
        (hostel_id,)
    )
    result = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return result


def set_linen_kit(hostel_id, bed_kind, items):
    """items: lista de {"item_name": str, "quantity": int}"""
    if bed_kind not in VALID_BED_KINDS:
        raise ValueError(f"Tipo de cama invalido: {bed_kind}.")

    resolved_items = []
    for entry in items:
        matches = find_inventory_item_by_name(hostel_id, entry["item_name"])
        if not matches:
            raise ValueError(f"Nenhum item de estoque encontrado com o nome '{entry['item_name']}'.")
        if len(matches) > 1:
            names = ", ".join(m["name"] for m in matches)
            raise ValueError(f"Mais de um item bate com '{entry['item_name']}': {names}. Seja mais especifico.")
        resolved_items.append((matches[0]["id"], int(entry.get("quantity", 1))))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO linen_kits (hostel_id, bed_kind) VALUES (?, ?)",
        (hostel_id, bed_kind)
    )
    cursor.execute(
        "SELECT id FROM linen_kits WHERE hostel_id = ? AND bed_kind = ?",
        (hostel_id, bed_kind)
    )
    kit_id = cursor.fetchone()["id"]

    cursor.execute("DELETE FROM linen_kit_items WHERE linen_kit_id = ?", (kit_id,))

    for item_id, quantity in resolved_items:
        cursor.execute(
            "INSERT INTO linen_kit_items (linen_kit_id, inventory_item_id, quantity) VALUES (?, ?, ?)",
            (kit_id, item_id, quantity)
        )

    conn.commit()
    conn.close()

    return {"bed_kind": bed_kind, "items_count": len(resolved_items)}


def get_linen_kit(hostel_id, bed_kind):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT i.id AS inventory_item_id, i.name, lki.quantity
        FROM linen_kits lk
        JOIN linen_kit_items lki ON lki.linen_kit_id = lk.id
        JOIN inventory_items i ON i.id = lki.inventory_item_id
        WHERE lk.hostel_id = ? AND lk.bed_kind = ?
        """,
        (hostel_id, bed_kind)
    )
    items = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return items


def checkin_reservation_to_bed(hostel_id, reservation_id, bed_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, guest_name FROM reservations WHERE id = ? AND hostel_id = ? AND status != 'cancelled'",
        (reservation_id, hostel_id)
    )
    reservation = cursor.fetchone()
    if not reservation:
        conn.close()
        raise ValueError("Reserva nao encontrada ou cancelada.")

    cursor.execute(
        "SELECT id, status, label FROM beds WHERE id = ? AND hostel_id = ?",
        (bed_id, hostel_id)
    )
    bed = cursor.fetchone()
    if not bed:
        conn.close()
        raise ValueError("Cama nao encontrada.")
    if bed["status"] != "free":
        conn.close()
        raise ValueError(f"A cama '{bed['label']}' nao esta livre (status atual: {bed['status']}).")

    cursor.execute(
        "UPDATE reservations SET bed_id = ?, checked_in_at = CURRENT_TIMESTAMP WHERE id = ?",
        (bed_id, reservation_id)
    )
    cursor.execute("UPDATE beds SET status = 'occupied' WHERE id = ?", (bed_id,))

    conn.commit()
    conn.close()

    return {"reservation_id": reservation_id, "bed_id": bed_id, "bed_label": bed["label"], "guest_name": reservation["guest_name"]}


def checkout_reservation_bed(hostel_id, reservation_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT bed_id, guest_name FROM reservations WHERE id = ? AND hostel_id = ?",
        (reservation_id, hostel_id)
    )
    reservation = cursor.fetchone()
    if not reservation:
        conn.close()
        raise ValueError("Reserva nao encontrada.")
    if not reservation["bed_id"]:
        conn.close()
        raise ValueError("Essa reserva nao tem cama atribuida (nao foi feito check-in).")

    cursor.execute(
        "SELECT label FROM beds WHERE id = ?",
        (reservation["bed_id"],)
    )
    bed = cursor.fetchone()

    cursor.execute("UPDATE beds SET status = 'needs_cleaning' WHERE id = ?", (reservation["bed_id"],))
    cursor.execute("UPDATE reservations SET checked_out_at = CURRENT_TIMESTAMP WHERE id = ?", (reservation_id,))

    conn.commit()
    conn.close()

    return {
        "reservation_id": reservation_id,
        "bed_id": reservation["bed_id"],
        "bed_label": bed["label"] if bed else None,
        "guest_name": reservation["guest_name"]
    }


def mark_bed_cleaned(hostel_id, bed_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, label, bed_kind, status FROM beds WHERE id = ? AND hostel_id = ?",
        (bed_id, hostel_id)
    )
    bed = cursor.fetchone()
    conn.close()

    if not bed:
        raise ValueError("Cama nao encontrada.")
    if bed["status"] != "needs_cleaning":
        raise ValueError(f"A cama '{bed['label']}' nao esta na lista de limpeza (status atual: {bed['status']}).")

    kit_items = get_linen_kit(hostel_id, bed["bed_kind"])
    linen_used = []

    conn = get_connection()
    cursor = conn.cursor()

    for kit_item in kit_items:
        cursor.execute(
            "SELECT quantity, in_laundry_quantity FROM inventory_items WHERE id = ?",
            (kit_item["inventory_item_id"],)
        )
        current = cursor.fetchone()
        if not current:
            continue

        new_quantity = max(0, current["quantity"] - kit_item["quantity"])
        new_in_laundry = (current["in_laundry_quantity"] or 0) + kit_item["quantity"]

        cursor.execute(
            "UPDATE inventory_items SET quantity = ?, in_laundry_quantity = ? WHERE id = ?",
            (new_quantity, new_in_laundry, kit_item["inventory_item_id"])
        )
        linen_used.append({"item_name": kit_item["name"], "quantity": kit_item["quantity"]})

    cursor.execute("UPDATE beds SET status = 'free' WHERE id = ?", (bed_id,))

    conn.commit()
    conn.close()

    return {
        "bed_id": bed_id,
        "bed_label": bed["label"],
        "linen_used": linen_used,
        "linen_kit_configured": len(kit_items) > 0
    }


def return_items_from_laundry(hostel_id, item_name, quantity):
    matches = find_inventory_item_by_name(hostel_id, item_name)

    if not matches:
        raise ValueError(f"Nenhum item de estoque encontrado com o nome '{item_name}'.")
    if len(matches) > 1:
        names = ", ".join(m["name"] for m in matches)
        raise ValueError(f"Mais de um item bate com '{item_name}': {names}. Seja mais especifico.")

    item = matches[0]
    quantity = int(quantity)
    returned = min(quantity, item["in_laundry_quantity"] or 0)

    if returned <= 0:
        raise ValueError(f"'{item['name']}' nao tem nada registrado na lavanderia.")

    new_quantity = item["quantity"] + returned
    new_in_laundry = (item["in_laundry_quantity"] or 0) - returned

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE inventory_items SET quantity = ?, in_laundry_quantity = ? WHERE id = ?",
        (new_quantity, new_in_laundry, item["id"])
    )

    conn.commit()
    conn.close()

    return {
        "item_name": item["name"],
        "returned": returned,
        "requested": quantity,
        "new_quantity": new_quantity,
        "still_in_laundry": new_in_laundry
    }


# ===== Historico de conversa do Ask StayFlow (agente do painel,
# operador logado) - chave hostel_id+user_id, separado do
# memory_service (que e guest-scoped, hostel_id+phone). Guardado no
# SQL (nao no arquivo JSON) - evita repetir a duplicacao de fonte de
# verdade ja documentada como debito tecnico no memory_service. =====

ASK_HISTORY_WINDOW = 40


def save_ask_message(hostel_id, user_id, role, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ask_messages (hostel_id, user_id, role, content) VALUES (?, ?, ?, ?)",
        (hostel_id, user_id, role, content)
    )
    conn.commit()
    conn.close()


def get_ask_history(hostel_id, user_id, limit=ASK_HISTORY_WINDOW):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT role, content FROM ask_messages
        WHERE hostel_id = ? AND user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (hostel_id, user_id, limit)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return list(reversed(rows))


def save_hostel_whatsapp_config(hostel_id, phone_number_id, access_token):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE hostels
        SET whatsapp_phone_number_id = ?, whatsapp_access_token = ?
        WHERE id = ?
        """,
        (phone_number_id, access_token, hostel_id)
    )

    conn.commit()
    conn.close()


# ===== BEDS24 (channel manager, conta master de agencia) =====

def save_beds24_refresh_token(refresh_token_encrypted):
    """Chamado uma vez, na ativacao inicial (troca do invite code)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO beds24_master_account (id, refresh_token_encrypted, updated_at)
        VALUES (1, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            refresh_token_encrypted = excluded.refresh_token_encrypted,
            updated_at = CURRENT_TIMESTAMP
        """,
        (refresh_token_encrypted,)
    )
    conn.commit()
    conn.close()


def update_beds24_access_token(access_token_encrypted, expires_at):
    """Chamado toda vez que o access token (curta duracao) e renovado."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE beds24_master_account SET access_token_encrypted = ?, access_token_expires_at = ? WHERE id = 1",
        (access_token_encrypted, expires_at)
    )
    conn.commit()
    conn.close()


def get_beds24_master_credentials():
    """Devolve dict com refresh_token_encrypted/access_token_encrypted/access_token_expires_at, ou None se nunca configurado."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT refresh_token_encrypted, access_token_encrypted, access_token_expires_at FROM beds24_master_account WHERE id = 1"
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_hostel_beds24_property_id(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT beds24_property_id FROM hostels WHERE id = ?", (hostel_id,))
    row = cursor.fetchone()
    conn.close()
    return row["beds24_property_id"] if row else None


def save_hostel_beds24_property_id(hostel_id, property_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE hostels SET beds24_property_id = ? WHERE id = ?", (property_id, hostel_id))
    conn.commit()
    conn.close()


def get_hostel_id_by_beds24_property_id(property_id):
    """
    Resolve qual hostel e dono de uma sub-propriedade do Beds24 - usado
    pelo webhook (que manda o propertyId, nao um hostel_id do StayFlow),
    mesmo padrao de get_hostel_id_by_whatsapp_phone_number_id acima.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM hostels WHERE beds24_property_id = ?", (property_id,))
    row = cursor.fetchone()
    conn.close()
    return row["id"] if row else None


def get_channel_room_mappings(hostel_id):
    """Modalidades do hostel + o quarto do Beds24 mapeado (se ja configurado)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT rc.id AS room_category_id, rc.name AS category_name, crm.beds24_room_id
        FROM room_categories rc
        LEFT JOIN channel_room_mapping crm
          ON crm.room_category_id = rc.id AND crm.hostel_id = rc.hostel_id
        WHERE rc.hostel_id = ?
        ORDER BY rc.name
        """,
        (hostel_id,)
    )
    mappings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return mappings


def save_channel_room_mapping(hostel_id, room_category_id, beds24_room_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM room_categories WHERE id = ? AND hostel_id = ?",
        (room_category_id, hostel_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Modalidade nao encontrada.")

    cursor.execute(
        """
        INSERT INTO channel_room_mapping (hostel_id, room_category_id, beds24_room_id)
        VALUES (?, ?, ?)
        ON CONFLICT(hostel_id, room_category_id) DO UPDATE SET beds24_room_id = excluded.beds24_room_id
        """,
        (hostel_id, room_category_id, beds24_room_id)
    )
    conn.commit()
    conn.close()


def delete_channel_room_mapping(hostel_id, room_category_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM channel_room_mapping WHERE hostel_id = ? AND room_category_id = ?",
        (hostel_id, room_category_id)
    )
    conn.commit()
    conn.close()


def get_room_category_id_by_beds24_room_id(hostel_id, beds24_room_id):
    """Busca inversa - usada pelo webhook de entrada (Fase 3) pra saber em qual modalidade encaixar a reserva."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT room_category_id FROM channel_room_mapping WHERE hostel_id = ? AND beds24_room_id = ?",
        (hostel_id, str(beds24_room_id))
    )
    row = cursor.fetchone()
    conn.close()
    return row["room_category_id"] if row else None


def get_hostel_id_by_beds24_room_id(beds24_room_id):
    """
    Resolve qual hostel e dono de um quarto do Beds24 sem precisar
    saber o hostel_id de antemao - usado pelo webhook de entrada, que
    recebe um roomId mas nao necessariamente um propertyId explicito.
    Cada beds24_room_id so pode estar mapeado a um hostel por vez (o
    quarto pertence fisicamente a uma unica sub-propriedade).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT hostel_id FROM channel_room_mapping WHERE beds24_room_id = ? LIMIT 1",
        (str(beds24_room_id),)
    )
    row = cursor.fetchone()
    conn.close()
    return row["hostel_id"] if row else None


def try_claim_webhook_event(beds24_booking_id, hostel_id, event_type, payload_json):
    """
    Registra esse evento de webhook como "em processamento" - se o
    Beds24 reentregar o mesmo evento (rede lenta, timeout do lado
    deles), a segunda tentativa esbarra na constraint UNIQUE e essa
    funcao devolve False, evitando duplicar a reserva. Devolve True
    apenas na primeira vez (deve seguir em frente com o processamento).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO channel_webhook_events
            (beds24_booking_id, hostel_id, event_type, payload_json, status)
            VALUES (?, ?, ?, ?, 'processing')
            """,
            (str(beds24_booking_id), hostel_id, event_type, payload_json)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        conn.rollback()
        return False
    finally:
        conn.close()


def finalize_webhook_event(beds24_booking_id, status, error_message=None, reservation_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE channel_webhook_events
        SET status = ?, error_message = ?, reservation_id = ?
        WHERE beds24_booking_id = ?
        """,
        (status, error_message, reservation_id, str(beds24_booking_id))
    )
    conn.commit()
    conn.close()


def create_reservation_from_channel(hostel_id, room_category_id, guest_name, guest_phone,
                                      checkin_date, checkout_date, external_booking_id, source, amount=0):
    """
    Cria uma reserva a partir de uma notificacao de reserva vinda de um
    channel manager (Beds24) - Booking.com/Airbnb/Hostelworld. Diferente
    do fluxo do WhatsApp (que recusa reservar se nao houver cama livre),
    aqui a reserva ja e um compromisso confirmado do lado da OTA - nao
    da pra simplesmente recusar por falta de cama. Tenta atribuir uma
    cama disponivel de verdade (com a mesma trava contra corrida da
    Fase 1); se nao houver nenhuma livre/cadastrada, cria a reserva
    mesmo assim sem cama especifica, pra equipe atribuir manualmente -
    perder o registro da reserva seria pior que deixar sem cama.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, price_per_night FROM room_categories WHERE id = ? AND hostel_id = ?",
        (room_category_id, hostel_id)
    )
    category = cursor.fetchone()
    conn.close()
    if not category:
        raise ValueError("Modalidade nao encontrada.")

    category_name = category["name"]
    checkin_date = (checkin_date or "").strip()
    checkout_date = (checkout_date or "").strip()

    nights = 0
    try:
        nights = max((datetime.date.fromisoformat(checkout_date) - datetime.date.fromisoformat(checkin_date)).days, 0)
    except (ValueError, TypeError):
        pass
    if not amount and category["price_per_night"]:
        amount = round(category["price_per_night"] * nights, 2)

    guest_phone = (guest_phone or "").strip()
    guest_id = None
    if guest_phone:
        guest_id = get_or_create_guest(hostel_id, guest_phone)
        if guest_name:
            update_guest_name(hostel_id, guest_phone, guest_name)

    def _insert(cursor, bed_id):
        cursor.execute(
            """
            INSERT INTO reservations
            (hostel_id, guest_id, guest_name, room_type, bed, bed_id, checkin_date,
             checkout_date, source, amount, status, external_booking_id)
            VALUES (?, ?, ?, ?, '', ?, ?, ?, ?, ?, 'confirmed', ?)
            """,
            (hostel_id, guest_id, guest_name, category_name, bed_id,
             checkin_date, checkout_date, source, amount, str(external_booking_id))
        )
        return cursor.lastrowid

    available = find_available_beds(hostel_id, category_name, checkin_date, checkout_date)
    if available:
        bed_id = available[0]["id"]
        return reservar_cama_com_trava(hostel_id, bed_id, checkin_date, checkout_date, lambda cursor: _insert(cursor, bed_id))

    conn = get_connection()
    cursor = conn.cursor()
    reservation_id = _insert(cursor, None)
    conn.commit()
    conn.close()
    return reservation_id


def get_reservation_id_by_external_booking_id(hostel_id, external_booking_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM reservations WHERE hostel_id = ? AND external_booking_id = ?",
        (hostel_id, str(external_booking_id))
    )
    row = cursor.fetchone()
    conn.close()
    return row["id"] if row else None


def update_reservation_from_channel(hostel_id, external_booking_id, guest_name, guest_phone,
                                      checkin_date, checkout_date, status, amount=None):
    """
    Atualiza uma reserva ja criada anteriormente a partir de um evento
    de webhook do Beds24 com o mesmo external_booking_id. Confirmado
    testando ao vivo: a Beds24 manda um webhook novo a CADA alteracao
    na reserva, nao so na criacao (o mesmo booking chegou duas vezes,
    a segunda com nome/telefone do hospede preenchidos que a primeira
    nao tinha) - por isso reserva repetida vira atualizacao, nao e
    simplesmente ignorada como duplicata.

    amount vem sempre do proprio canal (o preco real cobrado naquela
    plataforma, que pode ser diferente do preco cadastrado na
    modalidade do StayFlow - a OTA pode dar desconto) - None mantem o
    valor ja gravado, sem sobrescrever com algo que o payload nao trouxe.

    Nao reatribui cama nem revalida disponibilidade nesta rodada -
    so atualiza os campos direto. Fica pra uma proxima rodada se
    mudanca de data em reserva ja com cama atribuida se mostrar um
    problema real na pratica.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM reservations WHERE hostel_id = ? AND external_booking_id = ?",
        (hostel_id, str(external_booking_id))
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    reservation_status = "cancelled" if "cancel" in (status or "").lower() else "confirmed"

    if amount is not None:
        cursor.execute(
            """
            UPDATE reservations
            SET guest_name = ?, checkin_date = ?, checkout_date = ?, status = ?, amount = ?
            WHERE id = ?
            """,
            (guest_name, checkin_date, checkout_date, reservation_status, float(amount), row["id"])
        )
    else:
        cursor.execute(
            """
            UPDATE reservations
            SET guest_name = ?, checkin_date = ?, checkout_date = ?, status = ?
            WHERE id = ?
            """,
            (guest_name, checkin_date, checkout_date, reservation_status, row["id"])
        )
    conn.commit()
    conn.close()

    guest_phone = (guest_phone or "").strip()
    if guest_phone:
        guest_id = get_or_create_guest(hostel_id, guest_phone)
        if guest_name:
            update_guest_name(hostel_id, guest_phone, guest_name)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE reservations SET guest_id = ? WHERE id = ?", (guest_id, row["id"]))
        conn.commit()
        conn.close()

    return row["id"]


def get_quick_replies(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, hostel_id, text, created_at FROM quick_replies WHERE hostel_id = ? ORDER BY created_at DESC",
        (hostel_id,)
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def create_quick_reply(hostel_id, text):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO quick_replies (hostel_id, text) VALUES (?, ?)",
        (hostel_id, text)
    )
    quick_reply_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return quick_reply_id


def delete_quick_reply(quick_reply_id, hostel_id):
    """
    Apaga so se a resposta rapida pertencer ao hostel informado -
    evita que alguem apague (por id adivinhado) a resposta rapida de
    outro hostel.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM quick_replies WHERE id = ? AND hostel_id = ?",
        (quick_reply_id, hostel_id)
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_hostel_id_by_number(whatsapp_number):
    """
    Resolve qual hostel é dono de um número de WhatsApp — usado pelo
    webhook (routes/chat.py), que não tem sessão de usuário logado.
    Depende da coluna hostels.phone estar preenchida com o número
    oficial de WhatsApp de cada hostel.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM hostels WHERE phone = ?",
        (whatsapp_number,)
    )

    row = cursor.fetchone()
    conn.close()

    return row["id"] if row else None


if __name__ == "__main__":
    create_database()
    print("Banco de dados criado/atualizado com sucesso!")
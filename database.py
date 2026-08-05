import os
import secrets
import sqlite3
import unicodedata
import datetime

from utils.permissions import ALL_PERMISSIONS_STR

DATABASE = os.path.join(os.getenv("STAYFLOW_DATA_DIR", "."), "stayflow.db")

# reservations.source cujo valor significa "essa reserva nasceu dentro
# do proprio StayFlow" (manual, ou qualquer canal de chat que a IA
# atende) - distingue de reserva vinda de um canal externo/OTA (ex:
# Beds24), usado nos dois lugares que precisam saber se e seguro
# sincronizar pro Beds24 sem risco de ecoar de volta uma reserva que
# JA veio de la.
STAYFLOW_NATIVE_SOURCES = ("manual", "whatsapp", "messenger", "instagram")


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


# As 14 chaves que existiam antes das 5 novas de Sessao 9 (kitchen,
# maintenance, patrimonial_security, parking, scheduling) - mesmo
# raciocinio de _LEGACY_FULL_ACCESS_PERMISSIONS acima, fixo aqui de
# proposito (nao le de utils.permissions.ALL_PERMISSIONS, que ja inclui
# as chaves novas e nao serviria pra detectar quem era "acesso total"
# no esquema anterior a esta sessao).
_PRE_SESSION9_FULL_ACCESS_PERMISSIONS = {
    "dashboard", "chats", "opportunities", "reservations", "operations",
    "guests", "finance", "reports", "inventory", "revenue", "settings",
    "team", "security", "billing",
}

_SESSION9_NEW_PERMISSIONS = {"kitchen", "maintenance", "patrimonial_security", "parking", "scheduling"}


def _backfill_operational_modules_for_full_access_roles(cursor):
    """
    Mesmo problema de sempre (ver _backfill_security_billing_for_full_
    access_roles): role criada antes desta sessao guarda string
    congelada, entao os 5 modulos operacionais novos (cozinha,
    manutencao, seguranca patrimonial, estacionamento, escala) nao
    chegam sozinhos em quem ja tinha acesso total no esquema anterior.
    """
    cursor.execute("SELECT id, permissions FROM roles")
    roles = cursor.fetchall()

    for role in roles:
        current = set(p for p in (role["permissions"] or "").split(",") if p)

        if not _PRE_SESSION9_FULL_ACCESS_PERMISSIONS.issubset(current):
            continue

        if _SESSION9_NEW_PERMISSIONS.issubset(current):
            continue

        updated = current | _SESSION9_NEW_PERMISSIONS
        cursor.execute(
            "UPDATE roles SET permissions = ? WHERE id = ?",
            (",".join(sorted(updated)), role["id"])
        )


def _vehicles_table_needs_migration(cursor):
    """
    Detecta se vehicles ainda tem o schema antigo, com guest_id
    NOT NULL (antes de permitir manobrista registrar carro de quem
    chegou na hora, sem hospede formal cadastrado ainda).
    """
    cursor.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='vehicles'"
    )
    row = cursor.fetchone()

    if row is None:
        return False

    table_sql = (row["sql"] or "").replace(" ", "").replace("\n", "")
    return "guest_idINTEGERNOTNULL" in table_sql


def _migrate_vehicles_guest_id_nullable(cursor):
    """
    Reconstroi vehicles com guest_id opcional (e guest_name novo, pro
    caso sem hospede formal) - mesmo padrao ja usado pra
    users/guests em migracoes anteriores. Preserva todos os dados
    existentes.
    """
    cursor.execute("ALTER TABLE vehicles RENAME TO vehicles_old")

    cursor.execute("""
    CREATE TABLE vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        guest_id INTEGER,
        guest_name TEXT,
        reservation_id INTEGER,
        plate TEXT,
        model TEXT,
        color TEXT,
        spot_number TEXT,
        service_type TEXT NOT NULL DEFAULT 'autoatendimento',
        checked_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        checked_out_at TIMESTAMP
    )
    """)

    cursor.execute("""
        INSERT INTO vehicles (
            id, hostel_id, guest_id, reservation_id, plate, model, color,
            spot_number, service_type, checked_in_at, checked_out_at
        )
        SELECT
            id, hostel_id, guest_id, reservation_id, plate, model, color,
            spot_number, service_type, checked_in_at, checked_out_at
        FROM vehicles_old
    """)

    cursor.execute("DROP TABLE vehicles_old")


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

    # Webhook de saida generico (Fase 6): cliente que ja tem sistema
    # proprio e usa o StayFlow so pra atendimento/IA, sem adotar o mapa
    # de quartos como fonte de verdade, cadastra uma URL propria aqui.
    # Toda reserva criada/alterada/cancelada dispara um POST assinado
    # (outbound_webhook_secret, gerado na primeira vez que a URL e
    # salva) pra essa URL - ver dispatch_reservation_webhook. Nao e
    # segredo do mesmo nivel do token master do Beds24 (decisao 3 do
    # plano): se vazar, so permite forjar eventos NO SISTEMA DO
    # CLIENTE, nao expoe nada do StayFlow - por isso fica em texto
    # puro, mesmo padrao do token de WhatsApp.
    add_column_if_not_exists(cursor, "hostels", "outbound_webhook_url", "TEXT")
    add_column_if_not_exists(cursor, "hostels", "outbound_webhook_secret", "TEXT")

    # Integracao com Instagram Direct e Messenger (Facebook) - cada
    # hostel conecta a propria Pagina (Messenger) e a propria conta
    # Instagram (Instagram Login, sem depender da Pagina) via OAuth,
    # ou cola a credencial manualmente (mesmo par de colunas recebe o
    # valor nao importa qual dos dois caminhos foi usado). *_oauth_state
    # e so o valor anti-CSRF do fluxo, descartavel apos o callback -
    # nao e credencial de verdade.
    add_column_if_not_exists(cursor, "hostels", "facebook_page_id", "TEXT")
    add_column_if_not_exists(cursor, "hostels", "facebook_page_access_token", "TEXT")
    add_column_if_not_exists(cursor, "hostels", "facebook_oauth_state", "TEXT")
    add_column_if_not_exists(cursor, "hostels", "instagram_business_id", "TEXT")
    add_column_if_not_exists(cursor, "hostels", "instagram_access_token", "TEXT")
    add_column_if_not_exists(cursor, "hostels", "instagram_oauth_state", "TEXT")

    # WhatsApp ja tinha whatsapp_phone_number_id/whatsapp_access_token
    # (colunas acima, so config manual) - ganha tambem um fluxo de
    # conexao automatica (WhatsApp Embedded Signup), que grava nas
    # MESMAS duas colunas; so o state anti-CSRF do OAuth e novo aqui.
    add_column_if_not_exists(cursor, "hostels", "whatsapp_oauth_state", "TEXT")

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
    _backfill_operational_modules_for_full_access_roles(cursor)

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

    # Identidade externa de um hospede por canal (Instagram/Messenger/
    # WhatsApp) - modelo de identidade multi-canal de verdade, em vez de
    # forcar o id externo (IGSID/PSID) dentro da coluna guests.phone
    # (que continua existindo so pra numero de telefone real). guest_id
    # e a identidade canonica do lado do StayFlow; um mesmo hospede
    # podera futuramente ter mais de uma linha aqui (um por canal que
    # ele usou) - hoje cada canal ainda cria um guest_id proprio na
    # primeira mensagem, mesclar identidades fica pra uma rodada futura
    # (precisaria de UI de "mesclar hospede"). UNIQUE(hostel_id, channel,
    # external_id) e o que garante idempotencia: a segunda mensagem do
    # mesmo IGSID/PSID acha a MESMA linha em vez de criar hospede novo.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guest_channel_identities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        guest_id INTEGER NOT NULL,
        channel TEXT NOT NULL,
        external_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(hostel_id, channel, external_id)
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

    # Pagamento em dinheiro numa moeda estrangeira (ex: hospede paga em
    # dolar/real vivo num hostel que opera em peso argentino) - guarda o
    # valor recebido na moeda estrangeira E a cotacao usada, pra local_amount
    # (o que efetivamente entrou convertido pra moeda do hostel) poder ser
    # somado ao restante da receita real sem perder o registro de origem.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS currency_exchanges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        description TEXT,
        foreign_currency TEXT NOT NULL,
        foreign_amount REAL NOT NULL,
        exchange_rate REAL NOT NULL,
        local_amount REAL NOT NULL,
        market_rate REAL,
        profit REAL NOT NULL DEFAULT 0,
        operator_user_id INTEGER,
        operator_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # Colunas adicionadas depois da criacao original da tabela (cambio
    # como operacao de casa de cambio de verdade: cotacao atual de
    # mercado vs cotacao usada com o hospede, lucro da diferenca, e quem
    # operou) - add_column_if_not_exists cobre tanto banco novo quanto
    # banco que ja tinha currency_exchanges sem essas colunas.
    add_column_if_not_exists(cursor, "currency_exchanges", "market_rate", "REAL")
    add_column_if_not_exists(cursor, "currency_exchanges", "profit", "REAL NOT NULL DEFAULT 0")
    add_column_if_not_exists(cursor, "currency_exchanges", "operator_user_id", "INTEGER")
    add_column_if_not_exists(cursor, "currency_exchanges", "operator_name", "TEXT")
    add_column_if_not_exists(cursor, "currency_exchanges", "guest_id", "INTEGER")

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

    # ===== Camada compartilhada: Cozinha/Manutencao/Seguranca
    # Patrimonial/Estacionamento (Sessao 9) =====
    #
    # As quatro areas operacionais novas (cozinha, manutencao, seguranca
    # patrimonial, estacionamento) compartilham o mesmo miolo: alguem
    # relata algo (hospede ou equipe), vira um "chamado" com dono e
    # status, e a pessoa certa de plantao naquele setor e notificada -
    # em vez de reconstruir essa logica 4 vezes, ela existe uma vez
    # (sections/staff_shifts/tickets/ticket_notifications) e cada area
    # so acrescenta a tabela de detalhe especifica dela.

    # Substitui "texto livre" de setor/area (ex: "Salao A" digitado
    # diferente em dias diferentes quebraria a busca de "quem esta de
    # plantao aqui") por um cadastro real, com FK.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # A grade de escala - quem cobre qual setor, quando. Fonte de
    # verdade unica de "quem esta de plantao agora", consultada por
    # todo o resto (cozinha, manutencao, seguranca, estacionamento) na
    # hora de decidir quem notificar.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staff_shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        membership_id INTEGER NOT NULL,
        department TEXT NOT NULL,
        section_id INTEGER,
        shift_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'scheduled',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Troca/cobertura de turno - separado de staff_shifts de proposito,
    # pra manter a grade limpa (so "quem cobre o que, quando") e isolar
    # o processo de pedir/aceitar substituicao, com trilha de quem
    # pediu e quem assumiu.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shift_coverage_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shift_id INTEGER NOT NULL,
        requested_by_membership_id INTEGER NOT NULL,
        covering_membership_id INTEGER,
        status TEXT NOT NULL DEFAULT 'pending',
        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP
    )
    """)

    # O "chamado" generico - pedido de cozinha, chamado de manutencao e
    # incidente de seguranca sao so "tipos" dele (cada um com sua
    # tabela de detalhe especifica, ligada por ticket_id). Sem coluna
    # de prioridade fixa de proposito: a prioridade efetiva (base_urgency
    # + tempo de espera + peso da categoria) e calculada na hora de
    # ordenar/consultar, nao gravada uma vez e esquecida - um chamado
    # "medio" parado ha 3 dias tem que furar fila na frente de um
    # "medio" aberto ha 3 minutos, e isso so funciona se for recalculado
    # a cada consulta.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        reported_by_guest_id INTEGER,
        reported_by_membership_id INTEGER,
        location TEXT,
        description TEXT,
        base_urgency TEXT NOT NULL DEFAULT 'normal',
        status TEXT NOT NULL DEFAULT 'open',
        assigned_to_membership_id INTEGER,
        channel TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        assigned_at TIMESTAMP,
        resolved_at TIMESTAMP,
        resolution_notes TEXT
    )
    """)

    # Log de notificacao - sem isso nao da pra provar (nem ajustar)
    # que a pessoa certa foi avisada e quando, o que e o ponto central
    # de nao deixar isso virar um monte de notificacao solta.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ticket_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER NOT NULL,
        membership_id INTEGER NOT NULL,
        notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        channel TEXT,
        acknowledged_at TIMESTAMP
    )
    """)

    # ===== Cozinha / Room Service =====

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL DEFAULT 0,
        station TEXT NOT NULL DEFAULT 'cozinha',
        active INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # A "receita" - liga item do cardapio ao estoque ja existente
    # (inventory), pra dar baixa automatica sem precisar de nenhum
    # controle de estoque exclusivo da cozinha.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS menu_item_ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        menu_item_id INTEGER NOT NULL,
        inventory_item_id INTEGER NOT NULL,
        quantity REAL NOT NULL DEFAULT 1
    )
    """)

    # Status por ITEM, nao so pelo pedido inteiro - bebida sai antes de
    # comida num servico de mesa de verdade; o status do ticket geral e
    # derivado destes (ver get_kitchen_order_status).
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kitchen_order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER NOT NULL,
        menu_item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        unit_price REAL NOT NULL DEFAULT 0,
        notes TEXT,
        status TEXT NOT NULL DEFAULT 'pending'
    )
    """)

    # ===== Manutencao =====

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS maintenance_issues (
        ticket_id INTEGER PRIMARY KEY,
        category TEXT,
        guest_reported_urgency TEXT
    )
    """)

    # ===== Seguranca Patrimonial =====

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS security_incidents (
        ticket_id INTEGER PRIMARY KEY,
        incident_type TEXT,
        reported_via TEXT
    )
    """)

    # Um hotel pode ter mais de um sistema (camera de um fornecedor,
    # controle de acesso de outro, telefonia de um terceiro) - uma
    # linha POR CAPACIDADE, nao uma so pro hotel inteiro, exatamente
    # pra nao travar em "so funciona se o hotel tiver X sistema
    # especifico". provider='manual_fallback' (sem api) e o padrao
    # seguro de lancamento - so vira 'api' quando o hotel confirmar de
    # verdade o sistema que usa.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hostel_system_integrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        capability TEXT NOT NULL,
        provider TEXT NOT NULL DEFAULT 'manual_fallback',
        config TEXT,
        fallback_phone_number TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(hostel_id, capability)
    )
    """)

    # ===== Estacionamento =====

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        guest_id INTEGER,
        guest_name TEXT,
        reservation_id INTEGER,
        plate TEXT,
        model TEXT,
        color TEXT,
        spot_number TEXT,
        service_type TEXT NOT NULL DEFAULT 'autoatendimento',
        checked_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        checked_out_at TIMESTAMP
    )
    """)

    # guest_id agora e opcional - manobrista as vezes registra o carro
    # de alguem que chegou na hora, sem reserva/hospede formal ainda no
    # sistema (ver check_in_vehicle: guest_name cobre esse caso). Se a
    # tabela ja existia com guest_id NOT NULL (antes desta mudanca),
    # reconstroi pra tornar opcional - mesmo padrao ja usado pra
    # users/guests em migracoes anteriores.
    if _vehicles_table_needs_migration(cursor):
        _migrate_vehicles_guest_id_nullable(cursor)

    # Cobranca de estacionamento independente do tipo de servico
    # (manobrista/autoatendimento e cobranca sao dois eixos separados) -
    # preparado pros 3 modelos vistos no mercado: incluso pra todo
    # mundo, cobrado a parte, ou gratis so por categoria de quarto.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hostel_parking_settings (
        hostel_id INTEGER PRIMARY KEY,
        pricing_model TEXT NOT NULL DEFAULT 'incluso',
        daily_rate REAL DEFAULT 0,
        included_for_categories TEXT
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


def create_guest_without_phone(hostel_id, name):
    """
    Cria um hospede so com nome, sem telefone (reserva manual/estadia
    de longa duracao cadastrada sem numero) - sempre INSERT novo, nunca
    reaproveita um hospede existente. Sem telefone nao ha chave nenhuma
    pra saber que duas reservas "sem telefone" sao a mesma pessoa
    (phone=NULL nao serve de chave de dedup, diferente de
    get_or_create_guest); cada uma vira um hospede proprio.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO guests (hostel_id, phone, name) VALUES (?, NULL, ?)",
        (hostel_id, name)
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


def save_guest_date_of_birth_by_id(guest_id, date_of_birth):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE guests SET date_of_birth = ? WHERE id = ?", (date_of_birth, guest_id))
    conn.commit()
    conn.close()


def save_guest_nationality_by_id(guest_id, nationality):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE guests SET nationality = ? WHERE id = ?", (nationality, guest_id))
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


# ===== Equivalentes por guest_id das quatro funcoes acima - usadas pelo
# pipeline de mensagem (routes/chat.py) pra canais sem telefone de
# verdade (Instagram/Messenger), onde guests.phone fica NULL e a busca
# "WHERE phone = ?" nunca acharia a linha certa. WhatsApp tambem vai
# passar a usar essas versoes (guest_id ja resolvido uma vez no topo de
# process_incoming_message), evitando manter dois caminhos de consulta
# divergentes pro mesmo dado. =====

def is_guest_ai_paused_by_id(guest_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ai_paused FROM guests WHERE id = ?", (guest_id,))
    row = cursor.fetchone()
    conn.close()
    return bool(row["ai_paused"]) if row else False


def get_guest_language_by_id(guest_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM guests WHERE id = ?", (guest_id,))
    row = cursor.fetchone()
    conn.close()
    return row["language"] if row and row["language"] else None


def update_guest_name_by_id(guest_id, name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE guests SET name = ? WHERE id = ?", (name, guest_id))
    conn.commit()
    conn.close()


def get_guest_name_by_id(guest_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM guests WHERE id = ?", (guest_id,))
    row = cursor.fetchone()
    conn.close()
    return row["name"] if row and row["name"] else None


def update_guest_language_by_id(guest_id, language):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE guests SET language = ? WHERE id = ?", (language, guest_id))
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


def save_hostel_phone(hostel_id, phone):
    """
    Numero de WhatsApp oficial do hostel, em formato legivel (ex:
    "+5493883154375") - diferente de whatsapp_phone_number_id (o ID
    interno da Meta, usado so pra autenticar chamadas de API). Usado
    pra: (a) resolver o hostel no endpoint de teste manual
    (get_hostel_id_by_number), e (b) a IA sugerir esse numero pro
    hospede em canais que nao sao WhatsApp (Messenger/Instagram),
    como alternativa de contato.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE hostels SET phone = ? WHERE id = ?", (phone, hostel_id))
    conn.commit()
    conn.close()


def get_hostel_currency(hostel_id):
    """Moeda configurada em Configuracoes > Empresa. USD por padrao (mesmo default do frontend) se a hospedagem ainda nao configurou nada."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT currency FROM settings WHERE hostel_id = ?", (hostel_id,))
    row = cursor.fetchone()
    conn.close()
    return (row["currency"] if row and row["currency"] else "USD")


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


def count_recent_failed_logins(email, minutes=15):
    """
    Quantas tentativas de login FALHADAS existem pra esse email nos
    ultimos N minutos - usado pelo /login pra travar por forca bruta.
    Conta por email tentado (nao por user_id), entao cobre tanto
    contas reais quanto tentativas contra email que nem existe
    (log_login_attempt ja grava o email attempted nos dois casos).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) AS total FROM login_attempts
        WHERE email_attempted = ? AND success = 0
          AND created_at >= datetime('now', ?)
        """,
        (email, f"-{minutes} minutes")
    )
    total = cursor.fetchone()["total"]
    conn.close()
    return total


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


def get_or_create_conversation(guest_id, channel="api"):
    """
    channel so e usado na CRIACAO de uma conversa nova - uma conversa
    ja existente nunca tem o canal reescrito aqui (evita apagar o
    canal real gravado por quem criou a conversa, se essa funcao for
    chamada de novo por outro caminho). Default 'api' preserva o
    comportamento de todo chamador antigo que nunca passava channel.
    """
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
            (guest_id, channel)
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


def save_message_db_for_guest(guest_id, sender, message, channel="api"):
    """
    Mesmo resultado de save_message_db, mas recebe guest_id ja
    resolvido em vez de telefone - usada pelo pipeline de mensagem
    (routes/chat.py) pra qualquer canal, ja que Instagram/Messenger nao
    tem telefone de verdade pra resolver guest_id de novo aqui. De
    quebra, e a unica das duas que realmente grava o canal certo numa
    conversa nova (save_message_db, usada pelo WhatsApp legado, continua
    gravando 'api' - nao mexido pra nao arriscar regressao em codigo ja
    em producao).
    """
    conversation_id = get_or_create_conversation(guest_id, channel=channel)

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


def save_hostel_whatsapp_oauth_state(hostel_id, state):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE hostels SET whatsapp_oauth_state = ? WHERE id = ?", (state, hostel_id))
    conn.commit()
    conn.close()


def consume_hostel_whatsapp_oauth_state(hostel_id, state):
    """
    Confere o state anti-CSRF do callback contra o que foi salvo no
    connect, e ja limpa (nunca reutilizavel, mesmo que o callback seja
    chamado de novo por engano). Retorna True/False.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT whatsapp_oauth_state FROM hostels WHERE id = ?", (hostel_id,))
    row = cursor.fetchone()
    valid = bool(row and row["whatsapp_oauth_state"] and row["whatsapp_oauth_state"] == state)
    cursor.execute("UPDATE hostels SET whatsapp_oauth_state = NULL WHERE id = ?", (hostel_id,))
    conn.commit()
    conn.close()
    return valid


# ===== FACEBOOK MESSENGER =====

def get_hostel_id_by_facebook_page_id(page_id):
    """Resolve qual hostel e dono de uma Pagina do Facebook - usado pelo webhook."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM hostels WHERE facebook_page_id = ?", (page_id,))
    row = cursor.fetchone()
    conn.close()
    return row["id"] if row else None


def get_hostel_facebook_config(hostel_id):
    """Retorna (page_id, access_token) do hostel, ou (None, None)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT facebook_page_id, facebook_page_access_token FROM hostels WHERE id = ?",
        (hostel_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None, None
    return row["facebook_page_id"], row["facebook_page_access_token"]


def save_hostel_facebook_config(hostel_id, page_id, access_token):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE hostels SET facebook_page_id = ?, facebook_page_access_token = ? WHERE id = ?",
        (page_id, access_token, hostel_id)
    )
    conn.commit()
    conn.close()


def clear_hostel_facebook_config(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE hostels SET facebook_page_id = NULL, facebook_page_access_token = NULL WHERE id = ?",
        (hostel_id,)
    )
    conn.commit()
    conn.close()


def save_hostel_facebook_oauth_state(hostel_id, state):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE hostels SET facebook_oauth_state = ? WHERE id = ?", (state, hostel_id))
    conn.commit()
    conn.close()


def consume_hostel_facebook_oauth_state(hostel_id, state):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT facebook_oauth_state FROM hostels WHERE id = ?", (hostel_id,))
    row = cursor.fetchone()
    valid = bool(row and row["facebook_oauth_state"] and row["facebook_oauth_state"] == state)
    cursor.execute("UPDATE hostels SET facebook_oauth_state = NULL WHERE id = ?", (hostel_id,))
    conn.commit()
    conn.close()
    return valid


# ===== INSTAGRAM DIRECT =====

def get_hostel_id_by_instagram_id(instagram_business_id):
    """Resolve qual hostel e dono de uma conta Instagram - usado pelo webhook."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM hostels WHERE instagram_business_id = ?", (instagram_business_id,))
    row = cursor.fetchone()
    conn.close()
    return row["id"] if row else None


def get_hostel_instagram_config(hostel_id):
    """Retorna (instagram_business_id, access_token) do hostel, ou (None, None)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT instagram_business_id, instagram_access_token FROM hostels WHERE id = ?",
        (hostel_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None, None
    return row["instagram_business_id"], row["instagram_access_token"]


def save_hostel_instagram_config(hostel_id, instagram_business_id, access_token):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE hostels SET instagram_business_id = ?, instagram_access_token = ? WHERE id = ?",
        (instagram_business_id, access_token, hostel_id)
    )
    conn.commit()
    conn.close()


def clear_hostel_instagram_config(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE hostels SET instagram_business_id = NULL, instagram_access_token = NULL WHERE id = ?",
        (hostel_id,)
    )
    conn.commit()
    conn.close()


def save_hostel_instagram_oauth_state(hostel_id, state):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE hostels SET instagram_oauth_state = ? WHERE id = ?", (state, hostel_id))
    conn.commit()
    conn.close()


def consume_hostel_instagram_oauth_state(hostel_id, state):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT instagram_oauth_state FROM hostels WHERE id = ?", (hostel_id,))
    row = cursor.fetchone()
    valid = bool(row and row["instagram_oauth_state"] and row["instagram_oauth_state"] == state)
    cursor.execute("UPDATE hostels SET instagram_oauth_state = NULL WHERE id = ?", (hostel_id,))
    conn.commit()
    conn.close()
    return valid


def get_or_create_guest_by_channel(hostel_id, channel, external_id, phone=None, name=None):
    """
    Identidade canonica multi-canal: resolve o guest_id pela combinacao
    (hostel_id, channel, external_id) em guest_channel_identities, em
    vez de depender de guests.phone (que so faz sentido pra numero de
    telefone real). WhatsApp tambem usa esta funcao (channel='whatsapp',
    external_id=telefone) pra nao manter dois caminhos de codigo
    divergentes - get_or_create_guest (por telefone direto) continua
    existindo pros fluxos que nao passam por um canal de chat (ex:
    reserva manual digitando o telefone do hospede).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT guest_id FROM guest_channel_identities WHERE hostel_id = ? AND channel = ? AND external_id = ?",
        (hostel_id, channel, external_id)
    )
    identity = cursor.fetchone()

    if identity:
        guest_id = identity["guest_id"]
        # Preenche o nome retroativamente se o hospede ja existe mas
        # ainda esta sem nome (ex: criado antes do nome automatico do
        # Messenger entrar no ar, ou a primeira busca de perfil falhou
        # na hora) - nunca sobrescreve um nome que ja foi salvo.
        if name:
            cursor.execute("SELECT name FROM guests WHERE id = ?", (guest_id,))
            current = cursor.fetchone()
            if current and not current["name"]:
                cursor.execute("UPDATE guests SET name = ? WHERE id = ?", (name, guest_id))
                conn.commit()
        conn.close()
        return guest_id

    guest_phone = phone if channel == "whatsapp" else None

    # WhatsApp especificamente pode ja ter um hospede de ANTES desta
    # integracao (criado pelo caminho antigo, so por telefone, sem
    # nenhuma linha em guest_channel_identities ainda) - adota o
    # guest_id existente em vez de tentar inserir um novo com o mesmo
    # telefone, o que violaria o UNIQUE(hostel_id, phone) de guests.
    existing_guest_id = None
    if guest_phone:
        cursor.execute(
            "SELECT id FROM guests WHERE hostel_id = ? AND phone = ?",
            (hostel_id, guest_phone)
        )
        existing = cursor.fetchone()
        if existing:
            existing_guest_id = existing["id"]

    if existing_guest_id:
        guest_id = existing_guest_id
        cursor.execute(
            "INSERT INTO guest_channel_identities (hostel_id, guest_id, channel, external_id) VALUES (?, ?, ?, ?)",
            (hostel_id, guest_id, channel, external_id)
        )
        conn.commit()
        conn.close()
        return guest_id

    cursor.execute(
        "INSERT INTO guests (hostel_id, phone, name) VALUES (?, ?, ?)",
        (hostel_id, guest_phone, name)
    )
    guest_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO guest_channel_identities (hostel_id, guest_id, channel, external_id) VALUES (?, ?, ?, ?)",
        (hostel_id, guest_id, channel, external_id)
    )

    conn.commit()
    conn.close()
    return guest_id


def get_guest_channel(hostel_id, guest_id):
    """
    Canal do hospede, pra despacho de envio (send_message_to_guest_now)
    e pro badge de canal na lista de Chats. Um hospede pode, em teoria,
    ter mais de uma identidade de canal (get_or_create_guest_by_channel
    permite) - por ora pega a mais recente, ja que mesclar hospede entre
    canais e feature futura, nao implementada ainda. guests sem nenhuma
    linha em guest_channel_identities (hospede antigo, cadastrado antes
    desta integracao) cai no fallback 'whatsapp', preservando o
    comportamento de hoje.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT channel FROM guest_channel_identities WHERE hostel_id = ? AND guest_id = ? ORDER BY id DESC LIMIT 1",
        (hostel_id, guest_id)
    )
    row = cursor.fetchone()
    conn.close()
    return row["channel"] if row else "whatsapp"


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


def get_hostel_type(hostel_id):
    """
    Tipo de propriedade (hostel/hotel/pousada/resort/flat/customizado),
    o mesmo campo configurado em Configuracoes > Empresa - usado pela IA
    pra ajustar o proprio tom de atendimento (ver services/ai_service.py),
    pra nao soar como recepcionista de hostel casual falando com hospede
    de resort 5 estrelas, e vice-versa.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT hostel_type FROM settings WHERE hostel_id = ?", (hostel_id,))
    row = cursor.fetchone()
    conn.close()
    return row["hostel_type"] if row and row["hostel_type"] else None


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


def get_opportunities_list(hostel_id, limit=20, offset=0, sort="recent"):
    """
    Paginado (LIMIT/OFFSET por created_at DESC) pra tela nao virar uma
    lista gigante com o tempo - "mostrar mais" no frontend avanca o
    offset. sort="priority" ordena por urgencia+score em vez de data,
    usado pela caixa lateral "mais importantes" (sempre olha o conjunto
    inteiro, independente da paginacao da lista principal). total/
    almost_closed/probable_revenue sao agregados sobre TODAS as
    oportunidades (nao so a pagina atual), pra alimentar os KPIs do
    dashboard sem precisar buscar a lista inteira toda vez.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(o.estimated_value), 0) AS probable_revenue,
            SUM(CASE WHEN o.score >= 70 THEN 1 ELSE 0 END) AS almost_closed
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ?
    """, (hostel_id,))
    stats = cursor.fetchone()

    order_clause = (
        "CASE o.urgency WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END, o.score DESC, o.created_at DESC"
        if sort == "priority"
        else "o.created_at DESC"
    )

    cursor.execute(f"""
        SELECT
            o.id,
            g.name,
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
        ORDER BY {order_clause}
        LIMIT ? OFFSET ?
    """, (hostel_id, limit, offset))

    items = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "items": items,
        "total": stats["total"],
        "almost_closed": stats["almost_closed"] or 0,
        "probable_revenue": stats["probable_revenue"],
    }


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

    # Reserva com check-out ja confirmado sai da lista ativa - a estadia
    # acabou de verdade, o historico dela continua rastreavel pelo
    # perfil do hospede (aba Hospedes), essa lista fica só com o que
    # ainda esta em andamento ou por vir. Reserva cancelada tambem sai -
    # fica acessivel so pelo botao "Ver cancelamentos"
    # (get_cancelled_reservations), pra nao poluir a lista principal.
    # Stats continuam calculadas em cima do conjunto completo (nao
    # filtrado), pra nao subtrair receita ja confirmada so porque o
    # hospede ja foi embora ou a reserva foi cancelada.
    visible_reservations = [
        r for r in reservations if not r["checked_out_at"] and r["status"] != "cancelled"
    ]

    return {"reservations": visible_reservations, "stats": stats}


def get_cancelled_reservations(hostel_id):
    """
    Reservas canceladas, escondidas da lista principal (ver
    get_reservations_with_stats) e acessiveis so pelo botao "Ver
    cancelamentos" - mesmo formato de linha da lista principal, sem
    stats (nao faz sentido KPI em cima so de canceladas).
    """
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
        WHERE r.hostel_id = ? AND r.status = 'cancelled'
        ORDER BY r.checkin_date DESC, r.id DESC
        """,
        (hostel_id,)
    )

    reservations = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return reservations


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
            ) AS total_value,
            (
                SELECT r.checked_out_at
                FROM reservations r
                WHERE r.guest_id = g.id
                ORDER BY r.id DESC
                LIMIT 1
            ) AS last_checked_out_at
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

    guest_dict = dict(guest)
    guest_dict["channel"] = get_guest_channel(hostel_id, guest_id)

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

    cursor.execute("""
        SELECT foreign_currency, foreign_amount, exchange_rate, market_rate,
               local_amount, profit, operator_name, created_at
        FROM currency_exchanges
        WHERE hostel_id = ? AND guest_id = ?
        ORDER BY created_at DESC
    """, (hostel_id, guest_id))

    exchanges = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "guest": guest_dict,
        "messages": messages,
        "opportunities": opportunities,
        "documents": documents,
        "reservations": get_guest_reservations(hostel_id, guest_id),
        "exchanges": exchanges
    }


def erase_guest_data(hostel_id, guest_id):
    """
    Remove/anonimiza os dados pessoais de um hospede a pedido dele
    (direito ao esquecimento - LGPD/Ley 25.326). Documentos de
    identidade sao apagados de verdade (arquivo no disco + registro no
    banco) e mensagens/conversas sao apagadas por completo. O cadastro
    do hospede em si NAO e deletado - fica anonimizado (nome/telefone/
    email/documento zerados) pra reservas/oportunidades/cambios ja
    registrados (registros financeiros/operacionais legitimos de
    manter) nao ficarem orfaos nem perderem o historico de valores.

    Limitacao conhecida: a descricao de oportunidades (texto livre
    gerado pela IA a partir da conversa) pode mencionar o nome do
    hospede dentro do texto solto - nao e escaneada/limpa aqui, exigiria
    processamento de linguagem natural pra fazer isso com seguranca
    sem apagar contexto de negocio relevante.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM guests WHERE id = ? AND hostel_id = ?", (guest_id, hostel_id))
    if not cursor.fetchone():
        conn.close()
        raise ValueError("Hospede nao encontrado.")

    cursor.execute(
        "SELECT file_path FROM guest_documents WHERE hostel_id = ? AND guest_id = ?",
        (hostel_id, guest_id)
    )
    file_paths = [row["file_path"] for row in cursor.fetchall()]
    cursor.execute(
        "DELETE FROM guest_documents WHERE hostel_id = ? AND guest_id = ?",
        (hostel_id, guest_id)
    )

    cursor.execute("SELECT id FROM conversations WHERE guest_id = ?", (guest_id,))
    conversation_ids = [row["id"] for row in cursor.fetchall()]
    for conversation_id in conversation_ids:
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    cursor.execute("DELETE FROM conversations WHERE guest_id = ?", (guest_id,))

    cursor.execute("DELETE FROM guest_channel_identities WHERE guest_id = ?", (guest_id,))

    anonymized_name = "Hóspede removido"
    cursor.execute(
        """
        UPDATE guests
        SET name = ?, phone = NULL, email = NULL, date_of_birth = NULL,
            nationality = NULL, address = NULL, document_type = NULL,
            document_number = NULL
        WHERE id = ? AND hostel_id = ?
        """,
        (anonymized_name, guest_id, hostel_id)
    )
    cursor.execute(
        "UPDATE reservations SET guest_name = ? WHERE guest_id = ? AND hostel_id = ?",
        (anonymized_name, guest_id, hostel_id)
    )
    cursor.execute(
        "UPDATE vehicles SET guest_name = ? WHERE guest_id = ? AND hostel_id = ?",
        (anonymized_name, guest_id, hostel_id)
    )

    conn.commit()
    conn.close()

    # Apaga os arquivos do disco POR FORA da transacao - se algum
    # arquivo falhar ao remover (ex: ja tinha sido movido), os dados
    # no banco ja estao limpos, que e a parte que realmente importa
    # pra privacidade (o registro que aponta pro documento ja sumiu).
    for file_path in file_paths:
        try:
            os.remove(file_path)
        except OSError:
            pass

    return {"erased_documents": len(file_paths), "erased_conversations": len(conversation_ids)}


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
            (
                SELECT ci.channel
                FROM guest_channel_identities ci
                WHERE ci.hostel_id = g.hostel_id AND ci.guest_id = g.id
                ORDER BY ci.id DESC LIMIT 1
            ) AS channel,
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

    # Estadia de longa duracao (stay_type='indefinite') nasce SEMPRE com
    # amount=0 (nao tem valor fechado, o que existe e uma diaria
    # acumulando saldo devedor - ver get_reservation_balance) - somar
    # so reservations.amount deixava qualquer pagamento registrado pra
    # morador fixo (reservation_payments) invisivel na receita, mesmo
    # sendo dinheiro de verdade ja recebido. Reserva fixa continua
    # usando amount normalmente (sem mudanca de comportamento).
    cursor.execute("""
        SELECT COALESCE(SUM(
            CASE WHEN r.stay_type = 'indefinite' THEN COALESCE(rp.total, 0) ELSE r.amount END
        ), 0) AS total
        FROM reservations r
        LEFT JOIN (
            SELECT reservation_id, SUM(amount) AS total
            FROM reservation_payments
            GROUP BY reservation_id
        ) rp ON rp.reservation_id = r.id
        WHERE r.hostel_id = ? AND r.status = 'confirmed'
    """, (hostel_id,))
    confirmed_revenue = cursor.fetchone()["total"]

    # local_amount = valor creditado ao hospede na cotacao usada;
    # profit = lucro do hostel na diferenca pra cotacao atual de mercado
    # (0 quando nao ha cotacao de referencia informada). Os dois juntos
    # sao o valor real que o cambio gerou de receita.
    cursor.execute(
        "SELECT COALESCE(SUM(local_amount + profit), 0) AS total FROM currency_exchanges WHERE hostel_id = ?",
        (hostel_id,)
    )
    confirmed_revenue += cursor.fetchone()["total"]

    # Financeiro mostra so o que realmente entrou na empresa - reserva
    # confirmada e pagamento de verdade. Oportunidade (estimativa, ainda
    # nao fechada) fica de fora de proposito: ela ja tem casa propria no
    # Opportunity Center (get_opportunities_list), nao faz sentido
    # aparecer duas vezes com significados diferentes (estimativa vs
    # dinheiro reconciliado).
    cursor.execute("""
        SELECT
            'Reserva' AS type,
            guest_name || COALESCE(' - ' || NULLIF(room_type, ''), '') AS description,
            amount AS value,
            status,
            created_at
        FROM reservations
        WHERE hostel_id = ? AND status = 'confirmed'

        UNION ALL

        SELECT
            'Pagamento' AS type,
            r.guest_name || COALESCE(' - ' || NULLIF(rp.method, ''), '') AS description,
            rp.amount AS value,
            'confirmed' AS status,
            rp.paid_at AS created_at
        FROM reservation_payments rp
        JOIN reservations r ON r.id = rp.reservation_id
        WHERE rp.hostel_id = ?

        UNION ALL

        SELECT
            'Câmbio' AS type,
            COALESCE(NULLIF(description, ''), foreign_currency || ' em dinheiro') AS description,
            local_amount + profit AS value,
            'confirmed' AS status,
            created_at
        FROM currency_exchanges
        WHERE hostel_id = ?

        ORDER BY created_at DESC
        LIMIT 30
    """, (hostel_id, hostel_id, hostel_id))

    movements = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "confirmed_revenue": confirmed_revenue,
        "movements": movements
    }


def create_currency_exchange(
    hostel_id, description, foreign_currency, foreign_amount, exchange_rate,
    market_rate=None, operator_user_id=None, operator_name=None, guest_id=None
):
    """
    Cambio como operacao de casa de cambio de verdade: exchange_rate e
    a cotacao USADA (o que foi de fato dado ao hospede - normalmente
    mais baixa que o mercado), market_rate e a cotacao ATUAL de
    referencia no momento (ex: dolar blue via Bluelytics). profit e a
    diferenca que fica de lucro pro hostel - so existe quando
    market_rate foi informado, senao fica 0 (cambio registrado sem
    referencia de mercado, sem lucro calculado).
    """
    local_amount = foreign_amount * exchange_rate
    profit = foreign_amount * (market_rate - exchange_rate) if market_rate is not None else 0

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO currency_exchanges
            (hostel_id, description, foreign_currency, foreign_amount, exchange_rate,
             local_amount, market_rate, profit, operator_user_id, operator_name, guest_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (hostel_id, description, foreign_currency, foreign_amount, exchange_rate,
         local_amount, market_rate, profit, operator_user_id, operator_name, guest_id)
    )
    exchange_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return exchange_id


def get_currency_exchanges(hostel_id, limit=30):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM currency_exchanges
        WHERE hostel_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (hostel_id, limit)
    )
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return data


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
                                amount=0, status="pending", phone="",
                                email="", nationality="", bed_id=None):
    guest_name = (guest_name or "").strip()
    checkin_date = (checkin_date or "").strip()
    checkout_date = (checkout_date or "").strip()

    if not guest_name:
        raise ValueError("guest_name is required.")
    if not checkin_date or not checkout_date:
        raise ValueError("checkin_date and checkout_date are required.")

    amount = float(amount or 0)
    room_type = (room_type or "").strip()

    conn = get_connection()
    cursor = conn.cursor()

    # Se ninguem informou um valor explicito, calcula pelo preco por
    # noite cadastrado na modalidade (mesma logica ja usada em
    # create_reservation_from_chat/create_reservation_from_channel) -
    # sem isso toda reserva manual nascia com US$ 0,00 mesmo com preco
    # configurado, ficando pra equipe lembrar de digitar na mao.
    if not amount and room_type:
        cursor.execute(
            "SELECT price_per_night FROM room_categories WHERE hostel_id = ? AND LOWER(name) = LOWER(?)",
            (hostel_id, room_type)
        )
        category_row = cursor.fetchone()
        if category_row and category_row["price_per_night"]:
            try:
                nights = max((datetime.date.fromisoformat(checkout_date) - datetime.date.fromisoformat(checkin_date)).days, 0)
            except (ValueError, TypeError):
                nights = 0
            amount = round(category_row["price_per_night"] * nights, 2)
    conn.close()

    # get_or_create_guest (nao so SELECT) - mesmo bug ja corrigido em
    # create_indefinite_stay/create_reservation_from_chat: hospede novo
    # nunca virava registro em guests, entao nunca aparecia na aba
    # Hospedes nem levava telefone/email/nacionalidade pra lugar nenhum.
    # Sem telefone (reserva so com nome), cria o hospede mesmo assim -
    # sem isso a reserva nunca tinha guest_id nenhum, entao nao tinha
    # perfil pra abrir (o nome ficava so como texto solto na reserva).
    phone = (phone or "").strip()
    guest_id = None
    if phone:
        guest_id = get_or_create_guest(hostel_id, phone)
        if guest_name:
            update_guest_name(hostel_id, phone, guest_name)
    elif guest_name:
        guest_id = create_guest_without_phone(hostel_id, guest_name)

    if guest_id:
        extra_fields = {}
        if (email or "").strip():
            extra_fields["email"] = email.strip()
        if (nationality or "").strip():
            extra_fields["nationality"] = nationality.strip()
        if extra_fields:
            update_guest_profile(hostel_id, guest_id, **extra_fields)

    def _insert(cursor, chosen_bed_id):
        cursor.execute(
            """
            INSERT INTO reservations
            (hostel_id, guest_id, guest_name, room_type, bed, bed_id, checkin_date,
             checkout_date, source, payment_method, amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hostel_id, guest_id, guest_name, room_type,
                (bed or "").strip(), chosen_bed_id, checkin_date, checkout_date,
                (source or "manual").strip(), (payment_method or "").strip(),
                amount, (status or "pending").strip(),
            )
        )
        return cursor.lastrowid

    # Cama especifica escolhida na criacao (novo campo do formulario) -
    # mesma trava contra corrida ja usada pra reserva de canal/WhatsApp,
    # ja que agora a equipe tambem pode disputar uma cama especifica na
    # hora de criar.
    if bed_id:
        reservation_id = reservar_cama_com_trava(
            hostel_id, int(bed_id), checkin_date, checkout_date,
            lambda cursor: _insert(cursor, int(bed_id))
        )
    else:
        conn = get_connection()
        cursor = conn.cursor()
        reservation_id = _insert(cursor, None)
        conn.commit()
        conn.close()

    if room_type:
        sync_availability_to_channel(hostel_id, room_type, checkin_date, checkout_date)
        sync_booking_to_channel(hostel_id, reservation_id)

    dispatch_reservation_webhook(hostel_id, reservation_id, "created")

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
    # Sem telefone (comum pra morador fixo/funcionario), cria o hospede
    # mesmo assim - sem isso a estadia nunca tinha guest_id nenhum, sem
    # perfil pra abrir e sem jeito de aparecer na aba Hospedes.
    guest_id = None
    phone = (phone or "").strip()
    if phone:
        guest_id = get_or_create_guest(hostel_id, phone)
        update_guest_name(hostel_id, phone, guest_name)
    else:
        guest_id = create_guest_without_phone(hostel_id, guest_name)

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

    dispatch_reservation_webhook(hostel_id, reservation_id, "created")

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

    dispatch_reservation_webhook(hostel_id, reservation_id, "checked_out")

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
        WHERE b.hostel_id = ? AND LOWER(rc.name) = LOWER(?)
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
            "SELECT id FROM room_categories WHERE hostel_id = ? AND LOWER(name) = LOWER(?)",
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


def _flag_booking_needs_manual_setup(hostel_id, guest_id, guest_name, category_name, checkin_date, checkout_date):
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
        "SELECT id FROM opportunities WHERE guest_id = ? AND type = 'booking' AND status = 'open'",
        (guest_id,)
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
            guest_id,
            f"{guest_name} quer reservar '{category_name}' de {checkin_date} a {checkout_date}, mas essa "
            f"modalidade ainda nao tem nenhuma cama cadastrada - nao da pra confirmar disponibilidade automaticamente.",
            "Cadastrar as camas dessa modalidade no Mapa de Quartos e confirmar a reserva manualmente com o hospede."
        )
    )

    conn.commit()
    conn.close()


def create_reservation_from_chat(hostel_id, guest_id, guest_name, category_name, checkin_date, checkout_date, bed_id=None):
    """
    Cria a reserva automaticamente a partir da conversa da IA de
    atendimento - sempre status 'pending' (a equipe confirma depois,
    igual ja fazia manualmente). O valor e SEMPRE calculado a partir do
    price_per_night real da modalidade (nunca aceito como argumento do
    modelo). guest_id ja vem resolvido pelo chamador (routes/chat.py,
    via get_or_create_guest_by_channel) - funciona pra qualquer canal
    (WhatsApp, Messenger, Instagram), nao so WhatsApp; o canal real do
    hospede (get_guest_channel) vira o `source` da reserva, em vez de
    'whatsapp' hardcoded.

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
    channel = get_guest_channel(hostel_id, guest_id)

    if guest_name:
        update_guest_name_by_id(guest_id, guest_name)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id FROM reservations
        WHERE hostel_id = ? AND guest_id = ? AND source = ?
          AND status = 'pending' AND checkin_date = ? AND checkout_date = ?
        """,
        (hostel_id, guest_id, channel, checkin_date, checkout_date)
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
        "SELECT price_per_night FROM room_categories WHERE hostel_id = ? AND LOWER(name) = LOWER(?)",
        (hostel_id, category_name)
    )
    category_row = cursor.fetchone()

    cursor.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM beds b
        JOIN rooms r ON r.id = b.room_id
        JOIN room_categories rc ON rc.id = r.category_id
        WHERE b.hostel_id = ? AND LOWER(rc.name) = LOWER(?)
        """,
        (hostel_id, category_name)
    )
    bed_count = cursor.fetchone()["cnt"]
    conn.close()

    if bed_count == 0:
        _flag_booking_needs_manual_setup(hostel_id, guest_id, guest_name, category_name, checkin_date, checkout_date)
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
        cursor.execute(
            """
            INSERT INTO reservations
            (hostel_id, guest_id, guest_name, room_type, bed, bed_id, checkin_date,
             checkout_date, source, payment_method, amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (hostel_id, guest_id, guest_name, category_name, "", int(bed_id),
             checkin_date, checkout_date, channel, "", amount)
        )
        return cursor.lastrowid

    # Reconfere disponibilidade e insere numa unica transacao travada
    # (ver reservar_cama_com_trava) - fecha a janela de corrida que
    # existia aqui antes (checar com find_available_beds numa conexao,
    # inserir noutra, sem nada impedindo duas chamadas concorrentes de
    # passarem pela checagem e ambas inserirem pra mesma cama).
    reservation_id = reservar_cama_com_trava(hostel_id, int(bed_id), checkin_date, checkout_date, _insert_with_bed)

    sync_availability_to_channel(hostel_id, category_name, checkin_date, checkout_date)
    sync_booking_to_channel(hostel_id, reservation_id)
    dispatch_reservation_webhook(hostel_id, reservation_id, "created")

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
        "SELECT room_type, checkin_date, checkout_date FROM reservations WHERE id = ? AND hostel_id = ?",
        (reservation_id, hostel_id)
    )
    reservation = cursor.fetchone()
    if not reservation:
        conn.close()
        raise ValueError("Reservation not found.")

    cursor.execute(
        "UPDATE reservations SET status = ? WHERE id = ? AND hostel_id = ?",
        (status, reservation_id, hostel_id)
    )

    conn.commit()
    conn.close()

    # Mudar status (cancelar, reverter cancelamento, etc) muda quantas
    # unidades da modalidade estao realmente ocupadas nesse periodo -
    # ressincroniza com o Beds24 sempre, nao so no cancelamento (a
    # funcao recalcula do zero, entao chamar de novo e sempre seguro).
    if (reservation["room_type"] or "").strip():
        sync_availability_to_channel(
            hostel_id, reservation["room_type"], reservation["checkin_date"], reservation["checkout_date"]
        )
    sync_booking_to_channel(hostel_id, reservation_id)
    dispatch_reservation_webhook(hostel_id, reservation_id, "cancelled" if status == "cancelled" else "status_changed")

    # Pedido do usuario: reserva vinda do chat (Messenger/WhatsApp) fica
    # pendente ate a equipe confirmar manualmente - o hospede precisa
    # saber o resultado sem ter que perguntar. Nunca deixa uma falha de
    # rede/envio derrubar a mudanca de status em si (que ja foi
    # commitada acima).
    try:
        notify_guest_reservation_status(hostel_id, reservation_id, status)
    except Exception as error:
        print("Erro ao notificar hospede sobre mudanca de status da reserva:", error)


_RESERVATION_CONFIRMED_TEMPLATES = {
    "pt": "Sua reserva foi confirmada! ✅",
    "en": "Your reservation has been confirmed! ✅",
    "es": "¡Tu reserva fue confirmada! ✅",
    "fr": "Votre réservation a été confirmée ! ✅",
    "de": "Ihre Reservierung wurde bestätigt! ✅",
}
_RESERVATION_CANCELLED_TEMPLATES = {
    "pt": "Sua reserva foi cancelada. Se quiser reagendar ou tiver alguma dúvida, é só chamar por aqui.",
    "en": "Your reservation has been cancelled. If you'd like to rebook or have any questions, just message us here.",
    "es": "Tu reserva fue cancelada. Si querés reagendar o tenés alguna duda, escribinos por acá.",
    "fr": "Votre réservation a été annulée. Si vous souhaitez la reprogrammer ou avez des questions, écrivez-nous ici.",
    "de": "Ihre Reservierung wurde storniert. Wenn Sie neu buchen möchten oder Fragen haben, schreiben Sie uns einfach hier.",
}
_RESERVATION_CHECKIN_LABEL = {"pt": "Check-in", "en": "Check-in", "es": "Check-in", "fr": "Arrivée", "de": "Check-in"}
_RESERVATION_CHECKOUT_LABEL = {"pt": "Check-out", "en": "Check-out", "es": "Check-out", "fr": "Départ", "de": "Check-out"}
_RESERVATION_ADDRESS_LABEL = {"pt": "Endereço", "en": "Address", "es": "Dirección", "fr": "Adresse", "de": "Adresse"}
_RESERVATION_FROM_LABEL = {"pt": "a partir das", "en": "from", "es": "a partir de las", "fr": "à partir de", "de": "ab"}


def notify_guest_reservation_status(hostel_id, reservation_id, status):
    """
    Avisa o hospede de volta, no mesmo canal onde ele esta conversando
    (WhatsApp, Messenger ou Instagram), quando uma reserva e confirmada
    ou cancelada pela equipe - ja passando horario de check-in/check-out
    e endereco do hostel na confirmacao. So dispara pra hospede com
    canal de chat identificavel (guest_id presente e telefone/PSID/
    IGSID resolvivel) - reserva sem hospede vinculado (ex: cadastro
    manual so com nome) nao tem pra onde mandar, sai em silencio.
    """
    if status not in ("confirmed", "cancelled"):
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT guest_id, checkin_date, checkout_date FROM reservations WHERE id = ? AND hostel_id = ?",
        (reservation_id, hostel_id)
    )
    reservation = cursor.fetchone()
    if not reservation or not reservation["guest_id"]:
        conn.close()
        return

    guest_id = reservation["guest_id"]

    cursor.execute(
        "SELECT channel, external_id FROM guest_channel_identities WHERE hostel_id = ? AND guest_id = ? ORDER BY id DESC LIMIT 1",
        (hostel_id, guest_id)
    )
    identity = cursor.fetchone()
    if identity:
        channel, target = identity["channel"], identity["external_id"]
    else:
        cursor.execute("SELECT phone FROM guests WHERE id = ?", (guest_id,))
        guest_row = cursor.fetchone()
        channel, target = "whatsapp", (guest_row["phone"] if guest_row else None)

    cursor.execute("SELECT address, checkin FROM settings WHERE hostel_id = ?", (hostel_id,))
    settings_row = cursor.fetchone()
    conn.close()

    if not target or channel not in ("whatsapp", "messenger", "instagram"):
        return

    lang = get_guest_language_by_id(guest_id) or "pt"
    if lang not in _RESERVATION_CONFIRMED_TEMPLATES:
        lang = "pt"

    address = (settings_row["address"] if settings_row else None) or ""
    checkin_time = (settings_row["checkin"] if settings_row else None) or ""

    if status == "confirmed":
        lines = [_RESERVATION_CONFIRMED_TEMPLATES[lang]]
        if reservation["checkin_date"]:
            line = f"{_RESERVATION_CHECKIN_LABEL[lang]}: {reservation['checkin_date']}"
            if checkin_time:
                line += f" ({_RESERVATION_FROM_LABEL[lang]} {checkin_time})"
            lines.append(line)
        if reservation["checkout_date"]:
            lines.append(f"{_RESERVATION_CHECKOUT_LABEL[lang]}: {reservation['checkout_date']}")
        if address:
            lines.append(f"{_RESERVATION_ADDRESS_LABEL[lang]}: {address}")
        message = "\n".join(lines)
    else:
        message = _RESERVATION_CANCELLED_TEMPLATES[lang]

    _dispatch_reservation_status_message(hostel_id, guest_id, channel, target, message)


def _dispatch_reservation_status_message(hostel_id, guest_id, channel, target, message):
    from services.memory_service import save_message as save_memory_message

    if channel == "whatsapp":
        from services.whatsapp_service import send_whatsapp_message
        phone_number_id, access_token = get_hostel_whatsapp_config(hostel_id)
        sent = send_whatsapp_message(phone_number_id, access_token, target, message)
        memory_key = target
    elif channel == "instagram":
        from services.instagram_service import send_instagram_message
        instagram_business_id, access_token = get_hostel_instagram_config(hostel_id)
        sent = send_instagram_message(access_token, instagram_business_id, target, message)
        memory_key = f"instagram:{target}"
    else:
        from services.messenger_service import send_messenger_message
        _, access_token = get_hostel_facebook_config(hostel_id)
        sent = send_messenger_message(access_token, target, message)
        memory_key = f"messenger:{target}"

    if sent:
        save_memory_message(hostel_id, memory_key, "assistant", message)
        save_message_db_for_guest(guest_id, "staff", message, channel=channel)


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


def attempt_extend_reservation(hostel_id, guest_id, new_checkout_date):
    import datetime

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, room_type, bed, checkin_date, checkout_date, amount, status
        FROM reservations
        WHERE hostel_id = ? AND guest_id = ? AND status != 'cancelled'
        ORDER BY checkout_date DESC
        LIMIT 1
        """,
        (hostel_id, guest_id)
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
            guest_id,
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


def flag_extension_for_approval(hostel_id, guest_id, note):
    _create_extension_opportunity(
        guest_id,
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
        "SELECT id FROM room_categories WHERE hostel_id = ? AND LOWER(name) = LOWER(?)",
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

    # camas livres com reserva que JA CHEGOU NO DIA do check-in (nao
    # antes disso) aparecem como "reserved" (azul) no mapa - pedido
    # explicito do usuario: uma reserva pro mes que vem nao pode deixar
    # a cama "ocupada visualmente" com semanas de antecedencia, senao
    # ninguem consegue perceber que ela esta livre pra alugar antes
    # dessa data. A trava real contra dar a mesma cama pra duas reservas
    # continua em outro lugar (find_available_beds/reservar_cama_com_trava/
    # sync_availability_to_channel, que sempre olham o periodo completo,
    # nao so hoje) - isso aqui e so a cor exibida no mapa.
    free_bed_ids = [b["id"] for b in beds if b["status"] == "free"]
    reserved_bed_ids = set()
    if free_bed_ids:
        today = datetime.date.today().isoformat()
        placeholders = ",".join("?" * len(free_bed_ids))
        cursor.execute(
            f"""
            SELECT DISTINCT bed_id FROM reservations
            WHERE bed_id IN ({placeholders}) AND status != 'cancelled'
              AND checkin_date <= ? AND checkout_date >= ? AND checked_out_at IS NULL
            """,
            free_bed_ids + [today, today]
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

    dispatch_reservation_webhook(hostel_id, reservation_id, "checked_in")

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

    dispatch_reservation_webhook(hostel_id, reservation_id, "checked_out")

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


def get_hostel_outbound_webhook(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT outbound_webhook_url, outbound_webhook_secret FROM hostels WHERE id = ?",
        (hostel_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None, None
    return row["outbound_webhook_url"], row["outbound_webhook_secret"]


def save_hostel_outbound_webhook_url(hostel_id, url):
    """
    Salva/atualiza a URL do webhook de saida generico. O secret de
    assinatura e gerado so na primeira vez (nunca trocado so por trocar
    a URL) - troca de secret e uma acao separada e explicita
    (regenerate_hostel_outbound_webhook_secret), pra nao invalidar sem
    avisar a validacao que o cliente ja tenha configurado do lado dele.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT outbound_webhook_secret FROM hostels WHERE id = ?", (hostel_id,))
    row = cursor.fetchone()
    secret = row["outbound_webhook_secret"] if row and row["outbound_webhook_secret"] else secrets.token_hex(32)
    cursor.execute(
        "UPDATE hostels SET outbound_webhook_url = ?, outbound_webhook_secret = ? WHERE id = ?",
        (url, secret, hostel_id)
    )
    conn.commit()
    conn.close()
    return secret


def regenerate_hostel_outbound_webhook_secret(hostel_id):
    secret = secrets.token_hex(32)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE hostels SET outbound_webhook_secret = ? WHERE id = ?", (secret, hostel_id))
    conn.commit()
    conn.close()
    return secret


def clear_hostel_outbound_webhook(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE hostels SET outbound_webhook_url = NULL, outbound_webhook_secret = NULL WHERE id = ?",
        (hostel_id,)
    )
    conn.commit()
    conn.close()


def dispatch_reservation_webhook(hostel_id, reservation_id, event_type):
    """
    Fase 6 da integracao de canais (saida generica): notifica o sistema
    proprio do cliente (se ele tiver cadastrado uma URL em Configuracoes
    -> Integracoes) toda vez que uma reserva e criada/alterada/cancelada
    no StayFlow, de QUALQUER origem (manual, WhatsApp, Beds24) - ao
    contrario de sync_booking_to_channel/sync_availability_to_channel
    (que so rodam pra origem manual/whatsapp, pra nao ecoar de volta pro
    Beds24), aqui o cliente quer saber de td, inclusive reserva que
    chegou de uma OTA.

    Nunca levanta excecao - mesmo principio de sync_booking_to_channel:
    uma falha ao notificar o webhook do cliente nao pode derrubar a
    acao real (criar/alterar/cancelar reserva) no StayFlow.
    """
    try:
        url, secret = get_hostel_outbound_webhook(hostel_id)
        if not url:
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.id, r.guest_name, r.room_type, r.bed, r.checkin_date, r.checkout_date,
                   r.source, r.status, r.amount, r.external_booking_id,
                   r.checked_in_at, r.checked_out_at, r.stay_type,
                   g.phone, g.email
            FROM reservations r
            LEFT JOIN guests g ON g.id = r.guest_id
            WHERE r.id = ? AND r.hostel_id = ?
            """,
            (reservation_id, hostel_id)
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return

        payload = dict(row)
    except Exception as error:
        print(f"Erro ao montar payload do webhook de saida (hostel {hostel_id}, reserva {reservation_id}):", error)
        return

    from services.outbound_webhook_service import send_webhook
    result = send_webhook(url, secret, event_type, payload)
    print(f"Webhook de saida (hostel {hostel_id}, reserva {reservation_id}, evento {event_type}): {result}")


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


def get_room_category_name(hostel_id, room_category_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM room_categories WHERE hostel_id = ? AND id = ?",
        (hostel_id, room_category_id)
    )
    row = cursor.fetchone()
    conn.close()
    return row["name"] if row else None


def find_recent_unlinked_stayflow_reservation(hostel_id, room_type, guest_name, checkin_date, checkout_date):
    """
    Fecha o eco causado pela Fase 5 (saida - reserva real): quando o
    StayFlow cria uma reserva de verdade no Beds24
    (sync_booking_to_channel), a Beds24 as vezes manda o webhook de
    volta quase instantaneamente - se chegar antes da gente terminar de
    gravar o external_booking_id na reserva original, o webhook nao tem
    como saber que essa reserva "nova" e a MESMA que acabamos de criar,
    e cria uma linha duplicada (bug real observado em producao: reserva
    do Silvano apareceu duas vezes identicas).

    Busca uma reserva StayFlow-origin (manual/whatsapp) recente (ultimos
    10 minutos), ainda sem external_booking_id, com mesma modalidade,
    nome do hospede e datas - se achar, e quase certamente o eco da
    propria reserva que acabamos de criar, nao uma reserva nova de
    verdade. Janela de 10 minutos e o casamento exato de
    modalidade+nome+datas tornam colisao por coincidencia improvavel.
    """
    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in STAYFLOW_NATIVE_SOURCES)
    cursor.execute(
        f"""
        SELECT id FROM reservations
        WHERE hostel_id = ? AND LOWER(room_type) = LOWER(?) AND guest_name = ?
          AND checkin_date = ? AND checkout_date = ?
          AND source IN ({placeholders})
          AND external_booking_id IS NULL
          AND status != 'cancelled'
          AND created_at >= datetime('now', '-10 minutes')
        ORDER BY id DESC LIMIT 1
        """,
        (hostel_id, room_type, guest_name, checkin_date, checkout_date, *STAYFLOW_NATIVE_SOURCES)
    )
    row = cursor.fetchone()
    conn.close()
    return row["id"] if row else None


def link_external_booking_id(hostel_id, reservation_id, beds24_booking_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE reservations SET external_booking_id = ? WHERE id = ? AND hostel_id = ?",
        (str(beds24_booking_id), reservation_id, hostel_id)
    )
    conn.commit()
    conn.close()


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


def sync_availability_to_channel(hostel_id, category_name, checkin_date, checkout_date):
    """
    Fase 4 da integracao Beds24 (saida): avisa o Beds24 quando a
    disponibilidade de uma modalidade muda por causa de uma reserva
    manual ou vinda do WhatsApp (criacao ou cancelamento) - fecha o
    risco de overbooking entre canais (alguem reservar a mesma cama por
    uma OTA enquanto ja esta ocupada no StayFlow). NUNCA chamar isso
    pra reserva que already veio DO Beds24 (create_reservation_from_channel/
    update_reservation_from_channel) - ecoaria de volta pra eles algo
    que eles mesmos ja sabem.

    numAvail = total de camas da modalidade menos quantas reservas
    nao-canceladas (de QUALQUER origem, inclusive vindas do proprio
    Beds24) se cruzam com o periodo pedido - contagem por
    room_type (texto) em vez de bed_id especifico, porque reserva
    manual/WhatsApp so ganha uma cama especifica atribuida no check-in
    (bed_id fica null antes disso), entao contar so por bed_id
    subestimaria a ocupacao real.

    Escopo desta fase: so reserva com checkin/checkout definidos.
    Estadia de longa duracao (checkout_date null) nao e sincronizada -
    nao e o tipo de ocupacao que se espera anunciar numa OTA.

    Nunca levanta excecao - uma falha ao sincronizar disponibilidade
    nao pode derrubar a criacao/cancelamento da reserva no StayFlow
    (mesmo principio de services/whatsapp_service.py).
    """
    if not checkin_date or not checkout_date:
        print(f"Sync disponibilidade Beds24: ignorado (sem checkin/checkout) - categoria '{category_name}'.")
        return

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM room_categories WHERE hostel_id = ? AND LOWER(name) = LOWER(?)",
            (hostel_id, category_name)
        )
        category = cursor.fetchone()
        if not category:
            conn.close()
            print(f"Sync disponibilidade Beds24: modalidade '{category_name}' nao encontrada no hostel {hostel_id}, ignorado.")
            return

        cursor.execute(
            "SELECT beds24_room_id FROM channel_room_mapping WHERE hostel_id = ? AND room_category_id = ?",
            (hostel_id, category["id"])
        )
        mapping = cursor.fetchone()
        if not mapping:
            conn.close()
            print(f"Sync disponibilidade Beds24: modalidade '{category_name}' (hostel {hostel_id}) nao esta mapeada pro Beds24, ignorado.")
            return  # modalidade nao mapeada pro Beds24 - nada a sincronizar

        beds24_room_id = mapping["beds24_room_id"]

        cursor.execute(
            """
            SELECT COUNT(*) AS cnt FROM beds b
            JOIN rooms r ON r.id = b.room_id
            WHERE b.hostel_id = ? AND r.category_id = ?
            """,
            (hostel_id, category["id"])
        )
        total_beds = cursor.fetchone()["cnt"]

        cursor.execute(
            """
            SELECT COUNT(*) AS cnt FROM reservations
            WHERE hostel_id = ? AND LOWER(room_type) = LOWER(?) AND status != 'cancelled'
              AND checkin_date < ? AND checkout_date > ?
            """,
            (hostel_id, category_name, checkout_date, checkin_date)
        )
        occupied_count = cursor.fetchone()["cnt"]
        conn.close()

        num_avail = max(total_beds - occupied_count, 0)
    except Exception as error:
        print("Erro ao calcular disponibilidade pra sincronizar com o Beds24:", error)
        return

    print(
        f"Sync disponibilidade Beds24: categoria '{category_name}' (hostel {hostel_id}) -> "
        f"beds24_room_id={beds24_room_id}, periodo {checkin_date}..{checkout_date}, "
        f"total_camas={total_beds}, ocupadas={occupied_count}, numAvail={num_avail}"
    )
    from services.beds24_service import push_availability
    result = push_availability(beds24_room_id, checkin_date, checkout_date, num_avail)
    print(f"Sync disponibilidade Beds24: push_availability retornou {result}")


def sync_booking_to_channel(hostel_id, reservation_id):
    """
    Fase 5 da integracao Beds24 (saida - reserva de verdade, nao so
    disponibilidade agregada): cria ou atualiza no Beds24 a reserva
    correspondente a uma reserva StayFlow-origin (manual ou WhatsApp)
    numa modalidade mapeada, pra que apareca de verdade no painel deles
    e para que cancelar aqui cancele la tambem.

    So roda pra reserva com source in ('manual', 'whatsapp') - reserva
    com qualquer outro source veio DO Beds24 (ver
    create_reservation_from_channel/update_reservation_from_channel) e
    nunca deve ecoar de volta pra eles.

    Primeira vez (external_booking_id ainda null): cria a reserva no
    Beds24 e grava o id retornado nessa mesma reserva - dai em diante
    toda mudanca de status so faz update, nunca cria de novo.

    Fora do escopo por enquanto: check-in/check-out. O payload real do
    Beds24 mostra que eles guardam isso como um infoItem separado
    (code='CHECKIN'), nao como o status principal da reserva - mecanismo
    de escrita ainda nao confirmado, fica pra uma proxima rodada depois
    de testar criacao/cancelamento ao vivo.

    Nunca levanta excecao - falha aqui nao pode derrubar a acao no
    StayFlow.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT r.guest_name, r.room_type, r.checkin_date, r.checkout_date,
                   r.status, r.amount, r.source, r.external_booking_id,
                   g.phone, g.email
            FROM reservations r
            LEFT JOIN guests g ON g.id = r.guest_id
            WHERE r.id = ? AND r.hostel_id = ?
            """,
            (reservation_id, hostel_id)
        )
        reservation = cursor.fetchone()

        if not reservation or reservation["source"] not in STAYFLOW_NATIVE_SOURCES:
            conn.close()
            return
        if not reservation["checkin_date"] or not reservation["checkout_date"]:
            conn.close()
            return  # estadia de longa duracao - fora do escopo, nao se anuncia numa OTA
        # Reserva 'pending' (aguardando confirmacao da equipe - status
        # padrao de toda reserva vinda do WhatsApp) so cria booking real
        # no Beds24 quando a equipe de fato confirmar - nao faz sentido
        # publicar numa OTA algo que ainda pode ser recusado. Excecao:
        # se ja existe external_booking_id (ja foi criada antes e voltou
        # pra pending por algum motivo), atualiza mesmo assim.
        if reservation["status"] == "pending" and not reservation["external_booking_id"]:
            conn.close()
            return

        cursor.execute(
            "SELECT id FROM room_categories WHERE hostel_id = ? AND LOWER(name) = LOWER(?)",
            (hostel_id, reservation["room_type"])
        )
        category = cursor.fetchone()
        if not category:
            conn.close()
            return

        cursor.execute(
            "SELECT beds24_room_id FROM channel_room_mapping WHERE hostel_id = ? AND room_category_id = ?",
            (hostel_id, category["id"])
        )
        mapping = cursor.fetchone()
        if not mapping:
            conn.close()
            return

        cursor.execute("SELECT beds24_property_id FROM hostels WHERE id = ?", (hostel_id,))
        hostel_row = cursor.fetchone()
        conn.close()
        if not hostel_row or not hostel_row["beds24_property_id"]:
            return
    except Exception as error:
        print("Erro ao preparar sincronizacao de reserva com o Beds24:", error)
        return

    beds24_status = "cancelled" if reservation["status"] in ("cancelled", "no_show") else "confirmed"
    name_parts = (reservation["guest_name"] or "").strip().split(" ", 1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    from services.beds24_service import create_booking, update_booking_status

    if reservation["external_booking_id"]:
        print(f"Sync reserva Beds24: atualizando reserva ja existente id={reservation['external_booking_id']} pra status={beds24_status}")
        update_booking_status(reservation["external_booking_id"], beds24_status)
        return

    print(
        f"Sync reserva Beds24: criando reserva nova - propriedade={hostel_row['beds24_property_id']}, "
        f"quarto={mapping['beds24_room_id']}, hospede='{reservation['guest_name']}', "
        f"periodo {reservation['checkin_date']}..{reservation['checkout_date']}, status={beds24_status}"
    )
    new_booking_id = create_booking(
        hostel_row["beds24_property_id"], mapping["beds24_room_id"],
        first_name, last_name, reservation["phone"], reservation["email"],
        reservation["checkin_date"], reservation["checkout_date"],
        reservation["amount"], status=beds24_status,
    )
    if new_booking_id:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE reservations SET external_booking_id = ? WHERE id = ? AND hostel_id = ?",
            (new_booking_id, reservation_id, hostel_id)
        )
        conn.commit()
        conn.close()
        print(f"Sync reserva Beds24: reserva StayFlow {reservation_id} vinculada ao booking Beds24 {new_booking_id}")


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
        reservation_id = reservar_cama_com_trava(hostel_id, bed_id, checkin_date, checkout_date, lambda cursor: _insert(cursor, bed_id))
    else:
        conn = get_connection()
        cursor = conn.cursor()
        reservation_id = _insert(cursor, None)
        conn.commit()
        conn.close()

    dispatch_reservation_webhook(hostel_id, reservation_id, "created")
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

    dispatch_reservation_webhook(hostel_id, row["id"], "cancelled" if reservation_status == "cancelled" else "updated")

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


# ===== Camada compartilhada: Cozinha/Manutencao/Seguranca
# Patrimonial/Estacionamento (Sessao 9) =====
#
# "Chamado" generico (tickets) + escala (staff_shifts) + notificacao
# (ticket_notifications), reaproveitados pelos 4 modulos operacionais
# novos - ver comentario da criacao das tabelas em create_database()
# pro raciocinio completo.

_TICKET_URGENCY_WEIGHT = {"urgent": 0, "high": 1, "normal": 2, "low": 3}


def _minutes_since(timestamp_str):
    """
    Minutos desde um TIMESTAMP do SQLite (formato 'YYYY-MM-DD
    HH:MM:SS', sempre UTC por vir de CURRENT_TIMESTAMP) ate agora.
    Usado so pra ordenar por espera dentro do mesmo nivel de urgencia -
    nao precisa ser exato ao segundo.
    """
    if not timestamp_str:
        return 0
    try:
        created = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return 0
    return max(0, (datetime.datetime.utcnow() - created).total_seconds() / 60)


def _ticket_priority_rank(ticket_row):
    """
    Prioridade EFETIVA, calculada na hora (nao gravada) - urgencia
    define o "andar" (um "urgent" sempre fica na frente de um
    "normal"), tempo de espera desempata DENTRO do mesmo andar (um
    "normal" parado ha 3 dias fura fila na frente de um "normal" aberto
    ha 3 minutos). Quanto MENOR o numero, maior a prioridade.
    """
    weight = _TICKET_URGENCY_WEIGHT.get(ticket_row["base_urgency"], 2)
    waited = _minutes_since(ticket_row["created_at"])
    return weight * 100000 - waited


def create_ticket(hostel_id, ticket_type, location=None, description=None,
                   base_urgency="normal", reported_by_guest_id=None,
                   reported_by_membership_id=None, channel=None):
    """
    Cria um chamado generico - usado como base por cozinha (pedido),
    manutencao e seguranca patrimonial (incidente). base_urgency e o
    sinal BRUTO recebido (do hospede ou padrao do sistema) - a
    prioridade efetiva de fila e calculada depois, na consulta (ver
    _ticket_priority_rank), nunca gravada aqui.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO tickets (
            hostel_id, type, reported_by_guest_id, reported_by_membership_id,
            location, description, base_urgency, channel
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (hostel_id, ticket_type, reported_by_guest_id, reported_by_membership_id,
         location, description, base_urgency or "normal", channel)
    )
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id


def get_ticket(hostel_id, ticket_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM tickets WHERE id = ? AND hostel_id = ?",
        (ticket_id, hostel_id)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_open_tickets(hostel_id, ticket_type=None):
    """
    Chamados abertos (open/assigned/in_progress), ordenados pela
    prioridade efetiva calculada agora - nao pela ordem de criacao.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM tickets WHERE hostel_id = ? AND status IN ('open', 'assigned', 'in_progress')"
    params = [hostel_id]
    if ticket_type:
        query += " AND type = ?"
        params.append(ticket_type)

    cursor.execute(query, params)
    tickets = [dict(row) for row in cursor.fetchall()]
    conn.close()

    tickets.sort(key=_ticket_priority_rank)
    return tickets


def assign_ticket(hostel_id, ticket_id, membership_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE tickets SET status = 'assigned', assigned_to_membership_id = ?,
            assigned_at = CURRENT_TIMESTAMP
        WHERE id = ? AND hostel_id = ?
        """,
        (membership_id, ticket_id, hostel_id)
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def update_ticket_status(hostel_id, ticket_id, status):
    """
    Transicao generica de status (ex: 'in_progress') - resolve_ticket
    existe a parte pra 'resolved' porque esse caso tambem grava
    resolution_notes e resolved_at.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tickets SET status = ? WHERE id = ? AND hostel_id = ?",
        (status, ticket_id, hostel_id)
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def resolve_ticket(hostel_id, ticket_id, resolution_notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE tickets SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP,
            resolution_notes = ?
        WHERE id = ? AND hostel_id = ?
        """,
        (resolution_notes, ticket_id, hostel_id)
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def get_on_duty_staff(hostel_id, department, section_id=None):
    """
    Quem esta de plantao AGORA nesse departamento (e, se informado,
    setor) - consulta a grade de escala pela data e hora atuais.
    Fonte de verdade unica usada por cozinha/manutencao/seguranca/
    estacionamento pra decidir quem notificar. Nao trata turno que
    atravessa a meia-noite (start_time > end_time) como caso especial -
    fica pra uma proxima rodada se algum hostel precisar.
    """
    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    now_time = now.strftime("%H:%M")

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT s.id AS shift_id, s.membership_id, s.section_id, u.id AS user_id, u.name
        FROM staff_shifts s
        JOIN hostel_memberships m ON m.id = s.membership_id
        JOIN users u ON u.id = m.user_id
        WHERE s.hostel_id = ? AND s.department = ? AND s.status = 'scheduled'
          AND s.shift_date = ? AND s.start_time <= ? AND s.end_time > ?
    """
    params = [hostel_id, department, today, now_time, now_time]

    if section_id is not None:
        query += " AND s.section_id = ?"
        params.append(section_id)

    cursor.execute(query, params)
    staff = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return staff


def log_ticket_notification(ticket_id, membership_id, channel=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ticket_notifications (ticket_id, membership_id, channel) VALUES (?, ?, ?)",
        (ticket_id, membership_id, channel)
    )
    notification_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return notification_id


def acknowledge_ticket_notification(notification_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE ticket_notifications SET acknowledged_at = CURRENT_TIMESTAMP WHERE id = ?",
        (notification_id,)
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def notify_on_duty_staff_for_ticket(hostel_id, ticket_id, department, section_id=None, channel="dashboard"):
    """
    Combina get_on_duty_staff + log_ticket_notification - ponto unico
    que cozinha/manutencao/seguranca chamam pra "avisar quem tem que
    ser avisado, e so essa pessoa". Se ninguem estiver de plantao
    (buraco na escala), o chamado fica sem notificacao mas continua
    existindo - aparece pra qualquer um que olhar a fila de chamados
    abertos.
    """
    staff = get_on_duty_staff(hostel_id, department, section_id)
    for person in staff:
        log_ticket_notification(ticket_id, person["membership_id"], channel)
    return staff


def create_staff_shift(hostel_id, membership_id, department, shift_date, start_time, end_time, section_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO staff_shifts (hostel_id, membership_id, department, section_id, shift_date, start_time, end_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (hostel_id, membership_id, department, section_id, shift_date, start_time, end_time)
    )
    shift_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return shift_id


def get_staff_shifts(hostel_id, start_date=None, end_date=None):
    """
    Grade de escala pro periodo pedido - usada pra desenhar a visao
    semanal (linha=funcionario, coluna=dia) no dashboard.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT s.*, u.name AS staff_name, sec.name AS section_name
        FROM staff_shifts s
        JOIN hostel_memberships m ON m.id = s.membership_id
        JOIN users u ON u.id = m.user_id
        LEFT JOIN sections sec ON sec.id = s.section_id
        WHERE s.hostel_id = ? AND s.status = 'scheduled'
    """
    params = [hostel_id]
    if start_date:
        query += " AND s.shift_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND s.shift_date <= ?"
        params.append(end_date)
    query += " ORDER BY s.shift_date, s.start_time"

    cursor.execute(query, params)
    shifts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return shifts


def request_shift_coverage(shift_id, requested_by_membership_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO shift_coverage_requests (shift_id, requested_by_membership_id) VALUES (?, ?)",
        (shift_id, requested_by_membership_id)
    )
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return request_id


def accept_shift_coverage(request_id, covering_membership_id):
    """
    Alguem aceita cobrir o turno - so troca o dono do turno de verdade
    (staff_shifts.membership_id) quando o pedido esta 'pending', pra
    nao aceitar duas vezes por engano.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT shift_id, status FROM shift_coverage_requests WHERE id = ?",
        (request_id,)
    )
    row = cursor.fetchone()
    if not row or row["status"] != "pending":
        conn.close()
        return False

    cursor.execute(
        """
        UPDATE shift_coverage_requests SET status = 'approved',
            covering_membership_id = ?, resolved_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (covering_membership_id, request_id)
    )
    cursor.execute(
        "UPDATE staff_shifts SET membership_id = ? WHERE id = ?",
        (covering_membership_id, row["shift_id"])
    )
    conn.commit()
    conn.close()
    return True


def create_section(hostel_id, name, department):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sections (hostel_id, name, department) VALUES (?, ?, ?)",
        (hostel_id, name, department)
    )
    section_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return section_id


def get_sections(hostel_id, department=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM sections WHERE hostel_id = ?"
    params = [hostel_id]
    if department:
        query += " AND department = ?"
        params.append(department)
    query += " ORDER BY name"
    cursor.execute(query, params)
    sections = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sections


# ===== Cozinha / Room Service =====


def create_menu_item(hostel_id, name, category, price, station="cozinha"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO menu_items (hostel_id, name, category, price, station) VALUES (?, ?, ?, ?, ?)",
        (hostel_id, name, category, price, station)
    )
    menu_item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return menu_item_id


def get_menu_items(hostel_id, active_only=True):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM menu_items WHERE hostel_id = ?"
    params = [hostel_id]
    if active_only:
        query += " AND active = 1"
    query += " ORDER BY category, name"
    cursor.execute(query, params)
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return items


def find_menu_item_by_name(hostel_id, name_query):
    """
    Mesmo padrao de find_inventory_item_by_name - usado pela IA (via
    chat) pra resolver o nome que o hospede/modelo digitou pro
    menu_item_id real, sem exigir que o modelo saiba IDs internos.
    """
    items = get_menu_items(hostel_id, active_only=True)
    query_norm = _normalize_text(name_query)
    return [item for item in items if query_norm in _normalize_text(item["name"])]


def set_menu_item_active(hostel_id, menu_item_id, active):
    """
    Tirar item do ar (ex: acabou o ingrediente) sem apagar historico de
    pedidos antigos que ja usaram esse item.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE menu_items SET active = ? WHERE id = ? AND hostel_id = ?",
        (1 if active else 0, menu_item_id, hostel_id)
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def set_menu_item_ingredient(menu_item_id, inventory_item_id, quantity):
    """
    Define (cria ou atualiza) quanto de um item de estoque a "receita"
    de um item do cardapio consome - base da baixa automatica.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM menu_item_ingredients WHERE menu_item_id = ? AND inventory_item_id = ?",
        (menu_item_id, inventory_item_id)
    )
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            "UPDATE menu_item_ingredients SET quantity = ? WHERE id = ?",
            (quantity, existing["id"])
        )
    else:
        cursor.execute(
            "INSERT INTO menu_item_ingredients (menu_item_id, inventory_item_id, quantity) VALUES (?, ?, ?)",
            (menu_item_id, inventory_item_id, quantity)
        )

    conn.commit()
    conn.close()


def _deduct_ingredients_for_menu_item(cursor, menu_item_id, order_quantity):
    """
    Interno - da baixa no estoque (inventory_items) pra cada ingrediente
    da receita de um item do cardapio, multiplicado pela quantidade
    pedida. Nunca deixa quantidade negativa (mesma trava de
    adjust_inventory_quantity_by_name). Roda dentro da MESMA
    transacao/cursor de create_kitchen_order - se o pedido falhar,
    a baixa tambem nao acontece.
    """
    cursor.execute(
        "SELECT inventory_item_id, quantity FROM menu_item_ingredients WHERE menu_item_id = ?",
        (menu_item_id,)
    )
    for ingredient in cursor.fetchall():
        needed = ingredient["quantity"] * order_quantity
        cursor.execute(
            "UPDATE inventory_items SET quantity = MAX(0, quantity - ?) WHERE id = ?",
            (needed, ingredient["inventory_item_id"])
        )


def create_kitchen_order(hostel_id, location, items, reported_by_guest_id=None,
                          reported_by_membership_id=None, channel=None, base_urgency="normal"):
    """
    Cria o pedido de cozinha completo - ticket generico + um
    kitchen_order_item por item pedido (preco travado no momento do
    pedido, nao recalculado se o cardapio mudar depois) + baixa de
    estoque automatica pela receita de cada item. A IA confirma pedido
    de cozinha sozinha (decisao de produto - diferente de reserva, que
    fica sempre pending) - por isso o ticket ja nasce pronto pra
    cozinha ver, sem etapa de aprovacao manual.

    items: lista de dicts {"menu_item_id": int, "quantity": int, "notes": str opcional}
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tickets (
            hostel_id, type, reported_by_guest_id, reported_by_membership_id,
            location, description, base_urgency, channel
        ) VALUES (?, 'kitchen_order', ?, ?, ?, ?, ?, ?)
        """,
        (hostel_id, reported_by_guest_id, reported_by_membership_id,
         location, f"{len(items)} item(ns)", base_urgency, channel)
    )
    ticket_id = cursor.lastrowid

    for item in items:
        cursor.execute(
            "SELECT price FROM menu_items WHERE id = ? AND hostel_id = ?",
            (item["menu_item_id"], hostel_id)
        )
        menu_item = cursor.fetchone()
        if not menu_item:
            conn.rollback()
            conn.close()
            raise ValueError(f"Item de cardapio {item['menu_item_id']} nao encontrado.")

        quantity = item.get("quantity", 1)
        cursor.execute(
            """
            INSERT INTO kitchen_order_items (ticket_id, menu_item_id, quantity, unit_price, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ticket_id, item["menu_item_id"], quantity, menu_item["price"], item.get("notes"))
        )
        _deduct_ingredients_for_menu_item(cursor, item["menu_item_id"], quantity)

    conn.commit()
    conn.close()
    return ticket_id


def get_kitchen_order_items(ticket_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT koi.*, mi.name AS menu_item_name, mi.station
        FROM kitchen_order_items koi
        JOIN menu_items mi ON mi.id = koi.menu_item_id
        WHERE koi.ticket_id = ?
        """,
        (ticket_id,)
    )
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return items


def update_kitchen_order_item_status(ticket_id, item_id, status):
    """
    Status POR ITEM (pending/preparing/ready/delivered) - bebida sai
    antes de comida num servico de mesa de verdade. O status do pedido
    como um todo (get_kitchen_order_aggregate_status) e derivado disso,
    nao gravado separado.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE kitchen_order_items SET status = ? WHERE id = ? AND ticket_id = ?",
        (status, item_id, ticket_id)
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def get_kitchen_order_aggregate_status(ticket_id):
    """
    'pending' (nada pronto ainda), 'partially_ready' (so parte),
    'ready' (tudo pronto, nada entregue ainda) ou 'delivered' (tudo
    entregue) - derivado do status de cada kitchen_order_item, na hora,
    nunca gravado.
    """
    items = get_kitchen_order_items(ticket_id)
    if not items:
        return "pending"

    statuses = {item["status"] for item in items}
    if statuses == {"delivered"}:
        return "delivered"
    if statuses <= {"ready", "delivered"}:
        return "ready"
    if "ready" in statuses or "delivered" in statuses:
        return "partially_ready"
    return "pending"


# ===== Manutencao =====


def create_maintenance_ticket(hostel_id, location, description, category=None,
                               guest_reported_urgency=None, reported_by_guest_id=None,
                               reported_by_membership_id=None, channel=None, base_urgency="normal"):
    """
    guest_reported_urgency e o sinal BRUTO que o hospede deu (pode
    divergir de base_urgency, que e o que a equipe/IA decidiu usar de
    fato pra fila - modelo hibrido: pergunta pro hospede, mas o sistema
    ainda pode reordenar comparado aos outros chamados abertos).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tickets (
            hostel_id, type, reported_by_guest_id, reported_by_membership_id,
            location, description, base_urgency, channel
        ) VALUES (?, 'maintenance', ?, ?, ?, ?, ?, ?)
        """,
        (hostel_id, reported_by_guest_id, reported_by_membership_id,
         location, description, base_urgency, channel)
    )
    ticket_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO maintenance_issues (ticket_id, category, guest_reported_urgency) VALUES (?, ?, ?)",
        (ticket_id, category, guest_reported_urgency)
    )

    conn.commit()
    conn.close()
    return ticket_id


def get_recurring_maintenance_alerts(hostel_id, window_days=30, threshold=3):
    """
    Locais com 3+ (threshold) chamados de manutencao na mesma
    localizacao nos ultimos window_days dias - vira dado sempre
    (relatorio) e alerta ativo quando bate o limite, sem precisar de
    tabela/mecanismo proprio: e so uma consulta.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT location, COUNT(*) AS occurrences, MAX(created_at) AS last_occurrence
        FROM tickets
        WHERE hostel_id = ? AND type = 'maintenance'
          AND location IS NOT NULL AND location != ''
          AND created_at >= datetime('now', ?)
        GROUP BY location
        HAVING COUNT(*) >= ?
        ORDER BY occurrences DESC
        """,
        (hostel_id, f"-{window_days} days", threshold)
    )
    alerts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return alerts


# ===== Seguranca Patrimonial =====


def create_security_incident(hostel_id, location, description, incident_type=None,
                              reported_via="guest_chat", reported_by_guest_id=None,
                              reported_by_membership_id=None, channel=None, base_urgency="high"):
    """
    Urgencia padrao mais alta que os outros tipos (incidente de
    seguranca comeca em 'high', nao 'normal') - reflete que um relato
    de seguranca tipicamente nao deveria esperar na mesma fila que um
    pedido de cozinha.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tickets (
            hostel_id, type, reported_by_guest_id, reported_by_membership_id,
            location, description, base_urgency, channel
        ) VALUES (?, 'security_incident', ?, ?, ?, ?, ?, ?)
        """,
        (hostel_id, reported_by_guest_id, reported_by_membership_id,
         location, description, base_urgency, channel)
    )
    ticket_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO security_incidents (ticket_id, incident_type, reported_via) VALUES (?, ?, ?)",
        (ticket_id, incident_type, reported_via)
    )

    conn.commit()
    conn.close()
    return ticket_id


def set_hostel_system_integration(hostel_id, capability, provider="manual_fallback", config=None, fallback_phone_number=None):
    """
    Cria ou atualiza o adaptador de UMA capacidade (ex: 'call_dispatch',
    'camera_feed', 'access_control') - um hotel pode ter varias linhas,
    uma por capacidade, cada uma com seu proprio fornecedor. provider
    'manual_fallback' (sem API) e o padrao seguro - so vira 'api' quando
    o hotel confirmar de verdade o sistema que usa.
    """
    import json as _json

    conn = get_connection()
    cursor = conn.cursor()
    config_json = _json.dumps(config) if config is not None else None

    cursor.execute(
        "SELECT id FROM hostel_system_integrations WHERE hostel_id = ? AND capability = ?",
        (hostel_id, capability)
    )
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            """
            UPDATE hostel_system_integrations SET provider = ?, config = ?, fallback_phone_number = ?
            WHERE id = ?
            """,
            (provider, config_json, fallback_phone_number, existing["id"])
        )
    else:
        cursor.execute(
            """
            INSERT INTO hostel_system_integrations (hostel_id, capability, provider, config, fallback_phone_number)
            VALUES (?, ?, ?, ?, ?)
            """,
            (hostel_id, capability, provider, config_json, fallback_phone_number)
        )

    conn.commit()
    conn.close()


def get_hostel_system_integration(hostel_id, capability):
    """
    Devolve o adaptador configurado pra essa capacidade, ou um
    'manual_fallback' implicito (sem linha no banco) se o hotel nunca
    configurou nada - garante que quem chama SEMPRE tem um caminho
    valido (notificar quem esta de plantao + numero de contato), nunca
    trava por falta de configuracao.
    """
    import json as _json

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM hostel_system_integrations WHERE hostel_id = ? AND capability = ?",
        (hostel_id, capability)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"hostel_id": hostel_id, "capability": capability, "provider": "manual_fallback",
                "config": None, "fallback_phone_number": None}

    result = dict(row)
    result["config"] = _json.loads(result["config"]) if result["config"] else None
    return result


# ===== Estacionamento =====


def get_active_vehicle_for_guest(hostel_id, guest_id):
    """
    Veiculo do hospede ainda sem saida registrada - usado pelo pedido
    de manobrista via chat (a IA nao precisa saber vehicle_id, so pede
    o carro "do hospede que esta falando", resolvido aqui).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM vehicles WHERE hostel_id = ? AND guest_id = ? AND checked_out_at IS NULL ORDER BY checked_in_at DESC LIMIT 1",
        (hostel_id, guest_id)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def list_active_vehicles(hostel_id):
    """
    Todo veiculo ainda no estacionamento (sem saida registrada) -
    usado pela tela de Estacionamento no dashboard. guest_name final e
    o nome do hospede cadastrado quando existe (guest_id preenchido),
    ou o nome digitado na hora pelo manobrista (vehicles.guest_name)
    quando nao ha hospede formal ainda - por isso o COALESCE, e por
    isso NAO usa "v.*" direto (colidiria com o alias guest_name).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            v.id, v.hostel_id, v.guest_id, v.reservation_id, v.plate, v.model,
            v.color, v.spot_number, v.service_type, v.checked_in_at, v.checked_out_at,
            COALESCE(g.name, v.guest_name) AS guest_name
        FROM vehicles v
        LEFT JOIN guests g ON g.id = v.guest_id
        WHERE v.hostel_id = ? AND v.checked_out_at IS NULL
        ORDER BY v.checked_in_at DESC
        """,
        (hostel_id,)
    )
    vehicles = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return vehicles


def check_in_vehicle(hostel_id, guest_id=None, guest_name=None, plate=None, model=None,
                      color=None, spot_number=None, service_type="autoatendimento", reservation_id=None):
    """
    guest_id OU guest_name - manobrista pode registrar o carro de
    alguem que chegou na hora, sem hospede formal cadastrado ainda
    (guest_name cobre esse caso; guest_id continua sendo o caminho
    normal quando o hospede ja existe no sistema).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO vehicles (hostel_id, guest_id, guest_name, reservation_id, plate, model, color, spot_number, service_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (hostel_id, guest_id, guest_name, reservation_id, plate, model, color, spot_number, service_type)
    )
    vehicle_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return vehicle_id


def check_out_vehicle(hostel_id, vehicle_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE vehicles SET checked_out_at = CURRENT_TIMESTAMP WHERE id = ? AND hostel_id = ? AND checked_out_at IS NULL",
        (vehicle_id, hostel_id)
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def request_valet(hostel_id, vehicle_id, reported_by_guest_id=None, channel=None):
    """
    "Traz meu carro" - so faz sentido pra service_type='manobrista'; vira
    um ticket generico (type='valet_request'), notificado pelo mesmo
    caminho de escala/plantao (department='estacionamento') que os
    outros modulos.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT plate, model, color FROM vehicles WHERE id = ? AND hostel_id = ?",
        (vehicle_id, hostel_id)
    )
    vehicle = cursor.fetchone()
    description = None
    if vehicle:
        description = f"Placa {vehicle['plate'] or '?'} - {vehicle['model'] or ''} {vehicle['color'] or ''}".strip()

    cursor.execute(
        """
        INSERT INTO tickets (hostel_id, type, reported_by_guest_id, location, description, base_urgency, channel)
        VALUES (?, 'valet_request', ?, 'Estacionamento', ?, 'normal', ?)
        """,
        (hostel_id, reported_by_guest_id, description, channel)
    )
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return ticket_id


def get_hostel_parking_settings(hostel_id):
    import json as _json

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hostel_parking_settings WHERE hostel_id = ?", (hostel_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"hostel_id": hostel_id, "pricing_model": "incluso", "daily_rate": 0, "included_for_categories": None}

    result = dict(row)
    result["included_for_categories"] = _json.loads(result["included_for_categories"]) if result["included_for_categories"] else None
    return result


def set_hostel_parking_settings(hostel_id, pricing_model, daily_rate=0, included_for_categories=None):
    """
    included_for_categories: lista de room_category_id (so usada
    quando pricing_model == 'por_categoria') - gravada como JSON.
    """
    import json as _json

    conn = get_connection()
    cursor = conn.cursor()
    categories_json = _json.dumps(included_for_categories) if included_for_categories is not None else None

    cursor.execute(
        "SELECT hostel_id FROM hostel_parking_settings WHERE hostel_id = ?",
        (hostel_id,)
    )
    if cursor.fetchone():
        cursor.execute(
            "UPDATE hostel_parking_settings SET pricing_model = ?, daily_rate = ?, included_for_categories = ? WHERE hostel_id = ?",
            (pricing_model, daily_rate, categories_json, hostel_id)
        )
    else:
        cursor.execute(
            "INSERT INTO hostel_parking_settings (hostel_id, pricing_model, daily_rate, included_for_categories) VALUES (?, ?, ?, ?)",
            (hostel_id, pricing_model, daily_rate, categories_json)
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_database()
    print("Banco de dados criado/atualizado com sucesso!")
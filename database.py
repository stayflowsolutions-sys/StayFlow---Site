import os
import sqlite3

DATABASE = os.path.join(os.getenv("STAYFLOW_DATA_DIR", "."), "stayflow.db")


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

    # se for um banco antigo (criado antes do multi-tenant), migra
    if _guests_table_needs_migration(cursor):
        _migrate_guests_to_composite_unique(cursor)

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
        checkin_time TEXT,
        checkout_time TEXT,
        breakfast_time TEXT,
        languages TEXT,
        services TEXT,
        tours TEXT
    )
    """)

    # settings antigo (de antes do multi-tenant) não tinha essas colunas —
    # CREATE TABLE IF NOT EXISTS não adiciona coluna em tabela já existente,
    # então precisa migrar manualmente, igual fizemos com guests/leads.
    add_column_if_not_exists(cursor, "settings", "hostel_name", "TEXT")
    add_column_if_not_exists(cursor, "settings", "hostel_type", "TEXT")
    add_column_if_not_exists(cursor, "settings", "checkin", "TEXT")
    add_column_if_not_exists(cursor, "settings", "checkout", "TEXT")

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
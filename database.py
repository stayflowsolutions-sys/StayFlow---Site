import os
import sqlite3

from utils.permissions import ALL_PERMISSIONS_STR

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

    if _users_table_needs_migration(cursor):
        _migrate_users_to_memberships(cursor)

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
"""
Script de migração única: roda uma vez para converter o
conversations.json antigo (chave = telefone) para o novo formato
multi-tenant (chave = "hostel_id:telefone").

Todo histórico existente é atribuído ao hostel 1, que era o único
hostel existente antes do multi-tenant.

Uso:
    python migrate_conversations_json.py
"""

import json
import os
import shutil

MEMORY_FILE = "conversations.json"
DEFAULT_HOSTEL_ID = 1


def looks_already_migrated(key):
    return ":" in key and key.split(":", 1)[0].isdigit()


def main():
    if not os.path.exists(MEMORY_FILE):
        print("Nenhum conversations.json encontrado. Nada a fazer.")
        return

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if all(looks_already_migrated(k) for k in data.keys()):
        print("conversations.json já está no formato multi-tenant. Nada a fazer.")
        return

    backup_path = MEMORY_FILE + ".backup"
    shutil.copy(MEMORY_FILE, backup_path)
    print(f"Backup salvo em {backup_path}")

    migrated = {}
    for phone, value in data.items():
        if looks_already_migrated(phone):
            migrated[phone] = value
        else:
            new_key = f"{DEFAULT_HOSTEL_ID}:{phone}"
            migrated[new_key] = value

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(migrated, f, indent=4, ensure_ascii=False)

    print(f"Migrado com sucesso: {len(migrated)} conversa(s).")


if __name__ == "__main__":
    main()
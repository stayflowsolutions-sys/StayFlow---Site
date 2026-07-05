import json
import os
from datetime import datetime

MEMORY_FILE = "conversations.json"


def _tenant_key(hostel_id, phone):
    """
    Chave composta hostel+telefone. Sem isso, dois hostels diferentes
    com um hóspede de mesmo telefone compartilhariam o mesmo histórico
    de conversa — um veria o contexto do outro dentro do prompt da IA.
    """
    return f"{hostel_id}:{phone}"


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def save_message(hostel_id, phone, role, text):
    memory = load_memory()
    key = _tenant_key(hostel_id, phone)

    if key not in memory:
        memory[key] = {"messages": []}

    memory[key]["messages"].append({
        "role": role,
        "text": text,
        "time": str(datetime.now())
    })

    save_memory(memory)


def get_history(hostel_id, phone):
    memory = load_memory()
    key = _tenant_key(hostel_id, phone)
    history = []

    if key in memory:
        for item in memory[key]["messages"][-12:]:
            history.append({
                "role": item["role"],
                "content": item["text"]
            })

    return history
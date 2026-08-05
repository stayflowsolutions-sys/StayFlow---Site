"""
Script de diagnóstico único: verifica e força a reinscrição do webhook
do Instagram (campo "messages") pra cada hostel com Instagram
conectado - a inscrição do webhook do Instagram não é permanente
(já foi perdida silenciosamente uma vez antes, sem nenhum aviso), então
isso serve tanto pra checar o estado atual quanto pra garantir a
reinscrição sem precisar de mais uma rodada de teste manual de
mensagem indo e voltando.

Uso (via Shell do Render):
    python check_instagram_webhook.py
"""

import requests

from database import get_connection
from services.instagram_service import API_BASE


def main():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, hostel_name, instagram_business_id, instagram_access_token "
        "FROM hostels WHERE instagram_business_id IS NOT NULL AND instagram_access_token IS NOT NULL"
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("Nenhum hostel com Instagram conectado (instagram_business_id/access_token vazios).")
        return

    for row in rows:
        hostel_id = row["id"]
        hostel_name = row["hostel_name"]
        ig_id = row["instagram_business_id"]
        token = row["instagram_access_token"]

        print(f"\n=== hostel_id={hostel_id} ({hostel_name}) instagram_business_id={ig_id} ===")

        try:
            check = requests.get(
                f"{API_BASE}/{ig_id}/subscribed_apps",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            print(f"Estado atual da inscricao: status={check.status_code} body={check.text}")
        except Exception as error:
            print(f"Erro ao checar inscricao atual: {error}")

        try:
            resub = requests.post(
                f"{API_BASE}/{ig_id}/subscribed_apps",
                params={"subscribed_fields": "messages"},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            print(f"Reinscricao forcada: status={resub.status_code} body={resub.text}")
        except Exception as error:
            print(f"Erro ao forcar reinscricao: {error}")


if __name__ == "__main__":
    main()

"""
Script de configuração única: troca o invite code gerado manualmente no
painel do Beds24 (Settings > API > Generate invite code, na conta
master de agência do StayFlow) por um refresh token, e guarda
criptografado no banco. Só precisa rodar uma vez — depois disso a
integração renova o access token sozinha sob demanda.

Requer a env var BEDS24_ENCRYPTION_KEY já configurada (gere uma com
`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
e coloque no ambiente do servidor, nunca no código/git).

Uso:
    python setup_beds24_master.py <invite_code>
"""

import sys

import services.beds24_service as beds24_service


def main():
    if len(sys.argv) < 2:
        print("Uso: python setup_beds24_master.py <invite_code>")
        sys.exit(1)

    invite_code = sys.argv[1].strip()
    ok, error = beds24_service.setup_master_account(invite_code)

    if not ok:
        print(f"Falha ao configurar a conta master do Beds24: {error}")
        sys.exit(1)

    print("Conta master do Beds24 configurada com sucesso. Refresh token salvo (criptografado).")


if __name__ == "__main__":
    main()

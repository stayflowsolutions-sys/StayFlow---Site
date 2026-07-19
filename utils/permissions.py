"""
Fonte única de verdade das permissões disponíveis no sistema —
uma por seção do menu principal. Qualquer código que precise validar
ou listar permissões deve importar ALL_PERMISSIONS daqui, nunca
reescrever essa lista em outro lugar.
"""

ALL_PERMISSIONS = [
    "dashboard",
    "chats",
    "opportunities",
    "reservations",
    "operations",
    "guests",
    "finance",
    "reports",
    "inventory",
    "revenue",
    "settings",
    "team",
]

ALL_PERMISSIONS_STR = ",".join(ALL_PERMISSIONS)

PERMISSION_LABELS = {
    "dashboard": "Dashboard",
    "chats": "Chats",
    "opportunities": "Opportunity Center",
    "reservations": "Reservas",
    "operations": "Operações",
    "guests": "Hóspedes",
    "finance": "Financeiro",
    "reports": "Relatórios",
    "inventory": "Estoque",
    "revenue": "Receitas",
    "settings": "Configurações",
    "team": "Equipe",
}

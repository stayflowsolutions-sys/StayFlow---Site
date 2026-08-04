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
    "security",
    "billing",
    # Sessao 9 - modulos operacionais novos (cozinha, manutencao,
    # seguranca patrimonial, estacionamento, escala). "patrimonial_security"
    # (nao "security") de proposito - "security" ja significa seguranca
    # da CONTA (trocar senha/sessoes), nada a ver com seguranca fisica
    # do predio; usar o mesmo nome colidiria com o que ja existe.
    "kitchen",
    "maintenance",
    "patrimonial_security",
    "parking",
    "scheduling",
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
    "security": "Segurança",
    "billing": "Billing",
    "kitchen": "Cozinha",
    "maintenance": "Manutenção",
    "patrimonial_security": "Segurança Patrimonial",
    "parking": "Estacionamento",
    "scheduling": "Escala",
}

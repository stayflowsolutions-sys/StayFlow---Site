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
    "events",
    "portfolio",
    "partners",
]

ALL_PERMISSIONS_STR = ",".join(ALL_PERMISSIONS)

# Permissoes que so fazem sentido pra hospedagem (reserva de quarto,
# modulos operacionais do predio fisico) - mesma categorizacao usada
# no menu lateral (data-required-account-kind="lodging" em
# dashboard.html) pra esconder o item de nav correspondente. Uma
# agencia parceira nunca deveria ver checkbox pra essas no catalogo de
# cargos (Equipe > Novo cargo), mesmo que a permissao exista no
# sistema em abstrato.
LODGING_ONLY_PERMISSIONS = {
    "reservations", "operations", "inventory", "revenue",
    "kitchen", "maintenance", "patrimonial_security", "parking",
    "scheduling", "events", "partners",
}

# Permissoes exclusivas de agencia parceira - hospedagem nao ve.
AGENCY_ONLY_PERMISSIONS = {"portfolio"}


def permissions_for_account_kind(account_kind):
    """Subconjunto de ALL_PERMISSIONS que faz sentido oferecer pra esse tipo de conta - mesma categorizacao do menu lateral, so que pro catalogo de cargos (Equipe)."""
    if account_kind == "agency":
        return [p for p in ALL_PERMISSIONS if p not in LODGING_ONLY_PERMISSIONS]
    return [p for p in ALL_PERMISSIONS if p not in AGENCY_ONLY_PERMISSIONS]


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
    "events": "Eventos",
    "portfolio": "Meu Portfólio",
    "partners": "Parceiros",
}

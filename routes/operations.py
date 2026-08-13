from datetime import date

from flask import Blueprint, jsonify, request
from database import get_connection, get_cleaning_list, create_ticket, get_open_tickets, resolve_ticket
from utils.tenant import require_permission

operations_bp = Blueprint("operations", __name__)


@operations_bp.route("/operations/tasks", methods=["POST"])
@require_permission("operations")
def create_task_route(hostel_id):
    """
    Tarefa avulsa que nao se encaixa em cozinha/manutencao/seguranca
    (ex: "trocar lampada do corredor") - chamado generico (tickets,
    type='task'), sem setor de plantao fixo pra avisar (diferente dos
    outros 3, ninguem e notificado automaticamente - so entra na fila
    de Tarefas pra quem estiver olhando pegar).
    """
    data = request.get_json() or {}
    description = (data.get("description") or "").strip()
    if not description:
        return jsonify({"success": False, "message": "description is required."}), 400

    ticket_id = create_ticket(
        hostel_id, "task",
        location=(data.get("location") or "").strip() or None,
        description=description,
        base_urgency=data.get("base_urgency", "normal"),
        channel="dashboard",
    )
    return jsonify({"success": True, "id": ticket_id}), 201


@operations_bp.route("/operations/tasks/<int:ticket_id>/resolve", methods=["POST"])
@require_permission("operations")
def resolve_task_route(hostel_id, ticket_id):
    resolve_ticket(hostel_id, ticket_id)
    return jsonify({"success": True})


@operations_bp.route("/operations", methods=["GET"])
@require_permission("operations")
def operations(hostel_id):
    conn = get_connection()
    cursor = conn.cursor()

    today = date.today().isoformat()
    alerts = []

    # Cada alerta carrega "category" (pra filtro no painel do sino) e
    # "page" (pra clicar no alerta e ser levado direto pra tela
    # relacionada) - antes era so uma lista de strings, sem estrutura
    # nenhuma pra filtrar/navegar.

    # Check-ins e check-outs de hoje ainda não confirmados
    cursor.execute("""
        SELECT guest_name, checkin_date, checkout_date, status
        FROM reservations
        WHERE hostel_id = ?
          AND (checkin_date = ? OR checkout_date = ?)
          AND status != 'confirmed'
    """, (hostel_id, today, today))

    for row in cursor.fetchall():
        kind = "Check-in" if row["checkin_date"] == today else "Check-out"
        alerts.append({
            "category": "checkin_checkout",
            "message": f"{kind} de hoje ainda pendente: {row['guest_name']} (status: {row['status']})",
            "page": "reservations",
        })

    # Chegada de hoje sem check-in FISICO feito ainda - dispara mesmo
    # pra reserva ja confirmada (o alerta acima so cobre status !=
    # confirmed, mas a maioria das reservas ja chega confirmada antes
    # do dia da chegada). Avisa a recepcao que precisa atribuir uma cama
    # e confirmar a chegada de verdade - a cama so aparece "Reservada"
    # no mapa a partir de hoje tambem (ver get_bed_map), entao esse
    # aviso e o lembrete equivalente pro lado operacional.
    cursor.execute("""
        SELECT guest_name FROM reservations
        WHERE hostel_id = ? AND checkin_date = ? AND status != 'cancelled'
          AND checked_in_at IS NULL
    """, (hostel_id, today))

    for row in cursor.fetchall():
        alerts.append({
            "category": "arrival",
            "message": f"Chegada hoje - atribuir cama e confirmar check-in: {row['guest_name']}",
            "page": "roommap",
        })

    # Oportunidades urgentes ainda em aberto
    cursor.execute("""
        SELECT o.description, g.phone
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ? AND o.status = 'open' AND o.urgency = 'high'
    """, (hostel_id,))

    for row in cursor.fetchall():
        alerts.append({
            "category": "guest_urgent",
            "message": f"Hóspede aguardando resposta urgente ({row['phone']}): {row['description']}",
            "page": "chats",
        })

    # Itens de estoque no mínimo ou abaixo
    cursor.execute("""
        SELECT name, quantity, min_threshold, unit
        FROM inventory_items
        WHERE hostel_id = ? AND quantity <= min_threshold
    """, (hostel_id,))

    for row in cursor.fetchall():
        alerts.append({
            "category": "low_stock",
            "message": (
                f"Estoque baixo: {row['name']} ({row['quantity']} {row['unit']}, "
                f"mínimo {row['min_threshold']} {row['unit']})"
            ),
            "page": "inventory",
        })

    # Reservas criadas automaticamente (WhatsApp, Beds24/qualquer OTA -
    # tudo que nao veio de cadastro manual da equipe) nas ultimas 24h.
    # Janela de tempo em vez de "todas pra sempre" pra nao acumular
    # alerta de reserva antiga que a equipe ja viu ha dias.
    cursor.execute("""
        SELECT guest_name, source, checkin_date, checkout_date
        FROM reservations
        WHERE hostel_id = ? AND source != 'manual'
          AND created_at >= datetime('now', '-1 day')
        ORDER BY created_at DESC
    """, (hostel_id,))

    for row in cursor.fetchall():
        alerts.append({
            "category": "new_reservation",
            "message": (
                f"Nova reserva via {row['source']}: {row['guest_name']} "
                f"({row['checkin_date']} → {row['checkout_date']})"
            ),
            "page": "reservations",
        })

    conn.close()

    # Tarefas de limpeza vem direto do Mapa de Quartos - mesma fonte de
    # verdade (camas com status 'needs_cleaning'), sem tabela duplicada.
    cleaning_list = get_cleaning_list(hostel_id)
    tasks = [
        {
            "task": f"Limpar {item['label']} ({item['room_name']})",
            "assignee": "Equipe de limpeza",
            "status": "pending"
        }
        for item in cleaning_list
    ]

    # Tarefas avulsas criadas manualmente (ver /operations/tasks) - unica
    # com ticket_id no dict, pra so essas ganharem botao de "concluir" no
    # frontend (tarefa de limpeza resolve sozinha ao marcar a cama limpa).
    for ticket in get_open_tickets(hostel_id, ticket_type="task"):
        label = ticket["description"] or "Tarefa"
        if ticket["location"]:
            label = f"{label} ({ticket['location']})"
        tasks.append({
            "task": label,
            "assignee": "-",
            "status": "pending",
            "ticket_id": ticket["id"],
        })

    # Cada cama aguardando limpeza tambem conta como alerta (nao so
    # tarefa) - sem isso, um check-out nunca incrementava o sininho de
    # notificacoes nem aparecia pra quem loga so olhando o resumo geral.
    for item in cleaning_list:
        alerts.append({
            "category": "cleaning",
            "message": f"Limpeza pendente: {item['label']} ({item['room_name']})",
            "page": "roommap",
        })

    return jsonify({
        "alerts": alerts,
        "tasks": tasks
    })
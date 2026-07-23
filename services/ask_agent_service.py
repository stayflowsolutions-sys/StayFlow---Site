import json
import os

from openai import OpenAI
from dotenv import load_dotenv

from database import (
    get_effective_permissions,
    get_dashboard_stats,
    get_opportunities_list,
    get_reservations_with_stats,
    get_inventory_with_alerts,
    get_revenue_summary,
    get_guests_list,
    find_guest_by_name,
    get_guest_profile,
    get_chats_list,
    get_finance_summary,
    get_reports_summary,
    list_pending_supplier_orders,
    create_reservation_record,
    update_reservation_status_record,
    create_supplier_record,
    adjust_inventory_quantity_by_name,
    propose_supplier_order,
    send_supplier_order,
    cancel_pending_supplier_order,
    confirm_supplier_order_received,
    propose_guest_message,
    send_guest_message,
    cancel_guest_message_draft,
    get_bed_map,
    get_cleaning_list,
    checkin_reservation_to_bed,
    checkout_reservation_bed,
    mark_bed_cleaned,
    return_items_from_laundry,
    set_bed_maintenance,
    create_room_category,
    list_room_categories,
    create_room,
    create_rooms_bulk,
    create_bed,
    create_indefinite_stay,
    get_reservation_balance,
    record_reservation_payment,
    close_indefinite_stay,
)

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
Você é o Ask StayFlow, assistente interno do painel administrativo do StayFlow, falando com um funcionário/gestor do hostel (não com um hóspede).

Responda em português, de forma direta e útil. Use as ferramentas disponíveis pra buscar dado real antes de responder qualquer pergunta sobre números, reservas, hóspedes, conversas, estoque, oportunidades, financeiro ou receita — nunca invente ou estime valores. Se uma ferramenta não estiver disponível pra essa pessoa (permissão insuficiente), diga isso claramente e sugira quem ela pode procurar.

Você também pode executar ações reais quando pedido: criar reserva, atualizar status de reserva, cadastrar fornecedor, ajustar quantidade de estoque.

Regra crítica pra pedidos de reposição a fornecedor (nunca pule etapa):
1. Quando o usuário pedir pra encomendar algo a um fornecedor, use propose_supplier_order pra montar a mensagem e mostre o texto exato pro usuário, junto do nome do fornecedor. NUNCA chame confirm_and_send_supplier_order nesse mesmo passo.
2. Se a MENSAGEM SEGUINTE do usuário for uma confirmação simples (ex: "sim", "pode mandar", "manda", "confirma", "ok"), isso SEMPRE significa "envie o pedido que acabei de propor" — chame confirm_and_send_supplier_order imediatamente, SEM propor de novo e SEM pedir confirmação de novo.
3. Se o usuário pedir pra cancelar ou mudar algo antes de confirmar, use cancel_supplier_order.
4. Quando o usuário disser que um pedido chegou (ex: "chegaram os pães"), use confirm_supplier_order_received pra dar entrada automática no estoque — não peça pra ele fazer isso manualmente.

Regra crítica pra mensagem proativa a um hóspede (mesma lógica, nunca pule etapa):
1. Quando o usuário pedir pra avisar/mandar mensagem pra um hóspede, componha um texto natural e educado pro contexto pedido, e use propose_guest_message pra deixar pronto — mostre o texto exato pro usuário antes de qualquer coisa. NUNCA chame send_guest_message nesse mesmo passo.
2. Se a MENSAGEM SEGUINTE do usuário for uma confirmação simples (ex: "sim", "pode mandar", "manda", "confirma", "ok"), isso SEMPRE significa "envie o rascunho que acabei de propor" — chame send_guest_message imediatamente, SEM propor de novo e SEM pedir confirmação de novo. Só peça confirmação de novo se o usuário pedir pra mudar o texto.
3. Se o usuário pedir pra cancelar ou mudar o texto antes de confirmar, use cancel_guest_message.
4. Depois de enviada, a mensagem já entra na conversa normal do hóspede no WhatsApp — se ele responder, quem continua o atendimento é a IA de atendimento (não você), incluindo decidir sozinha sobre extensão de estadia dentro de limites seguros.
"""

def _guest_details(hostel_id, guest_id):
    profile = get_guest_profile(hostel_id, int(guest_id))
    if not profile:
        raise ValueError("Hóspede não encontrado.")
    return profile


TOOLS_CATALOG = [
    {
        "permission": "dashboard",
        "function": lambda hostel_id: get_dashboard_stats(hostel_id),
        "spec": {
            "type": "function",
            "function": {
                "name": "get_dashboard_overview",
                "description": "Retorna um resumo geral: total de hóspedes, mensagens, leads e oportunidades, além dos leads e mensagens mais recentes.",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    },
    {
        "permission": "opportunities",
        "function": lambda hostel_id: get_opportunities_list(hostel_id),
        "spec": {
            "type": "function",
            "function": {
                "name": "get_opportunities",
                "description": "Lista todas as oportunidades detectadas (leads, upsell, tours) com score, urgência, valor estimado e próxima ação sugerida.",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    },
    {
        "permission": "reservations",
        "function": lambda hostel_id: get_reservations_with_stats(hostel_id),
        "spec": {
            "type": "function",
            "function": {
                "name": "get_reservations",
                "description": "Lista as reservas e estatísticas agregadas (check-ins/check-outs de hoje, no-shows, receita confirmada).",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    },
    {
        "permission": "inventory",
        "function": lambda hostel_id: get_inventory_with_alerts(hostel_id),
        "spec": {
            "type": "function",
            "function": {
                "name": "get_inventory_alerts",
                "description": "Lista os itens de estoque, agrupados por categoria, e os alertas de itens abaixo do mínimo com sugestão de mensagem pro fornecedor.",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    },
    {
        "permission": "revenue",
        "function": lambda hostel_id: get_revenue_summary(hostel_id),
        "spec": {
            "type": "function",
            "function": {
                "name": "get_revenue_summary",
                "description": "Retorna o catálogo de experiências/upsells, as oportunidades abertas de tour/upsell, e a receita extra estimada.",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    },
    {
        "permission": "guests",
        "function": lambda hostel_id: get_guests_list(hostel_id),
        "spec": {
            "type": "function",
            "function": {
                "name": "get_guests",
                "description": "Lista todos os hóspedes do hostel, com quantidade de mensagens trocadas e valor total em oportunidades.",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    },
    {
        "permission": "guests",
        "function": lambda hostel_id, name: find_guest_by_name(hostel_id, name),
        "spec": {
            "type": "function",
            "function": {
                "name": "find_guest",
                "description": "Procura hóspedes pelo nome (busca parcial). Use antes de get_guest_details se não souber o ID do hóspede.",
                "parameters": {
                    "type": "object",
                    "properties": {"name": {"type": "string", "description": "Nome ou parte do nome do hóspede"}},
                    "required": ["name"]
                }
            }
        }
    },
    {
        "permission": "guests",
        "function": lambda hostel_id, guest_id: _guest_details(hostel_id, guest_id),
        "spec": {
            "type": "function",
            "function": {
                "name": "get_guest_details",
                "description": "Retorna o perfil completo de um hóspede pelo ID: dados de contato, histórico de mensagens e oportunidades. Use find_guest primeiro pra achar o ID.",
                "parameters": {
                    "type": "object",
                    "properties": {"guest_id": {"type": "integer", "description": "ID do hóspede"}},
                    "required": ["guest_id"]
                }
            }
        }
    },
    {
        "permission": "chats",
        "function": lambda hostel_id: get_chats_list(hostel_id),
        "spec": {
            "type": "function",
            "function": {
                "name": "get_chats_overview",
                "description": "Lista as conversas com hóspedes: última mensagem, quem mandou, e a intenção/oportunidade detectada mais recente de cada uma.",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    },
    {
        "permission": "finance",
        "function": lambda hostel_id: get_finance_summary(hostel_id),
        "spec": {
            "type": "function",
            "function": {
                "name": "get_finance_summary",
                "description": "Retorna receita confirmada, receita em risco, receita recuperável e recuperada, e as movimentações financeiras mais recentes.",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    },
    {
        "permission": "reports",
        "function": lambda hostel_id: get_reports_summary(hostel_id),
        "spec": {
            "type": "function",
            "function": {
                "name": "get_reports_summary",
                "description": "Retorna receita por canal de origem da reserva e o funil hóspedes -> mensagens -> oportunidades -> reservas confirmadas.",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    },
    {
        "permission": "inventory",
        "function": lambda hostel_id: list_pending_supplier_orders(hostel_id),
        "spec": {
            "type": "function",
            "function": {
                "name": "list_pending_supplier_orders",
                "description": "Lista os pedidos de reposição a fornecedor que ainda estão pendentes de confirmação de envio, ou já enviados e aguardando chegada.",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    },
    {
        "permission": "reservations",
        "function": lambda hostel_id, **kw: create_reservation_record(hostel_id, **kw),
        "spec": {
            "type": "function",
            "function": {
                "name": "create_reservation",
                "description": "Cria uma nova reserva. checkin_date e checkout_date no formato AAAA-MM-DD.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guest_name": {"type": "string"},
                        "room_type": {"type": "string"},
                        "bed": {"type": "string"},
                        "checkin_date": {"type": "string", "description": "AAAA-MM-DD"},
                        "checkout_date": {"type": "string", "description": "AAAA-MM-DD"},
                        "source": {"type": "string"},
                        "payment_method": {"type": "string"},
                        "amount": {"type": "number"},
                        "status": {"type": "string", "enum": ["pending", "confirmed", "cancelled"]},
                        "phone": {"type": "string", "description": "Telefone do hóspede, se souber (pra linkar com o cadastro existente)"}
                    },
                    "required": ["guest_name", "checkin_date", "checkout_date"]
                }
            }
        }
    },
    {
        "permission": "reservations",
        "function": lambda hostel_id, reservation_id, status: update_reservation_status_record(hostel_id, int(reservation_id), status),
        "spec": {
            "type": "function",
            "function": {
                "name": "update_reservation_status",
                "description": "Atualiza o status de uma reserva existente.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reservation_id": {"type": "integer"},
                        "status": {"type": "string", "enum": ["pending", "confirmed", "cancelled"]}
                    },
                    "required": ["reservation_id", "status"]
                }
            }
        }
    },
    {
        "permission": "reservations",
        "function": lambda hostel_id, guest_name, checkin_date, daily_rate, room_type="", bed_id=None, phone="": create_indefinite_stay(hostel_id, guest_name, checkin_date, daily_rate, room_type, int(bed_id) if bed_id else None, phone),
        "spec": {
            "type": "function",
            "function": {
                "name": "create_indefinite_stay",
                "description": "Registra um morador de longa duração (ex: funcionário que mora no hostel), sem data de saída definida. daily_rate pode ser 0 (não paga nada) ou um valor real que acumula saldo devedor por dia, abatido conforme pagamentos forem registrados.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guest_name": {"type": "string"},
                        "checkin_date": {"type": "string", "description": "Data de início, AAAA-MM-DD"},
                        "daily_rate": {"type": "number", "description": "Valor cobrado por dia, 0 se não pagar nada"},
                        "room_type": {"type": "string"},
                        "bed_id": {"type": "integer", "description": "Opcional - cama específica que a pessoa já ocupa"},
                        "phone": {"type": "string"}
                    },
                    "required": ["guest_name", "checkin_date", "daily_rate"]
                }
            }
        }
    },
    {
        "permission": "reservations",
        "function": lambda hostel_id, reservation_id: get_reservation_balance(hostel_id, int(reservation_id)),
        "spec": {
            "type": "function",
            "function": {
                "name": "get_reservation_balance",
                "description": "Consulta o saldo de um morador de longa duração: dias ocupados, valor devido total, total pago, e saldo (positivo = deve, negativo = tem crédito por ter pago a mais).",
                "parameters": {
                    "type": "object",
                    "properties": {"reservation_id": {"type": "integer"}},
                    "required": ["reservation_id"]
                }
            }
        }
    },
    {
        "permission": "reservations",
        "function": lambda hostel_id, reservation_id, amount, method=None, note=None: record_reservation_payment(hostel_id, int(reservation_id), amount, method, note),
        "spec": {
            "type": "function",
            "function": {
                "name": "record_reservation_payment",
                "description": "Registra um pagamento recebido de um morador de longa duração, abatendo do saldo devedor (ou aumentando o crédito se pagar mais do que deve).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reservation_id": {"type": "integer"},
                        "amount": {"type": "number"},
                        "method": {"type": "string"},
                        "note": {"type": "string"}
                    },
                    "required": ["reservation_id", "amount"]
                }
            }
        }
    },
    {
        "permission": "reservations",
        "function": lambda hostel_id, reservation_id, checkout_date=None: close_indefinite_stay(hostel_id, int(reservation_id), checkout_date),
        "spec": {
            "type": "function",
            "function": {
                "name": "close_indefinite_stay",
                "description": "Encerra a estadia de um morador de longa duração (saiu de verdade), libera a cama pra limpeza e mostra o saldo final.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reservation_id": {"type": "integer"},
                        "checkout_date": {"type": "string", "description": "Opcional, padrão é hoje"}
                    },
                    "required": ["reservation_id"]
                }
            }
        }
    },
    {
        "permission": "inventory",
        "function": lambda hostel_id, name, phone="", email="": create_supplier_record(hostel_id, name, phone, email),
        "spec": {
            "type": "function",
            "function": {
                "name": "create_supplier",
                "description": "Cadastra um novo fornecedor.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "phone": {"type": "string"},
                        "email": {"type": "string"}
                    },
                    "required": ["name"]
                }
            }
        }
    },
    {
        "permission": "inventory",
        "function": lambda hostel_id, item_name, delta: adjust_inventory_quantity_by_name(hostel_id, item_name, int(delta)),
        "spec": {
            "type": "function",
            "function": {
                "name": "adjust_inventory_quantity",
                "description": "Ajusta a quantidade de um item de estoque pelo nome. Use delta positivo pra adicionar, negativo pra remover/consumir.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "item_name": {"type": "string"},
                        "delta": {"type": "integer", "description": "Quanto somar (positivo) ou subtrair (negativo) da quantidade atual"}
                    },
                    "required": ["item_name", "delta"]
                }
            }
        }
    },
    {
        "permission": "inventory",
        "function": lambda hostel_id, item_name, quantity: propose_supplier_order(hostel_id, item_name, int(quantity)),
        "spec": {
            "type": "function",
            "function": {
                "name": "propose_supplier_order",
                "description": "Monta (mas NÃO envia) uma mensagem de pedido de reposição pro fornecedor de um item de estoque. Sempre use esta ferramenta primeiro e mostre o texto pro usuário antes de confirmar o envio.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "item_name": {"type": "string"},
                        "quantity": {"type": "integer"}
                    },
                    "required": ["item_name", "quantity"]
                }
            }
        }
    },
    {
        "permission": "inventory",
        "function": lambda hostel_id, order_id=None: send_supplier_order(hostel_id, int(order_id) if order_id else None),
        "spec": {
            "type": "function",
            "function": {
                "name": "confirm_and_send_supplier_order",
                "description": "Envia de verdade, por WhatsApp, o pedido de reposição já proposto com propose_supplier_order. SÓ chame depois que o usuário confirmar explicitamente que quer enviar.",
                "parameters": {
                    "type": "object",
                    "properties": {"order_id": {"type": "integer", "description": "Opcional - se não souber, deixe em branco pra usar o pedido pendente mais recente"}}
                }
            }
        }
    },
    {
        "permission": "inventory",
        "function": lambda hostel_id, order_id=None: cancel_pending_supplier_order(hostel_id, int(order_id) if order_id else None),
        "spec": {
            "type": "function",
            "function": {
                "name": "cancel_supplier_order",
                "description": "Cancela um pedido de reposição que ainda não foi enviado ao fornecedor.",
                "parameters": {
                    "type": "object",
                    "properties": {"order_id": {"type": "integer", "description": "Opcional - se não souber, deixe em branco pra usar o pedido pendente mais recente"}}
                }
            }
        }
    },
    {
        "permission": "inventory",
        "function": lambda hostel_id, item_name=None: confirm_supplier_order_received(hostel_id, item_name),
        "spec": {
            "type": "function",
            "function": {
                "name": "confirm_supplier_order_received",
                "description": "Confirma que um pedido enviado ao fornecedor chegou, e dá entrada automática da quantidade pedida no estoque.",
                "parameters": {
                    "type": "object",
                    "properties": {"item_name": {"type": "string", "description": "Nome do item recebido, se houver mais de um pedido em aberto"}}
                }
            }
        }
    },
    {
        "permission": "guests",
        "function": lambda hostel_id, guest_name, message: propose_guest_message(hostel_id, guest_name, message),
        "spec": {
            "type": "function",
            "function": {
                "name": "propose_guest_message",
                "description": "Monta (mas NÃO envia) uma mensagem proativa pra um hóspede. Sempre use esta ferramenta primeiro e mostre o texto pro usuário antes de confirmar o envio.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guest_name": {"type": "string"},
                        "message": {"type": "string", "description": "Texto da mensagem, já pronto e natural, em português"}
                    },
                    "required": ["guest_name", "message"]
                }
            }
        }
    },
    {
        "permission": "guests",
        "function": lambda hostel_id, draft_id=None: send_guest_message(hostel_id, int(draft_id) if draft_id else None),
        "spec": {
            "type": "function",
            "function": {
                "name": "send_guest_message",
                "description": "Envia de verdade, por WhatsApp, a mensagem já proposta com propose_guest_message. SÓ chame depois que o usuário confirmar explicitamente que quer enviar.",
                "parameters": {
                    "type": "object",
                    "properties": {"draft_id": {"type": "integer", "description": "Opcional - se não souber, deixe em branco pra usar o rascunho pendente mais recente"}}
                }
            }
        }
    },
    {
        "permission": "guests",
        "function": lambda hostel_id, draft_id=None: cancel_guest_message_draft(hostel_id, int(draft_id) if draft_id else None),
        "spec": {
            "type": "function",
            "function": {
                "name": "cancel_guest_message",
                "description": "Cancela uma mensagem proativa a um hóspede que ainda não foi enviada.",
                "parameters": {
                    "type": "object",
                    "properties": {"draft_id": {"type": "integer", "description": "Opcional - se não souber, deixe em branco pra usar o rascunho pendente mais recente"}}
                }
            }
        }
    },
    {
        "permission": "operations",
        "function": lambda hostel_id: get_bed_map(hostel_id),
        "spec": {
            "type": "function",
            "function": {
                "name": "get_bed_map",
                "description": "Retorna o mapa de quartos e camas do hostel: cada quarto com suas camas, tipo (normal ou beliche) e status (livre, ocupada, precisa de limpeza).",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    },
    {
        "permission": "operations",
        "function": lambda hostel_id: get_cleaning_list(hostel_id),
        "spec": {
            "type": "function",
            "function": {
                "name": "get_cleaning_list",
                "description": "Lista as camas que estão aguardando limpeza agora (checkout já feito, ainda não foi marcada como limpa).",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    },
    {
        "permission": "operations",
        "function": lambda hostel_id, reservation_id, bed_id: checkin_reservation_to_bed(hostel_id, int(reservation_id), int(bed_id)),
        "spec": {
            "type": "function",
            "function": {
                "name": "checkin_reservation",
                "description": "Faz o check-in de uma reserva numa cama específica, marcando a cama como ocupada. A cama precisa estar livre.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reservation_id": {"type": "integer"},
                        "bed_id": {"type": "integer"}
                    },
                    "required": ["reservation_id", "bed_id"]
                }
            }
        }
    },
    {
        "permission": "operations",
        "function": lambda hostel_id, reservation_id: checkout_reservation_bed(hostel_id, int(reservation_id)),
        "spec": {
            "type": "function",
            "function": {
                "name": "checkout_reservation",
                "description": "Faz o check-out de uma reserva, liberando a cama pra limpeza (ela entra na lista de limpeza automaticamente).",
                "parameters": {
                    "type": "object",
                    "properties": {"reservation_id": {"type": "integer"}},
                    "required": ["reservation_id"]
                }
            }
        }
    },
    {
        "permission": "operations",
        "function": lambda hostel_id, bed_id: mark_bed_cleaned(hostel_id, int(bed_id)),
        "spec": {
            "type": "function",
            "function": {
                "name": "mark_bed_cleaned",
                "description": "Marca uma cama como limpa: ela volta a ficar livre, as roupas de cama sujas vão pra lavanderia e as limpas correspondentes saem do estoque.",
                "parameters": {
                    "type": "object",
                    "properties": {"bed_id": {"type": "integer"}},
                    "required": ["bed_id"]
                }
            }
        }
    },
    {
        "permission": "operations",
        "function": lambda hostel_id, bed_id, under_maintenance=True: set_bed_maintenance(hostel_id, int(bed_id), bool(under_maintenance)),
        "spec": {
            "type": "function",
            "function": {
                "name": "set_bed_maintenance",
                "description": "Coloca uma cama em manutenção (precisa estar livre) ou tira ela da manutenção, devolvendo pra livre.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "bed_id": {"type": "integer"},
                        "under_maintenance": {"type": "boolean", "description": "true pra colocar em manutenção, false pra tirar"}
                    },
                    "required": ["bed_id"]
                }
            }
        }
    },
    {
        "permission": "inventory",
        "function": lambda hostel_id, item_name, quantity: return_items_from_laundry(hostel_id, item_name, int(quantity)),
        "spec": {
            "type": "function",
            "function": {
                "name": "return_items_from_laundry",
                "description": "Registra que roupas de cama voltaram limpas da lavanderia, devolvendo a quantidade pro estoque disponível.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "item_name": {"type": "string"},
                        "quantity": {"type": "integer"}
                    },
                    "required": ["item_name", "quantity"]
                }
            }
        }
    },
    {
        "permission": "operations",
        "function": lambda hostel_id: list_room_categories(hostel_id),
        "spec": {
            "type": "function",
            "function": {
                "name": "get_room_categories",
                "description": "Lista as modalidades de quarto já cadastradas (ex: Standard Duplo, Suíte, Dormitório Misto).",
                "parameters": {"type": "object", "properties": {}}
            }
        }
    },
    {
        "permission": "operations",
        "function": lambda hostel_id, name, capacity=None, price_per_night=None, description=None: create_room_category(hostel_id, name, capacity, price_per_night, description),
        "spec": {
            "type": "function",
            "function": {
                "name": "create_room_category",
                "description": "Cria uma nova modalidade de quarto (ex: 'Standard Duplo', 'Suíte Premium', 'Dormitório Misto 6 camas'). Crie a modalidade antes de criar quartos dela.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "capacity": {"type": "integer", "description": "Quantas pessoas/camas cabem nessa modalidade, opcional"},
                        "price_per_night": {"type": "number", "description": "Preço da diária, usado pela IA de atendimento pra cotar preço real ao hóspede"},
                        "description": {"type": "string", "description": "Ex: 'Inclui café da manhã'"}
                    },
                    "required": ["name"]
                }
            }
        }
    },
    {
        "permission": "operations",
        "function": lambda hostel_id, name, category_name=None, floor=None: create_room(hostel_id, name, category_name, floor),
        "spec": {
            "type": "function",
            "function": {
                "name": "create_room",
                "description": "Cria um único quarto novo, opcionalmente com modalidade e andar.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Nome/número do quarto"},
                        "category_name": {"type": "string"},
                        "floor": {"type": "string"}
                    },
                    "required": ["name"]
                }
            }
        }
    },
    {
        "permission": "operations",
        "function": lambda hostel_id, names, category_name=None, floor=None: create_rooms_bulk(hostel_id, names, category_name, floor),
        "spec": {
            "type": "function",
            "function": {
                "name": "create_rooms_bulk",
                "description": "Cria vários quartos de uma vez, todos com a mesma modalidade/andar. Use pra cadastro rápido de hotéis grandes (ex: 'cria os quartos 201 a 220').",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "names": {"type": "array", "items": {"type": "string"}, "description": "Lista de nomes/números dos quartos"},
                        "category_name": {"type": "string"},
                        "floor": {"type": "string"}
                    },
                    "required": ["names"]
                }
            }
        }
    },
    {
        "permission": "operations",
        "function": lambda hostel_id, room_id, label, bed_kind="single", bunk_group=None: create_bed(hostel_id, int(room_id), label, bed_kind, int(bunk_group) if bunk_group else None),
        "spec": {
            "type": "function",
            "function": {
                "name": "create_bed",
                "description": "Cria uma cama dentro de um quarto. bed_kind: 'single' (normal), 'bunk_top' ou 'bunk_bottom' (beliche - as duas metades do mesmo beliche precisam do mesmo bunk_group).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "room_id": {"type": "integer"},
                        "label": {"type": "string", "description": "Nome/número da cama, ex: 'Cama 1', 'Beliche A - Cima'"},
                        "bed_kind": {"type": "string", "enum": ["single", "bunk_top", "bunk_bottom"]},
                        "bunk_group": {"type": "integer", "description": "Obrigatório se bed_kind for bunk_top/bunk_bottom, pra parear as duas metades do mesmo beliche"}
                    },
                    "required": ["room_id", "label"]
                }
            }
        }
    },
]

MAX_TOOL_ROUNDS = 6


def _default_json(obj):
    return str(obj)


def ask_agent(hostel_id, user_id, history, message):
    """
    Agente do Ask StayFlow - responde perguntas e executa ações reais
    usando dado do hostel, via function calling de verdade (loop
    multi-rodada: chama tool, executa, devolve resultado real, deixa o
    modelo decidir se chama outra ou já responde). hostel_id/user_id
    SEMPRE vem da sessao (nunca de argumento do modelo) - cada tool so
    executa se a permissao efetiva da pessoa incluir o dominio dela.
    Pedido a fornecedor e sempre propose -> (confirmacao do usuario) ->
    send, nunca envia direto - ver SYSTEM_PROMPT.
    """
    permissions = get_effective_permissions(user_id, hostel_id)
    allowed_tools = [t for t in TOOLS_CATALOG if t["permission"] in permissions]
    tools_by_name = {t["spec"]["function"]["name"]: t for t in allowed_tools}
    tool_specs = [t["spec"] for t in allowed_tools]

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + history
        + [{"role": "user", "content": message}]
    )

    for _ in range(MAX_TOOL_ROUNDS):
        kwargs = dict(model="gpt-4.1-mini", temperature=0.3, messages=messages)
        if tool_specs:
            kwargs["tools"] = tool_specs
            kwargs["tool_choice"] = "auto"
        response = client.chat.completions.create(**kwargs)

        response_message = response.choices[0].message

        if not response_message.tool_calls:
            return response_message.content

        messages.append(response_message)

        for tool_call in response_message.tool_calls:
            tool_name = tool_call.function.name
            tool_entry = tools_by_name.get(tool_name)

            if not tool_entry:
                result = {"error": "Ferramenta indisponível ou sem permissão."}
            else:
                try:
                    tool_args = json.loads(tool_call.function.arguments or "{}")
                    result = tool_entry["function"](hostel_id, **tool_args)
                except ValueError as error:
                    result = {"error": str(error)}
                except Exception as error:
                    print(f"Erro ao executar tool '{tool_name}':", error)
                    result = {"error": "Erro interno ao executar essa ação."}

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, default=_default_json, ensure_ascii=False)
            })

    return "Não consegui concluir a análise agora — tente reformular a pergunta ou peça algo mais específico."

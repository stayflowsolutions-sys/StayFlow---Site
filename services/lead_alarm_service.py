import datetime
from zoneinfo import ZoneInfo

from database import claim_lead_alarm, get_due_lead_alarms
from services.push_service import send_push_to_admin

_TIMEZONE = "America/Argentina/Mendoza"


def check_lead_alarms():
    """
    Roda a cada 60s (ver app.py) - checa se algum compromisso da
    Prospeccao entrou na janela de algum dos alarmes configurados
    (alarm_offsets_minutes) e ainda nao foi avisado. Usa hora fixa de
    Mendoza porque essa e uma ferramenta de uso pessoal do dono da
    StayFlow, nao multi-tenant (ver plano aprovado).
    """
    now_local = datetime.datetime.now(ZoneInfo(_TIMEZONE)).replace(tzinfo=None)

    for lead_id, offset_minutes, lead in get_due_lead_alarms(now_local):
        if not claim_lead_alarm(lead_id, offset_minutes):
            continue  # outro worker ja ganhou essa corrida - nao manda de novo

        titulo = lead.get("name") or lead.get("property_name") or "Compromisso"
        hora = lead.get("next_action_time") or ""
        detalhe = f" — {lead['next_action']}" if lead.get("next_action") else ""
        send_push_to_admin(
            f"{titulo} às {hora}",
            f"Começa em {offset_minutes} minutos.{detalhe}",
            url="/admin.html",
        )

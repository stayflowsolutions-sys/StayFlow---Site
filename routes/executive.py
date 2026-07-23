import json
import os
from flask import Blueprint, jsonify, request
from openai import OpenAI
from dotenv import load_dotenv

from database import get_connection
from utils.tenant import require_permission

load_dotenv()

executive_bp = Blueprint("executive", __name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Idioma vem do seletor do Dashboard (?lang=), nao de preferencia do
# hostel - cada pessoa que olha o resumo pode estar num idioma
# diferente. "pt" e sempre o fallback se o valor for invalido/ausente.
LANGUAGE_NAMES = {
    "pt": "Portuguese",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
}

FALLBACK_SUMMARIES = {
    "pt": {
        "main_summary": "O StayFlow identificou atividade operacional recente, com oportunidades abertas que precisam de acompanhamento.",
        "priority_actions": [
            "Priorizar oportunidades com maior score.",
            "Responder hóspedes com urgência alta.",
            "Revisar conversas recentes antes de perder intenção de reserva."
        ],
    },
    "en": {
        "main_summary": "StayFlow identified recent operational activity, with open opportunities that need follow-up.",
        "priority_actions": [
            "Prioritize opportunities with the highest score.",
            "Reply to high-urgency guests.",
            "Review recent conversations before losing booking intent."
        ],
    },
    "es": {
        "main_summary": "StayFlow identificó actividad operativa reciente, con oportunidades abiertas que necesitan seguimiento.",
        "priority_actions": [
            "Priorizar las oportunidades con mayor puntaje.",
            "Responder a los huéspedes con alta urgencia.",
            "Revisar las conversaciones recientes antes de perder la intención de reserva."
        ],
    },
    "fr": {
        "main_summary": "StayFlow a identifié une activité opérationnelle récente, avec des opportunités ouvertes qui nécessitent un suivi.",
        "priority_actions": [
            "Prioriser les opportunités avec le meilleur score.",
            "Répondre aux clients à forte urgence.",
            "Vérifier les conversations récentes avant de perdre l'intention de réservation."
        ],
    },
    "de": {
        "main_summary": "StayFlow hat kürzliche Betriebsaktivität erkannt, mit offenen Chancen, die eine Nachverfolgung benötigen.",
        "priority_actions": [
            "Chancen mit dem höchsten Score priorisieren.",
            "Gästen mit hoher Dringlichkeit antworten.",
            "Aktuelle Unterhaltungen prüfen, bevor die Buchungsabsicht verloren geht."
        ],
    },
}


def fallback_summary(stats, lang="pt"):
    base = FALLBACK_SUMMARIES.get(lang, FALLBACK_SUMMARIES["pt"])
    return {
        "main_summary": base["main_summary"],
        "priority_actions": base["priority_actions"],
        "revenue_opportunity": stats.get("revenue_opportunity", 0),
        "risk_level": "medium"
    }


@executive_bp.route("/executive-summary", methods=["GET"])
@require_permission("dashboard")
def executive_summary(hostel_id):
    lang = request.args.get("lang", "pt")
    if lang not in LANGUAGE_NAMES:
        lang = "pt"
    language_name = LANGUAGE_NAMES[lang]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) AS total_guests FROM guests WHERE hostel_id = ?",
        (hostel_id,)
    )
    total_guests = cursor.fetchone()["total_guests"]

    cursor.execute("""
        SELECT COUNT(*) AS total_messages
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        JOIN guests g ON c.guest_id = g.id
        WHERE g.hostel_id = ?
    """, (hostel_id,))
    total_messages = cursor.fetchone()["total_messages"]

    cursor.execute("""
        SELECT COUNT(*) AS open_opportunities
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ? AND o.status = 'open'
    """, (hostel_id,))
    open_opportunities = cursor.fetchone()["open_opportunities"]

    cursor.execute("""
        SELECT COALESCE(SUM(o.estimated_value), 0) AS revenue_opportunity
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ? AND o.status = 'open'
    """, (hostel_id,))
    revenue_opportunity = cursor.fetchone()["revenue_opportunity"]

    cursor.execute("""
        SELECT
            o.type, o.description, o.score, o.urgency,
            o.estimated_value, o.next_action, g.phone
        FROM opportunities o
        JOIN guests g ON o.guest_id = g.id
        WHERE g.hostel_id = ? AND o.status = 'open'
        ORDER BY o.score DESC, o.created_at DESC
        LIMIT 5
    """, (hostel_id,))
    opportunities = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT g.phone, m.sender, m.message, m.created_at
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        JOIN guests g ON c.guest_id = g.id
        WHERE g.hostel_id = ?
        ORDER BY m.created_at DESC, m.id DESC
        LIMIT 8
    """, (hostel_id,))
    recent_messages = [dict(row) for row in cursor.fetchall()]

    conn.close()

    stats = {
        "total_guests": total_guests,
        "total_messages": total_messages,
        "open_opportunities": open_opportunities,
        "revenue_opportunity": revenue_opportunity,
        "opportunities": opportunities,
        "recent_messages": recent_messages
    }

    prompt = f"""
Você é o gerente digital inteligente do StayFlow, um SaaS premium para hotelaria.

Analise os dados reais abaixo, referentes exclusivamente a UM hostel,
e gere um resumo executivo para o gestor desse hostel.

Dados:
{json.dumps(stats, ensure_ascii=False)}

Retorne somente JSON válido neste formato:

{{
  "main_summary": "resumo curto e claro, em {language_name}",
  "priority_actions": [
    "ação 1, em {language_name}",
    "ação 2, em {language_name}",
    "ação 3, em {language_name}"
  ],
  "revenue_opportunity": 0,
  "risk_level": "low | medium | high"
}}

Regras:
- Seja objetivo.
- Foque em dinheiro, risco e ações práticas.
- Não invente dados que não estejam na base.
- Escreva main_summary e priority_actions em {language_name}, mesmo que os dados de entrada estejam em português.
- risk_level continua sempre em inglês (low/medium/high), nunca traduza esse valor.
- Retorne somente JSON.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": f"Você é o motor executivo do StayFlow. Retorne somente JSON válido, com main_summary e priority_actions escritos em {language_name}."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.choices[0].message.content.strip()

        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        summary = json.loads(content)

    except Exception as error:
        print("Executive Summary error:", error)
        summary = fallback_summary(stats, lang)

    return jsonify(summary)
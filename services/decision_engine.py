import json
import os
from openai import OpenAI
from dotenv import load_dotenv

from database import get_connection

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def fallback_analysis(message):
    return {
        "intent": "general",
        "score": 0,
        "urgency": "low",
        "estimated_value": 0,
        "description": "Não foi possível analisar a mensagem com segurança.",
        "next_action": "Revisar manualmente a conversa."
    }


def analyze_with_ai(message):
    prompt = f"""
Analyze this hostel guest message and return ONLY valid JSON.

Message:
{message}

Return this exact structure:
{{
  "intent": "booking",
  "score": 94,
  "urgency": "high",
  "estimated_value": 420,
  "description": "Cliente demonstrou alta intenção de reservar.",
  "next_action": "Responder em até 10 minutos."
}}

Rules:
- intent must be one of: booking, tour, upsell, human_help, follow_up, general
- score must be a number from 0 to 100
- urgency must be one of: low, medium, high
- estimated_value must be a number
- description must be in Portuguese
- next_action must be in Portuguese
- return only JSON, no markdown, no explanation
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": "You are StayFlow's decision engine for hospitality operations. Always return only valid JSON."
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

        return json.loads(content)

    except Exception as error:
        print("Decision Engine error:", error)
        return fallback_analysis(message)


def analyze_message(hostel_id, phone, message):
    analysis = analyze_with_ai(message)

    if analysis.get("intent") == "general":
        return analysis

    conn = get_connection()
    cursor = conn.cursor()

    # busca o hóspede SEMPRE escopado por hostel_id — sem isso,
    # a oportunidade poderia ser gravada no hóspede errado (de
    # outro hostel) se o telefone coincidisse.
    cursor.execute(
        "SELECT id FROM guests WHERE hostel_id = ? AND phone = ?",
        (hostel_id, phone)
    )

    guest = cursor.fetchone()

    if not guest:
        conn.close()
        return analysis

    cursor.execute(
        """
        INSERT INTO opportunities
        (
            guest_id,
            type,
            description,
            status,
            score,
            urgency,
            estimated_value,
            next_action
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            guest["id"],
            analysis.get("intent"),
            analysis.get("description"),
            "open",
            analysis.get("score", 0),
            analysis.get("urgency", "low"),
            analysis.get("estimated_value", 0),
            analysis.get("next_action")
        )
    )

    conn.commit()
    conn.close()

    return analysis
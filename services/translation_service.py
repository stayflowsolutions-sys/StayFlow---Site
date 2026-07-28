import json
import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LANGUAGE_NAMES = {
    "pt": "Portuguese",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
}


def translate_texts(texts, lang):
    """
    Traduz uma lista de textos curtos (gerados pela IA em portugues no
    momento em que foram criados - ex: description/next_action de
    oportunidades) pro idioma atual de quem esta OLHANDO o Dashboard,
    numa unica chamada em lote (nao uma por texto, pra nao multiplicar
    latencia/custo a cada carregamento de pagina). "pt" (idioma em que
    o texto ja foi gerado) e um passthrough sem custo nenhum.

    Se a traducao falhar por qualquer motivo, devolve os textos
    originais - preferimos mostrar o texto certo no idioma errado a
    quebrar a tela.
    """
    if lang not in LANGUAGE_NAMES or lang == "pt":
        return list(texts)

    non_empty = [(i, t) for i, t in enumerate(texts) if t]
    if not non_empty:
        return list(texts)

    language_name = LANGUAGE_NAMES[lang]
    payload = {str(i): t for i, t in non_empty}

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You translate short hospitality-operations phrases from "
                        f"Portuguese to {language_name}. Return ONLY a valid JSON "
                        f"object mapping each input key to its translation, same "
                        f"keys, no extra text, no markdown."
                    )
                },
                {
                    "role": "user",
                    "content": json.dumps(payload, ensure_ascii=False)
                }
            ]
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        translated = json.loads(content)

        result = list(texts)
        for i, _ in non_empty:
            key = str(i)
            if key in translated and translated[key]:
                result[i] = translated[key]
        return result

    except Exception as error:
        print("Translation error:", error)
        return list(texts)


def translate_opportunity_fields(opportunities, lang):
    """
    Traduz description/next_action de uma lista de oportunidades (dict
    com essas chaves) in-place, devolvendo a mesma lista. Uma unica
    chamada em lote pra todos os campos de todas as oportunidades.
    """
    if lang not in LANGUAGE_NAMES or lang == "pt" or not opportunities:
        return opportunities

    descriptions = [o.get("description") or "" for o in opportunities]
    next_actions = [o.get("next_action") or "" for o in opportunities]

    translated_descriptions = translate_texts(descriptions, lang)
    translated_next_actions = translate_texts(next_actions, lang)

    for o, desc, action in zip(opportunities, translated_descriptions, translated_next_actions):
        if o.get("description"):
            o["description"] = desc
        if o.get("next_action"):
            o["next_action"] = action

    return opportunities

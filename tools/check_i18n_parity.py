"""
Confere que todo idioma, em cada um dos 3 dicionarios de traducao do
frontend, tem exatamente o mesmo conjunto de chaves - sem isso, uma
chave nova esquecida num idioma so aparece quebrada em producao, pra
quem usa aquele idioma especifico. Nao existia nenhuma rede de
seguranca automatica antes (a paridade dos idiomas ate aqui era so
disciplina manual).

Uso: python tools/check_i18n_parity.py
Saida: 0 e "OK" quando todos os idiomas tem as mesmas chaves em cada
dicionario; senao lista o que falta/sobra por idioma e sai com codigo 1.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SOURCES = [
    {
        "label": "i18n-landing-data.js",
        "path": ROOT / "assets" / "js" / "i18n-landing-data.js",
        "block_indent": "  ",
    },
    {
        "label": "i18n-dashboard-data.js",
        "path": ROOT / "assets" / "js" / "i18n-dashboard-data.js",
        "block_indent": "  ",
    },
    {
        "label": "admin.html (ADMIN_I18N)",
        "path": ROOT / "admin.html",
        "block_indent": "    ",
    },
]

LANG_HEADER_RE_TEMPLATE = r"(?m)^{indent}([a-z]{{2}}): \{{\n"


def _find_matching_brace(text, open_brace_pos):
    """Anda a partir de um '{' de abertura ate o '}' correspondente,
    ignorando chaves dentro de literais de string (aspas simples/duplas,
    respeitando escape) - necessario porque valores como "ARS {price}/mes"
    tem chave dentro de string, que nao deve contar pro balanceamento."""
    depth = 0
    i = open_brace_pos
    in_string = None
    escaped = False
    while i < len(text):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_string:
                in_string = None
        else:
            if ch in ("'", '"'):
                in_string = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    raise ValueError("Chave de abertura sem fechamento correspondente encontrado.")


def extract_language_blocks(text, block_indent):
    header_re = re.compile(LANG_HEADER_RE_TEMPLATE.format(indent=block_indent))
    blocks = {}
    for match in header_re.finditer(text):
        lang = match.group(1)
        open_brace_pos = match.end() - 2  # posicao do "{" que abre o bloco (match termina em "{\n")
        close_brace_pos = _find_matching_brace(text, open_brace_pos)
        block_text = text[open_brace_pos + 1:close_brace_pos]
        blocks[lang] = block_text
    return blocks


def extract_keys(block_text):
    return set(re.findall(r'"([a-zA-Z0-9_.]+)"\s*:', block_text))


def check_source(source):
    text = source["path"].read_text(encoding="utf-8")
    blocks = extract_language_blocks(text, source["block_indent"])

    if not blocks:
        print(f"[{source['label']}] AVISO: nenhum bloco de idioma encontrado - verifique o parser.")
        return False

    keys_by_lang = {lang: extract_keys(block) for lang, block in blocks.items()}
    all_keys = set()
    for keys in keys_by_lang.values():
        all_keys |= keys

    ok = True
    print(f"[{source['label']}] idiomas encontrados: {sorted(keys_by_lang)} ({len(all_keys)} chaves no total)")
    for lang, keys in sorted(keys_by_lang.items()):
        missing = all_keys - keys
        extra = keys - all_keys  # sempre vazio por construcao, mantido por clareza
        if missing:
            ok = False
            print(f"  - {lang}: FALTAM {len(missing)} chaves: {sorted(missing)[:10]}{' ...' if len(missing) > 10 else ''}")
    if ok:
        print(f"  OK - todos os {len(keys_by_lang)} idiomas com as mesmas {len(all_keys)} chaves.")
    return ok


def main():
    overall_ok = True
    for source in SOURCES:
        if not check_source(source):
            overall_ok = False
        print()

    if overall_ok:
        print("OK - paridade de chaves confirmada em todos os dicionarios.")
        return 0

    print("FALHOU - existem chaves faltando (ver acima).")
    return 1


if __name__ == "__main__":
    sys.exit(main())

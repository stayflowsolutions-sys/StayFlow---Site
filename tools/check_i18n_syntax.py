"""
Confere que os dicionarios de i18n (assets/js/i18n-*.js) sao JS
sintaticamente validos - especificamente, que nenhuma linha
"chave": "valor" fica sem virgula antes da proxima linha do mesmo
tipo (ou de um comentario seguido de outra linha do mesmo tipo).

Motivado por um bug real de producao (09/09/2026): uma virgula
faltando entre "home.priorityActions.emptyDesc" e um comentario
"// ==== Chaves faltando ====" quebrou o parse do arquivo INTEIRO
(erro "Unexpected string" no navegador), derrubando STAYFLOW_
DASHBOARD_I18N por completo - e tools/check_i18n_parity.py, que e
baseado em regex e nunca executa o arquivo como JS de verdade, nunca
pegou esse tipo de erro (extrai as chaves com ou sem virgula do
mesmo jeito). Esse script fecha esse buraco especifico.

Nao e um parser de JS completo (não tenta validar todo o resto da
sintaxe) - so cobre o padrao real que já causou um bug: duas linhas
"chave": "valor" seguidas sem virgula entre elas, direto ou separadas
so por comentario(s)/linha(s) em branco.

Uso: python tools/check_i18n_syntax.py
Saida: 0 e "OK" se nenhum problema for encontrado; senao lista
arquivo:linha de cada virgula faltando e sai com codigo 1.
"""

import re
import sys
from pathlib import Path

# Console do Windows (cp1252/cp850) nao imprime CJK/cirilico direto -
# os dicionarios tem chines/japones/coreano/russo, entao qualquer
# problema reportado nessas linhas quebraria o proprio script de
# checagem sem isso.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

FILES = [
    ROOT / "assets" / "js" / "i18n-landing-data.js",
    ROOT / "assets" / "js" / "i18n-dashboard-data.js",
]

# Uma linha "chave": "valor" (aspas duplas, permite escapes \" dentro do
# valor) - mesmo padrao usado em todo o arquivo, incluindo linhas que já
# terminam com vírgula (capturada à parte).
KV_LINE_RE = re.compile(r'^\s*"(?:[^"\\]|\\.)+"\s*:\s*"(?:[^"\\]|\\.)*"(,)?\s*$')
COMMENT_OR_BLANK_RE = re.compile(r'^\s*(//.*)?\s*$')
CLOSING_BRACE_RE = re.compile(r'^\s*\}')


def check_file(path):
    if not path.exists():
        print(f"[{path.name}] AVISO: arquivo nao encontrado, pulando.")
        return True

    lines = path.read_text(encoding="utf-8").split("\n")
    problems = []

    for i, line in enumerate(lines):
        m = KV_LINE_RE.match(line)
        if not m or m.group(1):
            continue  # nao e linha "chave":"valor", ou ja tem virgula - ok

        # Acha a proxima linha "significativa" (pula comentarios/em branco)
        j = i + 1
        while j < len(lines) and COMMENT_OR_BLANK_RE.match(lines[j]):
            j += 1
        if j >= len(lines):
            continue

        next_line = lines[j]
        if KV_LINE_RE.match(next_line) or CLOSING_BRACE_RE.match(next_line) is None and next_line.strip().startswith('"'):
            # proxima linha significativa tambem parece uma entrada de
            # chave/valor (ou comeca com aspas, ex: chave sem virgula
            # antes de uma chave que nao bateu no regex por algum
            # motivo) - virgula faltando confirmada.
            if not CLOSING_BRACE_RE.match(next_line):
                problems.append((i + 1, line.strip(), j + 1, next_line.strip()))

    if problems:
        print(f"[{path.name}] {len(problems)} virgula(s) faltando encontrada(s):")
        for line_no, line_text, next_no, next_text in problems:
            print(f"  - linha {line_no}: {line_text[:70]}")
            print(f"    (seguida por linha {next_no} sem virgula antes: {next_text[:70]})")
        return False

    print(f"[{path.name}] OK - nenhuma virgula faltando encontrada.")
    return True


def main():
    overall_ok = True
    for path in FILES:
        if not check_file(path):
            overall_ok = False
        print()

    if overall_ok:
        print("OK - sintaxe dos dicionarios i18n parece valida.")
        return 0

    print("FALHOU - virgula faltando encontrada (ver acima). Isso quebra o arquivo JS INTEIRO no navegador.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

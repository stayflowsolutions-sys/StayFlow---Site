"""
Confere que todo arquivo estatico (.css/.js) MODIFICADO no working tree
teve o numero de versao (?v=NNNN) bumpado em TODA pagina HTML que o
referencia - sem isso, o navegador de quem ja visitou o site continua
servindo a copia em cache antiga, nao importa quantas vezes o servidor
seja republicado.

Motivado por um incidente real (09/09/2026): static/css/app.css foi
editado 3 vezes ao longo do dia sem o "?v=1133" no <link> nunca ser
atualizado - nenhuma correcao chegava a ser vista pelo usuario, que
passou horas testando o que parecia ser o mesmo bug "voltando".
Mesma categoria de erro ja tinha acontecido antes nesta sessao com
i18n-dashboard-data.js (?v=1144 parado por dias).

Uso: python tools/check_cache_busting.py
Compara o working tree contra HEAD (git diff). Saida: 0 e "OK" se
todo asset estatico modificado teve o cache-busting bumpado em toda
pagina que o referencia; senao lista arquivo:pagina e sai com codigo 1.

Limitacao conhecida: so pega asset referenciado via "?v=NUMERO" no
proprio <link>/<script src>. Nao sabe de CDN/proxy externo, so cache
de navegador via query string.
"""

import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

# Extensoes que fazem sentido cache-bustar - imagens/fontes nao usam
# esse padrao no projeto, so CSS/JS.
STATIC_EXTENSIONS = (".css", ".js")

VERSION_REF_RE = re.compile(r'(?:href|src)="([^"?]+\.(?:css|js))\?v=(\d+)"')


def run_git(*args):
    result = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, encoding="utf-8")
    return result.stdout


def _git_prefix():
    """
    Prefixo desta pasta relativo a raiz do repositorio git (ex:
    "StayFlow---Site/" quando este script roda dentro do subtree
    copiado pra dentro do repo do backend; string vazia quando ROOT
    JA E a raiz do repo, como no repositorio canonico standalone).
    Necessario porque `git show HEAD:caminho` sempre espera caminho
    relativo a RAIZ DO REPO, nunca ao cwd - diferente de `git diff
    --relative`, que ja resolve isso sozinho.
    """
    return run_git("rev-parse", "--show-prefix").strip()


def modified_static_files():
    """Arquivos .css/.js modificados no working tree (staged + unstaged), relativos a ROOT."""
    names = set()
    for cmd in (["diff", "--relative", "--name-only", "HEAD"], ["diff", "--relative", "--cached", "--name-only"]):
        output = run_git(*cmd)
        for line in output.splitlines():
            line = line.strip()
            if line.endswith(STATIC_EXTENSIONS):
                names.add(line)
    return names


def html_files():
    return sorted(ROOT.glob("*.html"))


def extract_versions(text):
    """{asset_relative_path: version_str} pra todas as referencias ?v= num texto de HTML."""
    versions = {}
    for match in VERSION_REF_RE.finditer(text):
        asset_path, version = match.groups()
        versions[asset_path.lstrip("/")] = version
    return versions


def old_html_text(html_path, git_prefix):
    rel = html_path.relative_to(ROOT).as_posix()
    return run_git("show", f"HEAD:{git_prefix}{rel}")


def main():
    modified = modified_static_files()
    if not modified:
        print("Nenhum .css/.js modificado no working tree - nada pra checar.")
        return 0

    print(f"Assets estaticos modificados: {sorted(modified)}\n")

    git_prefix = _git_prefix()
    problems = []
    for html_path in html_files():
        rel_html = html_path.name
        try:
            old_text = old_html_text(html_path, git_prefix)
        except Exception:
            continue  # arquivo novo, sem HEAD pra comparar - pula
        new_text = html_path.read_text(encoding="utf-8")

        old_versions = extract_versions(old_text)
        new_versions = extract_versions(new_text)

        for asset_path, new_version in new_versions.items():
            # o asset foi modificado nesta sessao?
            if not any(asset_path.endswith(m) or m.endswith(asset_path) for m in modified):
                continue
            old_version = old_versions.get(asset_path)
            if old_version is not None and old_version == new_version:
                problems.append((asset_path, rel_html, new_version))

    if problems:
        print("FALHOU - asset modificado sem cache-busting atualizado:\n")
        for asset_path, rel_html, version in problems:
            print(f"  - {asset_path} (referenciado em {rel_html}) continua em ?v={version}")
        print("\nBumpe o numero de versao no <link>/<script src> de cada pagina listada antes de publicar.")
        return 1

    print("OK - todo asset estatico modificado teve o cache-busting atualizado nas paginas que o referenciam.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

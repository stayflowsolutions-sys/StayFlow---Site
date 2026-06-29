from pathlib import Path

css_path = Path("static/css/legacy.css")
content = css_path.read_text(encoding="utf-8", errors="ignore")

print("LEGACY SIZE:", len(content))
print("OK - builder funcionando")

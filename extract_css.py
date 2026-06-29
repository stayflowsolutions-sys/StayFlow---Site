from pathlib import Path 
 
css = Path("static/css/legacy.css").read_text(encoding="utf-8", errors="ignore") 
 
lines = css.split("\n") 
root = [] 
rest = [] 
in_root = False 
 
for line in lines: 
    if ":root" in line: 
        in_root = True 
    if in_root: 
        root.append(line) 
    else: 
        rest.append(line) 
    if in_root and "}" in line: 
        in_root = False 
 
Path("static/css/base.css").write_text("\n".join(root), encoding="utf-8") 
Path("static/css/legacy.css").write_text("\n".join(rest), encoding="utf-8") 
 
print("OK - CSS separado com sucesso") 

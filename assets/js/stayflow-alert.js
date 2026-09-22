// Substitui alert()/confirm()/prompt() nativos por um modal com a cara
// do StayFlow (caixa azul, nao a caixa branca do sistema operacional).
// window.alert vira um override direto (nenhum lugar do codigo depende
// do valor de retorno de alert(), so de ela aparecer) -
// stayflowConfirm/stayflowPrompt sao Promises novas porque um modal de
// verdade nao consegue bloquear a thread como confirm()/prompt()
// nativos bloqueiam; call-sites que usavam confirm()/prompt() nativos
// viram "await stayflowConfirm(...)"/"await stayflowPrompt(...)"
// dentro de funcoes async.
//
// Extraido de dashboard.html (v1.157.0) pra ser compartilhado por
// qualquer pagina que precise do mesmo modal (admin.html,
// admin-hostel.html, etc) - exige o markup #sfAlertOverlay (ver
// dashboard.html) e o CSS .sf-alert-* (ja em static/css/app.css)
// presentes na pagina. "T" e opcional (nem toda pagina tem essa funcao
// de i18n - admin.html usa "AT" em vez disso) - por isso o fallback do
// texto do botao Cancelar checa "typeof T" antes de chamar, pra nunca
// estourar ReferenceError numa pagina sem "T" global.
let sfAlertResolve = null;

function sfAlertClose(value){
  const overlay = document.getElementById("sfAlertOverlay");
  if(overlay) overlay.classList.remove("open");
  if(sfAlertResolve){
    const resolve = sfAlertResolve;
    sfAlertResolve = null;
    resolve(value);
  }
}

function sfAlertOpen({ message, showCancel, showInput, defaultValue, okLabel, cancelLabel }){
  const overlay = document.getElementById("sfAlertOverlay");
  const msgEl = document.getElementById("sfAlertMessage");
  const inputEl = document.getElementById("sfAlertInput");
  const actionsEl = document.getElementById("sfAlertActions");
  if(!overlay || !msgEl || !inputEl || !actionsEl){
    // Fallback extremo (HTML do modal nao carregou por algum motivo) -
    // nunca deixa a acao travada sem nenhum jeito de responder.
    if(showInput) return Promise.resolve(window.prompt(message, defaultValue));
    if(showCancel) return Promise.resolve(window.confirm(message));
    window.alert(message);
    return Promise.resolve(true);
  }

  msgEl.textContent = message;
  inputEl.style.display = showInput ? "block" : "none";
  inputEl.value = showInput ? (defaultValue || "") : "";

  actionsEl.innerHTML = "";
  if(showCancel){
    const cancelBtn = document.createElement("button");
    cancelBtn.type = "button";
    cancelBtn.className = "btn secondary";
    cancelBtn.textContent = cancelLabel || (typeof T === "function" ? T("common.cancel", "Cancelar") : "Cancelar");
    cancelBtn.onclick = () => sfAlertClose(showInput ? null : false);
    actionsEl.appendChild(cancelBtn);
  }
  const okBtn = document.createElement("button");
  okBtn.type = "button";
  okBtn.className = "btn";
  okBtn.textContent = okLabel || "OK";
  okBtn.onclick = () => sfAlertClose(showInput ? inputEl.value : true);
  actionsEl.appendChild(okBtn);

  if(showInput){
    inputEl.onkeydown = (e) => { if(e.key === "Enter") sfAlertClose(inputEl.value); };
  }

  overlay.classList.add("open");
  setTimeout(() => (showInput ? inputEl : okBtn).focus(), 50);

  return new Promise(resolve => { sfAlertResolve = resolve; });
}

window.alert = function(message){
  sfAlertOpen({ message: String(message), showCancel: false });
};

window.stayflowConfirm = function(message, opts){
  return sfAlertOpen({ message: String(message), showCancel: true, okLabel: opts && opts.okLabel, cancelLabel: opts && opts.cancelLabel });
};

window.stayflowPrompt = function(message, defaultValue){
  return sfAlertOpen({ message: String(message), showCancel: true, showInput: true, defaultValue });
};

document.addEventListener("keydown", (e) => {
  if(e.key === "Escape"){
    const overlay = document.getElementById("sfAlertOverlay");
    if(overlay && overlay.classList.contains("open")) sfAlertClose(null);
  }
});

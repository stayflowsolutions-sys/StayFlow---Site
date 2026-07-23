// StayFlow - Chats live integration
// Consome /chats e /guests/<id> para alimentar a aba "Chats".

let stayflowCurrentGuestId = null;

// ===== Divisores de data no chat (estilo WhatsApp) =====
// created_at vem do backend como "YYYY-MM-DD HH:MM:SS" (timezone local
// do servidor). Comparamos só a parte da data (dia/mês/ano), sem
// conversão de timezone — mesma lógica simples que apps de chat usam
// pra agrupar por dia.
function stayflowParseServerDate(dateStr) {
    if (!dateStr) return null;
    const d = new Date(String(dateStr).replace(" ", "T"));
    return isNaN(d.getTime()) ? null : d;
}

function stayflowDayKey(dateStr) {
    const d = stayflowParseServerDate(dateStr);
    if (!d) return null;
    return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
}

// ===== Bandeira do país a partir do código de discagem =====
// Chave = código de discagem sem o "+". Checamos do prefixo mais
// longo (3 dígitos) pro mais curto (1 dígito) porque vários códigos
// compartilham o começo (ex.: 591/593/595/598 começam com "59").
const STAYFLOW_COUNTRY_FLAGS = {
    // América do Sul
    "55": "🇧🇷",   // Brasil
    "54": "🇦🇷",   // Argentina
    "595": "🇵🇾",  // Paraguai
    "598": "🇺🇾",  // Uruguai
    "56": "🇨🇱",   // Chile
    "51": "🇵🇪",   // Peru
    "57": "🇨🇴",   // Colômbia
    "58": "🇻🇪",   // Venezuela
    "593": "🇪🇨",  // Equador
    "591": "🇧🇴",  // Bolívia
    "597": "🇸🇷",  // Suriname
    "592": "🇬🇾",  // Guiana
    "594": "🇬🇫",  // Guiana Francesa
    // América do Norte / Central
    "1": "🇺🇸",    // EUA/Canadá (código compartilhado do NANP)
    "52": "🇲🇽",   // México
    "506": "🇨🇷",  // Costa Rica
    "507": "🇵🇦",  // Panamá
    // Europa
    "34": "🇪🇸",   // Espanha
    "351": "🇵🇹",  // Portugal
    "44": "🇬🇧",   // Reino Unido
    "33": "🇫🇷",   // França
    "49": "🇩🇪",   // Alemanha
    "39": "🇮🇹",   // Itália
    // Outros comuns
    "81": "🇯🇵",   // Japão
    "86": "🇨🇳",   // China
    "91": "🇮🇳",   // Índia
    "61": "🇦🇺",   // Austrália
    "7": "🇷🇺",    // Rússia
};

function stayflowCountryFlag(phone) {
    if (!phone) return "";
    const match = String(phone).match(/^\+?(\d{1,3})/);
    if (!match) return "";
    const numDigits = match[1];
    for (let len = 3; len >= 1; len--) {
        const code = numDigits.slice(0, len);
        if (STAYFLOW_COUNTRY_FLAGS[code]) return STAYFLOW_COUNTRY_FLAGS[code];
    }
    return "";
}

function stayflowFormatDateDivider(dateStr) {
    const msgDate = stayflowParseServerDate(dateStr);
    if (!msgDate) return "";

    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(today.getDate() - 1);

    const sameDay = (a, b) =>
        a.getFullYear() === b.getFullYear() &&
        a.getMonth() === b.getMonth() &&
        a.getDate() === b.getDate();

    if (sameDay(msgDate, today)) return "Hoje";
    if (sameDay(msgDate, yesterday)) return "Ontem";

    const months = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
    const label = `${msgDate.getDate()} de ${months[msgDate.getMonth()]}`;

    // Ano só aparece se for diferente do ano atual (mensagem "5 de
    // julho" de hoje não precisa de ano; uma de 2025 precisa, senão
    // fica ambíguo).
    return msgDate.getFullYear() !== today.getFullYear()
        ? `${label} de ${msgDate.getFullYear()}`
        : label;
}

async function loadChats() {
    try {
        const response = await fetch("/chats");
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const chats = await response.json();
        console.log("StayFlow chats:", chats);

        const list = document.getElementById("realChatList");
        if (!list) return;

        list.innerHTML = "<h2>Conversas</h2>";

        if (!chats.length) {
            const empty = document.createElement("div");
            empty.className = "chat-item";
            empty.innerHTML = `
                <div class="chat-name">
                    <span>Nenhuma conversa encontrada.</span>
                    <span class="status-pill ai">Live</span>
                </div>
                <div class="chat-preview">Quando houver mensagens, elas aparecerão aqui.</div>
            `;
            list.appendChild(empty);
            return;
        }

        chats.forEach(chat => {
            const item = document.createElement("div");
            item.className = "chat-item sf-clickable-row";
            item.dataset.guestId = chat.guest_id;

            const lastMessage = chat.last_message || "";
            const preview = lastMessage.length > 90
                ? lastMessage.slice(0, 90) + "..."
                : lastMessage;

            const intent = chat.intent || "-";
            const urgency = (chat.urgency || "low").toLowerCase();
            const score = chat.score ?? 0;
            const flag = stayflowCountryFlag(chat.phone);

            item.innerHTML = `
                <div class="chat-name">
                    <span>${flag ? flag + " " : ""}${chat.name || chat.phone || "Sem telefone"}</span>
                    <span class="status-pill ${urgency}">
                        ${intent} · ${score}/100
                    </span>
                </div>
                <div class="chat-preview">${preview || "Sem mensagens recentes."}</div>
            `;

            item.addEventListener("click", () => {
                document.querySelectorAll("#realChatList .chat-item").forEach(el => el.classList.remove("active"));
                item.classList.add("active");
                loadGuestProfile(chat.guest_id);
            });

            list.appendChild(item);
        });

        // Seleciona automaticamente o primeiro chat, se existir
        const first = list.querySelector(".chat-item");
        if (first && chats[0]) {
            first.classList.add("active");
            loadGuestProfile(chats[0].guest_id);
        }

    } catch (err) {
        console.error("Erro ao carregar chats:", err);
        const list = document.getElementById("realChatList");
        if (list) {
            list.innerHTML = `
                <h2>Conversas</h2>
                <div class="chat-item">
                    <div class="chat-name">
                        <span>Erro ao carregar conversas.</span>
                        <span class="status-pill ai">Erro</span>
                    </div>
                    <div class="chat-preview">Tente novamente mais tarde.</div>
                </div>
            `;
        }
    }
}

async function loadGuestProfile(guestId) {
    try {
        const response = await fetch(`/guests/${guestId}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        console.log("StayFlow guest profile:", data);

        const guest = data.guest || {};
        const messages = data.messages || [];
        const opportunities = data.opportunities || [];

        stayflowCurrentGuestId = guest.id || guestId;

        const takeoverBtn = document.getElementById("chatTakeoverBtn");
        if (takeoverBtn) {
            takeoverBtn.style.display = "inline-flex";
            takeoverBtn.textContent = guest.ai_paused ? "Devolver pra IA" : "Assumir conversa";
            takeoverBtn.classList.toggle("secondary", !guest.ai_paused);
        }

        // Título da conversa
        const chatTitle = document.getElementById("chatTitle");
        if (chatTitle) {
            const flag = stayflowCountryFlag(guest.phone);
            chatTitle.textContent = `Conversa · ${flag ? flag + " " : ""}${guest.name || guest.phone || "Hóspede"}`;
        }

        // Mensagens
        const chatMessages = document.getElementById("chatMessages");
        if (chatMessages) {
            chatMessages.innerHTML = "";
            if (!messages.length) {
                chatMessages.innerHTML = `<div class="msg bot">Nenhuma mensagem registrada para este hóspede.</div>`;
            } else {
                let lastDayKey = null;
                messages.forEach(msg => {
                    const dayKey = stayflowDayKey(msg.created_at);
                    if (dayKey && dayKey !== lastDayKey) {
                        const divider = document.createElement("div");
                        divider.className = "date-divider";
                        divider.innerHTML = `<span>${stayflowFormatDateDivider(msg.created_at)}</span>`;
                        chatMessages.appendChild(divider);
                        lastDayKey = dayKey;
                    }

                    const div = document.createElement("div");
                    div.className = `msg ${msg.sender === "user" ? "user" : "bot"}`;
                    div.textContent = msg.message;
                    chatMessages.appendChild(div);
                });
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }

        // Perfil do hóspede (painel direito)
        const guestName = document.getElementById("guestName");
        const guestSubtitle = document.getElementById("guestSmartSubtitle");
        const guestPhone = document.getElementById("guestPhone");
        const guestIntentTag = document.getElementById("guestIntentTag");
        const guestUrgencyTag = document.getElementById("guestUrgencyTag");
        const guestPayment = document.getElementById("guestPayment");
        const guestValue = document.getElementById("guestValue");
        const guestStatus = document.getElementById("guestStatus");
        const guestMessageCount = document.getElementById("guestMessageCount");
        const guestNotes = document.getElementById("guestNotes");
        const guestNextAction = document.getElementById("guestNextAction");
        const guestAIHistory = document.getElementById("guestAIHistory");

        if (guestName) guestName.textContent = guest.name || guest.phone || "Hóspede";
        if (guestSubtitle) guestSubtitle.textContent = "Perfil consolidado a partir das mensagens reais.";

        if (guestPhone) guestPhone.textContent = guest.phone || "-";

        // Usa a oportunidade mais recente, se existir
        const lastOpp = opportunities[0] || null;

        if (guestIntentTag) {
            guestIntentTag.textContent = `Intenção: ${lastOpp ? lastOpp.type : "-"}`;
        }
        if (guestUrgencyTag) {
            guestUrgencyTag.textContent = `Urgência: ${lastOpp ? lastOpp.urgency : "baixa"}`;
        }

        if (guestPayment) {
            guestPayment.textContent = `${lastOpp ? (lastOpp.score || 0) : 0}/100`;
        }
        if (guestValue) {
            const val = lastOpp ? Number(lastOpp.estimated_value || 0) : 0;
            guestValue.textContent = `R$ ${val.toFixed(2)}`;
        }
        if (guestStatus) {
            guestStatus.textContent = lastOpp ? (lastOpp.urgency || "baixa") : "Baixa";
        }
        if (guestMessageCount) {
            guestMessageCount.textContent = messages.length || 0;
        }

        if (guestNotes) {
    if (lastOpp) {
        guestNotes.textContent = lastOpp.description || "Oportunidade identificada para este hóspede.";
    } else {
        guestNotes.textContent = "Nenhuma oportunidade registrada para este hóspede ainda.";
    }
}

if (guestNextAction) {
    if (lastOpp && lastOpp.next_action) {
        guestNextAction.textContent = lastOpp.next_action;
    } else if (lastOpp) {
        guestNextAction.textContent = "Revisar a conversa e decidir a próxima ação.";
    } else {
        guestNextAction.textContent = "Aguardando recomendação operacional.";
    }
}


        if (guestAIHistory) {
            guestAIHistory.innerHTML = "";
            if (opportunities.length) {
                opportunities.forEach((opp, index) => {
                    const item = document.createElement("div");
                    item.className = "ai-history-item";
                    item.innerHTML = `
                        <div class="ai-history-time">${index === 0 ? "Agora" : "Anterior"}</div>
                        <div class="ai-history-text">
                            <strong>${opp.type || "Oportunidade"}</strong>
                            ${opp.description || "Sem descrição."}
                        </div>
                    `;
                    guestAIHistory.appendChild(item);
                });
            } else {
                guestAIHistory.innerHTML = `
                    <div class="ai-history-item">
                        <div class="ai-history-time">Agora</div>
                        <div class="ai-history-text">
                            <strong>Sem oportunidades</strong>
                            Quando houver oportunidades, a evolução aparecerá aqui.
                        </div>
                    </div>
                `;
            }
        }

    } catch (err) {
        console.error("Erro ao carregar guest profile:", err);
    }
}

// Assumir/devolver: quando a equipe assume, a IA para de responder SO
// esse hospede (mensagem/oportunidade continuam sendo salvas) - ate
// alguem devolver clicando de novo. Recarrega o perfil pra refletir
// o estado real vindo do backend, nao so o texto do botao.
window.toggleChatTakeover = async function () {
    if (!stayflowCurrentGuestId) return;

    const btn = document.getElementById("chatTakeoverBtn");
    const wantsToPause = btn && btn.textContent === "Assumir conversa";

    try {
        const res = await fetch(`/guests/${stayflowCurrentGuestId}/toggle-ai`, {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ paused: wantsToPause })
        });
        if (!res.ok) {
            alert("Não foi possível atualizar o estado da conversa.");
            return;
        }
        loadGuestProfile(stayflowCurrentGuestId);
    } catch (err) {
        alert("Erro de conexão ao atualizar a conversa.");
    }
};

// Envio manual real pro hóspede - substitui o antigo mockSend() desta
// caixa especifica (a de guest chat), que so ecoava uma mensagem fake.
window.sendMessageToGuestUI = async function (button) {
    if (!button || !stayflowCurrentGuestId) return;

    const scope = button.closest(".chat-window");
    const input = scope ? scope.querySelector(".chat-input input") : null;
    if (!input) return;

    const text = input.value.trim();
    if (!text) return;
    input.value = "";

    const container = document.getElementById("chatMessages");
    if (container) {
        const div = document.createElement("div");
        div.className = "msg user";
        div.textContent = text;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    button.disabled = true;
    try {
        const res = await fetch(`/guests/${stayflowCurrentGuestId}/send-message`, {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            alert(data.message || "Não foi possível enviar a mensagem.");
        }
    } catch (err) {
        alert("Erro de conexão ao enviar a mensagem.");
    } finally {
        button.disabled = false;
    }
};

// loadChats() é chamado por dashboard.html no evento "stayflow:session-ready"
// (junto com todos os outros loaders da página), depois que /me confirma a
// sessão. Havia um segundo gatilho aqui, em DOMContentLoaded, que disparava
// sem esperar essa confirmação — além de causar o fetch duplicado em /chats,
// era o único loader da página que não esperava a sessão ser validada antes
// de bater numa rota protegida. Removido.

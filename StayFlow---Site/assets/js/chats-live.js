// StayFlow - Chats live integration
// Consome /chats e /guests/<id> para alimentar a aba "Chats".

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

            item.innerHTML = `
                <div class="chat-name">
                    <span>${chat.phone || "Sem telefone"}</span>
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

        // Título da conversa
        const chatTitle = document.getElementById("chatTitle");
        if (chatTitle) {
            chatTitle.textContent = `Conversa · ${guest.phone || "Hóspede"}`;
        }

        // Mensagens
        const chatMessages = document.getElementById("chatMessages");
        if (chatMessages) {
            chatMessages.innerHTML = "";
            if (!messages.length) {
                chatMessages.innerHTML = `<div class="msg bot">Nenhuma mensagem registrada para este hóspede.</div>`;
            } else {
                messages.forEach(msg => {
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

// Carrega chats automaticamente ao abrir a aba "Chats"
document.addEventListener("DOMContentLoaded", () => {
    // Se a aba chats for aberta manualmente depois, você pode chamar loadChats()
    // quando o usuário clicar no menu. Por ora, carregamos na inicialização:
    loadChats();
});

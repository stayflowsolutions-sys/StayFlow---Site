// StayFlow - Opportunity Center + Dashboard live integration
// Consome /opportunities e preenche:
// - Tabela do Opportunity Center (#opportunitiesTableBody), paginada
// - Caixa lateral "Mais importantes" (#opportunitiesPriorityList)
// - KPIs do dashboard (kpiOpportunities, metricAlmostClosed, metricProbableRevenue)
// - Ações prioritárias (#liveActivityBody)

// formatMoney() vem de dashboard.html (usa a moeda configurada em
// Configuracoes > Empresa) - script carregado depois, formatMoney ja
// existe no window quando as funcoes abaixo rodam (so no evento
// stayflow:session-ready, nunca antes).

const OPPORTUNITIES_PAGE_SIZE = 20;
const OPPORTUNITIES_PRIORITY_SIZE = 5;
let opportunitiesOffset = 0;
let opportunitiesTotal = 0;

function opportunityUrgencyPillClass(opportunity){
  return (opportunity.urgency || "low").toLowerCase();
}

// suggested_partner_item_id cobre 2 casos bem diferentes que reaproveitam
// o mesmo campo (decision_engine.py): hospedagem oferecendo catalogo de
// uma agencia PARCEIRA terceira (tour), ou imobiliaria oferecendo o
// PROPRIO catalogo pro proprio lead (matching de imovel). So o segundo
// caso e exclusivo de account_kind=agency + agency_category=imobiliaria
// (arquitetura garante mutuamente exclusivo - nunca os dois ao mesmo
// tempo) - usado pra nao chamar o vendedor de "parceiro" quando o
// vendedor e a propria conta.
function isOwnCatalogSuggestion(){
  const session = window.STAYFLOW_SESSION || {};
  return session.account_kind === "agency" && session.agency_category === "imobiliaria";
}

function opportunityDateLabel(createdAt){
  if(!createdAt) return "-";
  const date = new Date(createdAt.replace(" ", "T") + (createdAt.endsWith("Z") ? "" : "Z"));
  if(isNaN(date.getTime())) return createdAt;
  return date.toLocaleDateString() + " " + date.toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"});
}

function updateDashboardFromOpportunities(stats){
  const total = stats.total || 0;

  const kpiOpp = document.getElementById("kpiOpportunities");
  if (kpiOpp) kpiOpp.textContent = String(total);

  const metricAlmostClosed = document.getElementById("metricAlmostClosed");
  if (metricAlmostClosed) {
    metricAlmostClosed.textContent = total ? String(stats.almost_closed || 0) : "—";
  }

  const metricProbableRevenue = document.getElementById("metricProbableRevenue");
  if (metricProbableRevenue) {
    metricProbableRevenue.textContent = total ? formatMoney(stats.probable_revenue || 0) : "—";
  }
  // metricHumanReplies e metricRisk ficam como estão (não temos esses dados aqui)
}

function updatePriorityActionsFromOpportunities(opportunities){
  const tbody = document.getElementById("liveActivityBody");
  const emptyState = document.getElementById("liveActivityEmpty");

  if (!tbody) return;

  tbody.innerHTML = "";

  if (!opportunities.length){
    if (emptyState) emptyState.style.display = "flex";
    return;
  }

  if (emptyState) emptyState.style.display = "none";

  opportunities.forEach(opportunity => {
    const row = document.createElement("tr");

    const urgency = opportunityUrgencyPillClass(opportunity);
    const estimatedValue = Number(opportunity.estimated_value || 0);
    const actionLabel = escapeHtml(opportunity.next_action || T('opportunities.defaultAction', 'Revisar conversa manualmente.'));
    const impactLabel = estimatedValue > 0 ? formatMoney(estimatedValue) : "—";

    row.innerHTML = `
      <td>${actionLabel}</td>
      <td>
        <span class="status-pill ${urgency}">
          ${urgency.toUpperCase()}
        </span>
      </td>
      <td>${impactLabel}</td>
    `;

    tbody.appendChild(row);
  });
}

// Card clicavel do Opportunity Center (v1.147.0) - substitui a linha
// de tabela antiga. Reaproveita o visual ja usado no sidebar "Mais
// importantes" (updateOpportunitiesPrioritySidebar), so que clicavel e
// com o menu ☰ de acoes (Ver conversa/Responder manualmente/Sugerir
// resposta pra IA) - pedido explicito do usuario.
function opportunityCardHtml(opportunity){
  const urgency = opportunityUrgencyPillClass(opportunity);
  const score = Number(opportunity.score || 0);
  const estimatedValue = Number(opportunity.estimated_value || 0);
  const guestLabel = opportunity.name || opportunity.phone || "-";
  const guestLabelSafe = escapeHtml(guestLabel);
  const guestId = opportunity.guest_id || null;

  const canCharge = (opportunity.type === "tour" || opportunity.type === "upsell") && !isOwnCatalogSuggestion();
  const chargeArgs = JSON.stringify({
    chargeType: "tour",
    guestId: guestId,
    opportunityId: opportunity.id,
    title: opportunity.description || "",
    amount: estimatedValue || "",
    guestLabel: guestLabel,
  }).replace(/"/g, "&quot;");

  let partnerSuggestionHtml = "";
  if(opportunity.suggested_partner_item_id){
    const isOwnItem = isOwnCatalogSuggestion();
    const partnerChargeArgs = JSON.stringify({
      chargeType: "partner_item",
      portfolioItemId: opportunity.suggested_partner_item_id,
      guestId: guestId,
      opportunityId: opportunity.id,
      title: opportunity.suggested_partner_item_name || "",
      amount: opportunity.suggested_partner_item_price_type === "fixed" ? (opportunity.suggested_partner_item_price || "") : "",
      guestLabel: guestLabel,
    }).replace(/"/g, "&quot;");
    const suggestionText = isOwnItem
      ? T('opportunities.ownItemSuggestion', 'Sugestão: {item}', {item: escapeHtml(opportunity.suggested_partner_item_name || "")})
      : T('opportunities.partnerSuggestion', 'Sugestão: {item} via {agency}', {item: escapeHtml(opportunity.suggested_partner_item_name || ""), agency: escapeHtml(opportunity.suggested_partner_agency_name || "")});
    const suggestionBtnLabel = isOwnItem
      ? T('opportunities.offerOwnItemBtn', 'Oferecer imóvel')
      : T('opportunities.offerPartnerBtn', 'Oferecer parceiro');
    const suggestionOnClick = isOwnItem
      ? `openOfferPropertyModal(${partnerChargeArgs})`
      : `openGuestChargeModal(${partnerChargeArgs})`;
    partnerSuggestionHtml = `
      <div style="margin-top:6px;font-size:11px;color:var(--blue2)">💡 ${suggestionText}</div>
      <button type="button" class="btn secondary" style="font-size:11px;padding:6px 10px;margin-top:4px" onclick="event.stopPropagation();${suggestionOnClick}">${suggestionBtnLabel}</button>
    `;
  }

  const chargeBtnHtml = canCharge
    ? `<button type="button" class="btn secondary" style="font-size:11px;padding:6px 10px" onclick="event.stopPropagation();openGuestChargeModal(${chargeArgs})">${T('guestCharge.generateBtn', 'Gerar cobrança')}</button>`
    : "";

  const card = document.createElement("div");
  card.className = "opportunity-card";
  card.style.cssText = "background:#02070d;border:1px solid var(--line);border-radius:14px;padding:14px 16px;cursor:pointer";
  card.onclick = () => openOpportunityActionsModal(guestId, guestLabel);
  card.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">
      <div>
        <strong style="font-size:13px">${guestLabelSafe}</strong>
        <div style="font-size:11px;color:var(--muted);margin-top:2px">${opportunityDateLabel(opportunity.created_at)}</div>
      </div>
      <div style="display:flex;align-items:center;gap:8px">
        <span class="status-pill ${urgency}">${urgency.toUpperCase()}</span>
        <button type="button" class="btn secondary" style="padding:4px 10px;font-size:14px;line-height:1" title="${T('opportunities.actionsTitle', 'Ações')}" onclick="event.stopPropagation();openOpportunityActionsModal(${guestId}, '${guestLabelSafe.replace(/'/g, "\\'")}')">☰</button>
      </div>
    </div>
    <div style="margin:8px 0;font-size:13px">${escapeHtml(opportunity.description || intentLabel(opportunity.type, window.STAYFLOW_SESSION) || "-")}</div>
    ${partnerSuggestionHtml}
    <div style="font-size:12px;color:var(--muted);margin-top:6px">${T('opportunities.col.nextAction', 'Próxima ação')}: ${escapeHtml(opportunity.next_action || T('opportunities.defaultAction', 'Revisar conversa manualmente.'))}</div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px">
      <div style="display:flex;gap:14px;font-size:12px">
        <span style="color:var(--blue2);font-weight:700">${estimatedValue > 0 ? formatMoney(estimatedValue) : "—"}</span>
        <span style="color:var(--muted)">${T('opportunities.col.score', 'Score')}: ${score}/100</span>
      </div>
      ${chargeBtnHtml}
    </div>
  `;
  return card;
}

// Menu de acoes de uma oportunidade (v1.147.0, pedido explicito do
// usuario): "ver conversa, responder manualmente, sugerir resposta
// para a IA". openGenericModal ja existe globalmente (dashboard.html).
window.openOpportunityActionsModal = function(guestId, guestLabel){
  if(!guestId){
    alert(T('opportunities.action.noGuest', 'Essa oportunidade não tem um contato de WhatsApp associado.'));
    return;
  }
  const labelArg = JSON.stringify(guestLabel || "").replace(/"/g, "&quot;");
  openGenericModal(guestLabel || T('opportunities.actionsTitle', 'Ações'), `
    <div style="display:flex;flex-direction:column;gap:10px">
      <button type="button" class="btn secondary" onclick="goToGuestChat(${guestId})">${T('opportunities.action.viewChat', '💬 Ver conversa')}</button>
      <button type="button" class="btn secondary" onclick="openManualReplyModal(${guestId}, ${labelArg})">${T('opportunities.action.manualReply', '✍️ Responder manualmente')}</button>
      <button type="button" class="btn secondary" onclick="openSuggestReplyModal(${guestId}, ${labelArg})">${T('opportunities.action.suggestReply', '✨ Sugerir resposta pra IA')}</button>
    </div>
  `);
};

window.goToGuestChat = function(guestId){
  closeGenericModal();
  if(typeof openPage === "function") openPage("chats", document.querySelector('[data-page="chats"]'));
  if(typeof loadGuestProfile === "function") loadGuestProfile(guestId);
};

// "Responder manualmente" - texto EXATO que a equipe escreveu, sem IA
// no meio. Reaproveita o mesmo rascunho (guest_message_drafts) que o
// Ask StayFlow ja usa - so entra direto (create+send em sequencia,
// sem tela de revisao) porque a pessoa ja escreveu com intencao clara,
// diferente do fluxo de sugestao da IA (que sempre revisa antes).
window.openManualReplyModal = function(guestId, guestLabel){
  const labelArg = JSON.stringify(guestLabel || "").replace(/"/g, "&quot;");
  openGenericModal(T('opportunities.manualReply.title', '✍️ Responder manualmente'), `
    <p style="font-size:12px;color:var(--muted);margin-bottom:10px">${T('opportunities.manualReply.desc', 'Escreva a mensagem exata que o cliente vai receber.')}</p>
    <textarea id="opportunityManualReplyText" rows="5" style="width:100%;background:#02070d;border:1px solid var(--line);border-radius:12px;color:white;padding:10px 12px;resize:vertical"></textarea>
    <div style="display:flex;gap:10px;margin-top:14px">
      <button type="button" class="btn" onclick="submitManualReply(${guestId})">${T('opportunities.manualReply.sendBtn', 'Enviar')}</button>
      <button type="button" class="btn secondary" onclick="openOpportunityActionsModal(${guestId}, ${labelArg})">${T('common.cancel', 'Cancelar')}</button>
    </div>
  `);
};

window.submitManualReply = async function(guestId){
  const textEl = document.getElementById("opportunityManualReplyText");
  const text = (textEl ? textEl.value : "").trim();
  if(!text){
    alert(T('opportunities.manualReply.emptyError', 'Escreve a mensagem antes de enviar.'));
    return;
  }
  try{
    const draftRes = await fetch(`/opportunities/guest/${guestId}/manual-reply`, {
      method: "POST", credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ message: text }),
    });
    const draftData = await draftRes.json();
    if(!draftData.success){ alert(draftData.message || T('common.error.generic', 'Erro de conexão.')); return; }

    const sendRes = await fetch(`/opportunities/drafts/${draftData.draft_id}/send`, { method: "POST", credentials: "same-origin" });
    const sendData = await sendRes.json();
    if(!sendData.success || !sendData.sent){
      alert(T('opportunities.manualReply.sendFailed', 'Mensagem salva, mas não foi possível enviar pelo WhatsApp agora.'));
    }
    closeGenericModal();
    if(typeof loadOpportunities === "function") loadOpportunities();
  }catch(e){
    console.error("Erro ao responder manualmente:", e);
    alert(T('common.error.generic', 'Erro de conexão.'));
  }
};

// "Sugerir resposta pra IA" - campo de instrucao informal (opcional) +
// botao ✨ que tambem funciona sem nada escrito (IA le a conversa
// sozinha). SEMPRE mostra o rascunho antes de enviar (Enviar/Refazer),
// nunca manda direto - pedido explicito do usuario.
window.openSuggestReplyModal = function(guestId, guestLabel){
  window._lastSuggestDraftId = null;
  const labelArg = JSON.stringify(guestLabel || "").replace(/"/g, "&quot;");
  openGenericModal(T('opportunities.suggestReply.title', '✨ Sugerir resposta com IA'), `
    <p style="font-size:12px;color:var(--muted);margin-bottom:10px">${T('opportunities.suggestReply.desc', 'Escreva o que você quer transmitir (em qualquer formato — a IA reescreve pro cliente) ou deixe em branco e clique em Sugerir pra IA ler a conversa sozinha.')}</p>
    <textarea id="opportunitySuggestInstruction" rows="3" placeholder="${T('opportunities.suggestReply.placeholder', 'Ex: fala que esse imóvel já foi alugado mas que temos outro parecido')}" style="width:100%;background:#02070d;border:1px solid var(--line);border-radius:12px;color:white;padding:10px 12px;resize:vertical"></textarea>
    <div style="display:flex;gap:10px;margin-top:12px">
      <button type="button" class="btn" id="opportunitySuggestBtn" onclick="requestSuggestedReply(${guestId})">✨ ${T('opportunities.suggestReply.suggestBtn', 'Sugerir')}</button>
      <button type="button" class="btn secondary" onclick="openOpportunityActionsModal(${guestId}, ${labelArg})">${T('common.cancel', 'Cancelar')}</button>
    </div>
    <div id="opportunitySuggestResult" style="margin-top:16px"></div>
  `);
};

window.requestSuggestedReply = async function(guestId){
  const instructionEl = document.getElementById("opportunitySuggestInstruction");
  const instruction = (instructionEl ? instructionEl.value : "").trim();
  const btn = document.getElementById("opportunitySuggestBtn");
  const resultEl = document.getElementById("opportunitySuggestResult");

  // Refazer descarta o rascunho anterior em vez de deixar orfao - best
  // effort, nao trava se falhar.
  if(window._lastSuggestDraftId){
    fetch(`/opportunities/drafts/${window._lastSuggestDraftId}/cancel`, { method: "POST", credentials: "same-origin" }).catch(() => {});
    window._lastSuggestDraftId = null;
  }

  if(btn){ btn.disabled = true; btn.textContent = T('common.loading', 'Carregando...'); }
  if(resultEl) resultEl.innerHTML = "";

  try{
    const res = await fetch(`/opportunities/guest/${guestId}/suggest-reply`, {
      method: "POST", credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ instruction }),
    });
    const data = await res.json();
    if(!data.success){ alert(data.message || T('common.error.generic', 'Erro de conexão.')); return; }

    window._lastSuggestDraftId = data.draft_id;
    if(resultEl){
      const msgSafe = escapeHtml(data.message).replace(/\n/g, "<br>");
      resultEl.innerHTML = `
        <div style="background:#02070d;border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:13px;margin-bottom:10px">${msgSafe}</div>
        <div style="display:flex;gap:10px">
          <button type="button" class="btn" onclick="confirmSuggestedReply(${guestId}, ${data.draft_id})">${T('opportunities.suggestReply.sendBtn', 'Enviar')}</button>
          <button type="button" class="btn secondary" onclick="requestSuggestedReply(${guestId})">${T('opportunities.suggestReply.redoBtn', 'Refazer')}</button>
        </div>
      `;
    }
  }catch(e){
    console.error("Erro ao sugerir resposta:", e);
    alert(T('common.error.generic', 'Erro de conexão.'));
  }finally{
    if(btn){ btn.disabled = false; btn.textContent = "✨ " + T('opportunities.suggestReply.suggestBtn', 'Sugerir'); }
  }
};

window.confirmSuggestedReply = async function(guestId, draftId){
  try{
    const res = await fetch(`/opportunities/drafts/${draftId}/send`, { method: "POST", credentials: "same-origin" });
    const data = await res.json();
    if(!data.success || !data.sent){
      alert(T('opportunities.suggestReply.sendFailed', 'Não foi possível enviar pelo WhatsApp agora.'));
      return;
    }
    window._lastSuggestDraftId = null;
    closeGenericModal();
    if(typeof loadOpportunities === "function") loadOpportunities();
  }catch(e){
    console.error("Erro ao confirmar envio:", e);
    alert(T('common.error.generic', 'Erro de conexão.'));
  }
};

function updateOpportunityCenterTable(opportunities, append){
  const container = document.getElementById("opportunitiesTableBody");
  const emptyState = document.getElementById("opportunitiesEmpty");

  if (!container) return;

  if (!append) container.innerHTML = "";

  if (!append && !opportunities.length){
    if (emptyState) emptyState.style.display = "flex";
    return;
  }

  if (emptyState) emptyState.style.display = "none";

  opportunities.forEach((opportunity) => {
    container.appendChild(opportunityCardHtml(opportunity));
  });
}

function updateOpportunitiesLoadMoreButton(){
  const btn = document.getElementById("opportunitiesLoadMoreBtn");
  if (!btn) return;
  btn.style.display = opportunitiesOffset < opportunitiesTotal ? "inline-flex" : "none";
}

function updateOpportunitiesPrioritySidebar(opportunities){
  const listEl = document.getElementById("opportunitiesPriorityList");
  const emptyEl = document.getElementById("opportunitiesPriorityEmpty");
  if (!listEl) return;

  listEl.innerHTML = "";

  if (!opportunities.length){
    if (emptyEl) emptyEl.style.display = "flex";
    return;
  }
  if (emptyEl) emptyEl.style.display = "none";

  opportunities.forEach(opportunity => {
    const urgency = opportunityUrgencyPillClass(opportunity);
    const estimatedValue = Number(opportunity.estimated_value || 0);
    const guestLabel = escapeHtml(opportunity.name || opportunity.phone || "-");

    const card = document.createElement("div");
    card.style.cssText = "background:#02070d;border:1px solid var(--line);border-radius:14px;padding:12px 14px;";
    card.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:6px">
        <strong style="font-size:13px">${guestLabel}</strong>
        <span class="status-pill ${urgency}">${urgency.toUpperCase()}</span>
      </div>
      <div style="font-size:12px;color:var(--muted);margin-bottom:6px">${escapeHtml(opportunity.description || opportunity.type || "-")}</div>
      ${opportunity.suggested_partner_item_id ? `<div style="font-size:11px;color:var(--blue2);margin-bottom:6px">💡 ${isOwnCatalogSuggestion() ? T('opportunities.ownItemSuggestion', 'Sugestão: {item}', {item: escapeHtml(opportunity.suggested_partner_item_name || "")}) : T('opportunities.partnerSuggestion', 'Sugestão: {item} via {agency}', {item: escapeHtml(opportunity.suggested_partner_item_name || ""), agency: escapeHtml(opportunity.suggested_partner_agency_name || "")})}</div>` : ""}
      <div style="display:flex;justify-content:space-between;align-items:center;font-size:12px">
        <span style="color:var(--blue2);font-weight:700">${estimatedValue > 0 ? formatMoney(estimatedValue) : "—"}</span>
        <span style="color:var(--muted)">${T('opportunities.col.score', 'Score')}: ${Number(opportunity.score || 0)}/100</span>
      </div>
    `;
    listEl.appendChild(card);
  });
}

async function fetchOpportunitiesPage(offset, sort){
  const lang = window.StayFlowI18n ? StayFlowI18n.currentLang() : "pt";
  const limit = sort === "priority" ? OPPORTUNITIES_PRIORITY_SIZE : OPPORTUNITIES_PAGE_SIZE;
  const response = await fetch(
    `/opportunities?lang=${lang}&limit=${limit}&offset=${offset}&sort=${sort}`,
    { credentials: "same-origin" }
  );
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

window.loadMoreOpportunities = async function(){
  try{
    opportunitiesOffset += OPPORTUNITIES_PAGE_SIZE;
    const result = await fetchOpportunitiesPage(opportunitiesOffset, "recent");
    opportunitiesTotal = result.total || 0;
    updateOpportunityCenterTable(result.items || [], true);
    updateOpportunitiesLoadMoreButton();
  }catch(error){
    console.error("Erro ao carregar mais oportunidades:", error);
    opportunitiesOffset -= OPPORTUNITIES_PAGE_SIZE;
  }
};

async function loadOpportunities() {
  try {
    opportunitiesOffset = 0;
    const recent = await fetchOpportunitiesPage(0, "recent");
    opportunitiesTotal = recent.total || 0;

    updateOpportunityCenterTable(recent.items || [], false);
    updateOpportunitiesLoadMoreButton();
    updateDashboardFromOpportunities(recent);

    const priority = await fetchOpportunitiesPage(0, "priority");
    updateOpportunitiesPrioritySidebar(priority.items || []);
    updatePriorityActionsFromOpportunities(priority.items || []);

  } catch (error) {
    console.error("Erro ao carregar oportunidades:", error);

    const container = document.getElementById("opportunitiesTableBody");
    if (container) {
      container.innerHTML = `
        <tr>
          <td colspan="8">
            ${T('opportunities.loadError', 'Erro ao carregar oportunidades. Tente novamente mais tarde.')}
          </td>
        </tr>
      `;
    }
  }
}

// ---------------------------------------------------------------
// Leads capturados pela IA (capture_lead, v1.130.0) - diferente de
// Opportunity Center: oportunidade e deteccao PASSIVA de intencao em
// qualquer conversa, lead e uma acao EXPLICITA da IA quando ja tem
// nome+contato+interesse reais pra time seguir. Tabela/rota propria
// (/leads), sem paginacao (volume baixo) nem kanban.
// ---------------------------------------------------------------

const LEAD_STATUS_ORDER = ["new", "contacted", "converted", "lost"];
let leadBrokersCache = [];

function leadStatusLabel(status){
  const fallback = { new: "Novo", contacted: "Contatado", converted: "Convertido", lost: "Perdido" };
  const key = LEAD_STATUS_ORDER.includes(status) ? status : "new";
  return T(`leads.status.${key}`, fallback[key]);
}

function leadRowHtml(lead){
  const name = escapeHtml(lead.guest_name || "-");
  const phone = escapeHtml(lead.phone || "-");
  const interest = escapeHtml(lead.interest || "-");
  const status = LEAD_STATUS_ORDER.includes(lead.status) ? lead.status : "new";
  const options = LEAD_STATUS_ORDER
    .map(s => `<option value="${s}" ${s === status ? "selected" : ""}>${leadStatusLabel(s)}</option>`)
    .join("");

  // Roteamento automatico por fila (v1.133.0) atribui um corretor na
  // criacao do lead, mas o select sempre permite reatribuir manualmente
  // (corretor de ferias, erro de fila) - "Sem corretor" so aparece
  // quando a conta ainda nao tinha nenhum corretor ativo no momento
  // da captura (fila vazia), nao e um estado normal de uso.
  const brokerOptions = `<option value="">${T('leads.brokerNone', 'Sem corretor')}</option>` +
    leadBrokersCache.map(b => `<option value="${b.membership_id}" ${lead.membership_id === b.membership_id ? "selected" : ""}>${escapeHtml(b.name)}</option>`).join("");

  return `
    <tr>
      <td>${opportunityDateLabel(lead.created_at)}</td>
      <td>${name}</td>
      <td>${phone}</td>
      <td>${interest}</td>
      <td><select onchange="updateLeadBroker(${lead.id}, this.value)">${brokerOptions}</select></td>
      <td><select onchange="updateLeadStatus(${lead.id}, this.value)">${options}</select></td>
    </tr>
  `;
}

async function loadLeads(){
  const tbody = document.getElementById("leadsTableBody");
  const emptyState = document.getElementById("leadsEmpty");
  if (!tbody) return;

  try {
    const [leadsRes, brokersRes] = await Promise.all([
      fetch("/leads", { credentials: "same-origin" }),
      fetch("/leads/brokers", { credentials: "same-origin" }),
    ]);
    const data = await leadsRes.json();
    const brokersData = await brokersRes.json();
    leadBrokersCache = (brokersData && brokersData.brokers) || [];
    const items = (data && data.leads) || [];

    tbody.innerHTML = items.map(leadRowHtml).join("");
    if (emptyState) emptyState.style.display = items.length ? "none" : "flex";
  } catch (error) {
    console.error("Erro ao carregar leads:", error);
  }
}

window.updateLeadStatus = async function(leadId, status){
  try {
    const res = await fetch(`/leads/${leadId}/status`, {
      method: "PATCH",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      console.warn("Erro ao atualizar status do lead:", data.message);
      loadLeads();
    }
  } catch (error) {
    console.error("Erro ao atualizar status do lead:", error);
    loadLeads();
  }
};

window.updateLeadBroker = async function(leadId, membershipId){
  try {
    const res = await fetch(`/leads/${leadId}/broker`, {
      method: "PATCH",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ membership_id: membershipId ? Number(membershipId) : null }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      console.warn("Erro ao reatribuir corretor do lead:", data.message);
      loadLeads();
    }
  } catch (error) {
    console.error("Erro ao reatribuir corretor do lead:", error);
    loadLeads();
  }
};

// ---------------------------------------------------------------
// Opportunity Center em pipeline (kanban) - toggle "Lista | Pipeline"
// ao lado do titulo. Reaproveita 100% o mesmo /opportunities (so pede
// limit maior, o teto ja existente de 100 por chamada) - stage e um
// campo NOVO e independente de status (que nunca sai de 'open' em
// lugar nenhum do backend, achado documentado desde a v1.63.0),
// movido so por botao/select, nunca drag-and-drop.
// ---------------------------------------------------------------

const OPPORTUNITY_STAGE_ORDER = ["new", "contacted", "negotiating", "won", "lost"];
let opportunitiesCurrentView = "list";

function opportunityStageLabel(stage){
  const fallback = {
    new: "Novo", contacted: "Contatado", negotiating: "Negociando", won: "Ganho", lost: "Perdido"
  };
  const key = OPPORTUNITY_STAGE_ORDER.includes(stage) ? stage : "new";
  return T(`opportunities.stage.${key}`, fallback[key]);
}

window.setOpportunitiesView = function(view){
  opportunitiesCurrentView = view;
  document.querySelectorAll(".opportunities-view-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-view") === view);
  });

  const listView = document.getElementById("opportunitiesListView");
  const kanbanView = document.getElementById("opportunitiesKanbanView");
  if(listView) listView.style.display = view === "list" ? "block" : "none";
  if(kanbanView) kanbanView.style.display = view === "kanban" ? "block" : "none";

  if(view === "kanban") loadOpportunitiesKanban();
};

function kanbanCardHtml(opportunity){
  const urgency = opportunityUrgencyPillClass(opportunity);
  const estimatedValue = Number(opportunity.estimated_value || 0);
  const guestLabel = escapeHtml(opportunity.name || opportunity.phone || "-");
  const stage = OPPORTUNITY_STAGE_ORDER.includes(opportunity.stage) ? opportunity.stage : "new";
  const options = OPPORTUNITY_STAGE_ORDER
    .map(s => `<option value="${s}" ${s === stage ? "selected" : ""}>${opportunityStageLabel(s)}</option>`)
    .join("");

  return `
    <div class="kanban-card" data-opportunity-id="${opportunity.id}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:6px">
        <strong style="font-size:12px">${guestLabel}</strong>
        <span class="status-pill ${urgency}" style="font-size:10px;padding:3px 7px">${urgency.toUpperCase()}</span>
      </div>
      <div style="font-size:11px;color:var(--muted)">${escapeHtml(opportunity.description || opportunity.type || "-")}</div>
      <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px">
        <span style="color:var(--blue2);font-weight:700">${estimatedValue > 0 ? formatMoney(estimatedValue) : "—"}</span>
        <span style="color:var(--muted)">${Number(opportunity.score || 0)}/100</span>
      </div>
      <select onchange="updateOpportunityStage(${opportunity.id}, this.value)">${options}</select>
    </div>
  `;
}

function renderOpportunitiesKanban(items){
  const board = document.getElementById("opportunitiesKanbanBoard");
  if(!board) return;

  const grouped = {};
  OPPORTUNITY_STAGE_ORDER.forEach(s => { grouped[s] = []; });
  items.forEach(o => {
    const stage = OPPORTUNITY_STAGE_ORDER.includes(o.stage) ? o.stage : "new";
    grouped[stage].push(o);
  });

  board.innerHTML = OPPORTUNITY_STAGE_ORDER.map(stage => {
    const cardsHtml = grouped[stage].map(kanbanCardHtml).join("");
    return `
      <div class="kanban-column">
        <div class="kanban-column-header">
          <span>${opportunityStageLabel(stage)}</span>
          <span>${grouped[stage].length}</span>
        </div>
        ${cardsHtml || `<div style="font-size:11px;color:var(--muted);text-align:center;padding:10px 0">—</div>`}
      </div>
    `;
  }).join("");
}

async function loadOpportunitiesKanban(){
  try{
    const lang = window.StayFlowI18n ? StayFlowI18n.currentLang() : "pt";
    const res = await fetch(`/opportunities?lang=${lang}&limit=100&offset=0&sort=recent`, { credentials: "same-origin" });
    if(!res.ok) return;
    const data = await res.json();
    renderOpportunitiesKanban(data.items || []);
  }catch(e){
    console.error("Erro ao carregar pipeline de oportunidades:", e);
  }
}

function reloadOpportunitiesKanbanIfActive(){
  if(opportunitiesCurrentView === "kanban") loadOpportunitiesKanban();
}

window.updateOpportunityStage = async function(opportunityId, stage){
  try{
    const res = await fetch(`/opportunities/${opportunityId}/stage`, {
      method: "PATCH", credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ stage }),
    });
    if(!res.ok){
      console.error("Erro ao mover oportunidade de etapa");
    }
  }catch(e){
    console.error("Erro ao mover oportunidade de etapa:", e);
  }finally{
    loadOpportunitiesKanban();
  }
};

// ---------------------------------------------------------------
// Oferecer imovel proprio (imobiliaria) - achado em auditoria: antes
// disso, o botao "Oferecer imovel" reaproveitava openGuestChargeModal()
// (link de pagamento Mercado Pago, pensado pra passeio/aluguel de
// verdade) - nao faz sentido nenhum gerar cobranca pra "oferecer" um
// imovel, o lead ainda nem decidiu nada. Em vez disso, monta uma
// mensagem editavel com o imovel sugerido e manda direto pro cliente
// via /guests/<id>/send-message (mesmo endpoint que a aba Chats usa,
// ver chats-live.js) - sem processador de pagamento nenhum envolvido.
// ---------------------------------------------------------------

function openOfferPropertyModal(opts){
  opts = opts || {};
  const guestId = opts.guestId || null;
  const itemName = opts.title || "";
  const amount = opts.amount;
  const guestLabel = opts.guestLabel || "";

  const priceText = amount ? ` (${formatMoney(Number(amount))})` : "";
  const suggestedMessage = T('portfolio.offerProperty.suggestedMessage', 'Olá! Encontrei um imóvel que pode te interessar: {item}{price}. Posso te mandar mais detalhes?', { item: itemName, price: priceText });

  openGenericModal(T('portfolio.offerProperty.modalTitle', '🏠 Oferecer imóvel'), `
    ${guestLabel ? `<p style="margin:0 0 14px;color:var(--muted);font-size:13px">${T('portfolio.offerProperty.clientLabel', 'Cliente')}: <strong style="color:white">${escapeHtml(guestLabel)}</strong></p>` : ""}
    <div>
      <label style="display:block;font-size:11px;color:var(--muted);margin-bottom:4px">${T('portfolio.offerProperty.messageLabel', 'Mensagem pro cliente')}</label>
      <textarea id="offerPropertyMessage" rows="5" style="width:100%;background:#02070d;border:1px solid var(--line);border-radius:15px;color:white;padding:11px 12px;resize:vertical">${escapeHtml(suggestedMessage)}</textarea>
    </div>
    <div id="offerPropertyMessageResult" class="generic-modal-message"></div>
    <div style="display:flex;justify-content:flex-end;margin-top:14px">
      <button class="btn" type="button" id="offerPropertySendBtn" onclick="submitOfferProperty(${guestId})">${T('portfolio.offerProperty.sendBtn', 'Enviar pro cliente')}</button>
    </div>
  `);
}

async function submitOfferProperty(guestId){
  const msg = document.getElementById("offerPropertyMessageResult");
  const btn = document.getElementById("offerPropertySendBtn");
  const text = (document.getElementById("offerPropertyMessage")?.value || "").trim();
  if(msg){ msg.textContent = ""; msg.className = "generic-modal-message"; }

  if(!text){
    if(msg){ msg.textContent = T('portfolio.offerProperty.emptyError', 'Escreva uma mensagem antes de enviar.'); msg.classList.add("error"); }
    return;
  }
  if(!guestId){
    if(msg){ msg.textContent = T('portfolio.offerProperty.noGuestError', 'Não foi possível identificar o cliente dessa conversa.'); msg.classList.add("error"); }
    return;
  }

  if(btn) btn.disabled = true;
  try{
    const res = await fetch(`/guests/${guestId}/send-message`, {
      method: "POST", credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json().catch(() => ({}));
    if(!res.ok){
      if(msg){ msg.textContent = data.message || T('chats.sendMessageFailed', 'Não foi possível enviar a mensagem.'); msg.classList.add("error"); }
      if(btn) btn.disabled = false;
      return;
    }
    if(msg){ msg.textContent = T('portfolio.offerProperty.sentMsg', 'Mensagem enviada!'); msg.classList.add("success"); }
    setTimeout(() => { if(typeof closeGenericModal === "function") closeGenericModal(); }, 900);
  }catch(e){
    console.error("Erro ao enviar oferta de imóvel:", e);
    if(msg){ msg.textContent = T('chats.sendMessageConnError', 'Erro de conexão ao enviar a mensagem.'); msg.classList.add("error"); }
    if(btn) btn.disabled = false;
  }
}

// ---------------------------------------------------------------
// Cobranca ao hospede via Mercado Pago (guest_charges) - modal
// compartilhado por tres pontos de entrada: Opportunity Center
// (charge_type tour/rental, com opportunity_id), Reservas
// (charge_type='reservation' travado, com reservation_id) e "+ Nova
// cobranca" avulsa (sem origem nenhuma). Ver routes/guest_charges.py.
// ---------------------------------------------------------------

function openGuestChargeModal(opts){
  opts = opts || {};
  const lockedType = opts.chargeType || null;
  const guestId = opts.guestId || null;
  const opportunityId = opts.opportunityId || null;
  const reservationId = opts.reservationId || null;
  const portfolioItemId = opts.portfolioItemId || null;
  const defaultTitle = opts.title || "";
  const defaultAmount = opts.amount || "";
  const guestLabel = opts.guestLabel || "";

  const typeOptions = lockedType
    ? `<input type="hidden" id="chargeType" value="${escapeHtml(lockedType)}">`
    : `
      <select id="chargeType" style="width:100%;background:#02070d;border:1px solid var(--line);border-radius:15px;color:white;padding:11px 12px;">
        <option value="tour">${T('guestCharge.type.tour', 'Passeio/excursão')}</option>
        <option value="rental">${T('guestCharge.type.rental', 'Aluguel')}</option>
      </select>
    `;

  // "Hospede:" so faz sentido literal pra hospedagem - agencia parceira
  // (incl. imobiliaria) chama de PAX ou Clientes, mesma funcao ja usada
  // no menu/pagina de Hospedes (agencyGuestNoun, dashboard.html).
  const session = window.STAYFLOW_SESSION || {};
  const guestNounLabel = session.account_kind === "agency"
    ? (typeof agencyGuestNoun === "function" ? agencyGuestNoun(session) : "Cliente")
    : T('guestCharge.guestLabel', 'Hóspede');

  openGenericModal(T('guestCharge.modalTitle', '💳 Gerar cobrança'), `
    ${guestLabel ? `<p style="margin:0 0 14px;color:var(--muted);font-size:13px">${guestNounLabel}: <strong style="color:white">${escapeHtml(guestLabel)}</strong></p>` : ""}

    <div style="display:grid;gap:var(--gap)">
      <div>
        <label style="display:block;font-size:11px;color:var(--muted);margin-bottom:4px">${T('guestCharge.typeLabel', 'Tipo')}</label>
        ${typeOptions}
      </div>
      <div>
        <label style="display:block;font-size:11px;color:var(--muted);margin-bottom:4px">${T('guestCharge.titleLabel', 'Título')}</label>
        <input type="text" id="chargeTitle" value="${escapeHtml(defaultTitle)}" autocomplete="off" style="width:100%;background:#02070d;border:1px solid var(--line);border-radius:15px;color:white;padding:11px 12px;">
      </div>
      <div>
        <label style="display:block;font-size:11px;color:var(--muted);margin-bottom:4px">${T('guestCharge.descriptionLabel', 'Descrição (opcional)')}</label>
        <input type="text" id="chargeDescription" autocomplete="off" style="width:100%;background:#02070d;border:1px solid var(--line);border-radius:15px;color:white;padding:11px 12px;">
      </div>
      <div>
        <label style="display:block;font-size:11px;color:var(--muted);margin-bottom:4px">${T('guestCharge.totalLabel', 'Valor total')}</label>
        <input type="number" id="chargeTotalAmount" value="${escapeHtml(String(defaultAmount))}" min="0" step="0.01" style="width:100%;background:#02070d;border:1px solid var(--line);border-radius:15px;color:white;padding:11px 12px;">
      </div>
      <div>
        <label style="display:block;font-size:11px;color:var(--muted);margin-bottom:4px">${T('guestCharge.paymentModeLabel', 'Pagamento')}</label>
        <select id="chargePaymentMode" onchange="document.getElementById('chargeDepositRow').style.display = this.value === 'deposit' ? 'block' : 'none'" style="width:100%;background:#02070d;border:1px solid var(--line);border-radius:15px;color:white;padding:11px 12px;">
          <option value="full">${T('guestCharge.paymentMode.full', 'Valor cheio')}</option>
          <option value="deposit">${T('guestCharge.paymentMode.deposit', 'Sinal/depósito')}</option>
        </select>
      </div>
      <div id="chargeDepositRow" style="display:none">
        <label style="display:block;font-size:11px;color:var(--muted);margin-bottom:4px">${T('guestCharge.depositLabel', 'Valor do depósito')}</label>
        <input type="number" id="chargeDepositAmount" min="0" step="0.01" style="width:100%;background:#02070d;border:1px solid var(--line);border-radius:15px;color:white;padding:11px 12px;">
      </div>
    </div>

    <div id="chargeResult" style="display:none;margin-top:16px;padding:12px;background:#02070d;border:1px solid var(--line);border-radius:12px">
      <p style="margin:0 0 8px;font-size:12px;color:var(--muted)">${T('guestCharge.linkReady', 'Link de pagamento gerado:')}</p>
      <div style="display:flex;gap:8px">
        <input type="text" id="chargeLinkInput" readonly style="flex:1;background:#050c16;border:1px solid var(--line);border-radius:10px;color:white;padding:9px 10px;font-size:12px">
        <button type="button" class="btn secondary" onclick="copyGuestChargeLink()">${T('guestCharge.copyBtn', 'Copiar link')}</button>
      </div>
    </div>

    <div style="display:flex;justify-content:flex-end;margin-top:14px">
      <button class="btn" type="button" id="chargeSubmitBtn" onclick="submitGuestCharge()">${T('guestCharge.submitBtn', 'Gerar cobrança')}</button>
    </div>

    <div id="chargeMessage" class="generic-modal-message"></div>
  `);

  window._guestChargeContext = { guestId, opportunityId, reservationId, portfolioItemId };
}

async function submitGuestCharge(){
  const msg = document.getElementById("chargeMessage");
  if(msg){ msg.textContent = ""; msg.className = "generic-modal-message"; }

  const ctx = window._guestChargeContext || {};
  const chargeType = document.getElementById("chargeType").value;
  const title = (document.getElementById("chargeTitle").value || "").trim();
  const description = (document.getElementById("chargeDescription").value || "").trim();
  const totalAmount = parseFloat(document.getElementById("chargeTotalAmount").value);
  const paymentMode = document.getElementById("chargePaymentMode").value;
  const depositAmount = paymentMode === "deposit" ? parseFloat(document.getElementById("chargeDepositAmount").value) : null;

  if(!title || !totalAmount || totalAmount <= 0){
    if(msg){
      msg.textContent = T('guestCharge.validationError', 'Preencha título e um valor total maior que zero.');
      msg.classList.add("error");
    }
    return;
  }

  const btn = document.getElementById("chargeSubmitBtn");
  if(btn) btn.disabled = true;

  try{
    const res = await fetch("/guest-charges", {
      method: "POST",
      credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        charge_type: chargeType,
        title,
        description: description || null,
        total_amount: totalAmount,
        payment_mode: paymentMode,
        deposit_amount: depositAmount,
        guest_id: ctx.guestId,
        opportunity_id: ctx.opportunityId,
        reservation_id: ctx.reservationId,
        portfolio_item_id: ctx.portfolioItemId,
      })
    });
    const data = await res.json().catch(() => ({}));
    if(!res.ok || !data.success){
      if(msg){
        msg.textContent = data.message || T('guestCharge.submitFailed', 'Não foi possível gerar a cobrança.');
        msg.classList.add("error");
      }
      return;
    }

    const linkInput = document.getElementById("chargeLinkInput");
    const resultBox = document.getElementById("chargeResult");
    if(linkInput) linkInput.value = data.charge.mp_init_point || "";
    if(resultBox) resultBox.style.display = "block";
    if(btn) btn.style.display = "none";
  }catch(e){
    if(msg){
      msg.textContent = T('common.connectionError', 'Erro de conexão.');
      msg.classList.add("error");
    }
  }finally{
    if(btn) btn.disabled = false;
  }
}

function copyGuestChargeLink(){
  const input = document.getElementById("chargeLinkInput");
  if(!input || !input.value) return;
  input.select();
  navigator.clipboard?.writeText(input.value).catch(() => {});
}

// loadOpportunities() é chamado por dashboard.html no evento
// "stayflow:session-ready" (junto com os outros loaders da página),
// depois que /me confirma a sessão — mesmo padrão usado em todo o
// resto do app. Não tem gatilho próprio aqui de propósito: um
// DOMContentLoaded independente bateria em rota protegida antes da
// sessão ser confirmada (mesmo problema já corrigido em chats-live.js).

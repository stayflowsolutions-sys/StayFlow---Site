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

function opportunityRowHtml(opportunity){
  const urgency = opportunityUrgencyPillClass(opportunity);
  const score = Number(opportunity.score || 0);
  const estimatedValue = Number(opportunity.estimated_value || 0);
  const guestLabel = escapeHtml(opportunity.name || opportunity.phone || "-");

  // "Gerar cobranca" so faz sentido pra oportunidade que a IA
  // classificou como passeio/upsell (tour/rental de verdade) - reserva,
  // pedido de ajuda humana e follow-up nao sao vendas cobraveis aqui.
  const canCharge = opportunity.type === "tour" || opportunity.type === "upsell";
  const chargeArgs = JSON.stringify({
    chargeType: "tour",
    guestId: opportunity.guest_id || null,
    opportunityId: opportunity.id,
    title: opportunity.description || "",
    amount: estimatedValue || "",
    guestLabel: opportunity.name || opportunity.phone || "",
  }).replace(/"/g, "&quot;");

  // Sugestao de parceiro (decision_engine.py) - so aparece quando a
  // hospedagem tem um item de portfolio de agencia ja ativado e o
  // hospede pediu algo do tipo 'tour'. Botao separado do "Gerar
  // cobranca" normal porque o vendedor de verdade e a agencia, nao a
  // hospedagem (ver routes/guest_charges.py, charge_type='partner_item').
  let partnerSuggestionHtml = "";
  if(opportunity.suggested_partner_item_id){
    const isOwnItem = isOwnCatalogSuggestion();
    const partnerChargeArgs = JSON.stringify({
      chargeType: "partner_item",
      portfolioItemId: opportunity.suggested_partner_item_id,
      guestId: opportunity.guest_id || null,
      opportunityId: opportunity.id,
      title: opportunity.suggested_partner_item_name || "",
      amount: opportunity.suggested_partner_item_price_type === "fixed" ? (opportunity.suggested_partner_item_price || "") : "",
      guestLabel: opportunity.name || opportunity.phone || "",
    }).replace(/"/g, "&quot;");
    const suggestionText = isOwnItem
      ? T('opportunities.ownItemSuggestion', 'Sugestão: {item}', {item: escapeHtml(opportunity.suggested_partner_item_name || "")})
      : T('opportunities.partnerSuggestion', 'Sugestão: {item} via {agency}', {item: escapeHtml(opportunity.suggested_partner_item_name || ""), agency: escapeHtml(opportunity.suggested_partner_agency_name || "")});
    const suggestionBtnLabel = isOwnItem
      ? T('opportunities.offerOwnItemBtn', 'Oferecer imóvel')
      : T('opportunities.offerPartnerBtn', 'Oferecer parceiro');
    // Imovel proprio (imobiliaria) NAO e cobrado via link de pagamento
    // (openGuestChargeModal, feito pra passeio/aluguel de verdade) -
    // "oferecer" um imovel e mandar a informacao pro lead decidir, nao
    // gerar cobranca. Sugestao de PARCEIRO (agencia terceira) continua
    // no fluxo de cobranca normal, isso nao mudou.
    const suggestionOnClick = isOwnItem
      ? `openOfferPropertyModal(${partnerChargeArgs})`
      : `openGuestChargeModal(${partnerChargeArgs})`;
    partnerSuggestionHtml = `
      <div style="margin-top:6px;font-size:11px;color:var(--blue2)">
        💡 ${suggestionText}
      </div>
      <button type="button" class="btn secondary" style="font-size:11px;padding:6px 10px;margin-top:4px" onclick="${suggestionOnClick}">${suggestionBtnLabel}</button>
    `;
  }

  return `
    <td>${opportunityDateLabel(opportunity.created_at)}</td>
    <td>${guestLabel}</td>
    <td>
      <span class="status-pill ${urgency}">
        ${urgency.toUpperCase()}
      </span>
    </td>
    <td>${escapeHtml(opportunity.description || opportunity.type || "-")}${partnerSuggestionHtml}</td>
    <td>${score}/100</td>
    <td>${formatMoney(estimatedValue)}</td>
    <td>${escapeHtml(opportunity.next_action || T('opportunities.defaultAction', 'Revisar conversa manualmente.'))}</td>
    <td>${canCharge ? `<button type="button" class="btn secondary" style="font-size:11px;padding:6px 10px" onclick="openGuestChargeModal(${chargeArgs})">${T('guestCharge.generateBtn', 'Gerar cobrança')}</button>` : "—"}</td>
  `;
}

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
    const row = document.createElement("tr");
    row.innerHTML = opportunityRowHtml(opportunity);
    container.appendChild(row);
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

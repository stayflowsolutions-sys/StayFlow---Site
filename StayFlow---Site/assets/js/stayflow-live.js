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
    const actionLabel = opportunity.next_action || T('opportunities.defaultAction', 'Revisar conversa manualmente.');
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
  const guestLabel = opportunity.name || opportunity.phone || "-";

  return `
    <td>${opportunityDateLabel(opportunity.created_at)}</td>
    <td>${guestLabel}</td>
    <td>
      <span class="status-pill ${urgency}">
        ${urgency.toUpperCase()}
      </span>
    </td>
    <td>${opportunity.description || opportunity.type || "-"}</td>
    <td>${score}/100</td>
    <td>${formatMoney(estimatedValue)}</td>
    <td>${opportunity.next_action || T('opportunities.defaultAction', 'Revisar conversa manualmente.')}</td>
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
    const guestLabel = opportunity.name || opportunity.phone || "-";

    const card = document.createElement("div");
    card.style.cssText = "background:#02070d;border:1px solid var(--line);border-radius:14px;padding:12px 14px;";
    card.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:6px">
        <strong style="font-size:13px">${guestLabel}</strong>
        <span class="status-pill ${urgency}">${urgency.toUpperCase()}</span>
      </div>
      <div style="font-size:12px;color:var(--muted);margin-bottom:6px">${opportunity.description || opportunity.type || "-"}</div>
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
          <td colspan="7">
            ${T('opportunities.loadError', 'Erro ao carregar oportunidades. Tente novamente mais tarde.')}
          </td>
        </tr>
      `;
    }
  }
}

// loadOpportunities() é chamado por dashboard.html no evento
// "stayflow:session-ready" (junto com os outros loaders da página),
// depois que /me confirma a sessão — mesmo padrão usado em todo o
// resto do app. Não tem gatilho próprio aqui de propósito: um
// DOMContentLoaded independente bateria em rota protegida antes da
// sessão ser confirmada (mesmo problema já corrigido em chats-live.js).

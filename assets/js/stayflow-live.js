// StayFlow - Opportunity Center + Dashboard live integration
// Consome /opportunities e preenche:
// - Tabela do Opportunity Center (#opportunitiesTableBody)
// - KPIs do dashboard (kpiOpportunities, metricAlmostClosed, metricProbableRevenue)
// - Ações prioritárias (#liveActivityBody)

function formatCurrencyBRL(value){
  if (isNaN(value)) value = 0;
  return `R$ ${Number(value).toFixed(2)}`;
}

function updateDashboardFromOpportunities(opportunities){
  const totalOpps = opportunities.length;
  const almostClosed = opportunities.filter(o => Number(o.score || 0) >= 70).length;
  const probableRevenue = opportunities.reduce(
    (sum, o) => sum + Number(o.estimated_value || 0),
    0
  );

  const kpiOpp = document.getElementById("kpiOpportunities");
  if (kpiOpp) kpiOpp.textContent = String(totalOpps);

  const metricAlmostClosed = document.getElementById("metricAlmostClosed");
  if (metricAlmostClosed) {
    metricAlmostClosed.textContent = totalOpps ? String(almostClosed) : "—";
  }

  const metricProbableRevenue = document.getElementById("metricProbableRevenue");
  if (metricProbableRevenue) {
    metricProbableRevenue.textContent = totalOpps ? formatCurrencyBRL(probableRevenue) : "—";
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

    const urgency = (opportunity.urgency || "low").toLowerCase();
    const estimatedValue = Number(opportunity.estimated_value || 0);
    const actionLabel = opportunity.next_action || "Revisar conversa manualmente.";
    const impactLabel = estimatedValue > 0 ? formatCurrencyBRL(estimatedValue) : "—";

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

function updateOpportunityCenterTable(opportunities){
  const container = document.getElementById("opportunitiesTableBody");
  const emptyState = document.getElementById("opportunitiesEmpty");

  if (!container) return;

  container.innerHTML = "";

  if (!opportunities.length){
    container.innerHTML = `
      <tr>
        <td colspan="6">
          Nenhuma oportunidade ativa no momento.
        </td>
      </tr>
    `;
    if (emptyState) emptyState.style.display = "flex";
    return;
  }

  if (emptyState) emptyState.style.display = "none";

  opportunities.forEach((opportunity) => {
    const row = document.createElement("tr");

    const urgency = (opportunity.urgency || "low").toLowerCase();
    const score = Number(opportunity.score || 0);
    const estimatedValue = Number(opportunity.estimated_value || 0);

    row.innerHTML = `
      <td>${opportunity.phone || "-"}</td>
      <td>
        <span class="status-pill ${urgency}">
          ${urgency.toUpperCase()}
        </span>
      </td>
      <td>${opportunity.type || "opportunity"}</td>
      <td>${score}/100</td>
      <td>${formatCurrencyBRL(estimatedValue)}</td>
      <td>${opportunity.next_action || "Revisar conversa manualmente."}</td>
    `;

    container.appendChild(row);
  });
}

async function loadOpportunities() {
  try {
    const response = await fetch("/opportunities", { credentials: "same-origin" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const opportunities = await response.json();
    console.log("StayFlow opportunities:", opportunities);

    updateOpportunityCenterTable(opportunities);
    updateDashboardFromOpportunities(opportunities);
    updatePriorityActionsFromOpportunities(opportunities);

  } catch (error) {
    console.error("Erro ao carregar oportunidades:", error);

    const container = document.getElementById("opportunitiesTableBody");
    if (container) {
      container.innerHTML = `
        <tr>
          <td colspan="6">
            Erro ao carregar oportunidades. Tente novamente mais tarde.
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

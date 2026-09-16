/**
 * HAOC VoIP Monitor Enterprise - JavaScript do Dashboard em Tempo Real
 * Atualização assíncrona contínua via AJAX, sem recarregar a página.
 */

let pollIntervalId = null;
let pollIntervalSeconds = 10;
let isPolling = false;

document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
});

function initDashboard() {
  // 1. Carregamento inicial de estatísticas e ramais
  carregarDadosCompletos();

  // 2. Intervalo de atualização configurável pelo usuário
  const intervalSelect = document.getElementById('select-intervalo');
  if (intervalSelect) {
    intervalSelect.addEventListener('change', (e) => {
      pollIntervalSeconds = parseInt(e.target.value, 10) || 10;
      reiniciarPolling();
    });
  }
  iniciarPolling();

  // 3. Event listeners de filtros de busca
  const inputBusca = document.getElementById('filtro-busca');
  const selectBloco = document.getElementById('filtro-bloco');
  const selectStatus = document.getElementById('filtro-status');
  const selectSetor = document.getElementById('filtro-setor');
  const selectOrdenar = document.getElementById('filtro-ordenar');

  let debounceTimeout = null;
  const triggerFiltragem = () => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      carregarRamais();
    }, 250);
  };

  if (inputBusca) inputBusca.addEventListener('input', triggerFiltragem);
  if (selectBloco) selectBloco.addEventListener('change', triggerFiltragem);
  if (selectStatus) selectStatus.addEventListener('change', triggerFiltragem);
  if (selectSetor) selectSetor.addEventListener('change', triggerFiltragem);
  if (selectOrdenar) selectOrdenar.addEventListener('change', triggerFiltragem);

  // 4. Botões de controle de varredura
  const btnScan = document.getElementById('btn-iniciar-varredura');
  if (btnScan) {
    btnScan.addEventListener('click', iniciarVarredura);
  }

  const btnCancelScan = document.getElementById('btn-cancelar-varredura');
  if (btnCancelScan) {
    btnCancelScan.addEventListener('click', cancelarVarredura);
  }
}

function iniciarPolling() {
  if (pollIntervalId) clearInterval(pollIntervalId);
  pollIntervalId = setInterval(() => {
    carregarDadosCompletos(true);
  }, pollIntervalSeconds * 1000);
}

function reiniciarPolling() {
  iniciarPolling();
  window.showToast(`Intervalo de atualização ajustado para ${pollIntervalSeconds}s.`, 'info');
}

async function carregarDadosCompletos(silencioso = false) {
  if (isPolling) return;
  isPolling = true;
  try {
    await Promise.all([carregarEstatisticas(), carregarRamais()]);
    atualizarTimestamp();
  } catch (err) {
    console.error("Erro ao atualizar dashboard:", err);
  } finally {
    isPolling = false;
  }
}

async function carregarEstatisticas() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById('stat-total').textContent = data.total_ramais || 0;
    document.getElementById('stat-online').textContent = data.online || 0;
    document.getElementById('stat-offline').textContent = data.offline || 0;
    document.getElementById('stat-inativo').textContent = data.inativos || 0;
    document.getElementById('stat-sem-ip').textContent = data.sem_ip || 0;
    document.getElementById('stat-disponibilidade').textContent = `${data.disponibilidade_pct || 0}%`;
    document.getElementById('stat-latencia').textContent = `${data.latencia_media_ms || 0} ms`;

    // Status da varredura
    const statusTag = document.getElementById('scan-engine-status');
    const pulseDot = document.getElementById('scan-pulse-dot');
    if (data.monitoramento_em_execucao) {
      if (statusTag) statusTag.textContent = "Varrendo rede...";
      if (pulseDot) pulseDot.className = "pulse-dot offline";
      document.getElementById('btn-iniciar-varredura')?.setAttribute('disabled', 'true');
      document.getElementById('btn-cancelar-varredura')?.removeAttribute('disabled');
    } else {
      if (statusTag) statusTag.textContent = "Pronto / Monitorando";
      if (pulseDot) pulseDot.className = "pulse-dot online";
      document.getElementById('btn-iniciar-varredura')?.removeAttribute('disabled');
      document.getElementById('btn-cancelar-varredura')?.setAttribute('disabled', 'true');
    }

    if (data.ultima_varredura) {
      document.getElementById('stat-ultima-varredura').textContent = formatarDataHora(data.ultima_varredura);
    }
  } catch (e) {
    console.error("Erro estatísticas:", e);
  }
}

async function carregarRamais() {
  const busca = document.getElementById('filtro-busca')?.value || '';
  const bloco = document.getElementById('filtro-bloco')?.value || '';
  const status = document.getElementById('filtro-status')?.value || '';
  const setor = document.getElementById('filtro-setor')?.value || '';
  const ordenar = document.getElementById('filtro-ordenar')?.value || 'status';

  const params = new URLSearchParams({
    busca,
    bloco,
    status,
    setor,
    ordenar,
  });

  const res = await fetch(`/api/ramais?${params.toString()}`);
  if (!res.ok) return;
  const data = await res.json();

  renderizarCartoes(data.por_bloco, data.total);
}

function renderizarCartoes(porBloco, total) {
  const container = document.getElementById('container-blocos');
  if (!container) return;

  const totalLabel = document.getElementById('contador-filtrados');
  if (totalLabel) totalLabel.textContent = `${total} ramal(is) encontrado(s)`;

  if (!porBloco || Object.keys(porBloco).length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 3rem; background: var(--bg-secondary); border-radius: var(--radius-lg); border: 1px dashed var(--border-color);">
        <p style="color: var(--text-muted); font-size: 1.1rem;">Nenhum ramal encontrado com os filtros informados.</p>
      </div>
    `;
    return;
  }

  let html = '';
  for (const [nomeBloco, ramais] of Object.entries(porBloco)) {
    const onlineNoBloco = ramais.filter(r => r.status === 'ONLINE').length;
    const totalNoBloco = ramais.length;

    html += `
      <div class="block-section" id="bloco-${nomeBloco.replace(/[^a-zA-Z0-9]/g, '_')}">
        <div class="block-header">
          <div style="display: flex; align-items: center; gap: 0.75rem;">
            <h3>${nomeBloco}</h3>
            <span class="badge ${onlineNoBloco === totalNoBloco ? 'status-online' : 'status-offline'}">
              ${onlineNoBloco}/${totalNoBloco} ONLINE
            </span>
          </div>
        </div>
        <div class="cards-grid">
    `;

    for (const r of ramais) {
      const statusClass = `status-${r.status.toLowerCase()}`;
      const critClass = r.criticidade ? r.criticidade.toLowerCase() : 'normal';

      let infoTempo = '';
      if (r.status === 'OFFLINE' && r.duracao_offline_segundos > 0) {
        infoTempo = `<span style="color: var(--status-offline); font-weight: 600;">⏱️ Off há ${r.duracao_offline_formatada}</span>`;
      } else if (r.status === 'ONLINE' && r.latencia_ms !== null) {
        infoTempo = `<span>📶 ${r.latencia_ms} ms</span>`;
      } else if (r.status === 'AGUARDANDO') {
        infoTempo = `<span>⚠️ Sem IP válido</span>`;
      } else {
        infoTempo = `<span>Inativo</span>`;
      }

      html += `
        <div class="voip-card" id="card-ramal-${r.id}">
          <div class="voip-card-top">
            <span class="voip-card-desc">${r.descricao}</span>
            <span class="badge ${statusClass}">${r.status}</span>
          </div>

          <div class="voip-card-details">
            <div class="detail-item">
              <strong>IP:</strong> ${r.ip || '<em style="color:var(--text-muted)">Não config.</em>'}
            </div>
            <div class="detail-item">
              <strong>MAC:</strong> ${r.mac_cisco || '<em style="color:var(--text-muted)">-</em>'}
            </div>
            <div class="detail-item">
              <strong>Modelo:</strong> ${r.modelo || 'Cisco'}
            </div>
            <div class="detail-item">
              <strong>Setor:</strong> ${r.setor || '-'}
            </div>
          </div>

          <div class="voip-card-footer">
            <div>${infoTempo}</div>
            <div style="display: flex; gap: 0.35rem;">
              ${r.ip ? `<button class="btn btn-secondary btn-sm" onclick="pingIndividual(${r.id}, '${r.ip}')" title="Testar Ping agora">Ping</button>` : ''}
              <a href="/ramais/${r.id}" class="btn btn-secondary btn-sm" title="Ver Detalhes">Detalhes</a>
            </div>
          </div>
        </div>
      `;
    }

    html += `
        </div>
      </div>
    `;
  }

  container.innerHTML = html;
}

async function pingIndividual(ramalId, ip) {
  const card = document.getElementById(`card-ramal-${ramalId}`);
  if (!card) return;

  const btn = card.querySelector('button');
  if (btn) {
    btn.disabled = true;
    btn.textContent = '...';
  }

  try {
    const res = await fetch(`/api/ramais/${ramalId}/ping`, { method: 'POST' });
    const data = await res.json();
    if (data.sucesso) {
      window.showToast(`Ping OK para ${ip}: ${data.latencia} ms`, 'success');
    } else {
      window.showToast(`Ping FALHOU para ${ip}: ${data.erro || 'Host inalcançável'}`, 'danger');
    }
    // Atualiza o estado visual
    await carregarDadosCompletos(true);
  } catch (e) {
    window.showToast(`Erro na requisição de ping: ${e.message}`, 'danger');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Ping';
    }
  }
}

async function iniciarVarredura() {
  try {
    const res = await fetch('/api/scan/start', { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      window.showToast(data.mensagem, 'info');
      carregarEstatisticas();
    } else {
      window.showToast(data.erro || 'Não foi possível iniciar a varredura.', 'warning');
    }
  } catch (err) {
    window.showToast('Erro de comunicação com o servidor.', 'danger');
  }
}

async function cancelarVarredura() {
  try {
    const res = await fetch('/api/scan/cancel', { method: 'POST' });
    const data = await res.json();
    window.showToast(data.mensagem, 'info');
  } catch (err) {
    window.showToast('Erro ao solicitar cancelamento.', 'danger');
  }
}

function atualizarTimestamp() {
  const span = document.getElementById('live-timestamp');
  if (span) {
    const now = new Date();
    span.textContent = now.toLocaleTimeString('pt-BR');
  }
}

function formatarDataHora(isoString) {
  if (!isoString) return '-';
  try {
    const d = new Date(isoString);
    return d.toLocaleTimeString('pt-BR');
  } catch {
    return isoString;
  }
}

/**
 * HAOC VoIP Monitor Enterprise - JavaScript de Importação e Diff de JSON Legado
 */

let analiseAtual = null;

document.addEventListener('DOMContentLoaded', () => {
  const formUpload = document.getElementById('form-upload-json');
  const fileInput = document.getElementById('input-json-file');
  const dropZone = document.getElementById('json-drop-zone');

  if (dropZone && fileInput) {
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.style.borderColor = 'var(--color-brand)';
      dropZone.style.background = 'var(--bg-tertiary)';
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.style.borderColor = 'var(--border-color)';
      dropZone.style.background = 'var(--bg-secondary)';
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.style.borderColor = 'var(--border-color)';
      dropZone.style.background = 'var(--bg-secondary)';
      if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        enviarArquivoParaAnalise();
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        enviarArquivoParaAnalise();
      }
    });
  }

  const btnAplicarTudo = document.getElementById('btn-aplicar-tudo');
  if (btnAplicarTudo) {
    btnAplicarTudo.addEventListener('click', () => aplicarImportacao(false));
  }

  const btnAplicarSelecionados = document.getElementById('btn-aplicar-selecionados');
  if (btnAplicarSelecionados) {
    btnAplicarSelecionados.addEventListener('click', () => aplicarImportacao(true));
  }
});

async function enviarArquivoParaAnalise() {
  const fileInput = document.getElementById('input-json-file');
  if (!fileInput || !fileInput.files[0]) return;

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('arquivo', file);

  const containerResultados = document.getElementById('container-analise');
  const loading = document.getElementById('analise-loading');
  if (loading) loading.style.display = 'block';
  if (containerResultados) containerResultados.style.display = 'none';

  try {
    const res = await fetch('/importacao/analisar', {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();

    if (!res.ok) {
      window.showToast(data.erro || 'Falha ao analisar arquivo.', 'danger');
      return;
    }

    analiseAtual = data.analise;
    renderizarAnalise(analiseAtual);
  } catch (err) {
    window.showToast(`Erro na requisição: ${err.message}`, 'danger');
  } finally {
    if (loading) loading.style.display = 'none';
  }
}

function renderizarAnalise(analise) {
  const container = document.getElementById('container-analise');
  if (!container) return;

  container.style.display = 'block';

  // Métricas do resumo
  document.getElementById('resumo-total').textContent = analise.total_no_arquivo;
  document.getElementById('resumo-novos').textContent = analise.novos.length;
  document.getElementById('resumo-alterados').textContent = analise.alterados.length;
  document.getElementById('resumo-removidos').textContent = analise.removidos.length;
  document.getElementById('resumo-inconsistentes').textContent = analise.inconsistentes.length;

  // Inconsistências
  const alertInconsistencias = document.getElementById('alerta-inconsistencias');
  const listaInconsistencias = document.getElementById('lista-inconsistencias');
  if (analise.inconsistentes.length > 0) {
    alertInconsistencias.style.display = 'block';
    listaInconsistencias.innerHTML = analise.inconsistentes
      .map(i => `<li><strong>Bloco ${i.bloco} - ${i.item.descricao || 'Sem descrição'}:</strong> ${i.erros.join(', ')}</li>`)
      .join('');
  } else {
    alertInconsistencias.style.display = 'none';
  }

  // Tabela de Diferenças
  const tbody = document.getElementById('tbody-diff');
  if (!tbody) return;

  let html = '';

  // Novos
  analise.novos.forEach(item => {
    html += `
      <tr>
        <td style="text-align: center;"><input type="checkbox" class="chk-item" value="${item.chave_estavel}" checked /></td>
        <td><span class="badge" style="background:#dcfce7; color:#15803d;">NOVO</span></td>
        <td><strong>${item.descricao}</strong></td>
        <td>${item.bloco}</td>
        <td>${item.ip || '-'}</td>
        <td>${item.mac_cisco || '-'}</td>
        <td>${item.modelo || '-'}</td>
        <td><span style="color:#15803d;">Novo ramal a ser cadastrado</span></td>
      </tr>
    `;
  });

  // Alterados
  analise.alterados.forEach(alt => {
    const item = alt.item;
    const diffs = alt.diferencas;
    let diffTexto = Object.entries(diffs)
      .map(([k, v]) => `<strong>${k}:</strong> ${v.anterior || '(vazio)'} ➔ <strong>${v.novo || '(vazio)'}</strong>`)
      .join('<br/>');

    html += `
      <tr>
        <td style="text-align: center;"><input type="checkbox" class="chk-item" value="${item.chave_estavel}" checked /></td>
        <td><span class="badge" style="background:#e0f2fe; color:#0369a1;">ALTERADO</span></td>
        <td><strong>${item.descricao}</strong></td>
        <td>${item.bloco}</td>
        <td>${item.ip || '-'}</td>
        <td>${item.mac_cisco || '-'}</td>
        <td>${item.modelo || '-'}</td>
        <td>${diffTexto}</td>
      </tr>
    `;
  });

  // Removidos (ausentes do arquivo)
  analise.removidos.forEach(item => {
    html += `
      <tr style="opacity: 0.75;">
        <td style="text-align: center;">-</td>
        <td><span class="badge" style="background:#fee2e2; color:#b91c1c;">AUSENTE NO ARQUIVO</span></td>
        <td>${item.descricao}</td>
        <td>${item.bloco}</td>
        <td>${item.ip || '-'}</td>
        <td>${item.mac_cisco || '-'}</td>
        <td>${item.modelo || '-'}</td>
        <td><span style="color:#b91c1c;">Presente no banco, não consta no JSON</span></td>
      </tr>
    `;
  });

  tbody.innerHTML = html;
}

async function aplicarImportacao(apenasSelecionados = false) {
  if (!analiseAtual) return;

  let itensSelecionados = null;
  if (apenasSelecionados) {
    const checkboxes = document.querySelectorAll('.chk-item:checked');
    itensSelecionados = Array.from(checkboxes).map(cb => cb.value);
    if (itensSelecionados.length === 0) {
      window.showToast('Nenhum ramal selecionado para aplicar.', 'warning');
      return;
    }
  }

  const removerAusentes = document.getElementById('chk-remover-ausentes')?.checked || false;

  if (!confirm('Deseja realmente aplicar as alterações no banco de dados? Um backup automático será criado preventivamente.')) {
    return;
  }

  try {
    const res = await fetch('/importacao/aplicar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        itens_selecionados: itensSelecionados,
        remover_ausentes: removerAusentes,
      }),
    });
    const data = await res.json();

    if (res.ok) {
      window.showToast(data.mensagem, 'success');
      setTimeout(() => {
        window.location.href = '/ramais';
      }, 1500);
    } else {
      window.showToast(data.erro || 'Falha ao aplicar importação.', 'danger');
    }
  } catch (err) {
    window.showToast(`Erro na requisição: ${err.message}`, 'danger');
  }
}

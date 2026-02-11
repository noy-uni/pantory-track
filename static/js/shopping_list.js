function toggleItem(checkbox) {
  const id = checkbox.getAttribute('data-id');
  const name = checkbox.getAttribute('data-name');
  const unit = checkbox.getAttribute('data-unit');
  
  const card = document.getElementById('card-' + id);
  const container = document.getElementById('arrival-container');
  const arrivalSection = document.getElementById('arrival-section'); // オレンジ枠の親
  const confirmBtn = document.getElementById('confirm-toggle-btn'); // 確認ボタン

  if (checkbox.checked) {
      card.classList.add('c-item-card--completed');
      
      // ★チェックが入ったら「セクション」と「確認ボタン」だけを表示
      arrivalSection.style.display = 'block';
      confirmBtn.style.display = 'block';

      const rowHtml = `
          <div class="c-arrival-row" id="arrival-row-${id}">
              <span class="c-arrival-row__name">${name}</span>
              <div class="c-arrival-row__controls">
                  <input type="number" name="qty_${id}" class="c-arrival-row__qty-input" value="1">
                  <span class="c-arrival-row__unit">${unit}</span>
              </div>
          </div>
      `;
      container.insertAdjacentHTML('beforeend', rowHtml);
  } else {
      card.classList.remove('c-item-card--completed');
      const row = document.getElementById('arrival-row-' + id);
      if (row) row.remove();

      // チェックがゼロになったら全部隠す
      if (container.querySelectorAll('.c-arrival-row').length === 0) {
          arrivalSection.style.display = 'none';
          resetArrivalUI();
      }
  }
}

// ★「確認する」ボタンを押した時の動き
document.getElementById('confirm-toggle-btn').onclick = function() {
  const arrivalSection = document.getElementById('arrival-section');
  const listContainer = document.getElementById('arrival-list-container');
  const submitBtn = document.getElementById('submit-btn');

  // オレンジの枠とリストを表示！
  arrivalSection.classList.add('c-arrival-section--confirmed');
  listContainer.style.display = 'block';
  
  // ボタンを入れ替え
  this.style.display = 'none';
  submitBtn.style.display = 'block';
};

function resetArrivalUI() {
  const section = document.getElementById('arrival-section');
  section.classList.remove('c-arrival-section--confirmed');
  document.getElementById('arrival-list-container').style.display = 'none';
  document.getElementById('confirm-toggle-btn').style.display = 'block';
  document.getElementById('submit-btn').style.display = 'none';
}
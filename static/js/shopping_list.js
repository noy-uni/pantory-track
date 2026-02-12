// ========================================
// お買い物リスト - JavaScript
// ========================================

/**
 * チェックボックスの状態が変わったときの処理
 */
function toggleItem(checkbox) {
  const id = checkbox.getAttribute('data-id');
  const name = checkbox.getAttribute('data-name');
  const unit = checkbox.getAttribute('data-unit');
  
  const card = document.getElementById('card-' + id);
  const container = document.getElementById('arrival-container');
  const arrivalSection = document.getElementById('arrival-section');
  const confirmBtn = document.getElementById('confirm-toggle-btn');

  if (checkbox.checked) {
    // チェックが入った場合
    card.classList.add('is-checked');
    
    // 入庫セクションを表示
    arrivalSection.classList.remove('hidden');
    arrivalSection.classList.add('is-visible');
    
    // 確認ボタンを表示（リストはまだ隠しておく）
    confirmBtn.classList.remove('hidden');

    // 入庫リストに商品を追加（ステッパー式・整数のみ）
    const rowHtml = `
      <div class="arrival-row" id="arrival-row-${id}">
        <div class="arrival-row__name">${name}</div>
        <div class="arrival-row__stepper">
          <button type="button" 
                  class="arrival-row__btn" 
                  onclick="decreaseQty(${id})">
            −
          </button>
          <div class="flex items-center gap-2">
            <span class="arrival-row__qty" id="qty-display-${id}">1</span>
            <span class="arrival-row__unit">${unit}</span>
          </div>
          <button type="button" 
                  class="arrival-row__btn" 
                  onclick="increaseQty(${id})">
            +
          </button>
        </div>
        <!-- 隠しフィールド（フォーム送信用） -->
        <input type="hidden" 
               name="qty_${id}" 
               id="qty-input-${id}" 
               value="1" 
               class="arrival-row__hidden-input">
      </div>
    `;
    container.insertAdjacentHTML('beforeend', rowHtml);
    
  } else {
    // チェックを外した場合
    card.classList.remove('is-checked');
    
    const row = document.getElementById('arrival-row-' + id);
    if (row) row.remove();

    // すべてのチェックが外れたら全体を隠す
    if (container.querySelectorAll('.arrival-row').length === 0) {
      arrivalSection.classList.add('hidden');
      arrivalSection.classList.remove('is-visible');
      resetArrivalUI();
    }
  }
}

/**
 * 数量を増やす（整数のみ・+1）
 */
function increaseQty(id) {
  const display = document.getElementById('qty-display-' + id);
  const input = document.getElementById('qty-input-' + id);
  
  let currentQty = parseInt(input.value);
  currentQty += 1;
  
  display.textContent = currentQty;
  input.value = currentQty;
}

/**
 * 数量を減らす（整数のみ・-1）
 */
function decreaseQty(id) {
  const display = document.getElementById('qty-display-' + id);
  const input = document.getElementById('qty-input-' + id);
  
  let currentQty = parseInt(input.value);
  if (currentQty > 1) {
    currentQty -= 1;
    display.textContent = currentQty;
    input.value = currentQty;
  }
}

/**
 * 「確認する」ボタンがクリックされたとき
 */
document.addEventListener('DOMContentLoaded', function() {
  const confirmBtn = document.getElementById('confirm-toggle-btn');
  const listContainer = document.getElementById('arrival-list-container');
  const submitBtn = document.getElementById('submit-btn');

  if (confirmBtn) {
    confirmBtn.addEventListener('click', function() {
      // 入庫リストを表示
      listContainer.classList.remove('hidden');
      
      // 確認ボタンを隠して、確定ボタンを表示
      this.classList.add('hidden');
      submitBtn.classList.remove('hidden');
      
      // スムーズにスクロール
      listContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  // フォーム送信時のバリデーション
  const form = document.getElementById('arrival-form');
  if (form) {
    form.addEventListener('submit', function(e) {
      const inputs = document.querySelectorAll('.arrival-row__hidden-input');
      let hasValidValue = false;
      
      inputs.forEach(input => {
        const value = parseInt(input.value);
        if (value > 0) {
          hasValidValue = true;
        }
      });
      
      if (!hasValidValue) {
        e.preventDefault();
        alert('⚠️ 入庫する数量を1つ以上入力してください');
      }
    });
  }
});

/**
 * UIをリセット（すべてのチェックが外れたとき）
 */
function resetArrivalUI() {
  const listContainer = document.getElementById('arrival-list-container');
  const confirmBtn = document.getElementById('confirm-toggle-btn');
  const submitBtn = document.getElementById('submit-btn');

  listContainer.classList.add('hidden');
  confirmBtn.classList.remove('hidden');
  submitBtn.classList.add('hidden');
}
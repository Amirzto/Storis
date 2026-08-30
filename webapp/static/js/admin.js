// ====================================
// TajDonater - Admin Panel JS
// ====================================

(function () {
  "use strict";

  const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
  if (tg) { try { tg.ready(); tg.expand(); } catch (e) {} }

  const INIT_DATA = tg ? tg.initData || "" : "";
  const LANG = "ru"; // админка всегда на русском интерфейсе

  let ADMIN_TOKEN = sessionStorage.getItem("admin_token") || "";
  let CURRENT_ADMIN = null;
  let CATEGORIES_CACHE = [];
  let CURRENT_SECTION = "dashboard";

  // ============= LOW-LEVEL FETCH HELPERS =============

  async function apiUser(path, options = {}) {
    const headers = Object.assign({}, options.headers || {}, { "X-Telegram-Init-Data": INIT_DATA });
    const res = await fetch(path, Object.assign({}, options, { headers }));
    return handleResponse(res);
  }

  async function apiAdmin(path, options = {}) {
    const headers = Object.assign({}, options.headers || {}, { "X-Admin-Token": ADMIN_TOKEN });
    const res = await fetch(path, Object.assign({}, options, { headers }));
    if (res.status === 401) {
      // Сессия истекла - вернуть на экран пароля
      ADMIN_TOKEN = "";
      sessionStorage.removeItem("admin_token");
      showLogin();
      throw new Error("Admin session expired");
    }
    return handleResponse(res);
  }

  async function apiAdminJSON(path, method, body) {
    return apiAdmin(path, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
  }

  async function handleResponse(res) {
    let json;
    try { json = await res.json(); } catch (e) { json = null; }
    if (!res.ok) {
      const detail = (json && (json.detail || json.message)) || `Ошибка ${res.status}`;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return json;
  }

  // ============= SCREEN SWITCHING =============

  function el(id) { return document.getElementById(id); }

  function showOnly(screenId) {
    ["admin-loading", "admin-no-access", "admin-login", "admin-shell"].forEach((id) => {
      el(id).style.display = id === screenId ? (id === "admin-shell" ? "block" : "flex") : "none";
    });
  }

  function showLogin() {
    showOnly("admin-login");
    const who = CURRENT_ADMIN
      ? `Здравствуйте, ${CURRENT_ADMIN.telegram_username ? "@" + CURRENT_ADMIN.telegram_username : CURRENT_ADMIN.telegram_id}`
      : "";
    el("admin-login-who").textContent = who;
    el("admin-login-error").textContent = "";
    el("admin-password-input").value = "";
  }

  // ============= TOAST =============

  let toastTimer = null;
  function toast(message, type = "") {
    const t = el("admin-toast");
    t.textContent = message;
    t.className = "admin-toast show" + (type ? " " + type : "");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.className = "admin-toast"; }, 3200);
  }

  // ============= MODAL =============

  function openModal(title, bodyHtml, { onMount, wide } = {}) {
    el("admin-modal-title").textContent = title;
    el("admin-modal-body").innerHTML = bodyHtml;
    el("admin-modal").style.maxWidth = wide ? "640px" : "460px";
    el("admin-modal-overlay").style.display = "flex";
    if (onMount) onMount(el("admin-modal-body"));
  }
  function closeModal() {
    el("admin-modal-overlay").style.display = "none";
    el("admin-modal-body").innerHTML = "";
  }
  el("admin-modal-close").addEventListener("click", closeModal);
  el("admin-modal-overlay").addEventListener("click", (e) => {
    if (e.target === el("admin-modal-overlay")) closeModal();
  });

  // Оборачивает группу полей в отдельную панель со своим заголовком —
  // раньше формы (особенно товара) были одним длинным списком полей подряд,
  // из-за чего сложную форму было неудобно читать и заполнять. Теперь форма
  // делится на понятные "окна": Основное / Поставщик / Изображение / Варианты.
  function formSection(icon, title, innerHtml) {
    return `<div style="background:var(--bg-input);border:1px solid var(--border-color);border-radius:var(--radius-md);padding:14px 14px 4px;margin-bottom:14px;">
      <div style="font-size:12px;font-weight:800;color:var(--text-secondary);text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px;display:flex;align-items:center;gap:6px;">
        <span>${icon}</span><span>${title}</span>
      </div>
      ${innerHtml}
    </div>`;
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }

  function imagePreviewHandler(inputId, previewId) {
    const input = el(inputId);
    const preview = el(previewId);
    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      if (!file) { preview.style.display = "none"; return; }
      preview.src = URL.createObjectURL(file);
      preview.style.display = "block";
    });
  }

  // ============= NAVIGATION =============

  const SECTION_LOADERS = {
    dashboard: loadDashboard,
    categories: loadCategories,
    products: loadProductsSection,
    orders: loadOrders,
    payments: loadPayments,
    users: loadUsers,
    reviews: loadReviews,
    paymethods: loadPaymethods,
    texts: loadTexts,
    settings: loadSettings,
  };

  function switchSection(name) {
    if (name === "more") {
      const sheet = el("admin-more-sheet");
      sheet.style.display = sheet.style.display === "block" ? "none" : "block";
      return;
    }
    el("admin-more-sheet").style.display = "none";
    CURRENT_SECTION = name;

    document.querySelectorAll(".admin-nav-item, .admin-tab-item").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.section === name);
    });
    document.querySelectorAll(".admin-section").forEach((sec) => {
      sec.classList.toggle("active", sec.id === "section-" + name);
    });

    const loader = SECTION_LOADERS[name];
    if (loader) loader().catch((e) => toast(e.message, "error"));
  }

  document.querySelectorAll("[data-section]").forEach((btn) => {
    btn.addEventListener("click", () => switchSection(btn.dataset.section));
  });

  // ============= DARK MODE / REFRESH =============

  function applyTheme() {
    const theme = localStorage.getItem("admin_theme") || "light";
    document.documentElement.setAttribute("data-theme", theme);
    el("admin-dark-toggle").textContent = theme === "dark" ? "☀️" : "🌙";
  }
  el("admin-dark-toggle").addEventListener("click", () => {
    const current = localStorage.getItem("admin_theme") || "light";
    localStorage.setItem("admin_theme", current === "dark" ? "light" : "dark");
    applyTheme();
  });
  applyTheme();

  el("admin-refresh-btn").addEventListener("click", () => {
    const loader = SECTION_LOADERS[CURRENT_SECTION];
    if (loader) loader().then(() => toast("Обновлено")).catch((e) => toast(e.message, "error"));
  });

  // ============= LOGIN FLOW =============

  el("admin-login-btn").addEventListener("click", doLogin);
  el("admin-password-input").addEventListener("keydown", (e) => { if (e.key === "Enter") doLogin(); });

  async function doLogin() {
    const password = el("admin-password-input").value;
    if (!password) return;
    el("admin-login-error").textContent = "";
    el("admin-login-btn").disabled = true;
    try {
      const res = await apiUser("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      ADMIN_TOKEN = res.data.token;
      CURRENT_ADMIN = res.data.admin;
      sessionStorage.setItem("admin_token", ADMIN_TOKEN);
      enterShell();
    } catch (e) {
      el("admin-login-error").textContent = "Неверный пароль";
    } finally {
      el("admin-login-btn").disabled = false;
    }
  }

  function enterShell() {
    showOnly("admin-shell");
    el("admin-current-name").textContent = CURRENT_ADMIN.telegram_username
      ? "@" + CURRENT_ADMIN.telegram_username
      : String(CURRENT_ADMIN.telegram_id);
    switchSection("dashboard");
    pollPendingBadge();
  }

  async function boot() {
    showOnly("admin-loading");
    let me;
    try {
      me = await apiUser("/api/user");
    } catch (e) {
      showOnly("admin-no-access");
      return;
    }
    if (!me.data.is_admin) {
      showOnly("admin-no-access");
      return;
    }
    CURRENT_ADMIN = me.data;

    if (ADMIN_TOKEN) {
      try {
        const meAdmin = await apiAdmin("/api/admin/me");
        CURRENT_ADMIN = meAdmin.data;
        enterShell();
        return;
      } catch (e) {
        // токен истёк - показать вход по паролю снова
      }
    }
    showLogin();
  }

  // ============= DASHBOARD =============

  async function loadDashboard() {
    const res = await apiAdmin("/api/admin/stats");
    const s = res.data;
    el("stat-total-users").textContent = s.total_users;
    el("stat-blocked-users").textContent = s.blocked_users;
    el("stat-total-orders").textContent = s.total_orders;
    el("stat-weekly-orders").textContent = s.weekly_orders_count;
    el("stat-topups").textContent = s.total_topups_confirmed;
    el("stat-topup-amount").textContent = s.total_topup_amount_somoni + " с.";
    el("stat-spent").textContent = s.total_spent_somoni + " с.";
    el("stat-pending-payments").textContent = s.pending_payments;
    updateBadge(s.pending_payments);
  }

  function updateBadge(count) {
    [el("admin-badge-payments"), el("admin-badge-payments-mobile")].forEach((b) => {
      if (!b) return;
      b.textContent = count;
      b.style.display = count > 0 ? "flex" : "none";
    });
  }

  function pollPendingBadge() {
    apiAdmin("/api/admin/stats").then((res) => updateBadge(res.data.pending_payments)).catch(() => {});
    setInterval(() => {
      if (!ADMIN_TOKEN) return;
      apiAdmin("/api/admin/stats").then((res) => updateBadge(res.data.pending_payments)).catch(() => {});
    }, 30000);
  }

  // ============= CATEGORIES =============

  async function loadCategories() {
    const res = await apiAdmin("/api/admin/categories");
    CATEGORIES_CACHE = res.data;
    renderCategories(res.data);
  }

  function renderCategories(list) {
    const box = el("categories-list");
    if (!list.length) {
      box.innerHTML = `<p class="admin-hint">Категорий пока нет. Добавьте первую — например «Free Fire».</p>`;
      return;
    }
    box.innerHTML = list.map((c) => `
      <div class="admin-entity-card">
        <img class="admin-entity-img" src="${c.image_url || ''}" onerror="this.style.opacity=0" alt="">
        <div class="admin-entity-body">
          <div class="admin-entity-title">${escapeHtml(c.name_ru)} <span style="color:var(--text-muted)">/ ${escapeHtml(c.name_tg)}</span></div>
          <div class="admin-entity-sub">${c.is_active ? "Активна" : "Скрыта"}</div>
        </div>
        <div class="admin-entity-actions">
          <button class="admin-btn admin-btn-secondary admin-btn-sm" data-open="${c.id}">Открыть</button>
          <button class="admin-btn admin-btn-secondary admin-btn-sm" data-edit="${c.id}">Изменить</button>
          <button class="admin-btn admin-btn-danger admin-btn-sm" data-del="${c.id}">Удалить</button>
        </div>
      </div>
    `).join("");

    box.querySelectorAll("[data-open]").forEach((b) => b.addEventListener("click", () => {
      const cat = list.find((c) => c.id === +b.dataset.open);
      switchSection("products");
      el("products-category-select").value = String(cat.id);
      loadProductsFor(cat.id);
    }));
    box.querySelectorAll("[data-edit]").forEach((b) => b.addEventListener("click", () => openCategoryModal(list.find((c) => c.id === +b.dataset.edit))));
    box.querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", () => deleteCategory(+b.dataset.del)));
  }

  el("btn-add-category").addEventListener("click", () => openCategoryModal(null));

  function openCategoryModal(cat) {
    const isEdit = !!cat;
    openModal(isEdit ? "Изменить категорию" : "Новая категория", `
      ${formSection("📝", "Название", `
        <label class="admin-label">Название (русский)</label>
        <input class="admin-input" id="f-name-ru" value="${escapeHtml(cat?.name_ru)}" placeholder="Например: Free Fire">
        <label class="admin-label">Номи (тоҷикӣ)</label>
        <input class="admin-input" id="f-name-tg" value="${escapeHtml(cat?.name_tg)}" placeholder="Масалан: Free Fire">
        ${isEdit ? `<label class="admin-label" style="display:flex;align-items:center;gap:8px;"><input type="checkbox" id="f-active" ${cat.is_active ? "checked" : ""}> Категория активна</label>` : ""}
      `)}
      ${formSection("📷", "Изображение", `
        <label class="admin-file-label">Фото категории<input type="file" id="f-image" accept="image/*" style="display:none"></label>
        <img id="f-image-preview" class="admin-modal-preview" style="${cat?.image_url ? 'display:block' : ''}" src="${cat?.image_url || ''}">
      `)}
      <div class="admin-modal-actions">
        <button class="admin-btn admin-btn-secondary" id="f-cancel">Отмена</button>
        <button class="admin-btn admin-btn-primary" id="f-save">Сохранить</button>
      </div>
    `, {
      onMount: () => {
        imagePreviewHandler("f-image", "f-image-preview");
        el("f-cancel").addEventListener("click", closeModal);
        el("f-save").addEventListener("click", () => saveCategory(cat?.id));
      },
    });
  }

  async function saveCategory(id) {
    const nameRu = el("f-name-ru").value.trim();
    const nameTg = el("f-name-tg").value.trim();
    if (!nameRu || !nameTg) { toast("Укажите название на обоих языках", "error"); return; }
    const fd = new FormData();
    fd.append("name_ru", nameRu);
    fd.append("name_tg", nameTg);
    const fileInput = el("f-image");
    if (fileInput.files[0]) fd.append("image", fileInput.files[0]);
    if (id && el("f-active")) fd.append("is_active", el("f-active").checked);

    try {
      await apiAdmin(id ? `/api/admin/categories/${id}` : "/api/admin/categories", { method: id ? "PUT" : "POST", body: fd });
      closeModal();
      toast(id ? "Категория обновлена" : "Категория добавлена", "success");
      loadCategories();
    } catch (e) { toast(e.message, "error"); }
  }

  async function deleteCategory(id) {
    if (!confirm("Удалить категорию и все её товары?")) return;
    try {
      await apiAdmin(`/api/admin/categories/${id}`, { method: "DELETE" });
      toast("Категория удалена", "success");
      loadCategories();
    } catch (e) { toast(e.message, "error"); }
  }

  // ============= PRODUCTS =============

  async function loadProductsSection() {
    if (!CATEGORIES_CACHE.length) {
      const res = await apiAdmin("/api/admin/categories");
      CATEGORIES_CACHE = res.data;
    }
    const select = el("products-category-select");
    select.innerHTML = CATEGORIES_CACHE.map((c) => `<option value="${c.id}">${escapeHtml(c.name_ru)}</option>`).join("");
    if (!CATEGORIES_CACHE.length) {
      el("products-list").innerHTML = `<tr><td colspan="7" class="admin-table-empty">Сначала добавьте категорию</td></tr>`;
      return;
    }
    select.onchange = () => loadProductsFor(+select.value);
    await loadProductsFor(+select.value);
  }

  let PRODUCTS_CACHE = [];
  async function loadProductsFor(categoryId) {
    const res = await apiAdmin(`/api/admin/products?category_id=${categoryId}`);
    // Автосортировка от дешёвого к дорогому
    PRODUCTS_CACHE = res.data.slice().sort((a, b) => a.price_somoni - b.price_somoni);
    renderProducts(PRODUCTS_CACHE, categoryId);
  }

  function renderProducts(list, categoryId) {
    const body = el("products-list");
    if (!list.length) {
      body.innerHTML = `<tr><td colspan="7" class="admin-table-empty">Товаров пока нет</td></tr>`;
      return;
    }
    body.innerHTML = list.map((p) => {
      const variantCount = p.variants ? Object.keys(p.variants).length : 0;
      return `
      <tr>
        <td>${escapeHtml(p.name_ru)}</td>
        <td>${p.price_somoni.toFixed(2)}</td>
        <td>${p.epinby_product_id}</td>
        <td>${p.epinby_product_type === "TOPUP" ? "Пополнение" : "Ваучер"}</td>
        <td>${variantCount ? variantCount + " регион(а)" : "—"}</td>
        <td>${p.is_active ? '<span class="admin-status-pill status-completed">Активен</span>' : '<span class="admin-status-pill status-failed">Скрыт</span>'}</td>
        <td class="admin-row-actions">
          <button class="admin-btn admin-btn-secondary admin-btn-sm" data-edit="${p.id}">✏️</button>
          <button class="admin-btn admin-btn-danger admin-btn-sm" data-del="${p.id}">🗑</button>
        </td>
      </tr>`;
    }).join("");

    body.querySelectorAll("[data-edit]").forEach((b) => b.addEventListener("click", () => openProductModal(list.find((p) => p.id === +b.dataset.edit), categoryId)));
    body.querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", () => deleteProduct(+b.dataset.del, categoryId)));
  }

  el("btn-add-product").addEventListener("click", () => {
    const categoryId = +el("products-category-select").value;
    if (!categoryId) { toast("Сначала добавьте категорию", "error"); return; }
    openEpinbyImportModal(categoryId);
  });

  // ============= ИМПОРТ ТОВАРА ИЗ EPINBY =============
  // Раньше товар добавлялся полностью вручную (включая Epinby ID вслепую).
  // Теперь: выбираешь товар из каталога поставщика — id/картинка/тип подтягиваются
  // сами, вручную остаётся ввести только своё название (tg/ru) и цену.
  let epinbyGamesCache = null;

  async function openEpinbyImportModal(categoryId) {
    openModal("Импорт товара из Epinby", `
      <div class="admin-text-fields" style="margin-bottom:12px;">
        <select class="admin-select admin-input-inline" id="ei-game" style="min-width:160px">
          <option value="">Все игры</option>
        </select>
        <input class="admin-input admin-input-inline" id="ei-search" placeholder="Поиск по названию товара">
      </div>
      <div id="ei-list" style="max-height:50vh; overflow-y:auto;">
        <p class="admin-hint">Загрузка каталога...</p>
      </div>
      <div class="admin-modal-actions">
        <button class="admin-btn admin-btn-secondary" id="ei-manual">Добавить вручную вместо импорта</button>
        <button class="admin-btn admin-btn-secondary" id="ei-cancel">Отмена</button>
      </div>
    `, {
      wide: true,
      onMount: async () => {
        el("ei-cancel").addEventListener("click", closeModal);
        el("ei-manual").addEventListener("click", () => openProductModal(null, categoryId));

        try {
          if (!epinbyGamesCache) {
            const res = await apiAdmin("/api/admin/epinby-games");
            epinbyGamesCache = res.data || [];
          }
          const gameSelect = el("ei-game");
          epinbyGamesCache.forEach((g) => {
            const opt = document.createElement("option");
            opt.value = g.id ?? g.game_id ?? "";
            opt.textContent = g.name ?? g.title ?? `Игра #${opt.value}`;
            gameSelect.appendChild(opt);
          });
        } catch (e) {
          toast("Не удалось загрузить список игр: " + e.message, "error");
        }

        let debounceTimer;
        const reload = () => loadEpinbyList(categoryId);
        el("ei-game").addEventListener("change", reload);
        el("ei-search").addEventListener("input", () => {
          clearTimeout(debounceTimer);
          debounceTimer = setTimeout(reload, 350);
        });
        reload();
      },
    });
  }

  async function loadEpinbyList(categoryId) {
    const listEl = el("ei-list");
    listEl.innerHTML = `<p class="admin-hint">Загрузка...</p>`;
    const gameId = el("ei-game").value;
    const search = el("ei-search").value.trim();
    try {
      const params = new URLSearchParams();
      if (gameId) params.set("game_id", gameId);
      if (search) params.set("search", search);
      const res = await apiAdmin(`/api/admin/epinby-products?${params.toString()}`);
      const items = res.data || [];
      if (!items.length) {
        listEl.innerHTML = `<p class="admin-hint">Ничего не найдено в каталоге Epinby.</p>`;
        return;
      }
      listEl.innerHTML = `<div class="admin-grid-cards">${items.map((p, i) => `
        <div class="admin-entity-card">
          <img class="admin-entity-img" src="${p.image_url || ''}" onerror="this.style.visibility='hidden'">
          <div class="admin-entity-body">
            <div class="admin-entity-title">${escapeHtml(p.name || 'Без названия')}</div>
            <div class="admin-entity-sub">Epinby ID: ${p.epinby_product_id ?? '—'} · ${p.type === 'TOPUP' ? 'Пополнение' : 'Ваучер'}</div>
          </div>
          <div class="admin-entity-actions">
            <button class="admin-btn admin-btn-primary admin-btn-sm" data-pick="${i}">Выбрать</button>
          </div>
        </div>`).join("")}</div>`;
      listEl.querySelectorAll("[data-pick]").forEach((b) => {
        b.addEventListener("click", () => {
          const picked = items[+b.dataset.pick];
          openProductModal(null, categoryId, picked);
        });
      });
    } catch (e) {
      listEl.innerHTML = `<p class="admin-hint">Ошибка загрузки каталога: ${escapeHtml(e.message)}</p>`;
    }
  }

  function variantRowHtml(region = "", epinbyId = "") {
    return `<div class="admin-text-fields" style="margin-bottom:8px;">
      <input class="admin-input admin-input-inline" style="min-width:110px" placeholder="Регион (GLOBAL, CIS...)" data-variant-region value="${escapeHtml(region)}">
      <input class="admin-input admin-input-inline" style="min-width:110px" placeholder="Epinby ID" type="number" data-variant-epinby value="${escapeHtml(epinbyId)}">
      <button type="button" class="admin-btn admin-btn-danger admin-btn-sm" data-variant-remove>✕</button>
    </div>`;
  }

  function openProductModal(product, categoryId, imported) {
    // imported — товар, выбранный в окне "Импорт из Epinby" (openEpinbyImportModal):
    // { epinby_product_id, name, image_url, type }. Из него подставляем всё,
    // КРОМЕ названия для покупателя и цены — их всегда вводит админ вручную.
    const isEdit = !!product;
    const variants = product?.variants || {};
    const variantRows = Object.entries(variants).map(([region, v]) => variantRowHtml(region, v.epinby_product_id)).join("");
    const epinbyId = product?.epinby_product_id ?? imported?.epinby_product_id ?? "";
    const epinbyType = product?.epinby_product_type ?? imported?.type ?? "VOUCHER";
    const imageUrl = product?.image_url ?? imported?.image_url ?? "";
    const importedHint = imported
      ? `<p class="admin-hint" style="margin-top:0">Товар поставщика: <b>${escapeHtml(imported.name || "")}</b> (Epinby ID ${epinbyId}) — картинка и тип подставлены автоматически, впишите своё название и цену.</p>`
      : "";

    openModal(isEdit ? "Изменить товар" : "Новый товар", `
      ${formSection("📝", "Основное", `
        <label class="admin-label">Название (русский)</label>
        <input class="admin-input" id="f-name-ru" value="${escapeHtml(product?.name_ru)}" placeholder="Например: 100 алмазов">
        <label class="admin-label">Номи (тоҷикӣ)</label>
        <input class="admin-input" id="f-name-tg" value="${escapeHtml(product?.name_tg)}" placeholder="Масалан: 100 алмос">
        <div class="admin-text-fields">
          <input class="admin-input" id="f-price" type="number" step="0.01" placeholder="Цена, сомони" value="${product?.price_somoni ?? ''}">
          <select class="admin-select" id="f-type" style="flex:1;min-width:180px;">
            <option value="VOUCHER" ${epinbyType !== "TOPUP" ? "selected" : ""}>Ваучер (код)</option>
            <option value="TOPUP" ${epinbyType === "TOPUP" ? "selected" : ""}>Пополнение (по ID игрока)</option>
          </select>
        </div>
      `)}
      ${formSection("🔗", "Поставщик (Epinby)", `
        ${importedHint}
        <label class="admin-label">Epinby Product ID</label>
        <input class="admin-input" id="f-epinby-id" type="number" placeholder="Epinby Product ID" value="${epinbyId}" ${imported ? "readonly" : ""}>
      `)}
      ${formSection("📷", "Изображение", `
        <label class="admin-file-label">Фото товара (необязательно, можно переопределить)<input type="file" id="f-image" accept="image/*" style="display:none"></label>
        <img id="f-image-preview" class="admin-modal-preview" style="${imageUrl ? 'display:block' : ''}" src="${imageUrl}">
      `)}
      ${formSection("🌍", "Региональные варианты (необязательно)", `
        <p class="admin-hint" style="margin-top:0">Например GLOBAL и CIS с разным Epinby ID — цена в мини-аппе останется общей.</p>
        <div id="variant-rows">${variantRows}</div>
        <button type="button" class="admin-btn admin-btn-secondary admin-btn-sm" id="f-add-variant" style="margin-bottom:14px;">+ Добавить регион</button>
      `)}

      <div class="admin-modal-actions">
        <button class="admin-btn admin-btn-secondary" id="f-cancel">Отмена</button>
        <button class="admin-btn admin-btn-primary" id="f-save">Сохранить</button>
      </div>
    `, {
      wide: true,
      onMount: () => {
        imagePreviewHandler("f-image", "f-image-preview");
        el("f-cancel").addEventListener("click", closeModal);
        el("f-add-variant").addEventListener("click", () => {
          el("variant-rows").insertAdjacentHTML("beforeend", variantRowHtml());
          bindVariantRemove();
        });
        bindVariantRemove();
        el("f-save").addEventListener("click", () => saveProduct(product?.id, categoryId, imported));
      },
    });
  }

  function bindVariantRemove() {
    document.querySelectorAll("[data-variant-remove]").forEach((b) => {
      b.onclick = () => b.closest("div").remove();
    });
  }

  function collectVariants() {
    const rows = document.querySelectorAll("#variant-rows > div");
    const variants = {};
    rows.forEach((row) => {
      const region = row.querySelector("[data-variant-region]").value.trim().toUpperCase();
      const epinbyId = row.querySelector("[data-variant-epinby]").value.trim();
      if (region && epinbyId) variants[region] = { epinby_product_id: parseInt(epinbyId, 10) };
    });
    return Object.keys(variants).length ? variants : null;
  }

  async function saveProduct(id, categoryId, imported) {
    const nameRu = el("f-name-ru").value.trim();
    const nameTg = el("f-name-tg").value.trim();
    const price = parseFloat(el("f-price").value);
    const epinbyId = parseInt(el("f-epinby-id").value, 10);
    if (!nameRu || !nameTg || isNaN(price) || isNaN(epinbyId)) {
      toast("Заполните название, цену и Epinby ID", "error"); return;
    }
    const fd = new FormData();
    if (!id) fd.append("category_id", categoryId);
    fd.append("name_ru", nameRu);
    fd.append("name_tg", nameTg);
    fd.append("price_somoni", price);
    fd.append("epinby_product_id", epinbyId);
    fd.append("epinby_product_type", el("f-type").value);
    const variants = collectVariants();
    fd.append("variants", variants ? JSON.stringify(variants) : "");
    const fileInput = el("f-image");
    if (fileInput.files[0]) {
      fd.append("image", fileInput.files[0]);
    } else if (imported?.image_url) {
      // Картинку не загружали руками — используем ссылку на картинку с сайта поставщика,
      // подставленную при импорте (см. openEpinbyImportModal / openProductModal).
      fd.append("image_url", imported.image_url);
    }

    try {
      await apiAdmin(id ? `/api/admin/products/${id}` : "/api/admin/products", { method: id ? "PUT" : "POST", body: fd });
      closeModal();
      toast(id ? "Товар обновлён" : "Товар добавлен", "success");
      loadProductsFor(categoryId);
    } catch (e) { toast(e.message, "error"); }
  }

  async function deleteProduct(id, categoryId) {
    if (!confirm("Удалить товар?")) return;
    try {
      await apiAdmin(`/api/admin/products/${id}`, { method: "DELETE" });
      toast("Товар удалён", "success");
      loadProductsFor(categoryId);
    } catch (e) { toast(e.message, "error"); }
  }

  // ============= ORDERS =============

  let ordersSearchTimer = null;
  el("orders-search").addEventListener("input", () => {
    clearTimeout(ordersSearchTimer);
    ordersSearchTimer = setTimeout(loadOrders, 350);
  });

  const STATUS_LABELS = {
    PENDING: "Ожидает", PROCESSING: "В обработке", COMPLETED: "Выполнен",
    FAILED: "Ошибка", PARTIAL: "Частично", CONFIRMED: "Подтверждено", REJECTED: "Отклонено",
  };
  const STATUS_CLASS = {
    PENDING: "status-pending", PROCESSING: "status-processing", COMPLETED: "status-completed",
    FAILED: "status-failed", PARTIAL: "status-partial", CONFIRMED: "status-confirmed", REJECTED: "status-rejected",
  };

  async function loadOrders() {
    const search = el("orders-search").value.trim();
    const res = await apiAdmin(`/api/admin/orders${search ? "?search=" + encodeURIComponent(search) : ""}`);
    const body = el("orders-list");
    if (!res.data.length) {
      body.innerHTML = `<tr><td colspan="6" class="admin-table-empty">Заказов за последние 7 дней нет</td></tr>`;
      return;
    }
    body.innerHTML = res.data.map((o) => `
      <tr>
        <td>#${o.id}</td>
        <td>${o.user_username ? "@" + escapeHtml(o.user_username) : ""} <span style="color:var(--text-muted)">(${o.user_telegram_id ?? "—"})</span></td>
        <td>${escapeHtml(o.product_name_ru)}</td>
        <td>${o.total_price_somoni.toFixed(2)} с.${o.is_refunded ? ' <span class="admin-status-pill status-partial">возврат</span>' : ""}</td>
        <td><span class="admin-status-pill ${STATUS_CLASS[o.status] || ""}">${STATUS_LABELS[o.status] || o.status}</span></td>
        <td>${new Date(o.created_at).toLocaleString("ru-RU")}</td>
      </tr>
    `).join("");
  }

  // ============= PAYMENTS (topups) =============

  async function loadPayments() {
    const res = await apiAdmin("/api/admin/payments/pending");
    const box = el("payments-list");
    if (!res.data.length) {
      box.innerHTML = `<p class="admin-hint">Нет пополнений, ожидающих подтверждения.</p>`;
      return;
    }
    box.innerHTML = res.data.map((p) => `
      <div class="admin-payment-item" data-payment="${p.id}">
        <img class="admin-payment-receipt" data-receipt="${p.id}" alt="Чек">
        <div class="admin-payment-info">
          <div class="admin-payment-amount">${p.amount_somoni} сомони</div>
          <div class="admin-payment-meta">${p.user_username ? "@" + escapeHtml(p.user_username) : ""} (ID: ${p.user_telegram_id ?? "—"}) · ${p.payment_method || ""}</div>
          <div class="admin-payment-meta">${new Date(p.created_at).toLocaleString("ru-RU")}</div>
        </div>
        <div class="admin-payment-actions">
          <button class="admin-btn admin-btn-success admin-btn-sm" data-confirm="${p.id}">✅ Подтвердить</button>
          <button class="admin-btn admin-btn-danger admin-btn-sm" data-reject="${p.id}">🚫 Отклонить</button>
        </div>
      </div>
    `).join("");

    // Подгрузить изображения чеков с авторизацией
    box.querySelectorAll("[data-receipt]").forEach(async (img) => {
      try {
        const res = await fetch(`/api/admin/payments/${img.dataset.receipt}/receipt`, { headers: { "X-Admin-Token": ADMIN_TOKEN } });
        if (res.ok) {
          const blob = await res.blob();
          img.src = URL.createObjectURL(blob);
          img.onclick = () => window.open(img.src, "_blank");
        }
      } catch (e) {}
    });

    box.querySelectorAll("[data-confirm]").forEach((b) => b.addEventListener("click", () => confirmPayment(+b.dataset.confirm)));
    box.querySelectorAll("[data-reject]").forEach((b) => b.addEventListener("click", () => rejectPaymentPrompt(+b.dataset.reject)));
  }

  async function confirmPayment(id) {
    if (!confirm("Подтвердить пополнение? Баланс пользователя будет увеличен.")) return;
    try {
      await apiAdmin(`/api/admin/payments/${id}/confirm`, { method: "POST" });
      toast("Пополнение подтверждено", "success");
      loadPayments(); loadDashboard();
    } catch (e) { toast(e.message, "error"); }
  }

  function rejectPaymentPrompt(id) {
    openModal("Отклонить пополнение", `
      <label class="admin-label">Причина (необязательно)</label>
      <textarea class="admin-input" id="f-note" rows="3" placeholder="Например: чек не читается"></textarea>
      <label class="admin-label" style="display:flex;align-items:center;gap:8px;">
        <input type="checkbox" id="f-block"> Заблокировать пользователя (если это фейковый чек)
      </label>
      <div class="admin-modal-actions">
        <button class="admin-btn admin-btn-secondary" id="f-cancel">Отмена</button>
        <button class="admin-btn admin-btn-danger" id="f-save">Отклонить</button>
      </div>
    `, {
      onMount: () => {
        el("f-cancel").addEventListener("click", closeModal);
        el("f-save").addEventListener("click", async () => {
          try {
            await apiAdminJSON(`/api/admin/payments/${id}/reject`, "POST", {
              note: el("f-note").value.trim() || null,
              block_user: el("f-block").checked,
            });
            closeModal();
            toast("Пополнение отклонено", "success");
            loadPayments(); loadDashboard();
          } catch (e) { toast(e.message, "error"); }
        });
      },
    });
  }

  // ============= USERS =============

  let usersSearchTimer = null;
  el("users-search").addEventListener("input", () => {
    clearTimeout(usersSearchTimer);
    usersSearchTimer = setTimeout(loadUsers, 350);
  });

  async function loadUsers() {
    const search = el("users-search").value.trim();
    const res = await apiAdmin(`/api/admin/users${search ? "?search=" + encodeURIComponent(search) : ""}`);
    const body = el("users-list");
    if (!res.data.users.length) {
      body.innerHTML = `<tr><td colspan="7" class="admin-table-empty">Пользователи не найдены</td></tr>`;
      return;
    }
    body.innerHTML = res.data.users.map((u) => `
      <tr>
        <td>${u.telegram_id}</td>
        <td>${u.telegram_username ? "@" + escapeHtml(u.telegram_username) : "—"}</td>
        <td>${u.balance_somoni.toFixed(2)} с.</td>
        <td>${u.total_spent.toFixed(2)} с.</td>
        <td>${new Date(u.created_at).toLocaleDateString("ru-RU")}</td>
        <td>${u.is_blocked ? '<span class="admin-status-pill status-failed">Заблокирован</span>' : '<span class="admin-status-pill status-completed">Активен</span>'}${u.is_admin ? ' <span class="admin-status-pill status-partial">Админ</span>' : ""}</td>
        <td class="admin-row-actions">
          ${u.is_admin ? "" : u.is_blocked
            ? `<button class="admin-btn admin-btn-success admin-btn-sm" data-unblock="${u.id}">Разблокировать</button>`
            : `<button class="admin-btn admin-btn-danger admin-btn-sm" data-block="${u.id}">Заблокировать</button>`}
        </td>
      </tr>
    `).join("");

    body.querySelectorAll("[data-block]").forEach((b) => b.addEventListener("click", () => toggleUserBlock(+b.dataset.block, true)));
    body.querySelectorAll("[data-unblock]").forEach((b) => b.addEventListener("click", () => toggleUserBlock(+b.dataset.unblock, false)));
  }

  async function toggleUserBlock(id, block) {
    if (block && !confirm("Заблокировать пользователя? Он потеряет доступ к боту.")) return;
    try {
      await apiAdmin(`/api/admin/users/${id}/${block ? "block" : "unblock"}`, { method: "POST" });
      toast(block ? "Пользователь заблокирован" : "Пользователь разблокирован", "success");
      loadUsers();
    } catch (e) { toast(e.message, "error"); }
  }

  // ============= REVIEWS =============

  async function loadReviews() {
    const res = await apiAdmin("/api/admin/reviews");
    const box = el("reviews-list");
    if (!res.data.length) {
      box.innerHTML = `<p class="admin-hint">Отзывов пока нет.</p>`;
      return;
    }
    box.innerHTML = res.data.map((r) => `
      <div class="admin-card">
        <h3>${"⭐".repeat(r.rating)} — ${escapeHtml(r.author_name)}</h3>
        <p style="font-size:13.5px;color:var(--text-secondary);margin:0 0 6px;">${escapeHtml(r.text_ru || "")}</p>
        <p style="font-size:13.5px;color:var(--text-muted);margin:0 0 12px;">${escapeHtml(r.text_tg || "")}</p>
        <div class="admin-row-actions">
          <button class="admin-btn admin-btn-secondary admin-btn-sm" data-edit="${r.id}">Изменить</button>
          <button class="admin-btn admin-btn-danger admin-btn-sm" data-del="${r.id}">Удалить</button>
        </div>
      </div>
    `).join("");

    box.querySelectorAll("[data-edit]").forEach((b) => b.addEventListener("click", () => openReviewModal(res.data.find((r) => r.id === +b.dataset.edit))));
    box.querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", () => deleteReview(+b.dataset.del)));
  }

  el("btn-add-review").addEventListener("click", () => openReviewModal(null));

  function openReviewModal(review) {
    openModal(review ? "Изменить отзыв" : "Добавить отзыв", `
      ${formSection("👤", "Автор и оценка", `
        <label class="admin-label">Имя автора</label>
        <input class="admin-input" id="f-author" value="${escapeHtml(review?.author_name)}" placeholder="Имя">
        <label class="admin-label">Оценка</label>
        <select class="admin-select" id="f-rating">
          ${[5, 4, 3, 2, 1].map((n) => `<option value="${n}" ${review?.rating === n ? "selected" : ""}>${"⭐".repeat(n)}</option>`).join("")}
        </select>
      `)}
      ${formSection("💬", "Текст отзыва", `
        <label class="admin-label">Текст (русский)</label>
        <textarea class="admin-input" id="f-text-ru" rows="3">${escapeHtml(review?.text_ru)}</textarea>
        <label class="admin-label">Матн (тоҷикӣ)</label>
        <textarea class="admin-input" id="f-text-tg" rows="3">${escapeHtml(review?.text_tg)}</textarea>
      `)}
      <div class="admin-modal-actions">
        <button class="admin-btn admin-btn-secondary" id="f-cancel">Отмена</button>
        <button class="admin-btn admin-btn-primary" id="f-save">Сохранить</button>
      </div>
    `, {
      onMount: () => {
        el("f-cancel").addEventListener("click", closeModal);
        el("f-save").addEventListener("click", async () => {
          const payload = {
            author_name: el("f-author").value.trim() || "Anonymous",
            rating: parseInt(el("f-rating").value, 10),
            text_ru: el("f-text-ru").value.trim(),
            text_tg: el("f-text-tg").value.trim(),
          };
          try {
            await apiAdminJSON(review ? `/api/admin/reviews/${review.id}` : "/api/admin/reviews", review ? "PUT" : "POST", payload);
            closeModal();
            toast("Отзыв сохранён", "success");
            loadReviews();
          } catch (e) { toast(e.message, "error"); }
        });
      },
    });
  }

  async function deleteReview(id) {
    if (!confirm("Удалить отзыв?")) return;
    try {
      await apiAdmin(`/api/admin/reviews/${id}`, { method: "DELETE" });
      toast("Отзыв удалён", "success");
      loadReviews();
    } catch (e) { toast(e.message, "error"); }
  }

  // ============= PAYMENT METHODS (requisites) =============

  async function loadPaymethods() {
    const res = await apiAdmin("/api/admin/payment-methods");
    const box = el("paymethods-list");
    if (!res.data.length) {
      box.innerHTML = `<p class="admin-hint">Реквизиты не добавлены.</p>`;
      return;
    }
    box.innerHTML = res.data.map((m) => `
      <div class="admin-entity-card">
        <img class="admin-entity-img" src="${m.image_url || ''}" onerror="this.style.opacity=0" alt="">
        <div class="admin-entity-body">
          <div class="admin-entity-title">${escapeHtml(m.name_ru)}</div>
          <div class="admin-entity-sub">${escapeHtml(m.account_number || "")} ${m.phone_number ? "· " + escapeHtml(m.phone_number) : ""}</div>
          <div class="admin-entity-sub">${escapeHtml(m.full_name || "")}</div>
          <div class="admin-entity-sub">${m.is_active ? "Активен" : "Скрыт"}</div>
        </div>
        <div class="admin-entity-actions">
          <button class="admin-btn admin-btn-secondary admin-btn-sm" data-edit="${m.id}">Изменить</button>
          <button class="admin-btn admin-btn-danger admin-btn-sm" data-del="${m.id}">Удалить</button>
        </div>
      </div>
    `).join("");

    box.querySelectorAll("[data-edit]").forEach((b) => b.addEventListener("click", () => openPaymethodModal(res.data.find((m) => m.id === +b.dataset.edit))));
    box.querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", () => deletePaymethod(+b.dataset.del)));
  }

  el("btn-add-paymethod").addEventListener("click", () => openPaymethodModal(null));

  function openPaymethodModal(method) {
    openModal(method ? "Изменить реквизит" : "Новый реквизит", `
      ${formSection("📝", "Название", `
        <label class="admin-label">Название (русский)</label>
        <input class="admin-input" id="f-name-ru" value="${escapeHtml(method?.name_ru)}" placeholder="Например: Алиф Мобайл">
        <label class="admin-label">Номи (тоҷикӣ)</label>
        <input class="admin-input" id="f-name-tg" value="${escapeHtml(method?.name_tg)}" placeholder="Масалан: Алиф Мобайл">
        ${method ? `<label class="admin-label" style="display:flex;align-items:center;gap:8px;"><input type="checkbox" id="f-active" ${method.is_active ? "checked" : ""}> Активен</label>` : ""}
      `)}
      ${formSection("🏦", "Реквизиты", `
        <label class="admin-label">Номер счёта / карты</label>
        <input class="admin-input" id="f-account" value="${escapeHtml(method?.account_number)}">
        <label class="admin-label">Телефон</label>
        <input class="admin-input" id="f-phone" value="${escapeHtml(method?.phone_number)}">
        <label class="admin-label">ФИО получателя</label>
        <input class="admin-input" id="f-fullname" value="${escapeHtml(method?.full_name)}">
      `)}
      ${formSection("📷", "Логотип / фото", `
        <label class="admin-file-label">Загрузить изображение<input type="file" id="f-image" accept="image/*" style="display:none"></label>
        <img id="f-image-preview" class="admin-modal-preview" style="${method?.image_url ? 'display:block' : ''}" src="${method?.image_url || ''}">
      `)}
      <div class="admin-modal-actions">
        <button class="admin-btn admin-btn-secondary" id="f-cancel">Отмена</button>
        <button class="admin-btn admin-btn-primary" id="f-save">Сохранить</button>
      </div>
    `, {
      wide: true,
      onMount: () => {
        imagePreviewHandler("f-image", "f-image-preview");
        el("f-cancel").addEventListener("click", closeModal);
        el("f-save").addEventListener("click", async () => {
          const fd = new FormData();
          fd.append("name_ru", el("f-name-ru").value.trim());
          fd.append("name_tg", el("f-name-tg").value.trim());
          fd.append("account_number", el("f-account").value.trim());
          fd.append("phone_number", el("f-phone").value.trim());
          fd.append("full_name", el("f-fullname").value.trim());
          if (method && el("f-active")) fd.append("is_active", el("f-active").checked);
          if (el("f-image").files[0]) fd.append("image", el("f-image").files[0]);
          try {
            await apiAdmin(method ? `/api/admin/payment-methods/${method.id}` : "/api/admin/payment-methods", { method: method ? "PUT" : "POST", body: fd });
            closeModal();
            toast("Реквизит сохранён", "success");
            loadPaymethods();
          } catch (e) { toast(e.message, "error"); }
        });
      },
    });
  }

  async function deletePaymethod(id) {
    if (!confirm("Удалить реквизит?")) return;
    try {
      await apiAdmin(`/api/admin/payment-methods/${id}`, { method: "DELETE" });
      toast("Реквизит удалён", "success");
      loadPaymethods();
    } catch (e) { toast(e.message, "error"); }
  }

  // ============= SITE TEXTS =============

  let TEXTS_CACHE = null;
  async function loadTexts() {
    const res = await apiAdmin("/api/admin/texts");
    TEXTS_CACHE = res.data;
    renderTexts(el("texts-search").value.trim().toLowerCase());
  }

  el("texts-search").addEventListener("input", () => renderTexts(el("texts-search").value.trim().toLowerCase()));

  function renderTexts(filter) {
    if (!TEXTS_CACHE) return;
    const { base, overrides } = TEXTS_CACHE;
    let keys = Object.keys(base);
    if (filter) {
      keys = keys.filter((k) => k.toLowerCase().includes(filter)
        || (base[k].ru || "").toLowerCase().includes(filter)
        || (base[k].tg || "").toLowerCase().includes(filter));
    }
    const box = el("texts-list");
    if (!keys.length) { box.innerHTML = `<p class="admin-hint">Ничего не найдено.</p>`; return; }
    box.innerHTML = keys.map((key) => {
      const val = overrides[key] || base[key];
      return `
      <div class="admin-text-row" data-key="${escapeHtml(key)}">
        <div class="admin-text-key">${escapeHtml(key)}</div>
        <div class="admin-text-fields">
          <input class="admin-input" data-lang="ru" value="${escapeHtml(val.ru)}" placeholder="Русский">
          <input class="admin-input" data-lang="tg" value="${escapeHtml(val.tg)}" placeholder="Тоҷикӣ">
          <button class="admin-btn admin-btn-primary admin-btn-sm" data-save-text>Сохранить</button>
        </div>
      </div>`;
    }).join("");

    box.querySelectorAll("[data-save-text]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const row = btn.closest(".admin-text-row");
        const key = row.dataset.key;
        const ru = row.querySelector('[data-lang="ru"]').value;
        const tg = row.querySelector('[data-lang="tg"]').value;
        try {
          const res = await apiAdminJSON("/api/admin/texts", "PUT", { [key]: { ru, tg } });
          TEXTS_CACHE.overrides = res.data.overrides;
          toast("Текст обновлён", "success");
        } catch (e) { toast(e.message, "error"); }
      });
    });
  }

  // ============= SETTINGS =============

  async function loadSettings() {
    const res = await apiAdmin("/api/admin/settings");
    el("setting-admin-group").value = res.data.admin_group_chat_id || "";
    el("setting-sales-channel").value = res.data.sales_channel_id || "";
  }

  el("btn-save-settings").addEventListener("click", async () => {
    try {
      await apiAdminJSON("/api/admin/settings", "PUT", {
        admin_group_chat_id: el("setting-admin-group").value.trim() || null,
        sales_channel_id: el("setting-sales-channel").value.trim() || null,
      });
      toast("Настройки сохранены", "success");
    } catch (e) { toast(e.message, "error"); }
  });

  el("btn-change-password").addEventListener("click", async () => {
    const newPassword = el("setting-new-password").value;
    if (newPassword.length < 4) { toast("Минимум 4 символа", "error"); return; }
    try {
      await apiAdminJSON("/api/admin/change-password", "POST", { new_password: newPassword });
      el("setting-new-password").value = "";
      toast("Пароль изменён", "success");
    } catch (e) { toast(e.message, "error"); }
  });

  // ============= START =============

  boot();
})();
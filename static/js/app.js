// ====================================
// TajDonater - Mini App Frontend Logic
// ====================================

const tg = window.Telegram ? window.Telegram.WebApp : null;
if (tg) {
  tg.ready();
  tg.expand();
}

// ============= CONFIG =============
const API_BASE = "/api";

// ============= STATE =============
const state = {
  language: "tg",
  theme: "light",
  currency: "somoni",
  user: null,
  categories: [],
  currentCategory: null,
  products: [],
  selectedProduct: null,
  selectedVariant: null,
  playerInfo: null,
  topupAmount: 0,
  selectedPaymentMethod: null,
  paymentMethods: [],
  historyTab: "orders",
  historyFilter: "all",
  navStack: ["menu"],
  exchangeRate: 0.108, // 1 RUB = X TJS (fetched from backend ideally)
};

// ============= TRANSLATIONS =============
const T = {
  tg: {
    txt_balance: "Баланс", txt_somoni: "сомонӣ", txt_topup_btn: "Пур кардан",
    txt_bonus_btn: "Рамзи бонус", txt_support_btn: "Дастгирӣ",
    txt_tab_games: "Бозиҳо", txt_loading_catalog: "Каталог бор мешавад...",
    txt_giftcode_soon: "Ҳоло холӣ аст. Бахши Gift Code ба зудӣ оғоз мешавад. Интизор шавед!",
    txt_player_id: "ID-и бозингар", txt_verify_btn: "Санҷидан",
    txt_select_region: "Минтақаро интихоб кунед",
    txt_select_product: "МАҲСУЛОТРО ИНТИХОБ КУНЕД",
    txt_confirm_title: "Тасдиқи фармоиш", txt_confirm_product: "Маҳсулот",
    txt_confirm_player: "Бозингар", txt_confirm_price: "Нарх",
    txt_confirm_balance: "Баланси шумо", txt_place_order: "✅ Фармоиш додан",
    txt_confirm_topup_btn: "Пур кардани баланс",
    txt_topup_title: "Пур кардани баланс", txt_select_amount: "МИҚДОРРО ИНТИХОБ КУНЕД",
    txt_somoni_label: "сомонӣ", txt_continue: "Идома додан →",
    txt_change_method: "Иваз кардани усул", txt_pay_to: "БА ИН ҲИСОБ ПУЛ ИБОРАТ КУНЕД",
    txt_somoni_sm: "сомонӣ", txt_click_to_copy: "Барои нусха гирифтан клик кунед",
    txt_phone_label: "РАҚАМИ ТЕЛЕФОН", txt_express_pay: "Тавассути ExpressPay пардохт кардан",
    txt_express_hint: "Саҳифаи пардохт дар браузер ё барнома кушода мешавад",
    txt_skip: "Пас аз пардохт", txt_upload_receipt: "Чаки пардохтро бор кунед:",
    txt_upload_photo: "Акси чакро бор кунед", txt_file_size: "JPG, PNG — ҳадди аксар 5МБ",
    txt_submit_receipt: "✅ Барои тасдиқ фиристодан",
    txt_history_title: "Таърих", txt_orders: "Фармоишҳо", txt_payments_tab: "Молия",
    txt_all: "Ҳама", txt_completed: "Иҷро шуд", txt_pending: "Дар интизор", txt_failed: "Бекор шуд",
    txt_no_orders: "Фармоишҳо нест",
    txt_profile_title: "Профил", txt_id_label: "ID: ",
    txt_balance_label: "БАЛАНС", txt_stat_somoni: "сомонӣ",
    txt_spent_label: "ҶАМЪИ ХАРҶОТ", txt_stat_somoni2: "сомонӣ",
    txt_profile_topup: "Пур кардани баланс",
    txt_lang_label: "Забон", txt_theme_label: "Реҷаи шабона",
    txt_invite_friends: "Даъват кардани дӯстон", txt_notifications: "Огоҳиҳо",
    txt_support_menu: "Дастгирӣ", txt_reviews_menu: "Баҳо ва шарҳҳо",
    txt_security_menu: "Амнияти маълумот",
    txt_reviews_title: "Баҳо ва шарҳҳо",
    txt_referral_title: "Даъват кардани дӯстон", txt_referral_system: "Истиноди реферал",
    txt_referral_desc: "Аз ҳар харид муваффақи дӯстатон 1% бонуси автоматӣ гиред!",
    txt_copy_link: "📋 Нусха гирифтан", txt_share_link: "📤 Мубодила",
    txt_invited_friends: "Дӯстони даъватшуда", txt_no_referrals: "Ҳоло ҳеч кас нест. Дӯстонатро даъват кунед ва бонус ҷамъ кунед",
    txt_support_page_title: "Дастгирӣ", txt_support_desc: "Бо мо тамос гиред",
    txt_notif_title: "Огоҳиҳо", txt_notif_off: "Огоҳиҳо ғайрифаъол аст",
    txt_notif_desc: "Барои гирифтани огоҳиҳо дар бораи харидҳо ва акцияҳо иҷозат диҳед",
    txt_allow: "Иҷозат додан", txt_notif_purchases: "ХАРИДҲО",
    txt_notif_order_done: "Вақте харид иҷро шавад", txt_notif_payment_ok: "Вақте пардохт муваффақ бошад",
    txt_notif_finance: "МОЛИЯ", txt_notif_balance: "Вақте баланс пур шавад",
    txt_notif_money_added: "Вақте пул ба ҳисобатон биёяд", txt_notif_news: "ХАБАРҲО",
    txt_notif_promo: "Рамзҳои нави промо", txt_notif_promo_desc: "Дар бораи тахфифҳо ва акцияҳо",
    txt_notif_footer: "Огоҳиҳо танҳо тавассути Telegram бот фиристода мешаванд. Паёмҳои SMS ё email нест. Ҳар вақт хомӯш карда метавонед.",
    txt_security_title: "Амният", txt_app_password: "ПАРОЛИ БАРНОМА",
    txt_set_password: "Гузоштани рамз", txt_password_desc: "Амнияти харидҳоро таъмин кунед",
    txt_google_acc: "ҲИСОБИ GOOGLE", txt_link_google: "Пайваст кардани Google",
    txt_google_desc: "Барои барқарор кардани рамз зарур аст", txt_biometric: "БИОМЕТРИКА",
    txt_biometric_desc: "Тасдиқи зуди харид",
    txt_nav_menu: "Меню", txt_nav_history: "Таърих", txt_nav_profile: "Танзимот",
    err_insufficient_balance: "Балансатон кофӣ нест. Лутфан ҳисобро пур кунед.",
    err_something_wrong: "Хатои номаълум рух дод",
    err_enter_player_id: "ID-и бозингарро ворид кунед",
    player_verified: "✅ Тасдиқ шуд:",
  },
  ru: {
    txt_balance: "Баланс", txt_somoni: "сомони", txt_topup_btn: "Пополнить",
    txt_bonus_btn: "Промокод", txt_support_btn: "Поддержка",
    txt_tab_games: "Игры", txt_loading_catalog: "Загрузка каталога...",
    txt_giftcode_soon: "Пока пусто. Раздел Gift Code скоро откроется. Ждите!",
    txt_player_id: "ID игрока", txt_verify_btn: "Проверить",
    txt_select_region: "Выберите регион",
    txt_select_product: "ВЫБЕРИТЕ ТОВАР",
    txt_confirm_title: "Подтверждение заказа", txt_confirm_product: "Товар",
    txt_confirm_player: "Игрок", txt_confirm_price: "Цена",
    txt_confirm_balance: "Ваш баланс", txt_place_order: "✅ Оформить заказ",
    txt_confirm_topup_btn: "Пополнить баланс",
    txt_topup_title: "Пополнение баланса", txt_select_amount: "ВЫБЕРИТЕ СУММУ",
    txt_somoni_label: "сомони", txt_continue: "Продолжить →",
    txt_change_method: "Изменить способ", txt_pay_to: "ОПЛАТИТЕ НА ЭТОТ СЧЁТ",
    txt_somoni_sm: "сомони", txt_click_to_copy: "Нажмите чтобы скопировать",
    txt_phone_label: "НОМЕР ТЕЛЕФОНА", txt_express_pay: "Оплатить через ExpressPay",
    txt_express_hint: "Страница оплаты откроется в браузере или приложении",
    txt_skip: "После оплаты", txt_upload_receipt: "Загрузите чек оплаты:",
    txt_upload_photo: "Загрузить фото чека", txt_file_size: "JPG, PNG — макс. 5МБ",
    txt_submit_receipt: "✅ Отправить на подтверждение",
    txt_history_title: "История", txt_orders: "Заказы", txt_payments_tab: "Финансы",
    txt_all: "Все", txt_completed: "Выполнено", txt_pending: "В ожидании", txt_failed: "Отменено",
    txt_no_orders: "Заказов нет",
    txt_profile_title: "Профиль", txt_id_label: "ID: ",
    txt_balance_label: "БАЛАНС", txt_stat_somoni: "сомони",
    txt_spent_label: "ВСЕГО ПОТРАЧЕНО", txt_stat_somoni2: "сомони",
    txt_profile_topup: "Пополнить баланс",
    txt_lang_label: "Язык", txt_theme_label: "Тёмная тема",
    txt_invite_friends: "Пригласить друзей", txt_notifications: "Уведомления",
    txt_support_menu: "Поддержка", txt_reviews_menu: "Оценки и отзывы",
    txt_security_menu: "Безопасность данных",
    txt_reviews_title: "Оценки и отзывы",
    txt_referral_title: "Пригласить друзей", txt_referral_system: "Реферальная система",
    txt_referral_desc: "Получайте 1% автоматический бонус с каждой покупки друга!",
    txt_copy_link: "📋 Скопировать", txt_share_link: "📤 Поделиться",
    txt_invited_friends: "Приглашённые друзья", txt_no_referrals: "Пока никого нет. Пригласите друзей и получайте бонус",
    txt_support_page_title: "Поддержка", txt_support_desc: "Свяжитесь с нами",
    txt_notif_title: "Уведомления", txt_notif_off: "Уведомления отключены",
    txt_notif_desc: "Разрешите получать уведомления о покупках и акциях",
    txt_allow: "Разрешить", txt_notif_purchases: "ПОКУПКИ",
    txt_notif_order_done: "Когда покупка выполнена", txt_notif_payment_ok: "Когда оплата прошла успешно",
    txt_notif_finance: "ФИНАНСЫ", txt_notif_balance: "Когда баланс пополнен",
    txt_notif_money_added: "Когда деньги поступят на счёт", txt_notif_news: "НОВОСТИ",
    txt_notif_promo: "Новые промокоды", txt_notif_promo_desc: "О скидках и акциях",
    txt_notif_footer: "Уведомления отправляются только через Telegram бота. SMS или email нет. В любой момент можно отключить.",
    txt_security_title: "Безопасность", txt_app_password: "ПАРОЛЬ ПРИЛОЖЕНИЯ",
    txt_set_password: "Установить пароль", txt_password_desc: "Обеспечьте безопасность покупок",
    txt_google_acc: "АККАУНТ GOOGLE", txt_link_google: "Привязать Google",
    txt_google_desc: "Необходимо для восстановления пароля", txt_biometric: "БИОМЕТРИЯ",
    txt_biometric_desc: "Быстрое подтверждение покупки",
    txt_nav_menu: "Меню", txt_nav_history: "История", txt_nav_profile: "Настройки",
    err_insufficient_balance: "Недостаточно средств. Пожалуйста, пополните баланс.",
    err_something_wrong: "Произошла ошибка",
    err_enter_player_id: "Введите ID игрока",
    player_verified: "✅ Подтверждено:",
  }
};

function t(key) {
  return (T[state.language] && T[state.language][key]) || key;
}

function applyTranslations() {
  document.querySelectorAll("[id^='txt-']").forEach(el => {
    const key = "txt_" + el.id.replace("txt-", "").replace(/-/g, "_");
    if (T[state.language][key]) el.textContent = T[state.language][key];
  });
  document.documentElement.lang = state.language;
}

// ============= API HELPER =============
async function apiCall(endpoint, options = {}) {
  const initData = tg ? tg.initData : "";
  try {
    const res = await fetch(API_BASE + endpoint, {
      ...options,
      headers: {
        "Content-Type": options.body instanceof FormData ? undefined : "application/json",
        "X-Telegram-Init-Data": initData,
        ...(options.headers || {})
      }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed");
    return data;
  } catch (err) {
    console.error("API error:", endpoint, err);
    throw err;
  }
}

// ============= INIT =============
async function initApp() {
  try {
    const savedLang = localStorage.getItem("tajdonater_lang");
    const savedTheme = localStorage.getItem("tajdonater_theme");
    if (savedLang) state.language = savedLang;
    if (savedTheme) state.theme = savedTheme;

    document.documentElement.setAttribute("data-theme", state.theme);
    document.getElementById("dark-theme-toggle").checked = state.theme === "dark";

    const userData = await apiCall("/user");
    state.user = userData.data;
    state.language = state.user.language || state.language;

    renderUserInfo();
    applyTranslations();
    updateLangButtons();
    await loadCategories();

    document.getElementById("loading-screen").style.display = "none";
    document.getElementById("main-app").style.display = "block";
  } catch (err) {
    console.error("Init error:", err);
    document.getElementById("loading-screen").style.display = "none";
    document.getElementById("main-app").style.display = "block";
    applyTranslations();
  }
}

function renderUserInfo() {
  if (!state.user) return;
  document.getElementById("user-name").textContent = "@" + (state.user.telegram_username || "user");
  document.getElementById("balance-value").textContent = formatAmount(state.user.balance_somoni);
  document.getElementById("profile-phone").textContent = state.user.phone_number || "—";
  document.getElementById("profile-tg-id").textContent = state.user.telegram_id;
  document.getElementById("profile-balance").textContent = formatAmount(state.user.balance_somoni);
  document.getElementById("profile-spent").textContent = formatAmount(state.user.total_spent || 0);
  const refLink = `https://t.me/TajDonaterBot/app?startapp=${state.user.telegram_id}`;
  const refBox = document.getElementById("referral-link-box");
  if (refBox) refBox.textContent = refLink;
}

function formatAmount(val) {
  return Number(val || 0).toLocaleString("ru-RU", { maximumFractionDigits: 2 });
}

// ============= NAVIGATION =============
function navigateTo(pageName, pushStack = true) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  const page = document.getElementById("page-" + pageName);
  if (page) page.classList.add("active");

  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  if (pageName === "menu") document.getElementById("nav-menu").classList.add("active");
  if (pageName === "history") { document.getElementById("nav-history").classList.add("active"); loadHistory(); }
  if (pageName === "profile") document.getElementById("nav-profile").classList.add("active");

  if (pageName === "reviews") loadReviews();
  if (pageName === "referral") loadReferrals();
  if (pageName === "topup") resetTopupForm();

  if (pushStack) state.navStack.push(pageName);
  if (tg) tg.HapticFeedback && tg.HapticFeedback.impactOccurred("light");
}

function goBack() {
  state.navStack.pop();
  const prev = state.navStack[state.navStack.length - 1] || "menu";
  navigateTo(prev, false);
}

// ============= THEME / LANGUAGE =============
document.getElementById("dark-mode-toggle") && (document.getElementById("dark-mode-toggle").onclick = toggleTheme);

function toggleTheme() {
  state.theme = state.theme === "light" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", state.theme);
  document.getElementById("dark-theme-toggle").checked = state.theme === "dark";
  localStorage.setItem("tajdonater_theme", state.theme);
}

function setLanguage(lang) {
  state.language = lang;
  localStorage.setItem("tajdonater_lang", lang);
  applyTranslations();
  updateLangButtons();
  apiCall("/user/language", { method: "POST", body: JSON.stringify({ language: lang }) }).catch(() => {});
  renderCategories();
}

function updateLangButtons() {
  document.getElementById("lang-tg").classList.toggle("active", state.language === "tg");
  document.getElementById("lang-ru").classList.toggle("active", state.language === "ru");
}

// ============= TABS (Games / Gift Code) =============
function switchTab(tab) {
  document.getElementById("tab-games").classList.toggle("active", tab === "games");
  document.getElementById("tab-giftcode").classList.toggle("active", tab === "giftcode");
  document.getElementById("categories-grid").style.display = tab === "games" ? "grid" : "none";
  document.getElementById("giftcode-section").style.display = tab === "giftcode" ? "block" : "none";
}

// ============= CATEGORIES =============
async function loadCategories() {
  try {
    const res = await apiCall("/categories");
    state.categories = res.data || [];
    renderCategories();
  } catch (err) {
    console.error("Failed to load categories", err);
  }
}

function renderCategories() {
  const grid = document.getElementById("categories-grid");
  if (!state.categories.length) {
    grid.innerHTML = `<div class="empty-state"><div class="empty-icon">📦</div><p>${t("txt_giftcode_soon")}</p></div>`;
    return;
  }
  grid.innerHTML = state.categories.map(cat => `
    <div class="category-card" onclick="openCategory(${cat.id})">
      <img src="${cat.image_url || '/static/img/placeholder.png'}" alt="${cat.name_tg}" />
      <div class="category-name">${state.language === "ru" ? cat.name_ru : cat.name_tg}</div>
    </div>
  `).join("");
}

async function openCategory(categoryId) {
  const category = state.categories.find(c => c.id === categoryId);
  if (!category) return;
  state.currentCategory = category;

  document.getElementById("category-title").textContent = state.language === "ru" ? category.name_ru : category.name_tg;

  try {
    const res = await apiCall(`/products?category_id=${categoryId}`);
    state.products = res.data || [];
  } catch (err) {
    state.products = [];
  }

  const needsPlayer = state.products.some(p => p.epinby_product_type === "TOPUP");
  document.getElementById("player-id-section").style.display = needsPlayer ? "block" : "none";
  document.getElementById("game-name-title").textContent = (state.language === "ru" ? category.name_ru : category.name_tg).toUpperCase();
  document.getElementById("game-icon").src = category.image_url || "/static/img/placeholder.png";
  document.getElementById("player-id-input").value = "";
  document.getElementById("player-verify-result").textContent = "";
  document.getElementById("regions-section").style.display = "none";
  state.playerInfo = null;
  state.selectedVariant = null;

  renderProducts();
  navigateTo("category");
}

function renderProducts() {
  const grid = document.getElementById("products-grid");
  if (!state.products.length) {
    grid.innerHTML = `<div class="empty-state"><div class="empty-icon">📦</div><p>${t("txt_giftcode_soon")}</p></div>`;
    return;
  }
  // Sort cheapest to priciest
  const sorted = [...state.products].sort((a, b) => a.price_somoni - b.price_somoni);
  grid.innerHTML = sorted.map(p => `
    <div class="product-card" id="prod-${p.id}" onclick="selectProduct(${p.id})">
      <img src="${p.image_url || '/static/img/product-placeholder.png'}" alt="" />
      <div class="product-amount">${state.language === "ru" ? p.name_ru : p.name_tg}</div>
      <div class="product-price">${formatAmount(p.price_somoni)} ${t("txt_somoni")}</div>
    </div>
  `).join("");
}

function selectProduct(productId) {
  document.querySelectorAll(".product-card").forEach(el => el.classList.remove("selected"));
  document.getElementById("prod-" + productId).classList.add("selected");
  state.selectedProduct = state.products.find(p => p.id === productId);
  updateBuyBar();
}

function updateBuyBar() {
  const bar = document.getElementById("buy-bar");
  const needsPlayer = state.selectedProduct && state.selectedProduct.epinby_product_type === "TOPUP";
  if (!state.selectedProduct) { bar.style.display = "none"; return; }
  if (needsPlayer && !state.playerInfo) { bar.style.display = "none"; return; }
  bar.style.display = "block";
  document.getElementById("buy-btn-text").textContent =
    `${state.language === "ru" ? "КУПИТЬ" : "ХАРИДАН"} — ${formatAmount(state.selectedProduct.price_somoni)} ${t("txt_somoni")}`;
}

// ============= PLAYER VALIDATION =============
async function validatePlayer() {
  const playerId = document.getElementById("player-id-input").value.trim();
  const resultEl = document.getElementById("player-verify-result");
  if (!playerId) {
    resultEl.textContent = t("err_enter_player_id");
    resultEl.className = "verify-result error";
    return;
  }
  if (!state.selectedProduct) {
    resultEl.textContent = state.language === "ru" ? "Сначала выберите товар" : "Аввал маҳсулот интихоб кунед";
    resultEl.className = "verify-result error";
    return;
  }
  resultEl.textContent = state.language === "ru" ? "Проверка..." : "Санҷиш...";
  resultEl.className = "verify-result";

  try {
    const res = await apiCall("/validate-player", {
      method: "POST",
      body: JSON.stringify({ product_id: state.selectedProduct.epinby_product_id, player_id: playerId })
    });
    state.playerInfo = { ...res.data, player_id: playerId };
    resultEl.textContent = `${t("player_verified")} ${res.data.nickname || res.data.player_name}`;
    resultEl.className = "verify-result success";

    if (state.selectedProduct.variants) {
      renderRegions();
      document.getElementById("regions-section").style.display = "block";
    }
    updateBuyBar();
  } catch (err) {
    resultEl.textContent = "❌ " + (err.message || t("err_something_wrong"));
    resultEl.className = "verify-result error";
    state.playerInfo = null;
    updateBuyBar();
  }
}

function renderRegions() {
  const list = document.getElementById("regions-list");
  const variants = state.selectedProduct.variants || {};
  const regions = Object.keys(variants);
  if (!regions.length) return;
  list.innerHTML = regions.map(r => `
    <div class="region-chip ${state.selectedVariant === r ? 'selected' : ''}" onclick="selectRegion('${r}')">
      🌐 ${r}
    </div>
  `).join("");
}

function selectRegion(region) {
  state.selectedVariant = region;
  renderRegions();
}

// ============= CONFIRM & ORDER =============
function confirmPurchase() {
  if (!state.selectedProduct) return;
  document.getElementById("confirm-product-name").textContent =
    state.language === "ru" ? state.selectedProduct.name_ru : state.selectedProduct.name_tg;
  document.getElementById("confirm-player-val").textContent =
    state.playerInfo ? (state.playerInfo.nickname || state.playerInfo.player_id) : "—";
  document.getElementById("confirm-price-val").textContent =
    `${formatAmount(state.selectedProduct.price_somoni)} ${t("txt_somoni")}`;
  document.getElementById("confirm-balance-val").textContent =
    `${formatAmount(state.user.balance_somoni)} ${t("txt_somoni")}`;
  document.getElementById("confirm-error").style.display = "none";
  document.getElementById("confirm-topup-btn").style.display = "none";
  navigateTo("confirm");
}

function showInsufficientBalance() {
  const errEl = document.getElementById("confirm-error");
  errEl.textContent = t("err_insufficient_balance");
  errEl.style.display = "block";
  document.getElementById("confirm-topup-btn").style.display = "block";
}

async function placeOrder() {
  const errEl = document.getElementById("confirm-error");
  errEl.style.display = "none";
  document.getElementById("confirm-topup-btn").style.display = "none";

  if (state.user.balance_somoni < state.selectedProduct.price_somoni) {
    showInsufficientBalance();
    return;
  }

  try {
    const payload = {
      product_id: state.selectedProduct.id,
      quantity: 1,
    };
    if (state.playerInfo) {
      payload.player_id = state.playerInfo.player_id;
      payload.server_id = state.playerInfo.server_id || null;
    }
    if (state.selectedVariant) payload.variant = state.selectedVariant;

    const res = await apiCall("/orders", { method: "POST", body: JSON.stringify(payload) });

    state.user.balance_somoni -= state.selectedProduct.price_somoni;
    renderUserInfo();

    if (tg) tg.HapticFeedback && tg.HapticFeedback.notificationOccurred("success");
    alert(state.language === "ru" ? "✅ Заказ оформлен!" : "✅ Фармоиш дода шуд!");

    state.navStack = ["menu"];
    navigateTo("history", false);
  } catch (err) {
    const msg = err.message || "";
    if (msg.toLowerCase().includes("insufficient")) {
      showInsufficientBalance();
    } else {
      errEl.textContent = "❌ " + (msg || t("err_something_wrong"));
      errEl.style.display = "block";
    }
  }
}

// ============= TOPUP FLOW =============
function resetTopupForm() {
  document.querySelectorAll(".amount-btn").forEach(b => b.classList.remove("selected"));
  document.getElementById("custom-amount").value = "";
  document.getElementById("custom-ruble").value = "";
  state.topupAmount = 0;
  document.getElementById("topup-continue-btn").disabled = true;
}

function selectAmount(amount) {
  state.topupAmount = amount;
  document.querySelectorAll(".amount-btn").forEach(b => b.classList.remove("selected"));
  event.target.classList.add("selected");
  document.getElementById("custom-amount").value = amount;
  document.getElementById("custom-ruble").value = Math.round(amount / state.exchangeRate);
  document.getElementById("topup-continue-btn").disabled = false;
}

function onCustomAmount() {
  const val = parseFloat(document.getElementById("custom-amount").value) || 0;
  state.topupAmount = val;
  document.getElementById("custom-ruble").value = val ? Math.round(val / state.exchangeRate) : "";
  document.getElementById("topup-continue-btn").disabled = val <= 0;
  document.querySelectorAll(".amount-btn").forEach(b => b.classList.remove("selected"));
}

async function continueTopup() {
  if (state.topupAmount <= 0) return;
  try {
    const res = await apiCall("/payment-methods");
    state.paymentMethods = res.data || [];
    renderPaymentMethods();
    navigateTo("payment-method");
  } catch (err) {
    alert(t("err_something_wrong"));
  }
}

function renderPaymentMethods() {
  const list = document.getElementById("payment-methods-list");
  document.getElementById("selected-method-detail").style.display = "none";
  list.style.display = "flex";
  list.innerHTML = state.paymentMethods.map(m => `
    <div class="payment-method-item" onclick="selectPaymentMethod(${m.id})">
      <img src="${m.image_url || '/static/img/payment-placeholder.png'}" onerror="this.style.display='none'" />
      <span class="pm-name">${state.language === "ru" ? m.name_ru : m.name_tg}</span>
    </div>
  `).join("");
}

function selectPaymentMethod(methodId) {
  state.selectedPaymentMethod = state.paymentMethods.find(m => m.id === methodId);
  document.getElementById("payment-methods-list").style.display = "none";
  document.getElementById("selected-method-detail").style.display = "block";
  document.getElementById("topup-amount-display").textContent = formatAmount(state.topupAmount);
  document.getElementById("method-phone").textContent = state.selectedPaymentMethod.phone_number || "—";
  document.getElementById("method-fullname").textContent = state.selectedPaymentMethod.full_name || "";
  document.getElementById("method-logo").src = state.selectedPaymentMethod.image_url || "";
  resetReceiptUpload();
}

function copyAmount() {
  navigator.clipboard.writeText(String(state.topupAmount));
  if (tg) tg.HapticFeedback && tg.HapticFeedback.impactOccurred("light");
}

function copyPhone() {
  const phone = state.selectedPaymentMethod ? state.selectedPaymentMethod.phone_number : "";
  navigator.clipboard.writeText(phone || "");
  if (tg) tg.HapticFeedback && tg.HapticFeedback.impactOccurred("light");
}

function openExpressPay() {
  if (state.selectedPaymentMethod && state.selectedPaymentMethod.expresspay_url) {
    if (tg) tg.openLink(state.selectedPaymentMethod.expresspay_url);
    else window.open(state.selectedPaymentMethod.expresspay_url, "_blank");
  }
}

// Receipt upload
let receiptFile = null;
function resetReceiptUpload() {
  receiptFile = null;
  document.getElementById("receipt-input").value = "";
  document.getElementById("receipt-placeholder").style.display = "block";
  document.getElementById("receipt-preview").style.display = "none";
  document.getElementById("submit-receipt-btn").disabled = true;
}

function handleReceiptUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) {
    alert(state.language === "ru" ? "Файл слишком большой (макс. 5МБ)" : "Файл хеле калон аст (ҳадди аксар 5МБ)");
    return;
  }
  receiptFile = file;
  const reader = new FileReader();
  reader.onload = e => {
    document.getElementById("receipt-preview").src = e.target.result;
    document.getElementById("receipt-preview").style.display = "block";
    document.getElementById("receipt-placeholder").style.display = "none";
    document.getElementById("submit-receipt-btn").disabled = false;
  };
  reader.readAsDataURL(file);
}

async function submitReceipt() {
  if (!receiptFile || !state.selectedPaymentMethod) return;
  const btn = document.getElementById("submit-receipt-btn");
  btn.disabled = true;

  try {
    const formData = new FormData();
    formData.append("amount_somoni", state.topupAmount);
    formData.append("payment_method_id", state.selectedPaymentMethod.id);
    formData.append("receipt", receiptFile);

    await apiCall("/payments", { method: "POST", body: formData });

    if (tg) tg.HapticFeedback && tg.HapticFeedback.notificationOccurred("success");
    alert(state.language === "ru"
      ? "✅ Чек отправлен на проверку. Ожидайте подтверждения."
      : "✅ Чек барои санҷиш фиристода шуд. Мунтазир шавед.");

    state.navStack = ["menu"];
    navigateTo("history", false);
  } catch (err) {
    alert("❌ " + (err.message || t("err_something_wrong")));
    btn.disabled = false;
  }
}

// ============= HISTORY =============
function switchHistoryTab(tab) {
  state.historyTab = tab;
  document.getElementById("htab-orders").classList.toggle("active", tab === "orders");
  document.getElementById("htab-payments").classList.toggle("active", tab === "payments");
  loadHistory();
}

function filterHistory(filter) {
  state.historyFilter = filter;
  document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
  event.target.classList.add("active");
  loadHistory();
}

async function loadHistory() {
  const list = document.getElementById("history-list");
  list.innerHTML = `<div class="empty-state"><div class="empty-icon">⏳</div></div>`;

  try {
    const endpoint = state.historyTab === "orders" ? "/orders" : "/payments";
    const res = await apiCall(endpoint);
    let items = res.data || [];

    if (state.historyFilter !== "all") {
      const statusMap = { completed: ["COMPLETED", "CONFIRMED"], pending: ["PENDING", "PROCESSING"], failed: ["FAILED", "REJECTED", "CANCELED"] };
      items = items.filter(i => statusMap[state.historyFilter].includes(i.status));
    }

    if (!items.length) {
      list.innerHTML = `<div class="empty-state"><div class="empty-icon">🕐</div><p>${t("txt_no_orders")}</p></div>`;
      return;
    }

    list.innerHTML = items.map(item => renderHistoryItem(item)).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><p>${t("err_something_wrong")}</p></div>`;
  }
}

function renderHistoryItem(item) {
  const isOrder = state.historyTab === "orders";
  const statusClass = ["COMPLETED", "CONFIRMED"].includes(item.status) ? "completed"
    : ["FAILED", "REJECTED", "CANCELED"].includes(item.status) ? "failed" : "pending";
  const icon = isOrder ? "🎮" : "💰";
  const iconBg = statusClass === "completed" ? "#e8f5e9" : statusClass === "failed" ? "#fde8ea" : "#fff8e1";
  const title = isOrder ? (state.language === "ru" ? item.product_name_ru : item.product_name_tg) : (state.language === "ru" ? "Пополнение" : "Пуркунӣ");
  const amount = isOrder ? item.total_price_somoni : item.amount_somoni;
  const date = new Date(item.created_at).toLocaleString(state.language === "ru" ? "ru-RU" : "tg-TJ", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
  const statusText = { completed: t("txt_completed"), failed: t("txt_failed"), pending: t("txt_pending") }[statusClass];

  return `
    <div class="history-item">
      <div class="history-item-icon" style="background:${iconBg};">${icon}</div>
      <div class="history-item-info">
        <div class="history-item-title">${title || "—"}</div>
        <div class="history-item-date">${date}</div>
      </div>
      <div>
        <div class="history-item-amount">${formatAmount(amount)} ${t("txt_somoni")}</div>
        <span class="status-badge status-${statusClass}">${statusText}</span>
      </div>
    </div>
  `;
}

// ============= REVIEWS =============
async function loadReviews() {
  try {
    const res = await apiCall("/reviews");
    const reviews = res.data.reviews || [];
    const avg = res.data.average || 0;
    const total = res.data.total || 0;

    document.getElementById("avg-rating").textContent = avg.toFixed(1);
    document.getElementById("total-reviews").textContent = `${total} ${state.language === "ru" ? "оценок" : "баҳо"}`;

    const list = document.getElementById("reviews-list");
    list.innerHTML = reviews.map(r => `
      <div class="review-item">
        <div class="review-header">
          <span class="review-author">${r.author_name}</span>
          <span class="review-date">${new Date(r.created_at).toLocaleDateString()}</span>
        </div>
        <div class="review-stars">${"★".repeat(r.rating)}${"☆".repeat(5 - r.rating)}</div>
        <div class="review-text">${(state.language === "ru" ? r.text_ru : r.text_tg) || ""}</div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Failed to load reviews", err);
  }
}

// ============= REFERRAL =============
async function loadReferrals() {
  try {
    const res = await apiCall("/referrals");
    const referrals = res.data.referrals || [];
    document.getElementById("referral-count").textContent = referrals.length;

    const list = document.getElementById("referrals-list");
    if (!referrals.length) {
      list.innerHTML = `<div class="empty-state"><div class="empty-icon">👥</div><p>${t("txt_no_referrals")}</p></div>`;
      return;
    }
    list.innerHTML = referrals.map(r => `
      <div class="history-item">
        <div class="history-item-icon" style="background:#e3f2fd;">👤</div>
        <div class="history-item-info">
          <div class="history-item-title">@${r.telegram_username || r.telegram_id}</div>
          <div class="history-item-date">${new Date(r.created_at).toLocaleDateString()}</div>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Failed to load referrals", err);
  }
}

function copyReferralLink() {
  const link = document.getElementById("referral-link-box").textContent;
  navigator.clipboard.writeText(link);
  if (tg) tg.HapticFeedback && tg.HapticFeedback.impactOccurred("light");
}

function shareReferralLink() {
  const link = document.getElementById("referral-link-box").textContent;
  if (tg) {
    tg.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(link)}`);
  } else {
    navigator.share ? navigator.share({ url: link }) : copyReferralLink();
  }
}

function copyUserId() {
  navigator.clipboard.writeText(String(state.user.telegram_id));
  if (tg) tg.HapticFeedback && tg.HapticFeedback.impactOccurred("light");
}

// ============= SUPPORT =============
function openSupport() {
  if (tg) tg.openTelegramLink("https://t.me/dr_kurbonov04");
  else window.open("https://t.me/dr_kurbonov04", "_blank");
}

// ============= NOTIFICATIONS =============
function requestNotifications() {
  alert(state.language === "ru" ? "Уведомления включены" : "Огоҳиҳо фаъол шуданд");
}

// ============= INIT ON LOAD =============
document.addEventListener("DOMContentLoaded", initApp);

if (tg) {
  tg.onEvent("backButtonClicked", goBack);
}
/* ====================================
   TajDonater - Admin Panel Stylesheet
   ==================================== */

:root {
  --bg-main: #fdf6ec;
  --bg-card: #ffffff;
  --bg-input: #f7f0e3;
  --accent: #7c6cf0;
  --accent-dark: #5f4fd8;
  --accent-gradient: linear-gradient(135deg, #8b7cf6, #6a5cf0);
  --text-main: #2b2b33;
  --text-secondary: #8a8a94;
  --text-muted: #b5b0c2;
  --success: #3ecf6a;
  --success-bg: #e8f5e9;
  --danger: #f24957;
  --danger-bg: #fde8ea;
  --warning: #f5a623;
  --warning-bg: #fff4e0;
  --info-bg: #e3f2fd;
  --border-color: #efe8d8;
  --radius-lg: 18px;
  --radius-md: 12px;
  --radius-sm: 8px;
  --shadow: 0 2px 10px rgba(0,0,0,0.05);
  --sidebar-w: 240px;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

[data-theme="dark"] {
  --bg-main: #16151d;
  --bg-card: #201f29;
  --bg-input: #262530;
  --text-main: #f0f0f5;
  --text-secondary: #9a97ab;
  --text-muted: #6d6a7c;
  --border-color: #2e2c3a;
  --shadow: 0 2px 10px rgba(0,0,0,0.3);
}

* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }

html, body {
  margin: 0; padding: 0; height: 100%;
  font-family: var(--font);
  background: var(--bg-main);
  color: var(--text-main);
}

button, input, select, textarea { font-family: inherit; }

#admin-app { min-height: 100vh; }

/* ============= LOADING / GATE SCREENS ============= */
.admin-loading {
  position: fixed; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 16px;
  background: var(--bg-main); color: var(--text-secondary); z-index: 999;
}
.admin-loading-spinner {
  width: 40px; height: 40px; border-radius: 50%;
  border: 3px solid var(--border-color); border-top-color: var(--accent);
  animation: admin-spin 0.8s linear infinite;
}
@keyframes admin-spin { to { transform: rotate(360deg); } }

.admin-gate {
  position: fixed; inset: 0; display: flex; align-items: center; justify-content: center;
  background: var(--bg-main); padding: 20px; z-index: 998;
}
.admin-gate-card {
  background: var(--bg-card); border-radius: var(--radius-lg); box-shadow: var(--shadow);
  padding: 32px 24px; max-width: 360px; width: 100%; text-align: center;
}
.admin-gate-icon { font-size: 40px; margin-bottom: 12px; }
.admin-gate-card h2 { margin: 0 0 8px; font-size: 20px; }
.admin-gate-sub { color: var(--text-secondary); font-size: 14px; margin: 0 0 16px; }
.admin-error { color: var(--danger); font-size: 13px; min-height: 18px; margin-top: 10px; }

/* ============= INPUTS / BUTTONS ============= */
.admin-input, .admin-select, textarea.admin-input {
  width: 100%; padding: 12px 14px; margin-bottom: 12px;
  border: 1px solid var(--border-color); border-radius: var(--radius-sm);
  background: var(--bg-input); color: var(--text-main); font-size: 14px; outline: none;
}
.admin-input:focus, .admin-select:focus { border-color: var(--accent); }
.admin-input-inline { margin-bottom: 0; max-width: 280px; }
.admin-label { display: block; font-size: 13px; color: var(--text-secondary); margin-bottom: 6px; font-weight: 600; }
.admin-hint { color: var(--text-secondary); font-size: 13px; margin: -8px 0 14px; }

.admin-btn {
  border: none; border-radius: var(--radius-sm); padding: 11px 18px;
  font-size: 14px; font-weight: 600; cursor: pointer; transition: opacity .15s, transform .1s;
}
.admin-btn:active { transform: scale(0.97); }
.admin-btn-primary { background: var(--accent-gradient); color: #fff; }
.admin-btn-secondary { background: var(--bg-input); color: var(--text-main); border: 1px solid var(--border-color); }
.admin-btn-danger { background: var(--danger-bg); color: var(--danger); }
.admin-btn-success { background: var(--success-bg); color: var(--success); }
.admin-btn-block { width: 100%; margin-top: 4px; }
.admin-btn:disabled { opacity: .5; cursor: not-allowed; }
.admin-btn-sm { padding: 7px 12px; font-size: 12.5px; }

.admin-icon-btn {
  width: 36px; height: 36px; border-radius: 50%; border: none;
  background: var(--bg-input); color: var(--text-main); font-size: 16px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}

/* ============= TOPBAR ============= */
.admin-topbar {
  height: 58px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 18px; background: var(--bg-card); border-bottom: 1px solid var(--border-color);
  position: sticky; top: 0; z-index: 50;
}
.admin-topbar-brand { display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 15px; }
.admin-topbar-logo { font-size: 18px; }
.admin-topbar-actions { display: flex; align-items: center; gap: 8px; }
.admin-topbar-user { font-size: 13px; color: var(--text-secondary); margin-right: 6px; }

/* ============= LAYOUT ============= */
.admin-body { display: flex; min-height: calc(100vh - 58px); }

.admin-sidebar {
  width: var(--sidebar-w); flex-shrink: 0; background: var(--bg-card);
  border-right: 1px solid var(--border-color); padding: 14px 10px;
  display: flex; flex-direction: column; gap: 2px;
}
.admin-nav-item {
  display: flex; align-items: center; gap: 10px; width: 100%; text-align: left;
  padding: 11px 12px; border: none; background: transparent; border-radius: var(--radius-sm);
  color: var(--text-secondary); font-size: 14px; cursor: pointer; position: relative;
}
.admin-nav-item span { flex: 1; }
.admin-nav-item.active, .admin-nav-item:hover { background: var(--bg-input); color: var(--text-main); }
.admin-nav-item.active { color: var(--accent-dark); font-weight: 600; }

.admin-badge {
  background: var(--danger); color: #fff; font-size: 11px; font-weight: 700;
  min-width: 18px; height: 18px; border-radius: 9px; display: flex;
  align-items: center; justify-content: center; padding: 0 5px;
}

.admin-tabbar { display: none; }
.admin-more-sheet {
  position: fixed; bottom: 60px; left: 10px; right: 10px; z-index: 60;
  background: var(--bg-card); border-radius: var(--radius-md); box-shadow: var(--shadow);
  padding: 8px; border: 1px solid var(--border-color);
}

.admin-main { flex: 1; padding: 24px; max-width: 1200px; }

/* ============= SECTIONS ============= */
.admin-section { display: none; }
.admin-section.active { display: block; animation: admin-fade .15s ease; }
@keyframes admin-fade { from { opacity: 0; } to { opacity: 1; } }

.admin-page-title { font-size: 20px; margin: 0 0 18px; }
.admin-section-header {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  flex-wrap: wrap; margin-bottom: 18px;
}
.admin-section-header .admin-page-title { margin-bottom: 0; margin-right: auto; }

/* ============= STATS ============= */
.admin-stats-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 14px;
}
.admin-stat-card {
  background: var(--bg-card); border-radius: var(--radius-md); box-shadow: var(--shadow);
  padding: 16px; border: 1px solid var(--border-color);
}
.admin-stat-highlight { border-color: var(--warning); background: var(--warning-bg); }
.admin-stat-label { font-size: 12.5px; color: var(--text-secondary); margin-bottom: 6px; }
.admin-stat-value { font-size: 24px; font-weight: 700; }

/* ============= CARDS GRID (categories/reviews/paymethods) ============= */
.admin-grid-cards {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 14px;
}
.admin-card {
  background: var(--bg-card); border-radius: var(--radius-md); box-shadow: var(--shadow);
  border: 1px solid var(--border-color); padding: 16px; margin-bottom: 16px;
}
.admin-card h3 { margin: 0 0 12px; font-size: 15px; }

.admin-entity-card {
  background: var(--bg-card); border-radius: var(--radius-md); box-shadow: var(--shadow);
  border: 1px solid var(--border-color); overflow: hidden; display: flex; flex-direction: column;
}
.admin-entity-img {
  width: 100%; height: 110px; object-fit: cover; background: var(--bg-input);
}
.admin-entity-body { padding: 12px 14px; flex: 1; display: flex; flex-direction: column; gap: 4px; }
.admin-entity-title { font-weight: 600; font-size: 14px; }
.admin-entity-sub { font-size: 12.5px; color: var(--text-secondary); }
.admin-entity-actions { display: flex; gap: 8px; padding: 0 14px 14px; }
.admin-entity-actions .admin-btn { flex: 1; }

/* ============= TABLES ============= */
.admin-table {
  width: 100%; border-collapse: collapse; background: var(--bg-card);
  border-radius: var(--radius-md); overflow: hidden; box-shadow: var(--shadow);
  border: 1px solid var(--border-color); font-size: 13.5px;
}
.admin-table th {
  text-align: left; padding: 12px 14px; background: var(--bg-input);
  color: var(--text-secondary); font-size: 12px; text-transform: uppercase; letter-spacing: .3px;
}
.admin-table td { padding: 11px 14px; border-top: 1px solid var(--border-color); vertical-align: middle; }
.admin-table tr:hover td { background: var(--bg-input); }
.admin-table-empty { text-align: center; color: var(--text-muted); padding: 30px !important; }

.admin-status-pill {
  display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11.5px; font-weight: 700;
}
.status-completed, .status-confirmed { background: var(--success-bg); color: var(--success); }
.status-pending, .status-processing { background: var(--warning-bg); color: var(--warning); }
.status-failed, .status-canceled, .status-rejected { background: var(--danger-bg); color: var(--danger); }
.status-partial { background: var(--info-bg); color: var(--accent-dark); }

.admin-row-actions { display: flex; gap: 6px; }

/* ============= PAYMENTS LIST ============= */
.admin-payments-list { display: flex; flex-direction: column; gap: 12px; }
.admin-payment-item {
  background: var(--bg-card); border-radius: var(--radius-md); box-shadow: var(--shadow);
  border: 1px solid var(--border-color); padding: 14px; display: flex; gap: 14px; align-items: center; flex-wrap: wrap;
}
.admin-payment-receipt {
  width: 64px; height: 64px; border-radius: var(--radius-sm); object-fit: cover;
  cursor: pointer; background: var(--bg-input); flex-shrink: 0;
}
.admin-payment-info { flex: 1; min-width: 160px; }
.admin-payment-amount { font-size: 17px; font-weight: 700; }
.admin-payment-meta { font-size: 12.5px; color: var(--text-secondary); }
.admin-payment-actions { display: flex; gap: 8px; }

/* ============= TEXTS EDITOR ============= */
.admin-texts-list { display: flex; flex-direction: column; gap: 10px; }
.admin-text-row {
  background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md);
  padding: 12px 14px; box-shadow: var(--shadow);
}
.admin-text-key { font-size: 11.5px; color: var(--text-muted); font-family: monospace; margin-bottom: 8px; }
.admin-text-fields { display: flex; gap: 10px; flex-wrap: wrap; align-items: flex-start; }
.admin-text-fields .admin-input { flex: 1; min-width: 200px; margin-bottom: 0; }
.admin-text-fields .admin-btn { flex-shrink: 0; }

/* ============= MODAL ============= */
.admin-modal-overlay {
  position: fixed; inset: 0; background: rgba(20,18,30,0.45);
  display: flex; align-items: center; justify-content: center; z-index: 200; padding: 16px;
}
.admin-modal {
  background: var(--bg-card); border-radius: var(--radius-lg); box-shadow: var(--shadow);
  width: 100%; max-width: 460px; max-height: 88vh; display: flex; flex-direction: column; overflow: hidden;
}
.admin-modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 18px; border-bottom: 1px solid var(--border-color);
}
.admin-modal-header h3 { margin: 0; font-size: 16px; }
.admin-modal-body { padding: 18px; overflow-y: auto; }
.admin-modal-body .admin-input:last-child { margin-bottom: 0; }
.admin-modal-actions { display: flex; gap: 10px; margin-top: 4px; }
.admin-modal-actions .admin-btn { flex: 1; }
.admin-modal-preview {
  width: 100%; height: 120px; object-fit: cover; border-radius: var(--radius-sm);
  margin-bottom: 12px; background: var(--bg-input); display: none;
}
.admin-file-label {
  display: block; padding: 10px 14px; border: 1px dashed var(--border-color); border-radius: var(--radius-sm);
  text-align: center; color: var(--text-secondary); font-size: 13px; cursor: pointer; margin-bottom: 12px;
}

/* ============= TOAST ============= */
.admin-toast {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%) translateY(20px);
  background: var(--text-main); color: var(--bg-main); padding: 12px 20px; border-radius: var(--radius-md);
  font-size: 13.5px; box-shadow: var(--shadow); opacity: 0; pointer-events: none; transition: all .2s; z-index: 300;
  max-width: 90vw; text-align: center;
}
.admin-toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
.admin-toast.error { background: var(--danger); color: #fff; }
.admin-toast.success { background: var(--success); color: #fff; }

/* ============= RESPONSIVE ============= */
@media (max-width: 860px) {
  .admin-sidebar { display: none; }
  .admin-tabbar {
    display: flex; position: fixed; bottom: 0; left: 0; right: 0; height: 58px;
    background: var(--bg-card); border-top: 1px solid var(--border-color); z-index: 55;
  }
  .admin-tab-item {
    flex: 1; border: none; background: transparent; font-size: 19px; position: relative;
    color: var(--text-secondary); display: flex; align-items: center; justify-content: center;
  }
  .admin-tab-item.active { color: var(--accent-dark); }
  .admin-badge-tab { position: absolute; top: 4px; right: 22%; }
  .admin-main { padding: 16px; padding-bottom: 76px; }
  .admin-topbar-user { display: none; }
  .admin-section-header { flex-direction: column; align-items: stretch; }
  .admin-input-inline { max-width: none; }
}
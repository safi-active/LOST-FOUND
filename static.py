# static.py
# All CSS & JS served from a single route.

CSS = """
:root{
  --primary:#1f4e79; --primary-2:#2f6fa8; --accent:#f5a623;
  --bg:#f4f6fa; --card:#ffffff; --text:#1c2530; --muted:#6b7785;
  --danger:#c0392b; --success:#1e8449; --warn:#b9770e; --info:#2471a3;
  --radius:12px; --shadow:0 2px 10px rgba(0,0,0,.06);
}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:var(--text);background:var(--bg)}
a{color:var(--primary);text-decoration:none}
a:hover{text-decoration:underline}
h1,h2,h3{color:var(--primary)}

/* STUDENT THEME */
.student-theme .topbar{display:flex;justify-content:space-between;align-items:center;
  padding:12px 22px;background:linear-gradient(90deg,var(--primary),var(--primary-2));color:#fff;flex-wrap:wrap;gap:10px}
.student-theme .brand{display:flex;gap:10px;align-items:center}
.student-theme .brand h1{font-size:1.05rem;margin:0;color:#fff}
.student-theme .brand small{color:#d7e6f5}
.student-theme .logo{font-size:1.6rem}
.student-theme nav{display:flex;gap:14px;flex-wrap:wrap}
.student-theme nav a{color:#eaf2fb;font-size:.92rem}
.student-theme .btn-logout{background:rgba(255,255,255,.15);padding:6px 10px;border-radius:8px}
.container{max-width:1100px;margin:22px auto;padding:0 16px}
.hero{background:#fff;padding:22px;border-radius:var(--radius);box-shadow:var(--shadow);margin-bottom:18px}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:10px}
.footer{text-align:center;padding:18px;color:var(--muted);font-size:.8rem}

/* ADMIN THEME */
.admin-theme{display:flex;min-height:100vh;background:var(--bg)}
.sidebar{width:230px;background:#0e2436;color:#cfdce8;padding:20px 14px;flex-shrink:0}
.side-brand{font-size:1.15rem;font-weight:600;color:#fff;margin-bottom:20px}
.sidebar nav{display:flex;flex-direction:column;gap:4px}
.sidebar nav a{color:#cfdce8;padding:10px 12px;border-radius:8px;font-size:.92rem}
.sidebar nav a:hover{background:#183449;text-decoration:none}
.sidebar .danger-link{color:#f5b7b1;margin-top:10px}
.admin-main{flex:1;padding:22px 26px;overflow-x:auto}
.admin-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px}

/* Shared components */
.auth-card{background:#fff;padding:24px;border-radius:var(--radius);box-shadow:var(--shadow);max-width:420px;margin:20px auto}
.auth-card.wide{max-width:720px}
.auth-card h2{margin-top:0}
.auth-card label{display:block;margin:10px 0 4px;font-size:.88rem;color:var(--muted);font-weight:600}
.auth-card input,.auth-card select,.auth-card textarea{width:100%;padding:10px 12px;border:1px solid #d0d7e0;border-radius:8px;font-size:.95rem;background:#fff}
.auth-card textarea{resize:vertical}
.auth-card form{margin-top:6px}
.btn-primary,.btn-secondary,.btn-danger{display:inline-block;padding:10px 16px;border-radius:8px;border:none;cursor:pointer;font-size:.92rem;font-weight:600;margin-top:12px}
.btn-primary{background:var(--primary);color:#fff}
.btn-primary:hover{background:var(--primary-2);text-decoration:none}
.btn-secondary{background:#e9eef5;color:var(--primary)}
.btn-secondary:hover{background:#dbe4ef;text-decoration:none}
.btn-danger{background:var(--danger);color:#fff}
.btn-danger.sm{padding:5px 9px;font-size:.78rem;margin-top:0}
.flash-wrap{margin-bottom:14px}
.flash{padding:10px 14px;border-radius:8px;margin-bottom:6px;font-size:.9rem}
.flash-success{background:#e6f7ee;color:var(--success)}
.flash-error{background:#fdecea;color:var(--danger)}
.flash-info{background:#e8f1fb;color:var(--info)}
.muted{color:var(--muted);font-size:.88rem}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--accent);margin-left:6px}

.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.grid-3{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:18px}
.stat-card{background:#fff;border-radius:var(--radius);padding:18px;box-shadow:var(--shadow);display:flex;flex-direction:column;gap:6px;align-items:flex-start}
.stat-num{font-size:1.7rem;font-weight:700;color:var(--primary)}
.card-list{display:flex;flex-direction:column;gap:10px}
.grid-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.card{background:#fff;padding:16px;border-radius:var(--radius);box-shadow:var(--shadow)}
.card.unread{border-left:4px solid var(--accent)}
.card-head{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:6px}
.badge{font-size:.75rem;padding:3px 9px;border-radius:999px;font-weight:700}
.badge-pending{background:#fdf0dc;color:var(--warn)}
.badge-found{background:#e6f7ee;color:var(--success)}
.badge-returned{background:#e8f1fb;color:var(--info)}
.badge-unresolved{background:#fdecea;color:var(--danger)}
.badge-Stored,.badge-Matched,.badge-Collected{background:#eef1f6;color:var(--primary)}
.pill{background:var(--accent);color:#fff;border-radius:999px;font-size:.7rem;padding:1px 7px;margin-left:4px}

.table-wrap{background:#fff;border-radius:var(--radius);box-shadow:var(--shadow);overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th,td{padding:11px 12px;border-bottom:1px solid #eef1f6;text-align:left}
th{background:#f7f9fc;color:var(--muted);font-size:.8rem;text-transform:uppercase;letter-spacing:.04em}
tr:last-child td{border-bottom:none}
.actions-cell{display:flex;gap:6px;align-items:center}
.actions-cell form{display:inline}
.actions-sm{display:flex;gap:8px;margin-top:8px}
.link{color:var(--primary);font-weight:600}
.filter-bar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.filter-bar input,.filter-bar select{padding:9px 12px;border:1px solid #d0d7e0;border-radius:8px;font-size:.9rem}
.panel{background:#fff;border-radius:var(--radius);padding:18px;box-shadow:var(--shadow);margin-bottom:16px}
.panel input,.panel select,.panel textarea{width:100%;padding:9px 11px;border:1px solid #d0d7e0;border-radius:8px;margin-bottom:8px;font-size:.9rem}
details summary{cursor:pointer;margin-bottom:10px}
.timeline{display:flex;flex-direction:column;gap:8px;margin:10px 0}
.timeline-item{padding:10px 14px;background:#f7f9fc;border-left:4px solid var(--primary);border-radius:6px}
.thumb{max-width:220px;border-radius:8px;margin-top:8px;border:1px solid #e2e8f0}

@media (max-width:860px){
  .grid-2{grid-template-columns:1fr}
  .admin-theme{flex-direction:column}
  .sidebar{width:100%}
}
"""

JS = """
// Minimal client-side validation polish
document.addEventListener('DOMContentLoaded', function(){
  document.querySelectorAll('form').forEach(f => {
    f.addEventListener('submit', function(){
      const btn = f.querySelector('button[type=submit]');
      if(btn){ btn.disabled = true; btn.textContent = btn.textContent.trim()+' …'; setTimeout(()=>{btn.disabled=false;},2000); }
    });
  });
});
"""
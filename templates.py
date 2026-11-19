# templates.py
# All HTML templates embedded as strings. Rendered via flask.render_template_string.

STUDENT_BASE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{% block title %}Campus Lost & Found{% endblock %}</title>
<link rel="stylesheet" href="{{ url_for('static_css') }}"/>
</head>
<body class="student-theme">
<header class="topbar">
  <div class="brand">
    <span class="logo">🎒</span>
    <div>
      <h1>University Lost & Found</h1>
      <small>Student Portal</small>
    </div>
  </div>
  <nav>
    {% if session.get('role') == 'student' %}
      <a href="{{ url_for('student_dashboard') }}">Dashboard</a>
      <a href="{{ url_for('student_report_lost') }}">Report Lost</a>
      <a href="{{ url_for('student_my_reports') }}">My Reports</a>
      <a href="{{ url_for('student_found_items') }}">Found Items</a>
      <a href="{{ url_for('student_notifications') }}">Notifications
        {% if notif_count %}<span class="pill">{{ notif_count }}</span>{% endif %}
      </a>
      <a href="{{ url_for('student_profile') }}">Profile</a>
      <a href="{{ url_for('logout') }}" class="btn-logout">Logout</a>
    {% endif %}
  </nav>
</header>
<main class="container">
  {% with msgs = get_flashed_messages(with_categories=true) %}
    {% if msgs %}
      <div class="flash-wrap">
      {% for cat, m in msgs %}
        <div class="flash flash-{{ cat }}">{{ m }}</div>
      {% endfor %}
      </div>
    {% endif %}
  {% endwith %}
  {% block content %}{% endblock %}
</main>
<footer class="footer">University Logistics · Lost & Found Office · Built with Flask & MongoDB</footer>
</body>
</html>
"""

STUDENT_LOGIN = """
{% extends "base.html" %}
{% block title %}Student Login{% endblock %}
{% block content %}
<div class="auth-card">
  <h2>Student Login</h2>
  <form method="POST" action="{{ url_for('student_login') }}">
    <label>University Email</label>
    <input type="email" name="email" required placeholder="you@university.edu"/>
    <label>Password</label>
    <input type="password" name="password" required/>
    <button type="submit" class="btn-primary">Login</button>
  </form>
  <p class="muted">New student? <a href="{{ url_for('student_register') }}">Create an account</a></p>
</div>
{% endblock %}
"""

STUDENT_REGISTER = """
{% extends "base.html" %}
{% block title %}Student Registration{% endblock %}
{% block content %}
<div class="auth-card">
  <h2>Create Student Account</h2>
  <form method="POST" action="{{ url_for('student_register') }}">
    <label>Full Name</label>
    <input type="text" name="full_name" required minlength="2"/>
    <label>University Email</label>
    <input type="email" name="email" required placeholder="you@university.edu"/>
    <label>Password</label>
    <input type="password" name="password" required minlength="6"/>
    <label>Confirm Password</label>
    <input type="password" name="confirm" required minlength="6"/>
    <button type="submit" class="btn-primary">Register</button>
  </form>
  <p class="muted">Already registered? <a href="{{ url_for('student_login') }}">Login</a></p>
</div>
{% endblock %}
"""

STUDENT_DASHBOARD = """
{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}
{% block content %}
<section class="hero">
  <h2>Welcome, {{ student.full_name }} 👋</h2>
  <p class="muted">Student ID: <strong>{{ student.student_id }}</strong></p>
  <div class="actions">
    <a href="{{ url_for('student_report_lost') }}" class="btn-primary">+ Report Lost Item</a>
    <a href="{{ url_for('student_found_items') }}" class="btn-secondary">Browse Found Items</a>
  </div>
</section>

<div class="grid-3">
  <div class="stat-card"><span class="stat-num">{{ stats.total }}</span><span>My Reports</span></div>
  <div class="stat-card"><span class="stat-num">{{ stats.pending }}</span><span>Pending</span></div>
  <div class="stat-card"><span class="stat-num">{{ stats.found }}</span><span>Found</span></div>
  <div class="stat-card"><span class="stat-num">{{ stats.returned }}</span><span>Returned</span></div>
  <div class="stat-card"><span class="stat-num">{{ stats.unresolved }}</span><span>Unresolved</span></div>
</div>

<h3>Recent Notifications</h3>
<div class="card-list">
{% for n in recent_notifications %}
  <div class="card">
    <div class="card-head">
      <strong>{{ n.title }}</strong>
      {% if not n.read %}<span class="dot"></span>{% endif %}
    </div>
    <p>{{ n.message }}</p>
    <small class="muted">{{ n.created_at }}</small>
  </div>
{% else %}
  <p class="muted">No notifications yet.</p>
{% endfor %}
</div>
{% endblock %}
"""

STUDENT_REPORT_FORM = """
{% extends "base.html" %}
{% block title %}Report Lost Item{% endblock %}
{% block content %}
<div class="auth-card wide">
  <h2>Report a Lost Item</h2>
  <form method="POST" action="{{ url_for('student_report_lost') }}" enctype="multipart/form-data">
    <label>Item Name *</label>
    <input type="text" name="item_name" required maxlength="120"/>
    <label>Category *</label>
    <select name="category" required>
      <option value="">Select…</option>
      <option>Electronics</option><option>Books</option><option>Clothing</option>
      <option>Bags</option><option>Keys</option><option>ID Card</option>
      <option>Wallet</option><option>Jewellery</option><option>Other</option>
    </select>
    <label>Colour *</label>
    <input type="text" name="colour" required maxlength="60"/>
    <label>Date Lost *</label>
    <input type="date" name="date_lost" required/>
    <label>Location where lost (optional)</label>
    <input type="text" name="location" maxlength="120" placeholder="e.g. Library 2nd floor"/>
    <label>Description (optional)</label>
    <textarea name="description" rows="3" maxlength="500"></textarea>
    <label>Image (optional, max 4MB)</label>
    <input type="file" name="image" accept="image/*"/>
    <button type="submit" class="btn-primary">Submit Report</button>
  </form>
</div>
{% endblock %}
"""

STUDENT_MY_REPORTS = """
{% extends "base.html" %}
{% block title %}My Reports{% endblock %}
{% block content %}
<h2>My Lost-Item Reports</h2>
<div class="card-list">
{% for r in reports %}
  <div class="card">
    <div class="card-head">
      <strong>{{ r.item_name }}</strong>
      <span class="badge {{ r.badge }}">{{ r.status }}</span>
    </div>
    <p>Category: {{ r.category }} · Colour: {{ r.colour }}</p>
    <p>Date lost: {{ r.date_lost }} {% if r.location %} · Location: {{ r.location }}{% endif %}</p>
    <small class="muted">Submitted: {{ r.created_at }}</small>
    <div class="actions-sm">
      <a href="{{ url_for('student_report_detail', report_id=r._id) }}" class="btn-secondary">View Details</a>
    </div>
  </div>
{% else %}
  <p class="muted">You have not submitted any reports yet.</p>
{% endfor %}
</div>
{% endblock %}
"""

STUDENT_REPORT_DETAIL = """
{% extends "base.html" %}
{% block title %}Report Details{% endblock %}
{% block content %}
<div class="auth-card wide">
  <h2>{{ report.item_name }}</h2>
  <p><strong>Status:</strong> <span class="badge {{ report.badge }}">{{ report.status }}</span></p>
  <p><strong>Category:</strong> {{ report.category }}</p>
  <p><strong>Colour:</strong> {{ report.colour }}</p>
  <p><strong>Date Lost:</strong> {{ report.date_lost }}</p>
  <p><strong>Location:</strong> {{ report.location or '—' }}</p>
  <p><strong>Description:</strong> {{ report.description or '—' }}</p>
  {% if report.image %}
    <img src="{{ url_for('uploaded_file', filename=report.image) }}" class="thumb"/>
  {% endif %}
  <h3>Investigation History</h3>
  <div class="timeline">
  {% for h in history %}
    <div class="timeline-item">
      <strong>{{ h.status }}</strong>
      <small class="muted">{{ h.changed_at }} — {{ h.changed_by }}</small>
      {% if h.note %}<p>{{ h.note }}</p>{% endif %}
    </div>
  {% else %}
    <p class="muted">No status updates yet.</p>
  {% endfor %}
  </div>
  <a href="{{ url_for('student_my_reports') }}" class="btn-secondary">← Back</a>
</div>
{% endblock %}
"""

STUDENT_FOUND_ITEMS = """
{% extends "base.html" %}
{% block title %}Found Items{% endblock %}
{% block content %}
<h2>Available Found Items</h2>
<p class="muted">These items are held by the Logistics Office. If you recognise yours, contact us.</p>
<div class="card-list grid-list">
{% for it in items %}
  <div class="card">
    {% if it.image %}
      <img src="{{ url_for('uploaded_file', filename=it.image) }}" class="thumb"/>
    {% endif %}
    <div class="card-head"><strong>{{ it.item_name }}</strong>
      <span class="badge {{ it.badge }}">{{ it.status }}</span>
    </div>
    <p>{{ it.category }} · {{ it.colour }}</p>
    <p>Found at: {{ it.location_found }} on {{ it.date_found }}</p>
    <small class="muted">Storage: {{ it.storage_location }}</small>
  </div>
{% else %}
  <p class="muted">No found items currently registered.</p>
{% endfor %}
</div>
{% endblock %}
"""

STUDENT_NOTIFICATIONS = """
{% extends "base.html" %}
{% block title %}Notifications{% endblock %}
{% block content %}
<h2>Notifications</h2>
<div class="card-list">
{% for n in notifications %}
  <div class="card {% if not n.read %}unread{% endif %}">
    <div class="card-head"><strong>{{ n.title }}</strong>
      <small class="muted">{{ n.created_at }}</small></div>
    <p>{{ n.message }}</p>
    {% if n.link %}<a href="{{ n.link }}" class="btn-secondary">Open</a>{% endif %}
  </div>
{% else %}
  <p class="muted">You have no notifications.</p>
{% endfor %}
</div>
{% endblock %}
"""

STUDENT_PROFILE = """
{% extends "base.html" %}
{% block title %}Profile{% endblock %}
{% block content %}
<div class="grid-2">
  <div class="auth-card">
    <h2>My Profile</h2>
    <p><strong>Full Name:</strong> {{ student.full_name }}</p>
    <p><strong>Student ID:</strong> {{ student.student_id }}</p>
    <p><strong>Email:</strong> {{ student.email }}</p>
    <p><strong>Joined:</strong> {{ student.created_at }}</p>
  </div>
  <div class="auth-card">
    <h2>Change Password</h2>
    <form method="POST" action="{{ url_for('student_change_password') }}">
      <label>Current Password</label>
      <input type="password" name="current" required/>
      <label>New Password</label>
      <input type="password" name="new" required minlength="6"/>
      <label>Confirm New Password</label>
      <input type="password" name="confirm" required minlength="6"/>
      <button type="submit" class="btn-primary">Update Password</button>
    </form>
  </div>
</div>
{% endblock %}
"""

# ---------------- ADMIN TEMPLATES ----------------

ADMIN_BASE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{% block title %}Logistics Admin{% endblock %}</title>
<link rel="stylesheet" href="{{ url_for('static_css') }}"/>
</head>
<body class="admin-theme">
<aside class="sidebar">
  <div class="side-brand">🛡️ <span>Logistics</span></div>
  {% if session.get('role') == 'admin' %}
  <nav>
    <a href="{{ url_for('admin_dashboard') }}">📊 Dashboard</a>
    <a href="{{ url_for('admin_reports') }}">📄 Lost Reports</a>
    <a href="{{ url_for('admin_found_items') }}">📦 Found Items</a>
    <a href="{{ url_for('admin_students') }}">👥 Students</a>
    <a href="{{ url_for('admin_notifications') }}">🔔 Notifications
      {% if notif_count %}<span class="pill">{{ notif_count }}</span>{% endif %}
    </a>
    <a href="{{ url_for('admin_activity') }}">🕓 Activity Log</a>
    <a href="{{ url_for('logout') }}" class="danger-link">⎋ Logout</a>
  </nav>
  {% endif %}
</aside>
<main class="admin-main">
  <header class="admin-header">
    <h1>{% block heading %}Logistics Dashboard{% endblock %}</h1>
    <span class="muted">Signed in as {{ session.get('admin_name','Admin') }}</span>
  </header>
  {% with msgs = get_flashed_messages(with_categories=true) %}
    {% if msgs %}
      <div class="flash-wrap">
      {% for cat, m in msgs %}<div class="flash flash-{{ cat }}">{{ m }}</div>{% endfor %}
      </div>
    {% endif %}
  {% endwith %}
  {% block content %}{% endblock %}
</main>
</body>
</html>
"""

ADMIN_LOGIN = """
{% extends "admin_base.html" %}
{% block title %}Admin Login{% endblock %}
{% block heading %}Administrator Login{% endblock %}
{% block content %}
<div class="auth-card">
  <form method="POST" action="{{ url_for('admin_login') }}">
    <label>Admin Email</label>
    <input type="email" name="email" required/>
    <label>Password</label>
    <input type="password" name="password" required/>
    <button class="btn-primary" type="submit">Login</button>
  </form>
  <p class="muted"><a href="{{ url_for('student_login') }}">← Student portal</a></p>
</div>
{% endblock %}
"""

ADMIN_DASHBOARD = """
{% extends "admin_base.html" %}
{% block heading %}Dashboard Overview{% endblock %}
{% block content %}
<div class="grid-3">
  <div class="stat-card"><span class="stat-num">{{ stats.total_reports }}</span><span>Lost-Item Reports</span></div>
  <div class="stat-card"><span class="stat-num">{{ stats.pending }}</span><span>Pending Investigations</span></div>
  <div class="stat-card"><span class="stat-num">{{ stats.found }}</span><span>Items Found</span></div>
  <div class="stat-card"><span class="stat-num">{{ stats.returned }}</span><span>Items Returned</span></div>
  <div class="stat-card"><span class="stat-num">{{ stats.unresolved }}</span><span>Unresolved</span></div>
  <div class="stat-card"><span class="stat-num">{{ stats.found_items_registered }}</span><span>Found-Item Records</span></div>
</div>

<h3>Recent Reports</h3>
<div class="table-wrap">
<table>
<thead><tr><th>Item</th><th>Student</th><th>Status</th><th>Submitted</th><th></th></tr></thead>
<tbody>
{% for r in recent %}
  <tr>
    <td>{{ r.item_name }}</td>
    <td>{{ r.student_name }}</td>
    <td><span class="badge {{ r.badge }}">{{ r.status }}</span></td>
    <td>{{ r.created_at }}</td>
    <td><a href="{{ url_for('admin_report_detail', report_id=r._id) }}" class="link">View</a></td>
  </tr>
{% else %}<tr><td colspan="5" class="muted">No reports yet.</td></tr>{% endfor %}
</tbody>
</table>
</div>
{% endblock %}
"""

ADMIN_REPORTS = """
{% extends "admin_base.html" %}
{% block heading %}Lost-Item Management{% endblock %}
{% block content %}
<form method="GET" class="filter-bar">
  <input type="text" name="q" placeholder="Search item, category, student ID, location" value="{{ q }}"/>
  <select name="status">
    <option value="">All statuses</option>
    {% for s in ['Pending','Found','Returned','Unresolved'] %}
      <option value="{{ s }}" {% if status==s %}selected{% endif %}>{{ s }}</option>
    {% endfor %}
  </select>
  <button class="btn-primary" type="submit">Search</button>
</form>

<div class="table-wrap">
<table>
<thead><tr><th>Item</th><th>Student</th><th>Category</th><th>Location</th><th>Status</th><th>Actions</th></tr></thead>
<tbody>
{% for r in reports %}
<tr>
  <td>{{ r.item_name }}</td>
  <td>{{ r.student_name }}<br><small>{{ r.student_sid }}</small></td>
  <td>{{ r.category }}</td>
  <td>{{ r.location or '—' }}</td>
  <td><span class="badge {{ r.badge }}">{{ r.status }}</span></td>
  <td class="actions-cell">
    <a class="link" href="{{ url_for('admin_report_detail', report_id=r._id) }}">Manage</a>
    <form method="POST" action="{{ url_for('admin_delete_report', report_id=r._id) }}"
          onsubmit="return confirm('Delete this report permanently?');">
      <button class="btn-danger sm" type="submit">Delete</button>
    </form>
  </td>
</tr>
{% else %}<tr><td colspan="6" class="muted">No matching reports.</td></tr>{% endfor %}
</tbody>
</table>
</div>
{% endblock %}
"""

ADMIN_REPORT_DETAIL = """
{% extends "admin_base.html" %}
{% block heading %}Report: {{ report.item_name }}{% endblock %}
{% block content %}
<div class="grid-2">
  <div class="panel">
    <h3>Report Information</h3>
    <p><strong>Student:</strong> {{ report.student_name }} ({{ report.student_sid }})</p>
    <p><strong>Email:</strong> {{ report.student_email }}</p>
    <p><strong>Item:</strong> {{ report.item_name }}</p>
    <p><strong>Category:</strong> {{ report.category }} · <strong>Colour:</strong> {{ report.colour }}</p>
    <p><strong>Date Lost:</strong> {{ report.date_lost }}</p>
    <p><strong>Location:</strong> {{ report.location or '—' }}</p>
    <p><strong>Description:</strong> {{ report.description or '—' }}</p>
    {% if report.image %}<img src="{{ url_for('uploaded_file', filename=report.image) }}" class="thumb"/>{% endif %}
  </div>

  <div class="panel">
    <h3>Update Status</h3>
    <form method="POST" action="{{ url_for('admin_update_status', report_id=report._id) }}">
      <select name="status" required>
        {% for s in ['Pending','Found','Returned','Unresolved'] %}
        <option value="{{ s }}" {% if report.status==s %}selected{% endif %}>{{ s }}</option>
        {% endfor %}
      </select>
      <textarea name="note" rows="3" placeholder="Optional note for the student…"></textarea>
      <button class="btn-primary" type="submit">Save Status</button>
    </form>

    <h3>Edit Report Info</h3>
    <form method="POST" action="{{ url_for('admin_edit_report', report_id=report._id) }}">
      <input type="text" name="item_name" value="{{ report.item_name }}" required/>
      <input type="text" name="category" value="{{ report.category }}" required/>
      <input type="text" name="colour" value="{{ report.colour }}" required/>
      <input type="date" name="date_lost" value="{{ report.date_lost }}" required/>
      <input type="text" name="location" value="{{ report.location or '' }}"/>
      <textarea name="description" rows="2">{{ report.description or '' }}</textarea>
      <button class="btn-secondary" type="submit">Save Changes</button>
    </form>

    <h3>Match with Found Item & Notify Student</h3>
    <form method="POST" action="{{ url_for('admin_match_found', report_id=report._id) }}">
      <select name="found_id">
        <option value="">— select found item —</option>
        {% for it in found_items %}
          <option value="{{ it._id }}">{{ it.item_name }} · {{ it.colour }} · {{ it.location_found }}</option>
        {% endfor %}
      </select>
      <input type="text" name="message" placeholder="Custom message to student (optional)"/>
      <button class="btn-primary" type="submit">Confirm Match & Notify</button>
    </form>
    <form method="POST" action="{{ url_for('admin_mark_collected', report_id=report._id) }}">
      <button class="btn-secondary" type="submit">Mark as Returned / Collected</button>
    </form>
  </div>
</div>

<h3>Investigation History</h3>
<div class="timeline">
{% for h in history %}
  <div class="timeline-item">
    <strong>{{ h.status }}</strong>
    <small class="muted">{{ h.changed_at }} — {{ h.changed_by }}</small>
    {% if h.note %}<p>{{ h.note }}</p>{% endif %}
  </div>
{% else %}<p class="muted">No updates yet.</p>{% endfor %}
</div>
<a href="{{ url_for('admin_reports') }}" class="btn-secondary">← Back to reports</a>
{% endblock %}
"""

ADMIN_FOUND_ITEMS = """
{% extends "admin_base.html" %}
{% block heading %}Found-Item Management{% endblock %}
{% block content %}
<details class="panel">
  <summary><strong>+ Register New Found Item</strong></summary>
  <form method="POST" action="{{ url_for('admin_register_found') }}" enctype="multipart/form-data">
    <div class="grid-2">
      <input type="text" name="item_name" placeholder="Item name" required/>
      <input type="text" name="category" placeholder="Category" required/>
      <input type="text" name="colour" placeholder="Colour" required/>
      <input type="date" name="date_found" required/>
      <input type="text" name="location_found" placeholder="Location where found" required/>
      <input type="text" name="storage_location" placeholder="Storage location in office" required/>
      <input type="text" name="submitted_by" placeholder="Person who submitted item (optional)"/>
      <input type="file" name="image" accept="image/*"/>
    </div>
    <textarea name="description" rows="3" placeholder="Description"></textarea>
    <button class="btn-primary" type="submit">Register Found Item</button>
  </form>
</details>

<div class="table-wrap">
<table>
<thead><tr><th>Item</th><th>Category</th><th>Found At</th><th>Storage</th><th>Status</th><th>Actions</th></tr></thead>
<tbody>
{% for it in items %}
<tr>
  <td>{{ it.item_name }}<br><small>{{ it.colour }}</small></td>
  <td>{{ it.category }}</td>
  <td>{{ it.location_found }}<br><small>{{ it.date_found }}</small></td>
  <td>{{ it.storage_location }}</td>
  <td><span class="badge {{ it.badge }}">{{ it.status }}</span></td>
  <td class="actions-cell">
    <a class="link" href="{{ url_for('admin_edit_found', found_id=it._id) }}">Edit</a>
    <form method="POST" action="{{ url_for('admin_delete_found', found_id=it._id) }}"
          onsubmit="return confirm('Delete this found item?');">
      <button class="btn-danger sm" type="submit">Delete</button>
    </form>
  </td>
</tr>
{% else %}<tr><td colspan="6" class="muted">No found items registered.</td></tr>{% endfor %}
</tbody>
</table>
</div>
{% endblock %}
"""

ADMIN_EDIT_FOUND = """
{% extends "admin_base.html" %}
{% block heading %}Edit Found Item{% endblock %}
{% block content %}
<div class="panel">
  <form method="POST" action="{{ url_for('admin_edit_found', found_id=item._id) }}" enctype="multipart/form-data">
    <label>Item Name</label><input type="text" name="item_name" value="{{ item.item_name }}" required/>
    <label>Category</label><input type="text" name="category" value="{{ item.category }}" required/>
    <label>Colour</label><input type="text" name="colour" value="{{ item.colour }}" required/>
    <label>Date Found</label><input type="date" name="date_found" value="{{ item.date_found }}" required/>
    <label>Location Found</label><input type="text" name="location_found" value="{{ item.location_found }}" required/>
    <label>Storage Location</label><input type="text" name="storage_location" value="{{ item.storage_location }}" required/>
    <label>Submitted By</label><input type="text" name="submitted_by" value="{{ item.submitted_by or '' }}"/>
    <label>Description</label><textarea name="description" rows="3">{{ item.description or '' }}</textarea>
    <label>Status</label>
    <select name="status">
      {% for s in ['Stored','Matched','Collected'] %}
        <option value="{{ s }}" {% if item.status==s %}selected{% endif %}>{{ s }}</option>
      {% endfor %}
    </select>
    <label>Replace Image (optional)</label><input type="file" name="image" accept="image/*"/>
    <button class="btn-primary" type="submit">Save Changes</button>
  </form>
</div>
{% endblock %}
"""

ADMIN_STUDENTS = """
{% extends "admin_base.html" %}
{% block heading %}Student Management{% endblock %}
{% block content %}
<form method="GET" class="filter-bar">
  <input type="text" name="q" placeholder="Search by name, email, student ID" value="{{ q }}"/>
  <button class="btn-primary" type="submit">Search</button>
</form>
<div class="table-wrap">
<table>
<thead><tr><th>Student ID</th><th>Full Name</th><th>Email</th><th>Joined</th></tr></thead>
<tbody>
{% for s in students %}
<tr><td>{{ s.student_id }}</td><td>{{ s.full_name }}</td><td>{{ s.email }}</td><td>{{ s.created_at }}</td></tr>
{% else %}<tr><td colspan="4" class="muted">No students found.</td></tr>{% endfor %}
</tbody>
</table>
</div>
{% endblock %}
"""

ADMIN_NOTIFICATIONS = """
{% extends "admin_base.html" %}
{% block heading %}Notifications{% endblock %}
{% block content %}
<div class="card-list">
{% for n in notifications %}
  <div class="card {% if not n.read %}unread{% endif %}">
    <div class="card-head"><strong>{{ n.title }}</strong>
      <small class="muted">{{ n.created_at }}</small></div>
    <p>{{ n.message }}</p>
    {% if n.report_id %}<a href="{{ url_for('admin_report_detail', report_id=n.report_id) }}" class="btn-secondary">Open Report</a>{% endif %}
  </div>
{% else %}
  <p class="muted">No notifications.</p>
{% endfor %}
</div>
{% endblock %}
"""

ADMIN_ACTIVITY = """
{% extends "admin_base.html" %}
{% block heading %}Activity Log{% endblock %}
{% block content %}
<div class="table-wrap">
<table>
<thead><tr><th>When</th><th>Actor</th><th>Action</th><th>Target</th></tr></thead>
<tbody>
{% for a in logs %}
<tr><td>{{ a.created_at }}</td><td>{{ a.actor }}</td><td>{{ a.action }}</td><td>{{ a.target }}</td></tr>
{% else %}<tr><td colspan="4" class="muted">No activity yet.</td></tr>{% endfor %}
</tbody>
</table>
</div>
{% endblock %}
"""
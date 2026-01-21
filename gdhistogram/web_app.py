"""Web-based UI for GDHistogram using Flask."""

import os
import json
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
import secrets

from gdhistogram.config import APP_NAME, APP_VERSION, APP_DATA_DIR, AnalysisConfig, DEFAULT_CONFIG
from gdhistogram.auth.oauth_manager import OAuthManager
from gdhistogram.auth.token_storage import TokenStorage
from gdhistogram.api.google_client import GoogleClient
from gdhistogram.api.revision_fetcher import RevisionFetcher
from gdhistogram.api.snapshot_exporter import SnapshotExporter
from gdhistogram.analysis.diff_engine import DiffEngine
from gdhistogram.analysis.metrics_engine import MetricsEngine
from gdhistogram.analysis.event_detector import EventDetector
from gdhistogram.storage.database import Database, CacheManager
from gdhistogram.visualization.histogram import HistogramGenerator

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Global state
state = {
    "credentials": None,
    "client_secrets_path": None,
    "document_url": None,
    "file_id": None,
    "config": DEFAULT_CONFIG,
    "analysis_results": None,
    "histogram_html": None,
}

# HTML Templates
BASE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }} - GDHistogram</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
        }
        .container { max-width: 900px; margin: 0 auto; padding: 20px; }
        .card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h1 { color: #1a1a1a; margin-bottom: 10px; }
        h2 { color: #333; margin-bottom: 20px; font-size: 1.5rem; }
        p { color: #666; line-height: 1.6; margin-bottom: 15px; }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: #2563EB;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            text-decoration: none;
            transition: background 0.2s;
        }
        .btn:hover { background: #1d4ed8; }
        .btn-secondary { background: #6b7280; }
        .btn-secondary:hover { background: #4b5563; }
        .btn-success { background: #059669; }
        .btn-success:hover { background: #047857; }
        input[type="text"], input[type="file"], input[type="number"], textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            margin-bottom: 15px;
        }
        input:focus, textarea:focus {
            outline: none;
            border-color: #2563EB;
        }
        label { display: block; margin-bottom: 5px; font-weight: 500; color: #333; }
        .form-group { margin-bottom: 20px; }
        .header {
            background: linear-gradient(135deg, #2563EB, #7c3aed);
            color: white;
            padding: 40px 20px;
            text-align: center;
        }
        .header h1 { color: white; font-size: 2.5rem; }
        .header p { color: rgba(255,255,255,0.9); }
        .steps { display: flex; gap: 10px; margin-bottom: 30px; flex-wrap: wrap; }
        .step {
            padding: 8px 16px;
            background: #e5e7eb;
            border-radius: 20px;
            font-size: 14px;
            color: #666;
        }
        .step.active { background: #2563EB; color: white; }
        .step.done { background: #059669; color: white; }
        .alert { padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .alert-error { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
        .alert-success { background: #f0fdf4; color: #059669; border: 1px solid #bbf7d0; }
        .alert-info { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
        .stat-card { background: #f9fafb; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 1.8rem; font-weight: bold; color: #2563EB; }
        .stat-label { font-size: 0.85rem; color: #666; }
        .code { 
            background: #1f2937; 
            color: #e5e7eb; 
            padding: 15px; 
            border-radius: 8px; 
            font-family: monospace;
            overflow-x: auto;
            margin: 15px 0;
        }
        .progress { 
            width: 100%; 
            height: 8px; 
            background: #e5e7eb; 
            border-radius: 4px; 
            overflow: hidden;
            margin: 20px 0;
        }
        .progress-bar { 
            height: 100%; 
            background: #2563EB; 
            transition: width 0.3s;
        }
        .nav { display: flex; gap: 10px; margin-top: 20px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }
        th { background: #f9fafb; font-weight: 600; }
        .event-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        .event-spike { background: #fef3c7; color: #d97706; }
        .event-paste { background: #fecaca; color: #dc2626; }
        .event-idle { background: #dbeafe; color: #2563eb; }
    </style>
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
"""

WELCOME_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="header">
    <h1>📊 GDHistogram</h1>
    <p>Analyze Google Docs revision history to understand typing patterns</p>
</div>
<div class="container">
    <div class="card">
        <h2>Welcome!</h2>
        <p>GDHistogram analyzes your Google Docs revision history to:</p>
        <ul style="margin: 20px 0; padding-left: 20px; color: #666;">
            <li>Calculate typing speed (WPM) over time</li>
            <li>Detect anomalies like copy/paste events</li>
            <li>Identify speed spikes and idle periods</li>
            <li>Generate interactive histograms</li>
        </ul>
        <div class="alert alert-info">
            <strong>Privacy First:</strong> All analysis happens locally. We never store or transmit your document content.
        </div>
        <a href="/setup" class="btn">Get Started →</a>
    </div>
</div>
{% endblock %}
"""

SETUP_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="container">
    <div class="steps">
        <span class="step done">Welcome</span>
        <span class="step active">Setup</span>
        <span class="step">Auth</span>
        <span class="step">Document</span>
        <span class="step">Analyze</span>
        <span class="step">Results</span>
    </div>
    <div class="card">
        <h2>🔐 Setup Google API Credentials</h2>
        <p>To access your Google Docs revision history, you need to provide your own OAuth credentials.</p>
        
        <h3 style="margin: 20px 0 10px;">How to get credentials:</h3>
        <ol style="padding-left: 20px; color: #666; line-height: 2;">
            <li>Go to <a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a></li>
            <li>Create a new project or select existing</li>
            <li>Enable the <strong>Google Drive API</strong> and <strong>Google Docs API</strong></li>
            <li>Go to Credentials → Create Credentials → OAuth client ID</li>
            <li>Select "Desktop app" as application type</li>
            <li>Download the JSON file</li>
        </ol>
        
        <form action="/setup" method="POST" style="margin-top: 30px;">
            <div class="form-group">
                <label>Paste your client_secret.json content:</label>
                <textarea name="client_secrets" rows="10" placeholder='{"installed":{"client_id":"...","client_secret":"..."}}'></textarea>
            </div>
            {% if error %}
            <div class="alert alert-error">{{ error }}</div>
            {% endif %}
            <button type="submit" class="btn">Continue →</button>
        </form>
    </div>
</div>
{% endblock %}
"""

AUTH_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="container">
    <div class="steps">
        <span class="step done">Welcome</span>
        <span class="step done">Setup</span>
        <span class="step active">Auth</span>
        <span class="step">Document</span>
        <span class="step">Analyze</span>
        <span class="step">Results</span>
    </div>
    <div class="card">
        <h2>🔑 Authorize Access</h2>
        <p>Click the button below to authorize GDHistogram to read your Google Docs.</p>
        <div class="alert alert-info">
            We only request <strong>read-only</strong> access. GDHistogram cannot modify your documents.
        </div>
        
        {% if auth_url %}
        <p style="margin: 20px 0;">
            <a href="{{ auth_url }}" target="_blank" class="btn">Open Google Authorization →</a>
        </p>
        <form action="/auth/callback" method="POST" style="margin-top: 30px;">
            <div class="form-group">
                <label>Paste the authorization code here:</label>
                <input type="text" name="auth_code" placeholder="4/0AX4XfWh...">
            </div>
            <button type="submit" class="btn btn-success">Complete Authorization</button>
        </form>
        {% endif %}
        
        {% if error %}
        <div class="alert alert-error">{{ error }}</div>
        {% endif %}
    </div>
</div>
{% endblock %}
"""

DOCUMENT_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="container">
    <div class="steps">
        <span class="step done">Welcome</span>
        <span class="step done">Setup</span>
        <span class="step done">Auth</span>
        <span class="step active">Document</span>
        <span class="step">Analyze</span>
        <span class="step">Results</span>
    </div>
    <div class="card">
        <h2>📄 Select Document</h2>
        <p>Enter the URL of the Google Doc you want to analyze.</p>
        
        <form action="/document" method="POST">
            <div class="form-group">
                <label>Google Doc URL:</label>
                <input type="text" name="doc_url" placeholder="https://docs.google.com/document/d/..." value="{{ doc_url or '' }}">
            </div>
            {% if error %}
            <div class="alert alert-error">{{ error }}</div>
            {% endif %}
            {% if doc_info %}
            <div class="alert alert-success">
                <strong>Found:</strong> {{ doc_info.title }}<br>
                <small>{{ doc_info.revision_count }} revisions available</small>
            </div>
            {% endif %}
            <button type="submit" class="btn">Analyze Document →</button>
        </form>
    </div>
</div>
{% endblock %}
"""

ANALYZING_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="container">
    <div class="steps">
        <span class="step done">Welcome</span>
        <span class="step done">Setup</span>
        <span class="step done">Auth</span>
        <span class="step done">Document</span>
        <span class="step active">Analyze</span>
        <span class="step">Results</span>
    </div>
    <div class="card">
        <h2>⏳ Analyzing...</h2>
        <p>{{ status }}</p>
        <div class="progress">
            <div class="progress-bar" style="width: {{ progress }}%"></div>
        </div>
        <p style="text-align: center; color: #666;">{{ progress }}% complete</p>
        <script>
            setTimeout(function() { location.reload(); }, 2000);
        </script>
    </div>
</div>
{% endblock %}
"""

RESULTS_TEMPLATE = """
{% extends "base" %}
{% block content %}
<div class="container">
    <div class="steps">
        <span class="step done">Welcome</span>
        <span class="step done">Setup</span>
        <span class="step done">Auth</span>
        <span class="step done">Document</span>
        <span class="step done">Analyze</span>
        <span class="step active">Results</span>
    </div>
    
    <div class="card">
        <h2>📊 Analysis Results</h2>
        <p>Analysis complete for: <strong>{{ doc_title }}</strong></p>
        
        <div class="stats-grid" style="margin: 30px 0;">
            <div class="stat-card">
                <div class="stat-value">{{ "%.1f"|format(stats.mean_wpm) }}</div>
                <div class="stat-label">Average WPM</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ "%.1f"|format(stats.median_wpm) }}</div>
                <div class="stat-label">Median WPM</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ "%.1f"|format(stats.max_wpm) }}</div>
                <div class="stat-label">Max WPM</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.valid_intervals }}</div>
                <div class="stat-label">Intervals</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_chars_inserted }}</div>
                <div class="stat-label">Chars Added</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ event_count }}</div>
                <div class="stat-label">Events Detected</div>
            </div>
        </div>
    </div>
    
    <div class="card">
        <h2>📈 WPM Histogram</h2>
        {{ histogram_html | safe }}
    </div>
    
    {% if events %}
    <div class="card">
        <h2>🚨 Detected Events</h2>
        <table>
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Time</th>
                    <th>WPM</th>
                    <th>Reason</th>
                </tr>
            </thead>
            <tbody>
                {% for event in events %}
                <tr>
                    <td>
                        <span class="event-badge event-{{ event.event_type.value }}">
                            {{ event.event_type.value }}
                        </span>
                    </td>
                    <td>{{ event.timestamp.strftime('%Y-%m-%d %H:%M') }}</td>
                    <td>{{ "%.1f"|format(event.wpm) }}</td>
                    <td>{{ event.reason }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endif %}
    
    <div class="card">
        <div class="nav">
            <a href="/export/html" class="btn btn-success">Export HTML</a>
            <a href="/export/json" class="btn btn-secondary">Export JSON</a>
            <a href="/" class="btn btn-secondary">Start Over</a>
        </div>
    </div>
</div>
{% endblock %}
"""

# Template registry
templates = {
    "base": BASE_TEMPLATE,
    "welcome": WELCOME_TEMPLATE,
    "setup": SETUP_TEMPLATE,
    "auth": AUTH_TEMPLATE,
    "document": DOCUMENT_TEMPLATE,
    "analyzing": ANALYZING_TEMPLATE,
    "results": RESULTS_TEMPLATE,
}

def render(template_name, **kwargs):
    """Render a template with base."""
    from jinja2 import Environment, BaseLoader
    
    env = Environment(loader=BaseLoader())
    
    # Register base template
    base = env.from_string(templates["base"])
    
    # Create child template
    child_src = templates[template_name].replace('{% extends "base" %}', '')
    child = env.from_string(templates["base"].replace("{% block content %}{% endblock %}", child_src))
    
    return child.render(**kwargs)


@app.route("/")
def index():
    return render("welcome", title="Welcome")


@app.route("/setup", methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        try:
            secrets_json = request.form.get("client_secrets", "").strip()
            if not secrets_json:
                return render("setup", title="Setup", error="Please paste your client secrets JSON")
            
            # Validate JSON
            secrets_data = json.loads(secrets_json)
            if "installed" not in secrets_data and "web" not in secrets_data:
                return render("setup", title="Setup", error="Invalid client secrets format")
            
            # Save to temp file
            secrets_path = APP_DATA_DIR / "client_secrets.json"
            APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
            secrets_path.write_text(secrets_json)
            
            state["client_secrets_path"] = secrets_path
            return redirect(url_for("auth"))
            
        except json.JSONDecodeError:
            return render("setup", title="Setup", error="Invalid JSON format")
        except Exception as e:
            return render("setup", title="Setup", error=str(e))
    
    return render("setup", title="Setup")


@app.route("/auth", methods=["GET"])
def auth():
    if not state["client_secrets_path"]:
        return redirect(url_for("setup"))
    
    try:
        oauth = OAuthManager(state["client_secrets_path"])
        auth_url = oauth.get_authorization_url()
        return render("auth", title="Authorize", auth_url=auth_url)
    except Exception as e:
        return render("auth", title="Authorize", error=str(e))


@app.route("/auth/callback", methods=["POST"])
def auth_callback():
    auth_code = request.form.get("auth_code", "").strip()
    if not auth_code:
        return render("auth", title="Authorize", error="Please enter the authorization code")
    
    try:
        oauth = OAuthManager(state["client_secrets_path"])
        credentials = oauth.exchange_code(auth_code)
        state["credentials"] = credentials
        
        # Save tokens
        token_storage = TokenStorage()
        token_storage.save_credentials(credentials)
        
        return redirect(url_for("document"))
    except Exception as e:
        oauth = OAuthManager(state["client_secrets_path"])
        auth_url = oauth.get_authorization_url()
        return render("auth", title="Authorize", auth_url=auth_url, error=str(e))


@app.route("/document", methods=["GET", "POST"])
def document():
    if not state["credentials"]:
        # Try to load saved credentials
        try:
            token_storage = TokenStorage()
            state["credentials"] = token_storage.load_credentials()
        except:
            return redirect(url_for("auth"))
    
    if request.method == "POST":
        doc_url = request.form.get("doc_url", "").strip()
        if not doc_url:
            return render("document", title="Document", error="Please enter a document URL")
        
        try:
            # Extract file ID
            client = GoogleClient(state["credentials"])
            file_id = client.extract_file_id(doc_url)
            
            if not file_id:
                return render("document", title="Document", error="Could not extract file ID from URL")
            
            state["file_id"] = file_id
            state["document_url"] = doc_url
            
            return redirect(url_for("analyze"))
            
        except Exception as e:
            return render("document", title="Document", doc_url=doc_url, error=str(e))
    
    return render("document", title="Document")


@app.route("/analyze")
def analyze():
    if not state["file_id"]:
        return redirect(url_for("document"))
    
    # Start analysis in background
    if state.get("analysis_results") is None:
        threading.Thread(target=run_analysis, daemon=True).start()
        return render("analyzing", title="Analyzing", status="Starting analysis...", progress=0)
    
    if isinstance(state["analysis_results"], str) and state["analysis_results"].startswith("error:"):
        error = state["analysis_results"][6:]
        state["analysis_results"] = None
        return render("document", title="Document", error=error)
    
    if state["analysis_results"] == "in_progress":
        return render("analyzing", title="Analyzing", 
                     status=state.get("analysis_status", "Processing..."),
                     progress=state.get("analysis_progress", 0))
    
    return redirect(url_for("results"))


def run_analysis():
    """Run the analysis in background."""
    try:
        state["analysis_results"] = "in_progress"
        state["analysis_status"] = "Fetching revisions..."
        state["analysis_progress"] = 10
        
        # Fetch revisions
        fetcher = RevisionFetcher(state["credentials"])
        revisions = fetcher.fetch_all_revisions(state["file_id"])
        
        state["analysis_status"] = f"Found {len(revisions)} revisions. Exporting snapshots..."
        state["analysis_progress"] = 30
        
        # Export snapshots
        exporter = SnapshotExporter(state["credentials"])
        snapshots = []
        for i, rev in enumerate(revisions):
            snapshot = exporter.export_revision(state["file_id"], rev)
            snapshots.append(snapshot)
            state["analysis_progress"] = 30 + int(40 * (i + 1) / len(revisions))
        
        state["analysis_status"] = "Computing diffs..."
        state["analysis_progress"] = 75
        
        # Compute diffs
        diff_engine = DiffEngine()
        diffs = diff_engine.compute_all_diffs(snapshots)
        
        state["analysis_status"] = "Calculating metrics..."
        state["analysis_progress"] = 85
        
        # Calculate metrics
        metrics_engine = MetricsEngine(state["config"])
        metrics = metrics_engine.compute_all_metrics(diffs)
        statistics = metrics_engine.compute_statistics(metrics, diffs)
        
        state["analysis_status"] = "Detecting events..."
        state["analysis_progress"] = 90
        
        # Detect events
        event_detector = EventDetector(state["config"])
        events = event_detector.detect_all_events(diffs, metrics, metrics_engine)
        
        state["analysis_status"] = "Generating histogram..."
        state["analysis_progress"] = 95
        
        # Generate histogram
        histogram_gen = HistogramGenerator(state["config"])
        fig = histogram_gen.generate_histogram(metrics, events, statistics, "WPM Over Time")
        histogram_html = histogram_gen.get_figure_html(fig)
        
        state["analysis_results"] = {
            "doc_title": f"Document {state['file_id'][:8]}...",
            "revisions": len(revisions),
            "statistics": statistics,
            "events": events,
            "metrics": metrics,
            "histogram_html": histogram_html,
        }
        state["analysis_progress"] = 100
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        state["analysis_results"] = f"error:{str(e)}"


@app.route("/results")
def results():
    if not state.get("analysis_results") or state["analysis_results"] == "in_progress":
        return redirect(url_for("analyze"))
    
    if isinstance(state["analysis_results"], str):
        return redirect(url_for("document"))
    
    r = state["analysis_results"]
    return render("results", 
                 title="Results",
                 doc_title=r["doc_title"],
                 stats=r["statistics"],
                 events=r["events"],
                 event_count=len(r["events"]),
                 histogram_html=r["histogram_html"])


@app.route("/export/html")
def export_html():
    if not state.get("analysis_results"):
        return redirect(url_for("results"))
    
    r = state["analysis_results"]
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>GDHistogram Report</title></head>
    <body>
        <h1>GDHistogram Analysis Report</h1>
        <p>Document: {r['doc_title']}</p>
        <p>Average WPM: {r['statistics'].mean_wpm:.1f}</p>
        <p>Total intervals: {r['statistics'].valid_intervals}</p>
        <p>Events detected: {len(r['events'])}</p>
        <hr>
        {r['histogram_html']}
    </body>
    </html>
    """
    return html, 200, {'Content-Type': 'text/html', 
                       'Content-Disposition': 'attachment; filename=gdhistogram_report.html'}


@app.route("/export/json")
def export_json():
    if not state.get("analysis_results"):
        return jsonify({"error": "No results available"})
    
    r = state["analysis_results"]
    return jsonify({
        "document": r["doc_title"],
        "statistics": r["statistics"].to_dict(),
        "events": [e.to_dict() for e in r["events"]],
        "metrics": [m.to_dict() for m in r["metrics"]],
    })


@app.route("/reset")
def reset():
    state["analysis_results"] = None
    state["file_id"] = None
    state["document_url"] = None
    return redirect(url_for("index"))


def run_web_app(host="0.0.0.0", port=5000, debug=False):
    """Run the web application."""
    print(f"\n{'='*50}")
    print(f"  GDHistogram Web Interface")
    print(f"  Open http://localhost:{port} in your browser")
    print(f"{'='*50}\n")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_web_app(debug=True)

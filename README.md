# GDHistogram - Google Docs Revision History Analyzer

Analyze Google Docs revision history to understand typing behavior (WPM over time), detect anomalies (copy/paste events, speed spikes), and visualize with interactive histograms.

![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License MIT](https://img.shields.io/badge/License-MIT-green.svg)

---

## 🚀 Quick Start (5 minutes)

### Option A: GitHub Codespaces (Easiest - No Install)

1. **Click the green "Code" button** at the top of this repo
2. **Select "Codespaces"** → **"Create codespace on main"**
3. **Wait** for the codespace to load (~2 minutes)
4. **Run these commands** in the terminal:
   ```bash
   pip install -r requirements.txt
   python -m gdhistogram --web
   ```
5. **Click "Open in Browser"** when the popup appears (or go to Ports tab → port 5000 → click globe icon)

### Option B: Run Locally

```bash
# Clone and enter the repo
git clone https://github.com/NagusameCS/GDHistogram.git
cd GDHistogram

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python -m gdhistogram --web    # ← Web UI (works everywhere)
python -m gdhistogram          # ← Desktop UI (needs display)
```

---

## 🔑 Google Cloud Setup (Required - One Time, ~5 min)

**You need your own Google Cloud credentials to access Google Docs.**

### Step 1: Create Project
1. Go to **[console.cloud.google.com](https://console.cloud.google.com/)**
2. Click **"Select a project"** (top bar) → **"New Project"**
3. Name it `GDHistogram` → Click **"Create"**
4. Make sure the new project is selected in the dropdown

### Step 2: Enable APIs
1. Go to **[APIs & Services → Library](https://console.cloud.google.com/apis/library)**
2. Search **"Google Drive API"** → Click it → Click **"Enable"**
3. Search **"Google Docs API"** → Click it → Click **"Enable"**

### Step 3: Configure OAuth Consent Screen
1. Go to **[APIs & Services → OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)**
2. Select **"External"** → Click **"Create"**
3. Fill in **only these required fields**:
   - **App name**: `GDHistogram`
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Click **"Save and Continue"**
5. **Scopes page**: Just click **"Save and Continue"** (skip this)
6. **Test users page**: Click **"+ Add Users"** → Enter **your Gmail address** → Click **"Add"** → **"Save and Continue"**
7. Click **"Back to Dashboard"**

### Step 4: Create Credentials
1. Go to **[APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)**
2. Click **"+ Create Credentials"** → **"OAuth client ID"**
3. **Application type**: Select **"Desktop app"**
4. **Name**: `GDHistogram`
5. Click **"Create"**
6. **⬇️ Click "Download JSON"** and save the file!

### Step 5: Use in the App
When you run GDHistogram:
1. Open the downloaded `client_secret_xxx.json` file in any text editor
2. **Select all** and **Copy** the entire contents
3. **Paste** it into the Setup screen in the app
4. Click Continue, then authorize with your Google account

---

## 📖 Usage

1. **Start the app** → `python -m gdhistogram --web`
2. **Paste your credentials JSON** in the Setup screen
3. **Click "Open Google Authorization"** → Sign in → Copy the code → Paste it back
4. **Enter a Google Doc URL** like:
   - `https://docs.google.com/document/d/1ABC123xyz/edit`
5. **Click "Analyze Document"** and wait for results
6. **View the histogram** showing WPM over time and detected events
7. **Export** results as HTML or JSON

---

## ⚙️ Command Line Options

```bash
python -m gdhistogram [OPTIONS]

Options:
  --web          Run web interface (recommended)
  --port PORT    Port for web server (default: 5000)
  --check-deps   Check if dependencies are installed
  --version      Show version
```

---

## 📊 What It Detects

| Event | Color | Criteria |
|-------|-------|----------|
| **Copy/Paste** | 🔴 Red | ≥50 chars in ≤5 seconds |
| **Speed Spike** | 🟠 Orange | WPM ≥ mean + 3 std deviations |
| **Idle Burst** | 🔵 Blue | ≥100 chars after ≥10 min idle |

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| **Port 5000 in use** | Run with `--port 5001` |
| **"Access blocked" during auth** | Add yourself as a Test User in Step 3 |
| **Desktop UI crashes** | Use `--web` flag instead |
| **"No revisions found"** | Make sure you own the doc or have edit access |

---

## 🔒 Privacy & Security

- ✅ **Read-only access** - Cannot modify your documents
- ✅ **Local processing** - All analysis happens on your machine
- ✅ **No telemetry** - No data sent anywhere
- ✅ **Your credentials** - You control your own API access

---

## 📁 Project Structure

```
gdhistogram/
├── auth/           # OAuth & token management
├── api/            # Google Drive/Docs API clients
├── analysis/       # Diff engine, metrics, event detection
├── storage/        # SQLite caching
├── visualization/  # Plotly histogram generation
├── ui/             # PySide6 desktop UI
└── web_app.py      # Flask web UI
```

---

## 🧪 Development

```bash
# Run tests
pytest tests/ -v

# Format code
black gdhistogram/

# Type check
mypy gdhistogram/
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

# GDHistogram - Google Docs Revision History Analyzer

Analyze typing behavior and detect anomalies in Google Docs revision history.

## 🚀 Quick Start

### Option 1: Run in GitHub Codespaces
1. Click the green **Code** button → **Codespaces** → **Create codespace**
2. Wait for setup, then run:
   ```bash
   pip install -r requirements.txt
   python -m gdhistogram.web_app
   ```
3. Click the popup to open in browser, or go to the **Ports** tab

### Option 2: Run Locally
```bash
git clone https://github.com/NagusameCS/GDHistogram.git
cd GDHistogram
pip install -r requirements.txt
python -m gdhistogram.web_app
```

## 🔧 Setup Your Own Credentials

To use the app, you need Google OAuth credentials:

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable **Google Drive API** and **Google Docs API**

### 2. Create OAuth Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select **Desktop app**
4. Download the JSON file

### 3. Configure OAuth Consent Screen
1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type
3. Fill in app name and email
4. Add scopes:
   - `https://www.googleapis.com/auth/drive.readonly`
   - `https://www.googleapis.com/auth/documents.readonly`
5. Add test users (while in testing mode)

### 4. Run with Your Credentials
Set environment variables:
```bash
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"
python -m gdhistogram.web_app
```

Or paste the credentials JSON in the app's setup page.

## 🚀 Deploy Your Own Instance

### Railway (Recommended)
1. Fork this repo
2. Go to [railway.app](https://railway.app)
3. New Project → Deploy from GitHub repo
4. Add environment variables:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
5. Deploy!

### Render
1. Fork this repo
2. Go to [render.com](https://render.com)
3. New → Web Service → Connect your repo
4. Set **Start Command**: `gunicorn gdhistogram.web_app:app`
5. Add environment variables
6. Deploy!

## 📊 Features

- **WPM Analysis**: Calculate words-per-minute for each revision
- **Anomaly Detection**: Identify unusual typing patterns
- **Interactive Histogram**: Visualize typing speed distribution
- **Event Detection**: Find paste events, deletions, long pauses
- **Export**: Save results as HTML or JSON

## 📝 License

MIT License - see [LICENSE](LICENSE)

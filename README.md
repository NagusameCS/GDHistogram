# GDHistogram - Google Docs Revision History Analyzer

A local desktop application that analyzes Google Docs revision history to infer typing behavior (WPM over time), detect anomalies (spikes, copy/paste-like events), and render interactive histograms.

![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License MIT](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- **📊 WPM Analysis**: Calculate words-per-minute metrics across document revisions
- **🔍 Anomaly Detection**: Automatically detect copy/paste events, speed spikes, and idle bursts
- **📈 Interactive Visualization**: View colorblind-safe histograms with event markers
- **🔒 Privacy-First**: All processing happens locally - no data sent to external servers
- **📖 Read-Only**: Never modifies your documents (uses read-only API scopes)
- **✅ Deterministic**: Same document state always produces identical results
- **🔐 User-Owned Credentials**: No developer API keys - you control your own access

## Screenshots

The application provides an 8-screen linear flow:

1. **Welcome** - Introduction and feature overview
2. **Setup** - Configure your own Google Cloud OAuth credentials
3. **Authorization** - Grant read-only access to Google Docs
4. **Document Selection** - Enter document URL or ID
5. **Configuration** - Customize analysis parameters
6. **Analysis** - Watch real-time progress
7. **Results** - Interactive histogram and event tables
8. **Export** - Save results as PNG, JSON, or CSV

## Installation

### Prerequisites

- Python 3.11 or higher
- A Google Cloud account (free tier works)

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/NagusameCS/GDHistogram.git
   cd GDHistogram
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python run.py
   ```

### Installation via pip

```bash
pip install -e .
gdhistogram  # Run the application
```

## Google Cloud Setup

Since this application uses **your own credentials** (not developer-provided), you need to set up a Google Cloud project:

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter a project name (e.g., "GDHistogram")
4. Click "Create"

### Step 2: Enable Required APIs

1. In your project, go to **APIs & Services** → **Library**
2. Search for and enable:
   - **Google Drive API**
   - **Google Docs API**

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External** user type (unless you have a Workspace account)
3. Fill in the required fields:
   - App name: "GDHistogram" (or any name)
   - User support email: your email
   - Developer contact: your email
4. Click **Save and Continue**
5. On the Scopes page, click **Add or Remove Scopes**
6. Add these scopes:
   - `https://www.googleapis.com/auth/drive.readonly`
   - `https://www.googleapis.com/auth/documents.readonly`
7. Complete the remaining steps

### Step 4: Create OAuth Client ID

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select **Desktop app** as the application type
4. Enter a name (e.g., "GDHistogram Desktop")
5. Click **Create"
6. Click **Download JSON** to save `client_secret.json`

### Step 5: Use in Application

When you run GDHistogram, select this `client_secret.json` file in the Setup screen.

## Usage

### Basic Workflow

1. **Start the application**: `python run.py`
2. **Select your OAuth credentials**: Browse to your `client_secret.json`
3. **Authorize**: Click "Authorize in Browser" and grant access
4. **Enter document**: Paste a Google Docs URL or file ID
5. **Configure**: Adjust parameters or use defaults
6. **Analyze**: Click "Run Analysis" and wait for completion
7. **View results**: Explore the histogram and event tables
8. **Export**: Save as PNG, JSON, or CSV

### Supported Document Formats

You can enter:
- Full URL: `https://docs.google.com/document/d/DOCUMENT_ID/edit`
- File ID only: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`

### Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| Bin Size | 1 min | Time interval for histogram bars |
| Max Revisions | 2000 | Maximum revisions to process |
| Paste Char Threshold | 50 | Minimum chars for paste detection |
| Paste Time Threshold | 5s | Maximum time for paste detection |
| Spike Z-Score | 3.0 | Standard deviations above mean for spike |
| Idle Time Threshold | 10 min | Minimum idle time before burst detection |
| Idle Burst Chars | 100 | Minimum chars after idle for burst |

## Event Detection

### Copy/Paste Events (Red)

Detected when ALL conditions are true:
- ≥50 characters inserted
- ≤5 seconds between revisions
- Low overlap with existing document content

### Speed Spikes (Orange)

Detected when:
- WPM ≥ mean + (3 × standard deviation)

### Idle Bursts (Blue)

Detected when:
- Previous interval was ≥10 minutes idle
- Current interval has ≥100 characters inserted

## Export Formats

### PNG (Histogram Image)
High-resolution histogram with event markers.

### JSON (Raw Metrics)
Complete analysis data including:
- Document metadata
- All interval metrics
- Event details
- Configuration used

### CSV (Event Table)
Spreadsheet-friendly event list with timestamps and details.

## Architecture

```
GDHistogram
├── gdhistogram/
│   ├── auth/           # OAuth and token management
│   ├── api/            # Google API clients
│   ├── analysis/       # Diff, metrics, and event detection
│   ├── storage/        # SQLite caching
│   ├── visualization/  # Plotly histogram generation
│   └── ui/             # PySide6 interface
│       └── screens/    # Individual UI screens
```

### Key Components

- **OAuthManager**: Handles OAuth 2.0 flow with user-owned credentials
- **TokenStorage**: Encrypts tokens locally using machine-specific keys
- **RevisionFetcher**: Fetches revision metadata from Drive API
- **SnapshotExporter**: Exports revision content as plain text
- **DiffEngine**: Uses `difflib.SequenceMatcher` for deterministic diffing
- **MetricsEngine**: Calculates WPM and identifies anomalies
- **EventDetector**: Applies detection rules for events
- **HistogramGenerator**: Creates Plotly visualizations

## Security & Privacy

- **Read-only scopes**: Only `drive.readonly` and `documents.readonly`
- **Local processing**: All analysis happens on your machine
- **No telemetry**: No data sent to external servers
- **Encrypted tokens**: OAuth tokens encrypted with machine-specific keys
- **User-owned credentials**: You control your own API access

## Data Storage

All data is stored locally in `~/.gdhistogram/`:

```
~/.gdhistogram/
├── tokens.enc    # Encrypted OAuth tokens
├── cache.db      # SQLite cache for revisions
└── .salt         # Encryption salt
```

## Development

### Running Tests

```bash
pip install -r requirements.txt
pytest tests/
```

### Code Style

```bash
black gdhistogram/
mypy gdhistogram/
```

### Building

```bash
pip install build
python -m build
```

## Troubleshooting

### "Access denied" when fetching revisions

The document owner may have disabled revision history access. Try with a document you own.

### OAuth flow doesn't complete

Make sure port 8080 (or another available port) isn't blocked by your firewall.

### High memory usage with large documents

Documents with thousands of revisions use more memory. Consider lowering "Max Revisions" in configuration.

### Tokens not working after system change

Tokens are encrypted with machine-specific keys. If you change hardware, re-authorize the application.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read the contributing guidelines first.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Acknowledgments

- Google APIs for document access
- Plotly for interactive visualizations
- PySide6/Qt for the desktop interface
- Python difflib for deterministic text comparison
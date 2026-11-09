# Sleep Log Visualization

A Python application that retrieves sleep data from the Google Health API (the replacement for the Fitbit Web API) and creates visualizations showing your sleep patterns over time.

## Features

- **OAuth2 Authentication**: Google OAuth2 with PKCE
- **Sleep Data Retrieval**: Fetch sleep logs for any date range
- **Multiple Visualizations**:
  - Sleep periods chart showing when you sleep each day
  - Sleep duration trend over time
  - Sleep stages distribution (deep, light, REM, wake)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up a Google Cloud Project

The Fitbit Web API was shut down in November 2026. This app now uses the [Google Health API](https://developers.google.com/health).

1. Link your Fitbit / Google account to Google Health in the Google Health app.
2. In the [Google Cloud console](https://console.cloud.google.com/), create or select a project.
3. Enable the **Google Health API** (`health.googleapis.com`) in the API Library.
4. On **Google Auth Platform > Data Access**, add the scope `https://www.googleapis.com/auth/googlehealth.sleep.readonly`.
5. On **Google Auth Platform > Audience**, keep the status "Testing" and add your Google account email as a test user.
6. On **APIs & Services > Credentials**, create an **OAuth client ID**:
   - **Application type**: Web application
   - **Authorized redirect URI**: `http://localhost:8080/callback`
7. Note down the **Client ID** and **Client Secret**.

Note: while the app is in "Testing" status, Google refresh tokens expire after 7 days. The app then opens the browser again for a new sign-in.

### 3. Configure the Application

Copy the example config, then add your credentials:

```bash
cp config.example.py config.py
```

Edit `config.py`:

```python
CLIENT_ID = "your_client_id_here"
CLIENT_SECRET = "your_client_secret_here"
```

## Usage

### Basic Usage

```bash
# Get last 30 days of sleep data
python main.py

# Get last 7 days
python main.py --days 7

# Get specific date range
python main.py --start 2026-06-01 --end 2026-06-18

# Run with demo data (no API needed)
python main.py --demo
```

### Additional Options

```bash
# Save charts to specific directory
python main.py --output ./charts

# Save charts without displaying
python main.py --no-display

# Display charts without saving
python main.py --no-save

# Color all sleep periods with one color (default: #4809db)
python main.py --single-color "#2196f3"

# Set the image size in pixels (exact size), and the resolution
python main.py --width 1600 --height 900
python main.py --width 1200 --dpi 100   # height keeps the chart default
```

## Output

The application generates three types of charts:

### 1. Sleep Periods Chart (`sleep_periods.png`)

<img width="800" height="400" alt="sleep_periods" src="https://github.com/user-attachments/assets/bb6b59cb-833d-404d-bfcd-cf9b46c7ced3" />

A horizontal bar chart showing when you slept each day. The X-axis is the time of day (midnight to midnight, 00:00–24:00) and each row is a day. The chart spans from your first day of sleep (top) to your last (bottom), and sleep that crosses midnight wraps around to the left edge of the same row.

By default every sleep period is drawn in a single colour (`#4809db`, change it with `--single-color`). Pass an empty value (`--single-color ""`) to instead color each sleep stage:
- **Dark Blue**: Deep sleep
- **Light Blue**: Light sleep
- **Purple**: REM sleep
- **Amber**: Wake periods

### 2. Sleep Duration Chart (`sleep_duration.png`)

<img width="800" height="400" alt="sleep_duration" src="https://github.com/user-attachments/assets/c239ac08-5bd6-4a90-8047-b68b53369ce7" />

A line chart showing your total sleep duration for each day, with reference lines for recommended (8 hours) and minimum (7 hours) sleep.

### 3. Sleep Stages Chart (`sleep_stages.png`)

<img width="800" height="400" alt="sleep_stages" src="https://github.com/user-attachments/assets/5b1f7133-b3e4-4a30-b82b-f8b99db8aa08" />

A stacked bar chart showing the distribution of sleep stages for each day.

## Authentication

On first run, the application will:
1. Open your browser to the Google sign-in and consent page
2. Ask you to log in and grant permissions
3. Redirect back to a local server to capture the authorization code
4. Exchange the code for access tokens
5. Save tokens locally for future use

Tokens are stored in `google_health_tokens.json` and will be automatically refreshed when needed.

## Files

- `main.py` - Main application entry point
- `config.example.py` - Configuration template (copy to `config.py`)
- `config.py` - Your API credentials
- `google_auth.py` - Google OAuth2 authentication module
- `sleep_api.py` - Google Health API sleep client
- `sleep_chart.py` - Visualization functions
- `requirements.txt` - Python dependencies

## Troubleshooting

### "Invalid Client" Error
Make sure your Client ID and Client Secret are correctly entered in `config.py`.

### "access_denied" Error
Add your Google account as a test user on the **Audience** page of the Google Cloud console.

### "Invalid Redirect URI" Error
Ensure the redirect URI on your Google OAuth client matches exactly: `http://localhost:8080/callback`

### Port 8080 Already in Use
If another application is using port 8080, you can change the port in `config.py`:
```python
REDIRECT_URI = "http://localhost:9090/callback"
```
Remember to also update this on your Google OAuth client.

### No Sleep Data Found
- Ensure your Fitbit device is syncing sleep data to Google Health
- If you see "not linked to Google Health", link your account in the Google Health app
- Check that you've worn your device while sleeping
- Verify the date range you're querying has recorded sleep

## License

MIT License

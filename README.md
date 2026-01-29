# Fitbit Sleep Log Visualization

A Python application that retrieves sleep data from the Fitbit API and creates visualizations showing your sleep patterns over time.

## Features

- **OAuth2 Authentication**: Secure authentication with Fitbit's API using PKCE
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

### 2. Create a Fitbit Developer Account

1. Go to [Fitbit Developer Portal](https://dev.fitbit.com/)
2. Log in with your Fitbit account
3. Register a new application:
   - **Application Name**: Sleep Tracker (or any name)
   - **Description**: Personal sleep tracking application
   - **Application Website**: http://localhost
   - **Organization**: Personal
   - **Organization Website**: http://localhost
   - **Terms of Service URL**: http://localhost
   - **Privacy Policy URL**: http://localhost
   - **OAuth 2.0 Application Type**: Personal
   - **Redirect URL**: http://localhost:8080/callback
   - **Default Access Type**: Read-Only

4. After creating the app, note down your **Client ID** and **Client Secret**

### 3. Configure the Application

Edit `config.py` and add your credentials:

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
python main.py --start 2026-01-01 --end 2026-01-25

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
```

## Output

The application generates three types of charts:

### 1. Sleep Periods Chart (`sleep_periods.png`)
A horizontal bar chart showing when you slept each day. Time is displayed on the X-axis (6 PM to 6 PM), and each day is a row. Different colors represent sleep stages:
- **Dark Blue**: Deep sleep
- **Light Blue**: Light sleep
- **Purple**: REM sleep
- **Amber**: Wake periods

### 2. Sleep Duration Chart (`sleep_duration.png`)
A line chart showing your total sleep duration for each day, with reference lines for recommended (8 hours) and minimum (7 hours) sleep.

### 3. Sleep Stages Chart (`sleep_stages.png`)
A stacked bar chart showing the distribution of sleep stages for each day.

## Authentication

On first run, the application will:
1. Open your browser to the Fitbit authorization page
2. Ask you to log in and grant permissions
3. Redirect back to a local server to capture the authorization code
4. Exchange the code for access tokens
5. Save tokens locally for future use

Tokens are stored in `fitbit_tokens.json` and will be automatically refreshed when needed.

## Files

- `main.py` - Main application entry point
- `config.py` - Configuration settings (API credentials)
- `fitbit_auth.py` - OAuth2 authentication module
- `sleep_api.py` - Fitbit Sleep API client
- `sleep_chart.py` - Visualization functions
- `requirements.txt` - Python dependencies

## Troubleshooting

### "Invalid Client" Error
Make sure your Client ID and Client Secret are correctly entered in `config.py`.

### "Invalid Redirect URI" Error
Ensure the redirect URI in your Fitbit app settings matches exactly: `http://localhost:8080/callback`

### Port 8080 Already in Use
If another application is using port 8080, you can change the port in `config.py`:
```python
REDIRECT_URI = "http://localhost:9090/callback"
```
Remember to also update this in your Fitbit app settings.

### No Sleep Data Found
- Ensure your Fitbit device is syncing sleep data
- Check that you've worn your device while sleeping
- Verify the date range you're querying has recorded sleep

## License

MIT License

# Book-P-court

Flask app for submitting a pickleball court booking request through Selenium.

## Local run

```powershell
python -u app.py
```

Open `http://127.0.0.1:5000`.

## Render deploy

This repo is configured for Render using:

- `Dockerfile`
- `render.yaml`

Create a new Render Web Service from this GitHub repo and deploy. Render will build the Docker image, install Chromium plus Chromedriver, and start the app with Gunicorn.

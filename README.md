# Neon Mandala + Helix Turbine

An animated neon flower and Archimedes-style helix turbine visualization built with Python, NumPy, and OpenCV.

## Run on Windows

Install Python 3.11 or newer, then open PowerShell in this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe neon_opencv.py
```

## Controls

- `T`: switch between the flower and turbine
- `Space`: pause or resume
- `R`: restart the animation
- `Up` / `Down` or `+` / `-`: adjust turbine wind speed
- `Q` or `Esc`: close the window

The turbine is a stylized visual simulation, not an engineering or airflow model.

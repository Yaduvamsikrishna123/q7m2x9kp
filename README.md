# Wind Forecast Analytics

A pilot application for comparing UK wind generation forecasts with actual generation data and evaluating forecast accuracy for day-ahead energy procurement analysis.

## Features

- Daily forecast-versus-actual comparison
- Delivery date and decision cutoff selection
- Hourly generation data visualisation
- Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and forecast bias
- Matched interval and coverage metrics
- FastAPI endpoints and interactive API documentation
- Docker-based local development

## Technology Stack

- **Frontend:** React and Vite
- **Backend:** Python and FastAPI
- **Data source:** Elexon BMRS
- **Deployment for local development:** Docker Compose

## Project Structure

- `backend/` — API endpoints, Elexon client, and analysis logic
- `frontend/` — dashboard interface and visualisations
- `docker-compose.yml` — container configuration
- `.env.example` — example environment variables
- `.gitignore` — files excluded from Git
- `README.md` — project documentation

## Prerequisites

- Docker Desktop
- Docker Compose
- Internet access to retrieve data from Elexon BMRS

## Run Locally

1. Clone the repository:

   ```bash
   git clone https://github.com/Yaduvamsikrishna123/q7m2x9kp.git
   cd q7m2x9kp
   ```

2. Create a local `.env` file using `.env.example` as a reference. Adjust the values if needed for your local setup.

3. Build and start the application:

   ```bash
   docker compose up --build -d
   ```

4. Open the dashboard:

   `http://localhost:8080`

5. Open the API documentation:

   `http://localhost:8000/docs`

6. Check backend health:

   `http://localhost:8000/api/health`

To stop the application:

```bash
docker compose down
```

## API Endpoints

- `GET /api/health` — checks backend availability
- `GET /api/comparison` — compares forecasts and actuals for a delivery date
- `GET /api/accuracy` — evaluates forecast accuracy across January 2026

## Accuracy Metrics

- **MAE:** Average absolute forecast error
- **RMSE:** Square root of the mean squared forecast error
- **Bias:** Average signed forecast error
- **Coverage:** Matched forecast/actual intervals relative to the expected number of intervals

## Data and Assumptions

The prototype uses Elexon BMRS wind forecast and generation datasets for January 2026. The decision cutoff is configurable; the default cutoff is an assumption that must be confirmed against the applicable market deadline.

Forecast publication-time selection, data completeness, and metrics should be validated before operational use.



## Live Application

**Frontend Dashboard:** https://q7m2x9kp-web.vercel.app

**Backend API Health Check:** https://q7m2x9kp-api.vercel.app/api/health

**Interactive API Documentation:** https://q7m2x9kp-api.vercel.app/docs

## Source Code

**GitHub Repository:** https://github.com/Yaduvamsikrishna123/q7m2x9kp


## Repository

https://github.com/Yaduvamsikrishna123/q7m2x9kp

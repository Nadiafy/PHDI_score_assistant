# PHDI Score Application

This application calculates the Planetary Health Diet Index (PHDI) score from a user's daily food diary. It features both a web-based chat interface and a Telegram bot to log meals and instantly retrieve environmental impact scores.

## Structure
- `/backend`: FastAPI application that handles natural language food parsing via Google Gemini, nutritional queries, scoring logic, and the Telegram bot (`aiogram`).
- `/frontend`: Nuxt.js application for the web chat interface.

## Setup & Running

### Prerequisites
- Python 3.10+
- Node.js 18+
- API Keys for Google Gemini, USDA (optional), and a Telegram Bot Token.

### Backend & Telegram Bot
1. Navigate to `/backend`.
2. Install dependencies: `pip install -r requirements.txt`.
3. Create a `.env` file and add the following keys:
   - `GEMINI_API_KEY` (Required for NLP food logs parsing)
   - `TELEGRAM_BOT_TOKEN` (Required if you want to run the Telegram bot)
   - `USDA_API_KEY` (Optional, defaults to DEMO_KEY)
4. Run the server: `uvicorn main:app --reload`.
   - The API will be available at `http://localhost:8000`.
   - The Telegram bot will automatically start polling continuously in the background alongside the API.

### Frontend
1. Navigate to `/frontend`.
2. Install dependencies: `npm install`.
3. Run the development server: `npm run dev`.
   - The web app will be available at `http://localhost:3000`.

## Methodology
The PHDI score is calculated based on the EAT-Lancet methodology, scoring 16 food categories across Adequacy, Moderation, Optimum, and Ratio components for a total of 150 points. The backend leverages Google Gemini to extract quantities and food types from conversational inputs, falling back to heuristic category mapping when necessary.

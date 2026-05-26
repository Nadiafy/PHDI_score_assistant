from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import os
from nutrition_service import parse_food_log, get_nutritional_data, map_to_phdi
from phdi_logic import calculate_phdi_score
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from telegram_bot import start_telegram_bot, bot, dp
from auth import create_access_token, verify_token, generate_telegram_link_token, ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_db
from models import User, DailyLog
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from datetime import timedelta
from contextlib import asynccontextmanager

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "dummy_client_id")


bot_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_task
    # Startup
    bot_task = asyncio.create_task(start_telegram_bot())
    yield
    # Shutdown
    if bot_task:
        bot_task.cancel()
    if bot:
        await dp.storage.close()
        await bot.session.close()

app = FastAPI(title="PHDI Score API", lifespan=lifespan)

# Enable CORS for Nuxt.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FoodLogRequest(BaseModel):
    log_text: str

class GoogleAuthRequest(BaseModel):
    token: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str


@app.get("/")
def read_root():
    return {"message": "PHDI Score API is running"}

@app.post("/api/auth/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    try:
        if request.token == "dev_token":
            # Completely bypass DB for the dev token so we don't crash without PostgreSQL
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            # Use an arbitrary dummy UUID for the developer
            encoded_jwt = create_access_token(
                data={"sub": "00000000-0000-0000-0000-000000000000"}, expires_delta=access_token_expires
            )
            return {"access_token": encoded_jwt, "token_type": "bearer", "email": "dev@example.com"}
            
        idinfo = id_token.verify_oauth2_token(request.token, google_requests.Request(), GOOGLE_CLIENT_ID)
        email = idinfo['email']

        # Find or create user
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if not user:
            user = User(email=email)
            db.add(user)
            await db.commit()
            await db.refresh(user)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer", "email": email}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid token: {e}")

@app.post("/api/auth/link-telegram")
async def link_telegram(user_id: str = Depends(verify_token)):
    token = generate_telegram_link_token(user_id)
    # The actual bot username needs to be known. We'll assume 'PHDI_Bot' or use env var
    bot_username = os.getenv("PHDI_bot", "PHDI_bot")
    return {"link_url": f"https://t.me/{bot_username}?start={token}"}

@app.post("/calculate-phdi")
async def calculate_phdi(
    request: FoodLogRequest, 
    user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    try:
        from crud import upsert_daily_log
        # 1. Parse log
        items = await asyncio.to_thread(parse_food_log, request.log_text)
        print("web chat items:", items)
        # 2. Get nutrition and mapping
        enriched_items = []
        for item in items:
            nutri = await asyncio.to_thread(get_nutritional_data, item["food_item"], item["quantity_g"])
            item.update(nutri)
            enriched_items.append(item)
            
        # 3. Aggregate to PHDI categories
        percentages = map_to_phdi(enriched_items)
        
        # 4. Calculate score
        result = calculate_phdi_score(percentages)
        
        # 5. Upsert to DB
        import uuid
        try:
            await upsert_daily_log(
                db=db,
                user_id=uuid.UUID(user_id),
                log_text=request.log_text,
                total_score=result["total_score"],
                component_scores=result["component_scores"],
                source="web"
            )
        except Exception as e:
            print(f"Skipping DB upsert due to error: {e}")
        
        return {
            "status": "success",
            "items": enriched_items,
            "percentages": percentages,
            "total_score": result["total_score"],
            "component_scores": result["component_scores"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from sqlalchemy import desc

@app.get("/api/history/recent")
async def get_recent_history(
    user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    import uuid
    from datetime import date, timedelta
    thirty_days_ago = date.today() - timedelta(days=30)
    
    result = await db.execute(
        select(DailyLog)
        .where(
            DailyLog.user_id == uuid.UUID(user_id),
            DailyLog.date >= thirty_days_ago
        )
        .order_by(DailyLog.date.asc())
    )
    logs = result.scalars().all()
    
    return [
        {
            "date": log.date.isoformat(),
            "total_phdi_score": log.total_phdi_score
        }
        for log in logs
    ]

@app.get("/api/history")
async def get_full_history(
    skip: int = 0, limit: int = 50,
    user_id: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    import uuid
    result = await db.execute(
        select(DailyLog)
        .where(DailyLog.user_id == uuid.UUID(user_id))
        .order_by(desc(DailyLog.date))
        .offset(skip)
        .limit(limit)
    )
    logs = result.scalars().all()
    return logs

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import DailyLog, User
from datetime import date
import uuid

async def upsert_daily_log(
    db: AsyncSession,
    user_id: uuid.UUID,
    log_text: str,
    total_score: float,
    component_scores: dict,
    source: str
):
    today = date.today()
    result = await db.execute(select(DailyLog).where(
        DailyLog.user_id == user_id, 
        DailyLog.date == today
    ))
    daily_log = result.scalars().first()
    
    if daily_log:
        daily_log.raw_text_log = f"{daily_log.raw_text_log} + {log_text}" if daily_log.raw_text_log else log_text
        daily_log.total_phdi_score = total_score
        daily_log.component_scores = component_scores
        daily_log.source = source
    else:
        daily_log = DailyLog(
            user_id=user_id,
            date=today,
            raw_text_log=log_text,
            total_phdi_score=total_score,
            component_scores=component_scores,
            source=source
        )
        db.add(daily_log)
    await db.commit()
    await db.refresh(daily_log)
    return daily_log

async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalars().first()

"""Net worth tracker: assets, liabilities, and a growth projection."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Asset, Expense, Liability, User
from ..schemas import AssetCreate, AssetOut, LiabilityCreate, LiabilityOut

router = APIRouter(prefix="/api/networth", tags=["networth"])


def _summary(db: Session, current: User) -> dict:
    assets = db.query(Asset).filter(Asset.user_id == current.id).order_by(Asset.id).all()
    liabs = db.query(Liability).filter(Liability.user_id == current.id).order_by(Liability.id).all()
    total_assets = sum(a.value for a in assets)
    total_liab = sum(l.balance for l in liabs)
    net_worth = total_assets - total_liab

    # Estimate monthly net savings to project net-worth growth.
    expenses = db.query(Expense).filter(Expense.user_id == current.id).all()
    months = max(len({f"{e.spent_on.year}-{e.spent_on.month:02d}" for e in expenses}), 1)
    monthly_spend = sum(e.amount for e in expenses) / months
    monthly_debt_pay = sum(l.monthly_payment for l in liabs)
    monthly_net_add = max(current.monthly_income - monthly_spend, 0)

    # 5-year projection: assets grow ~8%/yr + contributions; liabilities amortize.
    projection = []
    a_bal, l_bal = total_assets, total_liab
    for yr in range(1, 6):
        a_bal = a_bal * 1.08 + monthly_net_add * 12
        l_bal = max(l_bal - monthly_debt_pay * 12, 0)
        projection.append({"year": yr, "net_worth": round(a_bal - l_bal)})

    return {
        "total_assets": round(total_assets),
        "total_liabilities": round(total_liab),
        "net_worth": round(net_worth),
        "assets": [AssetOut.model_validate(a).model_dump() for a in assets],
        "liabilities": [LiabilityOut.model_validate(l).model_dump() for l in liabs],
        "projection": projection,
    }


@router.get("")
def get_networth(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return _summary(db, current)


@router.post("/assets", response_model=AssetOut, status_code=201)
def add_asset(payload: AssetCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    a = Asset(user_id=current.id, **payload.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.delete("/assets/{asset_id}", status_code=204)
def delete_asset(asset_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    a = db.query(Asset).filter(Asset.id == asset_id, Asset.user_id == current.id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Asset not found")
    db.delete(a)
    db.commit()


@router.post("/liabilities", response_model=LiabilityOut, status_code=201)
def add_liability(payload: LiabilityCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    l = Liability(user_id=current.id, **payload.model_dump())
    db.add(l)
    db.commit()
    db.refresh(l)
    return l


@router.delete("/liabilities/{liab_id}", status_code=204)
def delete_liability(liab_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    l = db.query(Liability).filter(Liability.id == liab_id, Liability.user_id == current.id).first()
    if not l:
        raise HTTPException(status_code=404, detail="Liability not found")
    db.delete(l)
    db.commit()

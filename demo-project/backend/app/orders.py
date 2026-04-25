from fastapi import APIRouter

router = APIRouter()


@router.post("/api/orders/checkout")
def checkout():
    return {"orderId": "demo-order"}


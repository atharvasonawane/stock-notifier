from pydantic import Field, BaseModel
from typing import List


class TradeData(BaseModel):
    last_price: float = Field(alias="p")
    symbol: str = Field(alias="s")
    timestamp: int = Field(alias="t")
    volume: float = Field(alias="v")
    trade_conditions: List | None = Field(default=None, alias='c')


class WebSocketResponse(BaseModel):
    data: List[TradeData]
    type: str

class WebSocketRequest(BaseModel):
    type: str
    symbol: str
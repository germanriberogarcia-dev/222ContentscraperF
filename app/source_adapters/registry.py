from __future__ import annotations

from app.source_adapters.barista_magazine import BaristaMagazineAdapter
from app.source_adapters.daily_coffee_news import DailyCoffeeNewsAdapter
from app.source_adapters.perfect_daily_grind import PerfectDailyGrindAdapter
from app.source_adapters.sca import SpecialtyCoffeeAssociationAdapter
from app.source_adapters.tea_coffee_trade_journal import TeaCoffeeTradeJournalAdapter


def build_source_adapters():
    return [
        PerfectDailyGrindAdapter(),
        DailyCoffeeNewsAdapter(),
        SpecialtyCoffeeAssociationAdapter(),
        BaristaMagazineAdapter(),
        TeaCoffeeTradeJournalAdapter(),
    ]

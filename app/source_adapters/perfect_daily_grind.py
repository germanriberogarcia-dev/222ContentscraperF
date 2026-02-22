from app.models import SourceConfig
from app.source_adapters.base import BaseSourceAdapter


class PerfectDailyGrindAdapter(BaseSourceAdapter):
    def __init__(self):
        super().__init__(
            SourceConfig(
                id="perfect_daily_grind",
                name="Perfect Daily Grind",
                base_url="https://perfectdailygrind.com",
                feed_url="https://perfectdailygrind.com/feed/",
                listing_url="https://perfectdailygrind.com",
                article_selector="article",
                link_selector="h2 a, h3 a, a[href]",
                time_selector="time",
                snippet_selector="p",
                image_selector="img",
            )
        )

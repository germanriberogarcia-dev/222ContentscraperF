from app.models import SourceConfig
from app.source_adapters.base import BaseSourceAdapter


class DailyCoffeeNewsAdapter(BaseSourceAdapter):
    def __init__(self):
        super().__init__(
            SourceConfig(
                id="daily_coffee_news",
                name="Daily Coffee News",
                base_url="https://dailycoffeenews.com",
                feed_url="https://dailycoffeenews.com/feed/",
                listing_url="https://dailycoffeenews.com",
                article_selector="article",
                link_selector="h2 a, h3 a, a[href]",
                time_selector="time",
                snippet_selector="p",
                image_selector="img",
            )
        )

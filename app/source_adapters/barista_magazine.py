from app.models import SourceConfig
from app.source_adapters.base import BaseSourceAdapter


class BaristaMagazineAdapter(BaseSourceAdapter):
    def __init__(self):
        super().__init__(
            SourceConfig(
                id="barista_magazine",
                name="Barista Magazine",
                base_url="https://www.baristamagazine.com",
                feed_url="https://www.baristamagazine.com/feed/",
                listing_url="https://www.baristamagazine.com",
                article_selector="article",
                link_selector="h2 a, h3 a, a[href]",
                time_selector="time",
                snippet_selector="p",
                image_selector="img",
            )
        )

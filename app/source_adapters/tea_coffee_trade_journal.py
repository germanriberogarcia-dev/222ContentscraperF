from app.models import SourceConfig
from app.source_adapters.base import BaseSourceAdapter


class TeaCoffeeTradeJournalAdapter(BaseSourceAdapter):
    def __init__(self):
        super().__init__(
            SourceConfig(
                id="tea_coffee_trade_journal",
                name="Tea & Coffee Trade Journal",
                base_url="https://www.teaandcoffee.net",
                feed_url="https://www.teaandcoffee.net/feed/",
                listing_url="https://www.teaandcoffee.net/news/",
                article_selector="article, .news-item, .post",
                link_selector="h2 a, h3 a, a[href]",
                time_selector="time, .date",
                snippet_selector="p",
                image_selector="img",
            )
        )

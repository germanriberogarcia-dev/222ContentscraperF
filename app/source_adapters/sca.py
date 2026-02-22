from app.models import SourceConfig
from app.source_adapters.base import BaseSourceAdapter


class SpecialtyCoffeeAssociationAdapter(BaseSourceAdapter):
    def __init__(self):
        super().__init__(
            SourceConfig(
                id="sca",
                name="Specialty Coffee Association",
                base_url="https://sca.coffee",
                feed_url="https://sca.coffee/rss",
                listing_url="https://sca.coffee/news",
                article_selector="article, .news-item, .post",
                link_selector="h2 a, h3 a, a[href]",
                time_selector="time, .date",
                snippet_selector="p",
                image_selector="img",
            )
        )

"""Data items matching exact output format of original collectors."""

import scrapy


class RedditPost(scrapy.Item):
    source = scrapy.Field()
    id = scrapy.Field()
    title = scrapy.Field()
    selftext = scrapy.Field()
    created_utc = scrapy.Field()
    url = scrapy.Field()
    score = scrapy.Field()
    subreddit = scrapy.Field()
    permalink = scrapy.Field()


class RedditComment(scrapy.Item):
    source = scrapy.Field()
    id = scrapy.Field()
    link_id = scrapy.Field()
    parent_id = scrapy.Field()
    body = scrapy.Field()
    created_utc = scrapy.Field()
    score = scrapy.Field()
    permalink = scrapy.Field()
    subreddit = scrapy.Field()


class SiteItem(scrapy.Item):
    source = scrapy.Field()
    domain = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    text = scrapy.Field()


class TunisiaSatPost(scrapy.Item):
    source = scrapy.Field()
    thread_url = scrapy.Field()
    post_id = scrapy.Field()
    author = scrapy.Field()
    datetime = scrapy.Field()
    text = scrapy.Field()


class TunisiaSatPage(scrapy.Item):
    url = scrapy.Field()
    text = scrapy.Field()


class DerjaNinjaPage(scrapy.Item):
    url = scrapy.Field()
    text = scrapy.Field()


class DerjaNinjaCard(scrapy.Item):
    source = scrapy.Field()
    url = scrapy.Field()
    english = scrapy.Field()
    arabic = scrapy.Field()
    roman = scrapy.Field()


class BettounsiPage(scrapy.Item):
    url = scrapy.Field()
    text = scrapy.Field()


class YouTubeItem(scrapy.Item):
    source = scrapy.Field()
    video_id = scrapy.Field()
    transcript = scrapy.Field()
    comments = scrapy.Field()


class XItem(scrapy.Item):
    source = scrapy.Field()
    id = scrapy.Field()
    text = scrapy.Field()
    lang = scrapy.Field()
    created_at = scrapy.Field()
    metrics = scrapy.Field()


class FacebookPost(scrapy.Item):
    source = scrapy.Field()
    group_id = scrapy.Field()
    post = scrapy.Field()


class GoogleCSEItem(scrapy.Item):
    source = scrapy.Field()
    title = scrapy.Field()
    link = scrapy.Field()
    snippet = scrapy.Field()
    query = scrapy.Field()
    text = scrapy.Field()

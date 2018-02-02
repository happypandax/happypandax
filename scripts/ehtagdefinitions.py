"""
Scrape tag definitions from e-hentai wiki

Requires Scrapy (pip install scrapy)
"""

import scrapy

all_tags = {} # lang : { tag: description}

class TagScraper(scrapy.Spider):
    name = "Tags"

    start_urls = [
        "https://ehwiki.org/wiki/Category:Tag",
        ]

    def parse(self, response):
        for group in response.css("div.mw-category-group"):
            for tag in group.css("li a::attr(href)"):
                yield response.follow(tag, self.parse_tag)

        next_page = response.css("div#mw-pages a")[-1]
        if next_page.css("::text").extract_first() == "next page":
            next_page = next_page.css("::attr(href)").extract_first()
            if next_page is not None:
                yield response.follow(next_page, self.parse)

    def parse_tag(self, response):
        tag_name = response.css("#firstHeading::text").extract_first()
        description = ""
        language = "english"
        for x in response.css("div#mw-content-text li"):
            if x.css("b::text").extract_first() == "Description":
                l = x.css("::text").extract()[1:]
                for t in l:
                    txt = t
                    if not isinstance(t, str):
                        txt = t.css("::text").extract_first()
                    description += txt
                description = description[2:]
        if '/' in tag_name:
            tag_name, language = tag_name.split('/')
        all_tags.setdefault(language, {})[tag_name.lower()] = description
        yield


    def closed(self, reason):
        for lang, tags in all_tags.items():
            with open("tags_{}.yaml".format(lang.lower()), "w", encoding="utf-8") as f:
                for tag in sorted(tags):
                    description = tags[tag]
                    f.write("{}: {}\n".format(tag.lower(), description))
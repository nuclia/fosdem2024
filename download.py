from datetime import datetime
import json
import os

BASE_URL = "https://fosdem.org"
CACHE_FILE = "fosdem.cache.2024"


def compute(soup):
    cache = {}
    for event in soup.find_all("tr"):
        tds = [x for x in event.find_all("td")]
        if len(tds) > 2:
            title_td = tds[0]
            # Get abstract of the talk and all links
            a_talk_url = title_td.find_next("a")
            title = title_td.text
            if a_talk_url is not None:
                talk_url = BASE_URL + a_talk_url.get("href")
            authors_td = tds[1]
            authors = {
                x.text: BASE_URL + x.get("href") for x in authors_td.find_all("a")
            }
            day = 4 if tds[3].text == "Saturday" else 5
            hour, minute = tds[4].text.split(":")
            date = datetime.strptime(
                f"2023-02-0{day} {hour}-{minute}", "%Y-%m-%d %H-%M"
            )
            videos_td = tds[7]

            video = None
            videos = [x for x in videos_td.find_all("a") if "webm" in x.text.lower()]

            if talk_url not in cache or (
                cache[talk_url]["video"] is not None and len(videos) > 0
            ):
                talk_data = requests.get(talk_url).text
                talk_soup = BeautifulSoup(talk_data, "html.parser")
                event_abstract = talk_soup.find(
                    "div", attrs={"class": "event-abstract"}
                ).text
                event_description = talk_soup.find(
                    "div", attrs={"class": "event-description"}
                ).text
                attachments_ul = talk_soup.find(
                    "ul", attrs={"class": "event-attachments"}
                )
                if attachments_ul is not None:
                    attachment = BASE_URL + attachments_ul.find("a").get("href")
                else:
                    attachment = None

                room = (
                    talk_soup.find("ul", attrs={"class": "side-box"})
                    .find("li")
                    .find("a")
                    .text
                )

                if len(videos):
                    video = videos[0].get("href")

                if talk_url not in cache:
                    cache[talk_url] = {
                        "uploaded": False,
                        "rid": None,
                        "title": title,
                        "orig_url": BASE_URL + talk_url,
                        "authors": authors,
                        "video": video,
                        "abstract": event_abstract,
                        "description": event_description,
                        "attachment": attachment,
                        "date": date.isoformat(),
                    }
                if video != cache[talk_url].get("video"):
                    cache[talk_url]["video"] = video
                    cache[talk_url]["uploaded"] = False

                if attachment != cache[talk_url].get("attachment"):
                    cache[talk_url]["attachment"] = attachment
                    cache[talk_url]["uploaded"] = False

                if room != cache[talk_url].get("room"):
                    cache[talk_url]["room"] = room
                    cache[talk_url]["uploaded"] = False

                cache[talk_url].update()
                with open(CACHE_FILE, "w+") as cache_file:
                    cache_file.write(json.dumps(cache))


if not os.path.exists(CACHE_FILE):
    from bs4 import BeautifulSoup
    import requests

    data = requests.get("https://fosdem.org/2024/schedule/events/")
    soup = BeautifulSoup(data.text, "html.parser")
    compute(soup)

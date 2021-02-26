# coding=utf-8

import cloudscraper
from bs4 import BeautifulSoup


class JAVLibrary:
    class Languages:
        EN = "en"
        JP = "jp"
        CN = "cn"
        TW = "tw"

    BASE_URL = "http://www.javlibrary.com/"
    SEARCH_URL = "/vl_searchbyid.php?keyword="
    MOVIE_URL = "/?v="
    DMM_POSTER_URL = "http://pics.dmm.co.jp/mono/movie/adult/1{movie_id}/1{movie_id}ps.jpg"
    DMM_COVER_URL = "http://pics.dmm.co.jp/mono/movie/adult/1{movie_id}/1{movie_id}pl.jpg"

    def __init__(self, language):
        self.language = language

    def get_search_url(self, keyword):
        return JAVLibrary.BASE_URL + self.language + JAVLibrary.SEARCH_URL + keyword

    def get_movie_url(self, jav_library_id):
        return JAVLibrary.BASE_URL + self.language + JAVLibrary.MOVIE_URL + jav_library_id

    @staticmethod
    def get_poster_url(movie_id):
        return JAVLibrary.DMM_POSTER_URL.format(movie_id=movie_id)

    @staticmethod
    def get_cover_url(movie_id):
        return JAVLibrary.DMM_COVER_URL.format(movie_id=movie_id)

    def get_results(self, keyword):
        results = []
        score = 100
        # Bypass Cloudflare anti-bot page
        scraper = cloudscraper.create_scraper()
        # Search for keyword on javlibrary.com
        url = self.get_search_url(keyword)
        Log("Searching for matches from url: " + url)
        web_data = scraper.get(url).content.decode("utf-8")
        soup = BeautifulSoup(web_data, "html.parser")
        # Redirected to the search result page
        if soup.find("div", "videos"):
            # There is at least one match
            if soup.find("div", "video"):
                for video in soup.find_all("div", "video"):
                    movie_id = video.find("a")["href"][5:]
                    results.append(
                        MetadataSearchResult(
                            id=movie_id,
                            name=video.find("a")["title"],
                            year=None,
                            score=score
                        )
                    )
                    score = score - 1
            # There is no match
            else:
                return None
        # Redirected to the movie page
        else:
            try:
                movie_id = soup.find("h3", "post-title").find("a")["href"][7:]
            except AttributeError:
                Log("An exception occurred: " + url)
                return results
            results.append(
                MetadataSearchResult(
                    id=movie_id,
                    name=soup.find("div", {"id": "video_title"}).find("a").text.strip(),
                    year=None,
                    score=score
                )
            )
        return results

    def get_metadata(self, movie_id):
        # Result dict
        metadata = {
            "javlibrary_id": "",
            "id": "",
            "title": "",
            "originally_available_at": "2000-01-01",
            "duration": 0,
            "rating": 0.0,
            "studio": "",
            "roles": [],
            "posters": [],
            "directors": [],
            "year": 2000,
            "thumbs": [],
            "genres": [],
        }
        # Bypass Cloudflare anti-bot page
        scraper = cloudscraper.create_scraper()
        # Open movie url
        url = self.get_movie_url(movie_id)
        Log("Fetching metadata from: " + url)
        movie_data = scraper.get(url).content.decode("utf-8")
        movie_soup = BeautifulSoup(movie_data, "html.parser")
        metadata["javlibrary_id"] = movie_id
        metadata["title"] = movie_soup.find("div", {"id": "video_title"}).find("a").text.strip()
        for tr in movie_soup.find("div", {"id": "video_info"}).find_all("tr"):
            tr_header = tr.find_all("td")[0].text.strip()
            tr_text = tr.find_all("td")[1]
            if tr_header in ["ID:", "品番:", "识别码:", "識別碼:"]:
                movie_id = tr_text.text.strip().lower().replace("-", "")
                metadata["id"] = movie_id
                metadata["posters"] = [self.get_poster_url(movie_id)]
                metadata["thumbs"] = [self.get_cover_url(movie_id)]
            if tr_header in ["Release Date:", "発売日:", "发行日期:", "發行日期:"]:
                metadata["originally_available_at"] = tr_text.text.strip()
                metadata["year"] = int(tr_text.text.strip().split("-")[0])
            if tr_header in ["Length:", "収録時間:", "长度:", "長度:"]:
                metadata["duration"] = int(tr_text.find("span", "text").text.strip())
            if tr_header in ["Director:", "監督:", "导演:", "導演:"] and tr_text.find("span", "director"):
                metadata["directors"] = [tr_text.find("span", "director").text.strip()]
            if tr_header in ["Maker:", "メーカー:", "制作商:", "製作商:"]:
                metadata["studio"] = tr_text.find("span", "maker").text.strip()
            if tr_header in ["Genre(s):", "ジャンル:", "类别:", "類別:"]:
                for genre in tr_text.find_all("span", "genre"):
                    metadata["genres"].append(genre.text.strip())
            if tr_header in ["Cast:It's", "出演者:", "演员:", "演員:"]:
                for cast in tr_text.find_all("span", "cast"):
                    metadata["roles"].append(cast.text.strip())
            if tr_header in ["User Rating:", "平均評価:", "使用者评价:", "使用者評價:"]:
                try:
                    metadata["rating"] = float(tr_text.find("span", "score").text.strip("()"))
                except ValueError:
                    pass

        Log("Fetching metadata success")

        return metadata

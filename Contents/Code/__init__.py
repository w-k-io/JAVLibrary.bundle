# coding=utf-8

import os
from datetime import datetime
from urllib import quote

from cached_property import cached_property
import requests

from javlibrary import JAVLibrary


def Start():
    pass


class JavLibraryAgent(Agent.Movies):
    name = "JAVLibrary"
    languages = [
        Locale.Language.NoLanguage
    ]
    accepts_from = [
        'com.plexapp.agents.localmedia'
    ]
    contributes_to = [
        'com.plexapp.agents.none'
    ]

    def search(self, results, media, lang):
        # Movie name from folder
        media_path = media.items[0].parts[0].file
        folder_path = os.path.dirname(media_path)
        movie_name = self.get_movie_id_from_folder(folder_path)
        javlibrary_api = JAVLibrary(self.get_language(Prefs["javlibrary_language"]))
        search_results = javlibrary_api.get_results(movie_name)
        if search_results:
            for result in search_results:
                results.Append(
                    MetadataSearchResult(
                        id=result[0],
                        name=media.name,
                        year=None,
                        score=result[1],
                        lang=lang
                    )
                )

    def update(self, metadata, media, lang):
        javlibrary_api = JAVLibrary(self.get_language(Prefs["javlibrary_language"]))
        movie_metadata = javlibrary_api.get_metadata(metadata.id)
        metadata.title = movie_metadata["title"]
        metadata.title_sort = movie_metadata["id"]
        metadata.studio = movie_metadata["studio"]
        metadata.year = movie_metadata["year"]
        available_date = datetime.strptime(movie_metadata["originally_available_at"], "%Y-%m-%d").date()
        metadata.originally_available_at = available_date
        metadata.rating = movie_metadata["rating"]
        metadata.duration = movie_metadata["duration"]
        metadata.directors.clear()
        for director in movie_metadata["directors"]:
            metadata.directors.new().name = director
        metadata.directors.clear()
        for genre in movie_metadata["genres"]:
            metadata.genres.add(genre)
        metadata.roles.clear()
        for role in movie_metadata["roles"]:
            self.get_role(metadata.roles.new(), role)
        for key in metadata.posters.keys():
            del metadata.posters[key]
        for poster in movie_metadata["posters"]:
            metadata.posters[poster] = Proxy.Preview(HTTP.Request(poster).content)
        for key in metadata.art.keys():
            del metadata.art[key]
        for thumb in movie_metadata["thumbs"]:
            metadata.art[thumb] = Proxy.Preview(HTTP.Request(thumb).content)
        return metadata

    @staticmethod
    def get_language(language):
        languages = {
            "English": JAVLibrary.Languages.EN,
            "Japanese": JAVLibrary.Languages.JP,
            "Simplified Chinese": JAVLibrary.Languages.CN,
            "Traditional Chinese": JAVLibrary.Languages.TW
        }
        return languages[language]

    @staticmethod
    def get_movie_id_from_folder(folder_path):
        Log("Getting movie name from path: " + folder_path)
        folder_split = os.path.normpath(folder_path).split(os.sep)
        movie_name = folder_split[-1]
        Log("Found movie name from path: " + movie_name)
        return movie_name

    @cached_property
    def gfriends_map(self):
        github_template = 'https://raw.githubusercontent.com/xinxin8816/gfriends/master/{}/{}/{}'
        request_url = 'https://raw.githubusercontent.com/xinxin8816/gfriends/master/Filetree.json'

        Log("start loading gfriend file tree")

        response = requests.get(request_url)
        if response.status_code != 200:
            Log('request gfriend map failed {}'.format(response.status_code))
            return {}

        Log("gfriend file tree loaded success")

        map_json = response.json()
        map_json.pop('Filetree.json', None)
        map_json.pop('README.md', None)
        output = {}

        # plex doesnt support fucking recursive call
        first_lvls = map_json.keys()
        for first in first_lvls:
            second_lvls = map_json[first].keys()
            for second in second_lvls:
                for k, v in map_json[first][second].items():
                    output[k[:-4]] = github_template.format(
                        quote(first.encode("utf-8")),
                        quote(second.encode("utf-8")),
                        quote(v.encode("utf-8"))
                    )

        return output

    def get_role(self, role, actor):
        role.name = actor
        for actorname in filter(None, actor.split(" ")):
            role.photo = self.gfriends_map.get(actorname.upper(), "")
            if role.photo:
                break
        Log(role.photo)
        return role


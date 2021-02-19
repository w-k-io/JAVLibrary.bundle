# coding=utf-8

import os
from datetime import datetime

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
            metadata.roles.new().name = role
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

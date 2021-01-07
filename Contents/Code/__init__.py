# coding=utf-8

import os
from datetime import datetime

from Contents.Code.javlibrary import JAVLibrary


class JavLibraryAgent(Agent.Movies):
    name = "JAVLibrary"
    languages = [
        Locale.Language.English,
        Locale.Language.Japanese,
        Locale.Language.Chinese,
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
        javlibrary_api = JAVLibrary(Prefs["javlibrary_language"])
        search_results = javlibrary_api.get_metadata(movie_name)
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
        javlibrary_api = JAVLibrary(Prefs["javlibrary_language"])
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
        for director in metadata["directors"]:
            metadata.directors.new().name = director
        metadata.directors.clear()
        for genre in metadata["genres"]:
            metadata.genres.add(genre)
        metadata.roles.clear()
        for role in metadata["roles"]:
            metadata.roles.new().name = role
        metadata.duration = movie_metadata["duration"]
        return metadata

    @staticmethod
    def get_movie_name_from_folder(folder_path):
        folder_split = os.path.normpath(folder_path).split(os.sep)
        movie_name = folder_split[-1]
        return movie_name

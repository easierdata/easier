import random
from scipy.spatial import KDTree
import pandas as pd


class Cache:
    def __init__(self, cache_expiration):
        self.cache = {}
        self.cache_expiration = cache_expiration

    def ping_cache(self, scene_indicies) -> list:
        """Return a list of scenes that are cached. Add missing scenes to cache"""
        cached_scenes = []
        if self.cache_expiration == 0 and len(self.cache) > 0:
            self.cache.popitem()
            self.cache_expiration = 10

        for scene_index in scene_indicies:
            if scene_index in self.cache:
                cached_scenes.append(scene_index)
            elif self.cache_expiration > 0:
                self.cache[scene_index] = True

        self.cache_expiration -= 1

        return cached_scenes


def run_simulation(scenes, number_of_requests, number_of_scenes_per_request, cache):
    """Run the simulation and return the number of cold storage hits"""
    cold_storage_hits = 0
    tree = KDTree(scenes)
    for _ in range(number_of_requests):
        random_scene = random.choice(scenes)
        nearest_scene_indices = tree.query(
            random_scene, k=number_of_scenes_per_request
        )[1]
        requested_scenes = cache.ping_cache(nearest_scene_indices)
        if len(requested_scenes) < 4:
            cold_storage_hits += 1

    return cold_storage_hits


if __name__ == "__main__":
    NUMBER_OF_REQUESTS = 500
    ITERATIONS = 10
    CACHE_EXPIRATION = 10
    NUMBER_OF_SCENES_PER_REQUEST = 10
    SCENES = pd.read_csv("data/GIS/landsat_scenes_clipped.csv").values
    CACHE = Cache(CACHE_EXPIRATION)
    COLD_STORAGE_HITS = run_simulation(
        SCENES, NUMBER_OF_REQUESTS, NUMBER_OF_SCENES_PER_REQUEST, CACHE
    )
    # Dataframe to store results
    results = pd.DataFrame(
        columns=["Cache Expiration", "Cold Storage Hits", "Cold Storage Hit Rate"]
    )
    for cache_expiration in range(1, 11):
        for number_of_scenes_per_request in range(1, 11):
            CACHE = Cache(cache_expiration)
            cold_storage_hits = run_simulation(
                SCENES, NUMBER_OF_REQUESTS, NUMBER_OF_SCENES_PER_REQUEST, CACHE
            )
            results = results.append(
                {
                    "Number of Requests": NUMBER_OF_REQUESTS,
                    "Cache Expiration": cache_expiration,
                    "number of scenes per request": NUMBER_OF_SCENES_PER_REQUEST,
                    "Cold Storage Hits": cold_storage_hits,
                    "Cold Storage Hit Rate": cold_storage_hits / NUMBER_OF_REQUESTS,
                },
                ignore_index=True,
            )

    for number_of_scenes_per_request in range(2, 10):
        for cache_expiration in range(1, 11):
            CACHE = Cache(cache_expiration)
            cold_storage_hits = run_simulation(
                SCENES, NUMBER_OF_REQUESTS, number_of_scenes_per_request, CACHE
            )
            results = results.append(
                {
                    "Number of Requests": NUMBER_OF_REQUESTS,
                    "Cache Expiration": cache_expiration,
                    "number of scenes per request": number_of_scenes_per_request,
                    "Cold Storage Hits": cold_storage_hits,
                    "Cold Storage Hit Rate": cold_storage_hits / NUMBER_OF_REQUESTS,
                },
                ignore_index=True,
            )

    results = results.sort_values(by=["Cold Storage Hit Rate"])
    results.to_csv("data/results.csv", index=False)

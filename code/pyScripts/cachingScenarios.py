import random
from scipy.spatial import KDTree
import pandas as pd


def ping_cache(scene_indicies, cache_expiration) -> list:
    """Return a list of scenes that are cached. Add missing scenes to cache"""
    cache = {}
    cached_scenes = []
    if cache_expiration == 0 and len(cache) > 0:
        cache.popitem()
        cache_expiration = 10

    for scene_index in scene_indicies:
        if scene_index in cache:
            cached_scenes.append(scene_index)
        elif cache_expiration > 0:
            cache[scene_index] = True

    cache_expiration -= 1

    return cached_scenes


def run_simulation(scenes, number_of_requests, scenes_per_request, cache_expiration):
    """Run the simulation and return the number of cold storage hits"""
    cache = {}
    cold_storage_hits = 0
    cache.clear()
    tree = KDTree(scenes)
    for request in range(number_of_requests):
        random_scene = random.choice(scenes)
        nearest_scene_indices = tree.query(random_scene, k=4)[1]
        requested_scenes = ping_cache(nearest_scene_indices, CACHE_EXPIRATION)
        if len(requested_scenes) < 4:
            cold_storage_hits += 1

    return cold_storage_hits


if __name__ == "__main__":
    NUMBER_OF_REQUESTS = 1000
    CACHE_EXPIRATION = 0
    SCENES_PER_REQUEST = random.randint(4, 4)  # 4 scenes per request
    # Load Scenes from csv into pandas dataframe
    SCENES = pd.read_csv("scenes.csv", header=None).values
    run_simulation(SCENES, NUMBER_OF_REQUESTS, SCENES_PER_REQUEST, CACHE_EXPIRATION)

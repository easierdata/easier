import random

number_of_requests = 1000
cache = {}
cache_expiration = 0


def ping_cache(scene_indicies) -> list:
    """Return a list of scenes that are cached. Add missing scnene to the cache"""
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


scenes = landsat_scenes_clipped_with_sectors[["PATH", "ROW"]].values
cold_storage_hits = 0
cache.clear()
tree = KDTree(scenes)
for request in range(number_of_requests):
    random_scene = random.choice(scenes)
    nearest_scene_indices = tree.query(random_scene, k=4)[1]
    requested_scenes = ping_cache(nearest_scene_indices, cache, cache_expiration)
    if len(requested_scenes) < 4:
        cold_storage_hits += 1


cold_storage_hits

import requests

# URLs to test
urls = [
    "http://localhost:50000/bafybeigoe4ss23hrahns7sbqus6tas4ovvnhupmrnrym5zluu2ssg5yj5u",
    "http://localhost:50000/QmZJ7G6DyrzU1XGkm9pXjQZPiX4Q7zJnV9PZsVvKjCSMVK",
    "http://localhost:50000/nonexistent_cid",
]

for url in urls:
    response = requests.get(url)
    print(
        f"GET {url} returned status code {response.status_code} and content:\n{response.text}\n"
    )

from flask import Flask, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory storage for contents
contents = {
    "bafybeigoe4ss23hrahns7sbqus6tas4ovvnhupmrnrym5zluu2ssg5yj5u": "Hi, I am Landsat data",
    "QmZJ7G6DyrzU1XGkm9pXjQZPiX4Q7zJnV9PZsVvKjCSMVK": "Hi, I am a fake CID",
}


@app.route("/<content_cid>", methods=["GET"])
def get_content(content_cid):
    content = contents.get(content_cid)
    if content is not None:
        return content, 200  # Return the content with a 200 status code
    else:
        abort(404)  # If the content was not found, return a 404 status code


if __name__ == "__main__":
    app.run(port=50000)

# BackTube

[BackTube](https://backtube.app) is a streaming app for music lovers who can create and follow playlists of their favorite songs from Youtube or Bandcamp.

There are 4 different repositories:
- [UI](https://github.com/chaos87/backtube-ui)
- [Backend API](https://github.com/chaos87/backtube-backend-api)
- [Stream API](https://github.com/chaos87/backtube-stream-api)
- Youtube Music Search API (this repository)

## Installation

Install dependencies using pip.

```bash
pip install -r requirements.txt
```

## Usage

Start the server

```bash
python wsgi.py
```

Example of API call using cURL

```bash
curl \
  -H 'Content-Type: application/json' \
  -X POST \
  -d '{"query": "nirvana"}' \
  http://localhost:5000/search/yt
```

## Endpoints

- [POST] /setup/yt: To be used if you want to provide authenticated headers with your queries.
- [POST] /search/yt: The Youtube Music Search endpoint (see the example above).

## Dependencies

- [Youtube Music API](https://github.com/sigma67/ytmusicapi)
- [Flask](https://flask.palletsprojects.com/en/1.1.x/)
- [Pandas](https://pandas.pydata.org/)
- [Flask CORS](https://flask-cors.readthedocs.io/en/latest/)
- [Fuzzywuzzy](https://github.com/seatgeek/fuzzywuzzy)


## Contributing
Please open an issue prior to submitting a pull request, so that we can discuss whether it makes sense to be implemented or not.
Feature ideas or bug reports are more than welcome!

## License
[MIT](https://choosealicense.com/licenses/mit/)

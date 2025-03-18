from pydantic import Json
from typing_extensions import Optional
from jokeapi import Jokes
from pydantic.main import BaseModel

class JokeModel(BaseModel):
    id: int
    joke: Optional[str]
    setup: Optional[str]
    delivery: Optional[str]


async def print_joke() -> JokeModel:
    j = await Jokes()  # Initialise the class
    joke = await j.get_joke(blacklist=['nsfw', 'religious', 'political', 'racist', 'sexist', 'explicit'])  # Retrieve a random joke
    return JokeModel(joke=joke.get("joke"), setup=joke.get("setup"), delivery=joke.get("delivery"), id=joke["id"])

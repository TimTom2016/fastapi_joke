from typing_extensions import Optional,List
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
from cache import SqliteCache
from pydantic import BaseModel
import random
from joke import JokeModel, print_joke
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
class CacheItem(BaseModel):
    value: str
    timeout: int | None = None


cache_instance = SqliteCache("./cache.db")

def get_cache():
    return cache_instance


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")


@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str):
    return templates.TemplateResponse(
        request=request, name="item.html", context={"id": id}
    )

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request, name="base.html"
    )

@app.post("/clicked", response_class=HTMLResponse)
async def clicked(request: Request):
    return templates.TemplateResponse(
        request=request, name="clicked.html"
    )

@app.get("/cache/{key}")
def get_cache_value(key: str, cache: SqliteCache = Depends(get_cache)):
    """ Retrieve value from cache """
    value = cache.get(key)
    return {"key": key, "value": value}

@app.post("/cache/{key}")
def set_cache_value(key: str, item: CacheItem, cache: SqliteCache = Depends(get_cache)):
    """ Store value in cache """
    cache.set(key, item.value, item.timeout)
    return {"message": "Value set successfully"}

@app.delete("/cache/{key}")
def delete_cache_value(key: str, cache: SqliteCache = Depends(get_cache)):
    """ Delete key from cache """
    cache.delete(key)
    return {"message": "Value deleted"}

@app.delete("/cache")
def clear_cache(cache: SqliteCache = Depends(get_cache)):
    """ Clear the entire cache """
    cache.clear()
    return {"message": "Cache cleared"}

@app.get("/joke")
async def get_joke(request: Request, cache: SqliteCache = Depends(get_cache)):
    jokes_dict: Optional[dict] = cache.get("jokes_dict")
    if jokes_dict is None:
        # Initialize cache
        joke = await print_joke()
        # Using joke's string representation as key
        jokes_dict = {joke.id: joke}
        cache.set("jokes_dict", jokes_dict, 3600)
        logger.info(f"Initialized jokes cache with first joke: {joke}")

    if random.random() < 0.5 and jokes_dict:
        # Use a joke from cache
        joke = random.choice(list(jokes_dict.values()))
        logger.info(f"Joke retrieved from cache: {joke}")
    else:
        # Get a new joke
        joke = await print_joke()

        # Check for duplicates using string representation
        if joke.id not in jokes_dict:
            jokes_dict[joke.id] = joke
            cache.set("jokes_dict", jokes_dict, 3600)
            logger.info(f"New unique joke added to cache: {joke}")
        else:
            logger.info(f"Joke already in cache, not adding duplicate: {joke}")

    return templates.TemplateResponse(
        request=request, name="joke.html", context={"joke": joke}
    )

"""Proxy server."""
# built-in
import os
# external
import httpx
import redis
import toml
import uvicorn
from fastapi import FastAPI, Response, Request

app = FastAPI()

CONFIG = toml.load("config.toml")
# connect to the Redis database
db = redis.StrictRedis(host=os.environ.get("REDIS_HOST", CONFIG['database']['REDIS_HOST']),
                       port=os.environ.get("REDIS_PORT", CONFIG['database']['REDIS_PORT']))


@app.api_route("/{path:path}", methods=["GET", "POST"])
async def proxy(request: Request, response: Response, path: str):
    """
    Proxy end point that will capture any requests under it's IP and
    will serve as a gatekeeper against IP that in the blacklist of IPs.
    """
    # read every request that coming under host ip
    async with httpx.AsyncClient() as client:
        proxy = await client.get(f"http://{CONFIG['servers']['client']}/{path}")
    # check if user's ip not in the black list of ips
    # currently Redis contains only ips from the black list
    if not db.exists(request.client.host):
        # redirect responce to the end destination - client's web-site
        response.body = proxy.content
        response.status_code = proxy.status_code
        # return client's response to the used
        return response
    # for ips listed in the black list it will return this string
    return "Access denied"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

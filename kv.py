import yaml
import aiohttp
from typing import Dict, Union, List

with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

url = config["storage"]["kv"]["url"]
token = config["storage"]["kv"]["token"]


async def get_data(id: Union[str, int]):
    async with aiohttp.ClientSession() as session:
        async with session.get(
                url=f"https://{url}/",
                headers={
                    "Accept": "application/json",
                    "Read-Token": str(token["read"]),
                    "Read-Key": str(id)
                }) as resp:

            return await resp.json()


async def save_data(id: Union[str, int], data: Union[Dict, str]):
    isDict = isinstance(data, Dict)
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=f"https://{url}/",
                headers={
                    "Content-Type": "application/json" if isDict else "text/plain",
                    "Write-Token": str(token["write"]),
                    "Write-Key": str(id)},
                json=data if isDict else None,
                data=data if not isDict else None
        ) as resp:
            return resp


async def delete_data(_id: Union[str, int]):
    async with aiohttp.ClientSession() as session:
        async with session.delete(
                url=f"https://{url}/",
                headers={
                    "Delete-Token": str(token["delete"]),
                    "Delete-Key": str(id)
                }) as resp:
            return resp

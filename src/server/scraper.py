"""
This module scrapes data from FairPrice's internal API.
"""
"""
import asyncio
import aiohttp
from utils import database
"""
import json
import requests

with open(
    "/Users/lohith/Desktop/Sec 3 stuff/Comp+/Python/Coursework/kichn/fairprice_categories.json",
    "r",
) as cats:
    fairprice_categories = json.load(cats)

sub_categories = []
for cat in fairprice_categories:
    for sub_cat in cat["menu"]:
        if "menu" in sub_cat:
            for sub_sub_cat in sub_cat["menu"]:
                temp = sub_sub_cat["url"]
                temp = temp.split("/")
                sub_categories.append(temp[-1])
        else:
            temp = sub_cat["url"]
            temp = temp.split("/")
            sub_categories.append(temp[-1])

categories = []
for i in sub_categories:
    print(i)
    res = requests.get(
        "https://website-api.omni.fairprice.com.sg/api/product/v2?url=" + i
    )
    res = res.json()
    try:
        print(
            res["data"]["product"][0]["primaryCategory"]["parentCategory"][
                "parentCategory"
            ]
        )
    except KeyError:
        print(res)

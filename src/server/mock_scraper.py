import requests
from modules.database import DatabaseClient

db = DatabaseClient("src/client/static", "server-store")
img = requests.get(
    "https://media.nedigital.sg/fairprice/fpol/media/images/product/L/47440_L1_20210827.jpg"
).content

p_id = db.create_default_product(
    "Apple",
    "Fruits",
    [],
    img,
)
print(p_id)

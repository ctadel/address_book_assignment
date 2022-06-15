from fastapi import FastAPI
from fastapi.responses import UJSONResponse
from sqlite3 import connect
from pydantic import BaseModel
from dataclasses import dataclass
import math
import logging

app = FastAPI()
db = connect("book_database.db")

try:
    cursor = db.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS addressbook(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                address TEXT,
                coordinateX FLOAT,
                coordinateY FLOAT
            )
        """)
except Exception as e:
    print(e)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S", filename="address_book.log")
logger = logging.getLogger(__name__)

@dataclass
class Cordinates:
    """
        This class is used to store the cordinates of a location.
    """
    latitude: float
    longitude: float

    def __repr__(self):
        return f"[{self.latitude}, {self.longitude}]"

    @staticmethod
    def getLatLong(cX, cY, radius):
      earth = 6371
      maxLat = ((cX + math.pi / 2) * 180) / math.pi
      minLat = ((cX - math.pi / 2) * 180) / math.pi
      maxLng = ((cY + (math.pi * radius) / earth) * 180) / math.pi
      minLng = ((cY - (math.pi * radius) / earth) * 180) / math.pi
      return Cordinates(minLat, minLng), Cordinates(maxLat, maxLng)

class AddressBook(BaseModel):
    name: str
    phone: str
    address: str
    coordinateX: float
    coordinateY: float

class SearchAddressBook(BaseModel):
    radius: int = 10 # 10km range
    latitude: float
    longitude: float

@app.get("/")
async def get_addressbook_list():
    """
        Get all the addressbook entries
    """
    query = "SELECT * FROM addressbook"
    data = cursor.execute(query).fetchall()
    logger.info(f"Get all the addressbook entries")
    return UJSONResponse(data, status_code=200)

@app.post("/search/")
async def search_addressbook_list(search: SearchAddressBook):
    """
        Search addressbook entries based on the given cordinates and radius
    """
    location = Cordinates(search.latitude, search.longitude)
    minLat, maxLat = Cordinates.getLatLong(location.latitude, location.longitude, search.radius)
    data = cursor.execute("select * from addressbook where coordinateX between ? and ? and coordinateY between ? and ?", (minLat.latitude, maxLat.latitude, minLat.longitude, maxLat.longitude)).fetchall()
    if not data:
        logger.info(f"No addressbook entries found in the given range {location}")
        return UJSONResponse({"message": "No data found"}, status_code=204)

    logger.info(f"Get all the addressbook entries in the given range {location}")
    return UJSONResponse({"data":data},status_code=200)

@app.get("/{id}/")
async def get_addressbook_list_by_id(id: int):
    """
        Get individual addressbook entry by id
    """
    query = "SELECT name,phone,address,coordinateX,coordinateY FROM addressbook WHERE id=?"
    data = cursor.execute(query, (id,)).fetchone()
    if not data:
        logger.info(f"No addressbook entry found with id {id}")
        return UJSONResponse({"message": "No data found"}, status_code=204)

    logger.info(f"Get addressbook entry with id {id}")
    return UJSONResponse({"data":data}, status_code=200)

@app.put("/")
async def add_addressbook_list(addressbook: AddressBook):
    """
        Add new addressbook entry
    """
    query = "INSERT INTO addressbook(name,phone,address,coordinateX,coordinateY) VALUES(?,?,?,?,?)"
    cursor.execute(query, (addressbook.name, addressbook.phone, addressbook.address, addressbook.coordinateX, addressbook.coordinateY))
    db.commit()
    logger.info(f"Added new addressbook entry {addressbook.dict()}")
    return UJSONResponse({"message": "SUCCESS"}, status_code=201)

@app.patch("/{id}/")
async def update_addressbook_list_by_id(id: int, addressbook: AddressBook):
    """
        Update addressbook entry by id
    """
    query = "UPDATE addressbook SET name=?,phone=?,address=?,coordinateX=?,coordinateY=? WHERE id=?"
    cursor.execute(query, (addressbook.name, addressbook.phone, addressbook.address, addressbook.coordinateX, addressbook.coordinateY, id))
    db.commit()
    logger.info(f"Updated addressbook entry with id {id}")
    return UJSONResponse({"message": "SUCCESS"}, status_code=200)

@app.delete("/{id}/")
async def delete_addressbook_list_by_id(id: int):
    """
        Delete addressbook entry by id
    """
    data = cursor.execute("SELECT * FROM addressbook WHERE id=?", (id,)).fetchone()

    if data is None:
        logger.info(f"No addressbook entry found with id {id}")
        return UJSONResponse({"message": "No data found"}, status_code=204)

    query = "DELETE FROM addressbook WHERE id=?"
    cursor.execute(query, (id,))
    db.commit()
    logger.info(f"Deleted addressbook entry with id {data}")
    return UJSONResponse({"message": "SUCCESS"}, status_code=200)

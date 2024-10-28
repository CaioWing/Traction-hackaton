from fastapi import FastAPI
import pymongo


myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["Gearing"]


app = FastAPI()


@app.get("/orderServices/{item_id}")
def read_item(item_id: int):
    mycol = mydb["serviceOrders"]
    x = mycol.find()
    return {"item_id": x}

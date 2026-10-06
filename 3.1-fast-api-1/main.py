from fastapi import FastAPI, Request
from pydantic import BaseModel
from datetime import datetime
import uvicorn

app = FastAPI()


объявления = []
id_shnik = 1


class Obj(BaseModel):
    zagolovok: str
    opisanie: str
    cena: float
    avtor: str


@app.post("/advertisement")
def sozdat_obyavlenie(obj: Obj):
    global id_shnik
    d = obj.dict()
    d["id"] = id_shnik
    d['date_sozdania'] = str(datetime.now())
    id_shnik = id_shnik + 1
    объявления.append(d)
    print("создали обьявление -> ", d)
    return d


@app.get("/advertisement/{obj_id}")
def poluchit_obyavlenie(obj_id: int):
    for i in объявления:
        if i["id"] == obj_id:
            return i
    return {"error": "нет такого обьявления("}


@app.patch("/advertisement/{obj_id}")
def patch_obyavlenie(obj_id: int, data: dict):
    for i in объявления:
        if i["id"] == obj_id:
            for key in data:
                i[key] = data[key]
            print("обновили", obj_id)
            return i
    return {"error": "нет такого обьявления("}


@app.delete("/advertisement/{obj_id}")
def delete_obyavlenie(obj_id: int):
    global объявления
    for i in объявления:
        if i["id"] == obj_id:
            объявления.remove(i)
            return {"status": "ok", "message": "удалили"}
    return {"error": "нет такого обьявления("}


@app.get("/advertisement")
def search_obyavlenie(request: Request):
    params = dict(request.query_params)
    if len(params) == 0:
        return объявления

    res = []
    for i in объявления:
        flag = 1
        for k in params.keys():
            if str(i.get(k)) != str(params[k]):
                flag = 0
        if flag == 1:
            res.append(i)
    return res


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)

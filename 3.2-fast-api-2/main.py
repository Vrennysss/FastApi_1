from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import uvicorn
import uuid

app = FastAPI()

# авторизация тут самая простая, без jwt и прочего, просто токен в словаре
# чтобы проверить - логинишься на /login, берешь token из ответа
# и дальше суешь его в заголовок "token" на все запросы где надо

# =========== ОБЪЯВЛЕНИЯ ===========
объявления = []
id_shnik = 1


class Obj(BaseModel):
    zagolovok: str
    opisanie: str
    cena: float


# =========== ЮЗЕРЫ ===========
users = []
id_shnik_user = 1

# тут лежат токены, ключ - сам токен, значение - чей он и когда сгорит
tokens = {}


class UserIn(BaseModel):
    login: str
    parol: str
    group: str = "user"  # по идее тут должно быть user или admin, но я не проверяю, не до этого


class LoginIn(BaseModel):
    login: str
    parol: str


def kto_zapros(request: Request):
    # достаем юзера по токену из хедера, если токена нет или он протух - просто None (анонимус)
    token = request.headers.get("token")
    if not token:
        return None
    info = tokens.get(token)
    if info is None:
        return None
    if datetime.now() > info["expires"]:
        del tokens[token]  # протух, удаляем чтоб не копилось мусора
        return None
    for u in users:
        if u["id"] == info["user_id"]:
            return u
    return None


@app.post("/login")
def login(data: LoginIn):
    for u in users:
        if u["login"] == data.login and u["parol"] == data.parol:
            token = uuid.uuid4().hex
            tokens[token] = {
                "user_id": u["id"],
                "expires": datetime.now() + timedelta(hours=48),
            }
            print("залогинился", u["login"], "токен", token)
            return {"token": token}
    raise HTTPException(status_code=401, detail="неверный логин или пароль")


@app.post("/user")
def create_user(data: UserIn):
    global id_shnik_user
    u = data.dict()
    u["id"] = id_shnik_user
    id_shnik_user += 1
    users.append(u)
    print("создали юзера", u)
    return u


@app.get("/user")
def get_all_users(request: Request):
    me = kto_zapros(request)
    if me is None:
        raise HTTPException(status_code=403, detail="нет прав")
    return users


@app.get("/user/{user_id}")
def get_user(user_id: int):
    for u in users:
        if u["id"] == user_id:
            return u
    return {"error": "нет такого юзера("}


@app.patch("/user/{user_id}")
def patch_user(user_id: int, data: dict, request: Request):
    me = kto_zapros(request)
    if me is None:
        raise HTTPException(status_code=403, detail="нет прав")

    for u in users:
        if u["id"] == user_id:
            if me["group"] != "admin" and me["id"] != user_id:
                raise HTTPException(status_code=403, detail="нет прав")
            for key in data:
                u[key] = data[key]
            return u
    return {"error": "нет такого юзера("}


@app.delete("/user/{user_id}")
def delete_user(user_id: int, request: Request):
    me = kto_zapros(request)
    if me is None:
        raise HTTPException(status_code=403, detail="нет прав")

    for u in users:
        if u["id"] == user_id:
            if me["group"] != "admin" and me["id"] != user_id:
                raise HTTPException(status_code=403, detail="нет прав")
            users.remove(u)
            return {"status": "ok", "message": "удалили"}
    return {"error": "нет такого юзера("}


# =========== ОБЪЯВЛЕНИЯ (роуты) ===========
@app.post("/advertisement")
def sozdat_obyavlenie(obj: Obj, request: Request):
    global id_shnik
    me = kto_zapros(request)
    if me is None:
        raise HTTPException(status_code=403, detail="нет прав, залогинься")

    d = obj.dict()
    d["id"] = id_shnik
    d["avtor"] = me["login"]
    d["owner_id"] = me["id"]
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
def patch_obyavlenie(obj_id: int, data: dict, request: Request):
    me = kto_zapros(request)
    if me is None:
        raise HTTPException(status_code=403, detail="нет прав, залогинься")

    for i in объявления:
        if i["id"] == obj_id:
            if me["group"] != "admin" and i["owner_id"] != me["id"]:
                raise HTTPException(status_code=403, detail="это не твое обьявление")
            for key in data:
                i[key] = data[key]
            print("обновили", obj_id)
            return i
    return {"error": "нет такого обьявления("}


@app.delete("/advertisement/{obj_id}")
def delete_obyavlenie(obj_id: int, request: Request):
    me = kto_zapros(request)
    if me is None:
        raise HTTPException(status_code=403, detail="нет прав, залогинься")

    global объявления
    for i in объявления:
        if i["id"] == obj_id:
            if me["group"] != "admin" and i["owner_id"] != me["id"]:
                raise HTTPException(status_code=403, detail="это не твое обьявление")
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

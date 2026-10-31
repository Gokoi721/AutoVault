from contextlib import asynccontextmanager
from pathlib import Path
import shutil
import uuid

from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine, String, Integer, Float, Text, select, or_, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{(BASE_DIR / 'cars.db').as_posix()}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class Car(Base):
    __tablename__ = "cars"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    brand: Mapped[str] = mapped_column(String(80), index=True)
    model: Mapped[str] = mapped_column(String(100), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    price: Mapped[float] = mapped_column(Float, index=True)
    mileage: Mapped[int] = mapped_column(Integer, default=0)
    fuel: Mapped[str] = mapped_column(String(30), default="Бензин")
    transmission: Mapped[str] = mapped_column(String(30), default="Автомат")
    body_type: Mapped[str] = mapped_column(String(40), default="Седан")
    color: Mapped[str] = mapped_column(String(50), default="Чорний")
    engine_volume: Mapped[float] = mapped_column(Float, default=2.0)
    description: Mapped[str] = mapped_column(Text, default="")
    image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[str] = mapped_column(String(30), default="")

class CarImage(Base):
    """Додаткові фото для галереї авто."""
    __tablename__ = "car_images"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    car_id: Mapped[int] = mapped_column(Integer, index=True)
    filename: Mapped[str] = mapped_column(String(255))

Base.metadata.create_all(bind=engine)

# Демо-каталог: 10 прикладів авто для першого запуску.
# Значення цін і пробігу наведені для демонстрації, а фото завантажуються з зовнішніх URL.
DEMO_CARS = [
    {
        "brand": "BMW", "model": "M4 Competition", "year": 2023, "price": 78900,
        "mileage": 22000, "engine_volume": 3.0, "fuel": "Бензин", "transmission": "Автомат",
        "body_type": "Купе", "color": "Синій",
        "image": "https://commons.wikimedia.org/wiki/Special:FilePath/2024_BMW_M4_%28G82%29_Competition_DSC_7856.jpg?width=1200",
        "description": "Спортивне купе BMW M4 Competition з 3,0-літровим двигуном, агресивним дизайном та преміальним салоном. Демонстраційна пропозиція каталогу."
    },
    {
        "brand": "Mercedes-Benz", "model": "AMG GT", "year": 2024, "price": 139500,
        "mileage": 8000, "engine_volume": 4.0, "fuel": "Бензин", "transmission": "Автомат",
        "body_type": "Купе", "color": "Сріблястий",
        "image": "https://paultan.org/image/2023/08/2024-Mercedes-AMG-GT-debut-35.jpg",
        "description": "Потужне Mercedes-AMG GT у сріблястому кольорі. Спортивний силует, виразна решітка радіатора та комфортний салон. Дані для прикладу."
    },
    {
        "brand": "Audi", "model": "RS7 Sportback", "year": 2023, "price": 112000,
        "mileage": 17000, "engine_volume": 4.0, "fuel": "Бензин", "transmission": "Автомат",
        "body_type": "Ліфтбек", "color": "Синій",
        "image": "https://www.planetcarsz.com/img/carros/galeria/2024/01/audi-rs-7-sportback-performance-uk-version-2023-051-20240126100323-1280x925.jpg",
        "description": "Audi RS7 Sportback поєднує практичність п'ятидверного кузова з динамікою спортивного автомобіля та повним набором сучасних технологій."
    },
    {
        "brand": "Porsche", "model": "911 Carrera", "year": 2022, "price": 119000,
        "mileage": 24000, "engine_volume": 3.0, "fuel": "Бензин", "transmission": "Робот",
        "body_type": "Купе", "color": "Сріблястий",
        "image": "https://images.finder.porsche.com/3102afa9-3261-4fad-93d9-0b16335318bf/960",
        "description": "Класичне Porsche 911 Carrera зі сріблястим кузовом, характерним дизайном та орієнтацією на точне керування. Демонстраційні характеристики."
    },
    {
        "brand": "Toyota", "model": "GR Supra", "year": 2023, "price": 54000,
        "mileage": 11000, "engine_volume": 3.0, "fuel": "Бензин", "transmission": "Автомат",
        "body_type": "Купе", "color": "Червоний",
        "image": "https://www.earnhardttoyota.com/assets/stock/ColorMatched_01/Transparent/640/cc_2022TOC13_01_640/cc_2022TOC130004_01_640_D05.png",
        "description": "Компактне спортивне купе Toyota GR Supra в яскравому червоному кольорі. Чудовий варіант для тих, хто цінує спортивний характер."
    },
    {
        "brand": "Nissan", "model": "GT-R", "year": 2021, "price": 116000,
        "mileage": 30000, "engine_volume": 3.8, "fuel": "Бензин", "transmission": "Робот",
        "body_type": "Купе", "color": "Білий",
        "image": "https://platform.cstatic-images.com/in/v2/stock_photos/84a03a66-507f-46a3-bedb-e9457599f41b/1ea92263-8a97-4543-b75e-22881458723c.png",
        "description": "Nissan GT-R із повним приводом, впізнаваним силуетом і потужним 3,8-літровим двигуном. Дані та ціна наведені для демонстрації."
    },
    {
        "brand": "Ford", "model": "Mustang GT", "year": 2022, "price": 46900,
        "mileage": 26000, "engine_volume": 5.0, "fuel": "Бензин", "transmission": "Механіка",
        "body_type": "Купе", "color": "Чорний",
        "image": "https://images.dealersync.com/2074/Photos/1133802/2024051602152586672_image-5.jpg?_=0348ced426fafefc820cce0e9e5dcc546f30f162",
        "description": "Ford Mustang GT у чорному кольорі з атмосферним V8. Виразний маслкар із класичними спортивними пропорціями."
    },
    {
        "brand": "Lamborghini", "model": "Huracán EVO", "year": 2022, "price": 239000,
        "mileage": 9500, "engine_volume": 5.2, "fuel": "Бензин", "transmission": "Робот",
        "body_type": "Купе", "color": "Жовтий",
        "image": "https://www.sportovnivozy.cz/auta/200562/v/e1-lamborghini-huracan-evo-v10-awd-ceramic-car-2022.jpg",
        "description": "Lamborghini Huracán EVO — яскравий суперкар із двигуном V10, низьким кузовом та виразним жовтим забарвленням."
    },
    {
        "brand": "Tesla", "model": "Model S", "year": 2023, "price": 69900,
        "mileage": 14000, "engine_volume": 0.0, "fuel": "Електро", "transmission": "Автомат",
        "body_type": "Седан", "color": "Червоний",
        "image": "https://platform.cstatic-images.com/xlarge/in/v2/stock_photos/d5c757a0-71e4-46ff-abea-d7304edfb762/bb9f256f-f7c8-415e-99a9-8d5bcea46fdb.png",
        "description": "Електричний седан Tesla Model S із мінімалістичним салоном, великим запасом простору та сучасними мультимедійними можливостями."
    },
    {
        "brand": "Land Rover", "model": "Range Rover Sport", "year": 2023, "price": 87900,
        "mileage": 21000, "engine_volume": 3.0, "fuel": "Дизель", "transmission": "Автомат",
        "body_type": "Позашляховик", "color": "Червоний",
        "image": "https://img.stcrm.it/images/34377428/1200x/rrs_23my_10_fe_194_glhd_100522_risultato-jpg.jpg",
        "description": "Range Rover Sport — преміальний позашляховик із просторим салоном, високою посадкою та комфортом для щоденних поїздок."
    },
]

def seed_demo_cars():
    """Додає всі відсутні демо-картки, навіть якщо в базі вже є власні авто."""
    from datetime import datetime
    with SessionLocal() as db:
        existing_keys = {(brand, model) for brand, model in db.execute(select(Car.brand, Car.model)).all()}
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        missing = []
        for item in DEMO_CARS:
            key = (item["brand"], item["model"])
            if key not in existing_keys:
                missing.append(Car(**{**item, "created_at": now}))
                existing_keys.add(key)
        if missing:
            db.add_all(missing)
            db.commit()
            print(f"AutoVault: додано демо-карток: {len(missing)}")
        else:
            print("AutoVault: усі 10 демо-карток уже є в базі.")
        total = db.scalar(select(func.count()).select_from(Car)) or 0
        print(f"AutoVault: у базі всього автомобілів: {total}")

seed_demo_cars()

app = FastAPI(title="AutoVault — автомобільний каталог")
app.add_middleware(SessionMiddleware, secret_key="change-this-secret-key-before-deployment")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def img_src(name):
    if not name:
        return ""
    return name if name.startswith(("http://", "https://")) else f"/static/uploads/{name}"

def car_badges(car):
    """До двох бейджів для картки: (клас, текст, іконка)."""
    from datetime import datetime
    found = []
    if car.year >= datetime.now().year - 3:
        found.append(("new", "Свіжий", "spark"))
    if car.price >= 100000:
        found.append(("prem", "Преміум", "star"))
    if car.fuel in ("Електро", "Гібрид"):
        found.append(("ev", car.fuel, "bolt"))
    if 0 < car.mileage < 15000:
        found.append(("low", "Малий пробіг", "road"))
    return found[:2]

def _asset_version():
    # версія для /static/style.css і /static/app.js: змінюється при зміні файлів, тому кеш браузера не заважає
    try:
        return int(max((BASE_DIR / "static" / n).stat().st_mtime for n in ("style.css", "app.js")))
    except OSError:
        return 1

templates.env.globals["asset_v"] = _asset_version()
templates.env.globals["img_src"] = img_src
templates.env.globals["badges"] = car_badges

def db_session():
    return SessionLocal()

def current_user(request: Request):
    return request.session.get("user")

def render(request: Request, template: str, context: dict):
    context.update({"request": request, "user": current_user(request)})
    return templates.TemplateResponse(request=request, name=template, context=context)

@app.get("/")
def home(request: Request, q: str = "", brand: str = "", fuel: str = "", transmission: str = "",
         min_price: str = "", max_price: str = "", sort: str = "newest"):
    with db_session() as db:
        stmt = select(Car)
        if q.strip():
            term = f"%{q.strip()}%"
            stmt = stmt.where(or_(Car.brand.ilike(term), Car.model.ilike(term), Car.description.ilike(term)))
        if brand:
            stmt = stmt.where(Car.brand == brand)
        if fuel:
            stmt = stmt.where(Car.fuel == fuel)
        if transmission:
            stmt = stmt.where(Car.transmission == transmission)
        try:
            if min_price: stmt = stmt.where(Car.price >= float(min_price))
            if max_price: stmt = stmt.where(Car.price <= float(max_price))
        except ValueError:
            pass
        if sort == "price_asc": stmt = stmt.order_by(Car.price.asc())
        elif sort == "price_desc": stmt = stmt.order_by(Car.price.desc())
        elif sort == "year_desc": stmt = stmt.order_by(Car.year.desc())
        else: stmt = stmt.order_by(Car.id.desc())
        cars = db.scalars(stmt).all()
        brands = db.scalars(select(Car.brand).distinct().order_by(Car.brand)).all()
        total = db.scalar(select(func.count()).select_from(Car)) or 0
        with_photo = db.scalars(select(Car).where(Car.image.is_not(None)).order_by(Car.price.desc())).all()
        # прозорі PNG із зовнішніх сайтів погано виглядають на фоні hero, тому беремо інші
        hero_cars = [c for c in with_photo
                     if not (c.image.startswith("http") and c.image.lower().split("?")[0].endswith(".png"))][:4]
    return render(request, "index.html", {"cars": cars, "hero_cars": hero_cars, "q": q, "brand": brand, "fuel": fuel,
        "transmission": transmission, "min_price": min_price, "max_price": max_price,
        "sort": sort, "brands": brands, "total": total})

@app.get("/cars/{car_id:int}")
def car_detail(request: Request, car_id: int):
    with db_session() as db:
        car = db.get(Car, car_id)
        extra = db.scalars(select(CarImage).where(CarImage.car_id == car_id).order_by(CarImage.id)).all() if car else []
    if not car: raise HTTPException(404, "Автомобіль не знайдено")
    gallery = ([img_src(car.image)] if car.image else []) + [img_src(e.filename) for e in extra]
    return render(request, "detail.html", {"car": car, "gallery": gallery})

@app.get("/cars/new")
def new_car(request: Request):
    if not current_user(request): return RedirectResponse("/login?next=/cars/new", status_code=303)
    return render(request, "form.html", {"car": None, "mode": "new"})

@app.post("/cars/new")
async def create_car(request: Request, brand: str = Form(...), model: str = Form(...),
    year: int = Form(...), price: float = Form(...), mileage: int = Form(0),
    fuel: str = Form("Бензин"), transmission: str = Form("Автомат"),
    body_type: str = Form("Седан"), color: str = Form("Чорний"),
    engine_volume: float = Form(2.0), description: str = Form(""),
    image: UploadFile | None = File(None), gallery: list[UploadFile] = File(default=[])):
    require_login(request)
    validate_car(brand, model, year, price, mileage, engine_volume)
    image_name = save_image(image)
    from datetime import datetime
    with db_session() as db:
        car = Car(brand=brand.strip(), model=model.strip(), year=year, price=price, mileage=mileage,
            fuel=fuel, transmission=transmission, body_type=body_type, color=color,
            engine_volume=engine_volume, description=description.strip(), image=image_name,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M"))
        db.add(car); db.commit(); db.refresh(car)
        car_id = car.id
        save_gallery(db, car_id, gallery)
        db.commit()
    return RedirectResponse(f"/cars/{car_id}", status_code=303)

@app.get("/cars/{car_id}/edit")
def edit_car_page(request: Request, car_id: int):
    require_login(request)
    with db_session() as db:
        car = db.get(Car, car_id)
        extra = db.scalars(select(CarImage).where(CarImage.car_id == car_id).order_by(CarImage.id)).all()
    if not car: raise HTTPException(404, "Автомобіль не знайдено")
    return render(request, "form.html", {"car": car, "mode": "edit", "extra": extra})

@app.post("/cars/{car_id}/edit")
async def update_car(request: Request, car_id: int, brand: str = Form(...), model: str = Form(...),
    year: int = Form(...), price: float = Form(...), mileage: int = Form(0),
    fuel: str = Form("Бензин"), transmission: str = Form("Автомат"),
    body_type: str = Form("Седан"), color: str = Form("Чорний"),
    engine_volume: float = Form(2.0), description: str = Form(""),
    image: UploadFile | None = File(None), gallery: list[UploadFile] = File(default=[]),
    remove_images: list[int] = Form(default=[])):
    require_login(request)
    validate_car(brand, model, year, price, mileage, engine_volume)
    image_name = save_image(image)
    with db_session() as db:
        car = db.get(Car, car_id)
        if not car: raise HTTPException(404, "Автомобіль не знайдено")
        car.brand=brand.strip(); car.model=model.strip(); car.year=year; car.price=price
        car.mileage=mileage; car.fuel=fuel; car.transmission=transmission; car.body_type=body_type
        car.color=color; car.engine_volume=engine_volume; car.description=description.strip()
        if image_name:
            delete_image(car.image)
            car.image=image_name
        if remove_images:
            for im in db.scalars(select(CarImage).where(CarImage.car_id == car_id, CarImage.id.in_(remove_images))).all():
                delete_image(im.filename)
                db.delete(im)
        save_gallery(db, car_id, gallery)
        db.commit()
    return RedirectResponse(f"/cars/{car_id}", status_code=303)

@app.post("/cars/{car_id}/delete")
def delete_car(request: Request, car_id: int):
    require_login(request)
    with db_session() as db:
        car = db.get(Car, car_id)
        if not car: raise HTTPException(404, "Автомобіль не знайдено")
        delete_image(car.image)
        for im in db.scalars(select(CarImage).where(CarImage.car_id == car_id)).all():
            delete_image(im.filename)
            db.delete(im)
        db.delete(car); db.commit()
    return RedirectResponse("/", status_code=303)

@app.get("/login")
def login_page(request: Request, next: str = "/"):
    return render(request, "login.html", {"error": "", "next": next})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), next: str = Form("/")):
    # Demo login for local development. Change these credentials before deploying.
    if username == "admin" and password == "AutoVault2026!":
        request.session["user"] = username
        return RedirectResponse(next if next.startswith("/") and not next.startswith("//") else "/", status_code=303)
    return render(request, "login.html", {"error": "Неправильний логін або пароль.", "next": next})

@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

def require_login(request: Request):
    if not current_user(request):
        raise HTTPException(status_code=401, detail="Увійдіть в систему, щоб керувати каталогом.")

def validate_car(brand, model, year, price, mileage, engine_volume):
    from datetime import datetime
    if not brand.strip() or not model.strip(): raise HTTPException(400, "Марка та модель обов'язкові")
    if year < 1886 or year > datetime.now().year + 1: raise HTTPException(400, "Некоректний рік випуску")
    if price < 0 or mileage < 0 or engine_volume < 0: raise HTTPException(400, "Числові значення не можуть бути від'ємними")

def save_image(image: UploadFile | None):
    if not image or not image.filename: return None
    ext = Path(image.filename).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(400, "Дозволені зображення JPG, PNG або WEBP")
    filename = f"{uuid.uuid4().hex}{ext}"
    with (UPLOAD_DIR / filename).open("wb") as out:
        shutil.copyfileobj(image.file, out)
    return filename

def save_gallery(db, car_id, files):
    for f in files or []:
        name = save_image(f)
        if name:
            db.add(CarImage(car_id=car_id, filename=name))

def delete_image(filename):
    if filename:
        path = UPLOAD_DIR / Path(filename).name
        if path.exists(): path.unlink()

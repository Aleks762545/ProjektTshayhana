from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import dishes, orders, search, admin, categories, tags, ingredients
from app.api.routes.guests import router as guests
from app.api.routes.news import router as news
from app.api.routes.images import router as uploads
from app.api.routes.ai_chat import router as ai_chat

app = FastAPI(title=settings['app']['name'])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # можно ограничить домены в prod
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dishes, prefix='/api')
app.include_router(orders, prefix='/api')
app.include_router(search, prefix='/api')
app.include_router(admin, prefix='/api')
app.include_router(categories, prefix='/api')
app.include_router(tags, prefix='/api')
app.include_router(ingredients, prefix='/api')
app.include_router(guests, prefix="/api")
app.include_router(news, prefix="/api")
app.include_router(uploads, prefix="/api")
app.include_router(ai_chat, prefix='/api')

@app.get('/api/health')
def health():
    return {'status':'ok'}

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Путь к фронту
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
FRONTEND_DIR = os.path.abspath(FRONTEND_DIR)

# Раздача общей статики (js, css, images)
JS_DIR = os.path.join(FRONTEND_DIR, "js")
CSS_DIR = os.path.join(FRONTEND_DIR, "css")
PAGES_DIR = os.path.join(FRONTEND_DIR, "pages")

app.mount("/js", StaticFiles(directory=JS_DIR), name="js")
app.mount("/css", StaticFiles(directory=CSS_DIR), name="css")
app.mount("/pages", StaticFiles(directory=PAGES_DIR), name="pages")

# --- Админка ---
ADMIN_DIR = os.path.join(FRONTEND_DIR, "admin")
ADMIN_HTML_DIR = os.path.join(ADMIN_DIR, "html")
ADMIN_JS_DIR = os.path.join(ADMIN_DIR, "js")
ADMIN_CSS_DIR = os.path.join(ADMIN_DIR, "css")

app.mount("/admin/js", StaticFiles(directory=ADMIN_JS_DIR), name="admin-js")
app.mount("/admin/css", StaticFiles(directory=ADMIN_CSS_DIR), name="admin-css")

@app.get("/admin")
def serve_admin_index():
    index_path = os.path.join(ADMIN_HTML_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "admin index.html not found"}

@app.get("/admin/{page}")
def serve_admin_pages(page: str):
    requested = os.path.join(ADMIN_HTML_DIR, f"{page}.html")
    if os.path.isfile(requested):
        return FileResponse(requested)
    return {"error": f"{page}.html not found"}

# --- Основной фронт ---
@app.get("/")
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "index.html not found"}

@app.get("/{full_path:path}")
def serve_static_routes(full_path: str):
    requested = os.path.join(FRONTEND_DIR, full_path)

    if os.path.isfile(requested):
        return FileResponse(requested)

    if os.path.isdir(requested):
        index_file = os.path.join(requested, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)

    fallback = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(fallback):
        return FileResponse(fallback)

    return {"error": "Not found"}

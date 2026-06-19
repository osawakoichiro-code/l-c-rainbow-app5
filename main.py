from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from google.cloud import storage

from draw_rainbow1_2 import draw_rainbow

from datetime import datetime
import json
import os


# ============================================
# FastAPI
# ============================================

app = FastAPI()


# ============================================
# templates
# ============================================

templates = Jinja2Templates(
    directory="templates"
)


# ============================================
# static
# ============================================

if not os.path.exists("static"):

    os.makedirs("static")


app.mount(

    "/static",

    StaticFiles(directory="static"),

    name="static"

)


# ============================================
# Cloud Storage
# ============================================

BUCKET_NAME = "carreer-life-rainbow"

storage_client = storage.Client()


# ============================================
# Top Page
# ============================================

@app.get("/", response_class=HTMLResponse)

async def home(request: Request):

    return templates.TemplateResponse(

        "index_1_2.html",

        {

            "request": request

        }

    )


# ============================================
# Health Check
# ============================================

@app.get("/health")

async def health():

    return {

        "status": "ok"

    }


# ============================================
# Save JSON + Draw Rainbow
# ============================================

@app.post("/save")

async def save_json(data: dict):

    try:

        # ----------------------------------

        # timestamp

        # ----------------------------------

        timestamp = datetime.now().strftime(

            "%Y%m%d_%H%M%S"

        )


        # ----------------------------------

        # JSON保存

        # ----------------------------------

        json_filename = (

            f"data/"

            f"rainbow_{timestamp}.json"

        )


        bucket = storage_client.bucket(

            BUCKET_NAME

        )


        blob = bucket.blob(

            json_filename

        )


        json_string = json.dumps(

            data,

            ensure_ascii=False,

            indent=2

        )


        blob.upload_from_string(

            json_string,

            content_type="application/json"

        )


        # ----------------------------------

        # PNG生成

        # Cloud Runでは/tmpを使う

        # ----------------------------------

        png_local = (

            f"/tmp/"

            f"rainbow_{timestamp}.png"

        )


        draw_rainbow(

            data,

            png_local

        )


        # ----------------------------------

        # PNGアップロード

        # ----------------------------------

        png_filename = (

            f"image/"

            f"rainbow_{timestamp}.png"

        )


        blob_png = bucket.blob(

            png_filename

        )


        blob_png.upload_from_filename(

            png_local,

            content_type="image/png"

        )


        # ----------------------------------

        # 公開URL

        # （公開バケットの場合）

        # ----------------------------------

        image_url = (

            "https://storage.googleapis.com/"

            f"{BUCKET_NAME}/"

            f"{png_filename}"

        )


        return {

            "status":

                "success",

            "json":

                json_filename,

            "image":

                png_filename,

            "image_url":

                image_url

        }


    except Exception as e:


        return JSONResponse(

            status_code=500,

            content={

                "status":

                    "error",

                "message":

                    str(e)

            }

        )


# ============================================
# Local Run
# ============================================

if __name__ == "__main__":

    import uvicorn


    uvicorn.run(

        "main:app",

        host="0.0.0.0",

        port=8080,

        reload=True

    )

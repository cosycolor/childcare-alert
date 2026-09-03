import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print("=======================================================")
    print("[Childcare Program Alert Service] Server Starting...")
    print(f"Web URL: http://{host}:{port}")
    print("=======================================================")
    uvicorn.run("app.main:app", host=host, port=port, reload=False if os.environ.get("PORT") else True)



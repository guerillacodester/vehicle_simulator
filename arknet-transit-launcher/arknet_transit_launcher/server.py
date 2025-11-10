"""
Simple FastAPI app factory for arknet-transit-launcher.
This is a starter stub; the real server will import service_manager and adapters.
"""
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="ArkNet Transit Launcher")

    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "arknet-transit-launcher"}

    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(create_app(), host="0.0.0.0", port=7000)

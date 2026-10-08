
import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState

from utils.db_connection import engine, Base
from utils.config_env import ConfigEnv
from utils.logger import logger
from services.task.agent import agent_app
from routes.task import router


# --------------------------------------------------
# Configuration
# --------------------------------------------------

settings = ConfigEnv()

APP_NAME = "c4scale AI-ML-Management App Service"
APP_VERSION = "1.0.0"

ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "http://localhost:3000",
]

MAX_MESSAGE_SIZE = 8192


# --------------------------------------------------
# Application Lifecycle
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")

    # Use Alembic migrations in production.
    # Do not create tables automatically on startup.
    # Base.metadata.create_all(bind=engine)

    yield

    logger.info("Shutting down application")
    engine.dispose()


# --------------------------------------------------
# FastAPI Initialization
# --------------------------------------------------

app = FastAPI(
    title=APP_NAME,
    description="APIs for c4scale AI-ML Management",
    version=APP_VERSION,
    lifespan=lifespan,
)


# --------------------------------------------------
# CORS Middleware
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# --------------------------------------------------
# API Routes
# --------------------------------------------------

app.include_router(router)


@app.get("/health", tags=["Health Check"])
async def health_check():
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


# --------------------------------------------------
# WebSocket Chat
# --------------------------------------------------

@app.websocket("/chat")
async def chat_endpoint(websocket: WebSocket):

    # Validate browser origin.
    origin = websocket.headers.get("origin")

    if origin not in ALLOWED_ORIGINS:
        await websocket.close(code=1008)
        return

    # TODO: Authenticate and authorize the user
    # before accepting the connection.

    await websocket.accept()

    thread_id = str(uuid.uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id,
        },
        "recursion_limit": 25,
    }

    logger.info(
        "WebSocket connected | thread_id=%s",
        thread_id,
    )

    try:
        await websocket.send_json({
            "type": "connected",
            "thread_id": thread_id,
            "message": "Task Agent connected",
        })

        while True:

            # Receive client message
            message = await websocket.receive_text()

            if not message.strip():
                await websocket.send_json({
                    "type": "error",
                    "message": "Message cannot be empty",
                })
                continue

            if len(message.encode("utf-8")) > MAX_MESSAGE_SIZE:
                await websocket.close(
                    code=1009,
                    reason="Message too large",
                )
                break

            try:
                previous_message_id = None

                async for event in agent_app.astream(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": message,
                            }
                        ]
                    },
                    config=config,
                    stream_mode="values",
                ):

                    messages = event.get("messages", [])

                    if not messages:
                        continue

                    last_message = messages[-1]

                    if getattr(last_message, "type", None) != "ai":
                        continue

                    content = getattr(
                        last_message,
                        "content",
                        None,
                    )

                    if not isinstance(content, str) or not content:
                        continue

                    message_id = getattr(
                        last_message,
                        "id",
                        None,
                    )

                    if (
                        message_id is not None
                        and message_id == previous_message_id
                    ):
                        continue

                    previous_message_id = message_id

                    await websocket.send_json({
                        "type": "message",
                        "content": content,
                    })

                await websocket.send_json({
                    "type": "done",
                })

            except WebSocketDisconnect:
                raise

            except Exception:
                logger.exception(
                    "Agent execution failed | thread_id=%s",
                    thread_id,
                )

                await websocket.send_json({
                    "type": "error",
                    "message": "Unable to process your request",
                })

    except WebSocketDisconnect:
        logger.info(
            "WebSocket disconnected | thread_id=%s",
            thread_id,
        )

    except Exception:
        logger.exception(
            "WebSocket failure | thread_id=%s",
            thread_id,
        )

        if websocket.application_state == WebSocketState.CONNECTED:
            await websocket.close(code=1011)

    finally:
        logger.info(
            "WebSocket session ended | thread_id=%s",
            thread_id,
        )

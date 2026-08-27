"""Composicao da aplicacao FastAPI."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from gra_awards.api.routes import router
from gra_awards.config import DEFAULT_CSV_PATH
from gra_awards.infra.csv_loader import load_movies
from gra_awards.infra.database import create_connection

logger = logging.getLogger(__name__)


def create_app(csv_path: Path | None = None) -> FastAPI:

    source = csv_path or DEFAULT_CSV_PATH

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
       
        connection = create_connection()
        movie_count = load_movies(connection, source)
        logger.info("Carregados %s filmes de %s", movie_count, source)

        app.state.connection = connection
        try:
            yield
        finally:
            connection.close()

    app = FastAPI(
        title="Golden Raspberry Awards - Pior Filme",
        description=(
            "API RESTful para leitura da lista de indicados e vencedores da "
            "categoria Pior Filme do Golden Raspberry Awards."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )
    app.include_router(router)
    return app


app = create_app()

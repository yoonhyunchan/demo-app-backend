import os
from typing import Optional

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from sqlalchemy import create_engine, Integer, String, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv


class Base(DeclarativeBase):
    pass


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title, "completed": self.completed}


def create_app() -> Flask:
    load_dotenv()

    app = Flask(__name__)

    database_url = os.getenv(
        "DATABASE_URL",
        # Default for local dev; replace via .env for real Postgres
        "postgresql+psycopg2://todo_user:password@localhost:5432/todo_db",
    )

    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    CORS(app, origins=[o.strip() for o in cors_origins.split(",") if o.strip()])

    engine = create_engine(database_url, echo=False, pool_pre_ping=True)
    SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

    # Create tables on startup
    Base.metadata.create_all(engine)

    @app.teardown_appcontext
    def remove_session(_exc: Optional[BaseException]) -> None:
        SessionLocal.remove()

    @app.get("/api/health")
    def health() -> tuple:
        return jsonify({"status": "ok"}), 200

    @app.get("/api/todos")
    def list_todos():
        session = SessionLocal()
        todos = session.query(Todo).order_by(Todo.id.desc()).all()
        return jsonify([t.to_dict() for t in todos])

    @app.post("/api/todos")
    def create_todo():
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        if not title:
            abort(400, description="title is required")
        session = SessionLocal()
        todo = Todo(title=title, completed=False)
        try:
            session.add(todo)
            session.commit()
            session.refresh(todo)
            return jsonify(todo.to_dict()), 201
        except SQLAlchemyError as e:
            session.rollback()
            abort(500, description=str(e))

    @app.patch("/api/todos/<int:todo_id>")
    def update_todo(todo_id: int):
        data = request.get_json(silent=True) or {}
        session = SessionLocal()
        todo: Optional[Todo] = session.get(Todo, todo_id)
        if not todo:
            abort(404, description="todo not found")
        if "title" in data:
            new_title = (data.get("title") or "").strip()
            if not new_title:
                abort(400, description="title cannot be empty")
            todo.title = new_title
        if "completed" in data:
            todo.completed = bool(data.get("completed"))
        try:
            session.add(todo)
            session.commit()
            session.refresh(todo)
            return jsonify(todo.to_dict())
        except SQLAlchemyError as e:
            session.rollback()
            abort(500, description=str(e))

    @app.delete("/api/todos/<int:todo_id>")
    def delete_todo(todo_id: int):
        session = SessionLocal()
        todo: Optional[Todo] = session.get(Todo, todo_id)
        if not todo:
            abort(404, description="todo not found")
        try:
            session.delete(todo)
            session.commit()
            return ("", 204)
        except SQLAlchemyError as e:
            session.rollback()
            abort(500, description=str(e))

    return app


app = create_app()



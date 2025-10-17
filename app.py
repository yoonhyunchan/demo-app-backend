import os
from typing import Optional
import time

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from sqlalchemy import create_engine, Integer, String, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

from logging_config import setup_logging, get_logger


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

    # 로깅 초기화
    setup_logging(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE", "logs/app.log")
    )
    
    logger = get_logger("todo_app")
    logger.info("Todo 애플리케이션이 시작됩니다")

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
    logger.info("데이터베이스 테이블이 생성되었습니다")

    @app.teardown_appcontext
    def remove_session(_exc: Optional[BaseException]) -> None:
        SessionLocal.remove()

    # 요청 로깅 미들웨어
    @app.before_request
    def log_request_info():
        logger.info(f"요청: {request.method} {request.url} - IP: {request.remote_addr}")

    # 전역 예외 처리기
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"처리되지 않은 예외 발생: {type(e).__name__}: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(404)
    def handle_not_found(e):
        logger.warning(f"404 오류: {request.url}")
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(400)
    def handle_bad_request(e):
        logger.warning(f"400 오류: {str(e)}")
        return jsonify({"error": str(e)}), 400

    @app.errorhandler(500)
    def handle_internal_error(e):
        logger.error(f"500 오류: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

    @app.get("/health")
    def health() -> tuple:
        logger.info("헬스체크 요청")
        return jsonify({"status": "ok"}), 200

    @app.get("/api/todos")
    def list_todos():
        start_time = time.time()
        logger.info("Todo 목록 조회 요청")
        
        session = SessionLocal()
        try:
            todos = session.query(Todo).order_by(Todo.id.desc()).all()
            response_time = time.time() - start_time
            logger.info(f"Todo 목록 조회 완료: {len(todos)}개 항목, 응답시간: {response_time:.3f}초")
            return jsonify([t.to_dict() for t in todos])
        except Exception as e:
            logger.error(f"Todo 목록 조회 중 오류 발생: {str(e)}")
            raise
        finally:
            session.close()

    @app.post("/api/todos")
    def create_todo():
        start_time = time.time()
        logger.info("새 Todo 생성 요청")
        
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        
        if not title:
            logger.warning("Todo 생성 실패: 제목이 비어있음")
            abort(400, description="title is required")
        
        logger.info(f"새 Todo 생성 시도: '{title}'")
        
        session = SessionLocal()
        todo = Todo(title=title, completed=False)
        try:
            session.add(todo)
            session.commit()
            session.refresh(todo)
            response_time = time.time() - start_time
            logger.info(f"Todo 생성 완료: ID={todo.id}, 제목='{title}', 응답시간: {response_time:.3f}초")
            return jsonify(todo.to_dict()), 201
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Todo 생성 중 데이터베이스 오류: {str(e)}")
            abort(500, description=str(e))
        finally:
            session.close()

    @app.patch("/api/todos/<int:todo_id>")
    def update_todo(todo_id: int):
        start_time = time.time()
        logger.info(f"Todo 수정 요청: ID={todo_id}")
        
        data = request.get_json(silent=True) or {}
        session = SessionLocal()
        
        try:
            todo: Optional[Todo] = session.get(Todo, todo_id)
            if not todo:
                logger.warning(f"Todo 수정 실패: ID={todo_id} 항목을 찾을 수 없음")
                abort(404, description="todo not found")
            
            changes = []
            if "title" in data:
                new_title = (data.get("title") or "").strip()
                if not new_title:
                    logger.warning(f"Todo 수정 실패: ID={todo_id}, 제목이 비어있음")
                    abort(400, description="title cannot be empty")
                changes.append(f"제목: '{todo.title}' -> '{new_title}'")
                todo.title = new_title
            
            if "completed" in data:
                new_completed = bool(data.get("completed"))
                changes.append(f"완료상태: {todo.completed} -> {new_completed}")
                todo.completed = new_completed
            
            session.add(todo)
            session.commit()
            session.refresh(todo)
            response_time = time.time() - start_time
            logger.info(f"Todo 수정 완료: ID={todo_id}, 변경사항: {', '.join(changes)}, 응답시간: {response_time:.3f}초")
            return jsonify(todo.to_dict())
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Todo 수정 중 데이터베이스 오류: ID={todo_id}, 오류: {str(e)}")
            abort(500, description=str(e))
        finally:
            session.close()

    @app.delete("/api/todos/<int:todo_id>")
    def delete_todo(todo_id: int):
        start_time = time.time()
        logger.info(f"Todo 삭제 요청: ID={todo_id}")
        
        session = SessionLocal()
        try:
            todo: Optional[Todo] = session.get(Todo, todo_id)
            if not todo:
                logger.warning(f"Todo 삭제 실패: ID={todo_id} 항목을 찾을 수 없음")
                abort(404, description="todo not found")
            
            todo_title = todo.title
            session.delete(todo)
            session.commit()
            response_time = time.time() - start_time
            logger.info(f"Todo 삭제 완료: ID={todo_id}, 제목='{todo_title}', 응답시간: {response_time:.3f}초")
            return ("", 204)
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Todo 삭제 중 데이터베이스 오류: ID={todo_id}, 오류: {str(e)}")
            abort(500, description=str(e))
        finally:
            session.close()

    return app


app = create_app()



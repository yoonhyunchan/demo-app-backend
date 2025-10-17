import os
import sys
from pathlib import Path
from loguru import logger
from typing import Optional


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    로깅 설정을 초기화합니다.
    
    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (None이면 콘솔에만 출력)
    """
    # 기존 핸들러 제거
    logger.remove()
    
    # 콘솔 출력 설정
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 파일 출력 설정 (선택사항)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",  # 10MB마다 로그 파일 회전
            retention="30 days",  # 30일간 보관
            compression="zip",  # 압축 저장
            encoding="utf-8"
        )
    
    # 환경변수에서 로그 설정 읽기
    env_log_level = os.getenv("LOG_LEVEL", log_level)
    env_log_file = os.getenv("LOG_FILE", log_file)
    
    if env_log_file and env_log_file != log_file:
        log_path = Path(env_log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            env_log_file,
            level=env_log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            encoding="utf-8"
        )
    
    logger.info(f"로깅 시스템이 초기화되었습니다. 레벨: {env_log_level}")


def get_logger(name: str = None):
    """
    로거 인스턴스를 반환합니다.
    
    Args:
        name: 로거 이름 (기본값: None)
    
    Returns:
        loguru.Logger: 로거 인스턴스
    """
    if name:
        return logger.bind(name=name)
    return logger

# Todo API 로깅 시스템

이 프로젝트에는 포괄적인 로깅 시스템이 구현되어 있습니다.

## 로깅 기능

### 1. 로그 레벨
- **DEBUG**: 상세한 디버깅 정보
- **INFO**: 일반적인 정보 (기본값)
- **WARNING**: 경고 메시지
- **ERROR**: 오류 메시지
- **CRITICAL**: 심각한 오류

### 2. 로그 출력 위치
- **콘솔**: 컬러 포맷으로 실시간 출력
- **파일**: `logs/app.log`에 저장 (기본값)

### 3. 로그 파일 관리
- **회전**: 10MB마다 새 파일 생성
- **보관**: 30일간 보관
- **압축**: 오래된 로그는 zip으로 압축

### 4. 로깅되는 정보
- 애플리케이션 시작/종료
- 모든 HTTP 요청 (메서드, URL, IP)
- API 엔드포인트 호출 및 응답 시간
- 데이터베이스 작업 성공/실패
- 예외 및 오류 상황
- Todo CRUD 작업 상세 정보

## 환경 변수 설정

`.env` 파일에 다음 설정을 추가할 수 있습니다:

```bash
# 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# 로그 파일 경로 설정
LOG_FILE=logs/app.log
```

## 로그 예시

```
2024-01-15 10:30:15 | INFO     | todo_app:create_app:40 - Todo 애플리케이션이 시작됩니다
2024-01-15 10:30:15 | INFO     | todo_app:create_app:58 - 데이터베이스 테이블이 생성되었습니다
2024-01-15 10:30:20 | INFO     | todo_app:log_request_info:67 - 요청: POST /api/todos - IP: 127.0.0.1
2024-01-15 10:30:20 | INFO     | todo_app:create_todo:89 - 새 Todo 생성 요청
2024-01-15 10:30:20 | INFO     | todo_app:create_todo:98 - 새 Todo 생성 시도: '샘플 할일'
2024-01-15 10:30:20 | INFO     | todo_app:create_todo:107 - Todo 생성 완료: ID=1, 제목='샘플 할일', 응답시간: 0.045초
```

## 로그 모니터링

### 실시간 로그 확인
```bash
tail -f logs/app.log
```

### 특정 레벨 로그만 확인
```bash
grep "ERROR" logs/app.log
grep "WARNING" logs/app.log
```

### 로그 파일 크기 확인
```bash
ls -lh logs/
```

## 문제 해결

### 로그가 생성되지 않는 경우
1. `logs` 디렉토리 권한 확인
2. 환경 변수 `LOG_FILE` 설정 확인
3. 디스크 공간 확인

### 로그 파일이 너무 큰 경우
- 자동으로 10MB마다 회전되므로 별도 조치 불필요
- 필요시 `LOG_FILE` 경로를 다른 위치로 변경

## 개발자 참고사항

- 로깅은 `loguru` 라이브러리를 사용합니다
- 모든 로그는 UTF-8 인코딩으로 저장됩니다
- 프로덕션 환경에서는 `LOG_LEVEL=WARNING` 또는 `ERROR`로 설정 권장

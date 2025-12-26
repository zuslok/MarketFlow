# 🚀 MarketFlow - Profesyonel Seviye Yol Haritası

## 📊 Mevcut Durum Analizi

**Sahip olduklarınız:**
- ✅ Microservices mimarisi (api-service, etl-service, ingestion-service)
- ✅ RabbitMQ ile mesaj kuyruğu
- ✅ PostgreSQL veritabanı şeması
- ✅ Celery + Redis yapılandırması
- ✅ Docker Compose altyapısı
- ✅ Pydantic ile veri validasyonu

**Eksikler:**
- ❌ OOP ve SOLID prensipleri uygulanmamış
- ❌ Design patterns yok
- ❌ Repository pattern yok
- ❌ Dependency Injection yok
- ❌ Unit/Integration testler yok
- ❌ Dockerfile'lar boş
- ❌ Kubernetes yokok
- ❌ CI/CD pipeline yok
- ❌ Logging/Monitoring yok
- ❌ API versiyonlama yok
- ❌ Authentication/Authorization yok
- ❌ Rate limiting yok
- ❌ API documentation (OpenAPI) eksik

---

## 🎯 FAZLAR (Sırayla Uygula)

---

## 📦 FAZ 1: Proje Yapısını Profesyonelleştir

### 1.1 Monorepo Yapısı
```
MarketFlow/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── docker/
│   ├── api.Dockerfile
│   ├── etl.Dockerfile
│   └── ingestion.Dockerfile
├── k8s/
│   ├── base/
│   └── overlays/
├── scripts/
│   ├── setup.sh
│   └── run_tests.sh
├── services/
│   ├── api-service/
│   ├── etl-service/
│   ├── ingestion-service/
│   └── common/
├── tests/
│   ├── unit/
│   └── integration/
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── Makefile
├── README.md
└── .env.example
``````

### 1.2 Her Servis İçin Yapı
```
services/api-service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   └── endpoints/
│   │   │       ├── symbols.py
│   │   │       └── prices.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── security.py
│   │   └── exceptions.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities/
│   │   ├── repositories/
│   │   └── services/
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── database/
│   │   ├── cache/
│   │   └── messaging/
│   └── schemas/
│       ├── __init__.py
│       ├── symbol.py
│       └── price.py
├── tests/
├── Dockerfile
├── pyproject.toml
└── alembic/
```

---

## 📐 FAZ 2: SOLID Prensipleri ve Design Patterns

### 2.1 Repository Pattern
```python
# domain/repositories/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar("T")

class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[T]:
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def update(self, id: int, entity: T) -> Optional[T]:
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        pass
```

```python
# domain/repositories/symbol_repository.py
from abc import abstractmethod
from .base import BaseRepository
from domain.entities.symbol import Symbol

class SymbolRepository(BaseRepository[Symbol]):
    @abstractmethod
    async def get_by_symbol(self, symbol: str) -> Optional[Symbol]:
        pass
    
    @abstractmethod
    async def get_active_symbols(self) -> List[Symbol]:
        pass
```

```python
# infrastructure/database/repositories/postgres_symbol_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from domain.repositories.symbol_repository import SymbolRepository
from domain.entities.symbol import Symbol
from infrastructure.database.models import SymbolModel

class PostgresSymbolRepository(SymbolRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_by_id(self, id: int) -> Optional[Symbol]:
        result = await self._session.execute(
            select(SymbolModel).where(SymbolModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_symbol(self, symbol: str) -> Optional[Symbol]:
        result = await self._session.execute(
            select(SymbolModel).where(SymbolModel.symbol == symbol)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    def _to_entity(self, model: SymbolModel) -> Symbol:
        return Symbol(
            id=model.id,
            symbol=model.symbol,
            display_name=model.display_name,
            asset_type=model.asset_type,
            source=model.source,
            is_active=model.is_active
        )
```

### 2.2 Service Layer (Business Logic)
```python
# domain/services/symbol_service.py
from typing import List, Optional
from domain.repositories.symbol_repository import SymbolRepository
from domain.entities.symbol import Symbol
from schemas.symbol import SymbolCreate, SymbolUpdate

class SymbolService:
    def __init__(self, repository: SymbolRepository):
        self._repository = repository
    
    async def get_symbol(self, symbol_id: int) -> Optional[Symbol]:
        return await self._repository.get_by_id(symbol_id)
    
    async def get_active_symbols(self) -> List[Symbol]:
        return await self._repository.get_active_symbols()
    
    async def create_symbol(self, data: SymbolCreate) -> Symbol:
        # Business logic burada
        existing = await self._repository.get_by_symbol(data.symbol)
        if existing:
            raise ValueError(f"Symbol {data.symbol} already exists")
        
        entity = Symbol(**data.model_dump())
        return await self._repository.create(entity)
```

### 2.3 Dependency Injection Container
```python
# core/container.py
from dependency_injector import containers, providers
from infrastructure.database.session import AsyncSessionFactory
from infrastructure.database.repositories.postgres_symbol_repository import PostgresSymbolRepository
from domain.services.symbol_service import SymbolService

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    # Database
    db_session = providers.Factory(AsyncSessionFactory)
    
    # Repositories
    symbol_repository = providers.Factory(
        PostgresSymbolRepository,
        session=db_session
    )
    
    # Services
    symbol_service = providers.Factory(
        SymbolService,
        repository=symbol_repository
    )
```

### 2.4 Factory Pattern (Data Source)
```python
# infrastructure/data_sources/factory.py
from abc import ABC, abstractmethod
from enum import Enum

class DataSourceType(Enum):
    BINANCE = "binance"
    YAHOO = "yahoo"
    EXCHANGERATE = "exchangerate"

class DataSource(ABC):
    @abstractmethod
    async def fetch_price(self, symbol: str) -> dict:
        pass

class BinanceDataSource(DataSource):
    async def fetch_price(self, symbol: str) -> dict:
        # Binance API implementation
        pass

class YahooDataSource(DataSource):
    async def fetch_price(self, symbol: str) -> dict:
        # Yahoo Finance implementation
        pass

class DataSourceFactory:
    _sources = {
        DataSourceType.BINANCE: BinanceDataSource,
        DataSourceType.YAHOO: YahooDataSource,
    }
    
    @classmethod
    def create(cls, source_type: DataSourceType) -> DataSource:
        source_class = cls._sources.get(source_type)
        if not source_class:
            raise ValueError(f"Unknown source: {source_type}")
        return source_class()
```

### 2.5 Strategy Pattern (ETL Processing)
```python
# domain/strategies/etl_strategy.py
from abc import ABC, abstractmethod

class ETLStrategy(ABC):
    @abstractmethod
    async def extract(self, source: str) -> dict:
        pass
    
    @abstractmethod
    async def transform(self, data: dict) -> dict:
        pass
    
    @abstractmethod
    async def load(self, data: dict) -> None:
        pass

class CryptoETLStrategy(ETLStrategy):
    async def extract(self, source: str) -> dict:
        # Crypto-specific extraction
        pass
    
    async def transform(self, data: dict) -> dict:
        # Normalize crypto data
        pass
    
    async def load(self, data: dict) -> None:
        # Store in database
        pass
```

---

## 🔐 FAZ 3: Authentication & Security

### 3.1 JWT Authentication
```python
# core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

class TokenData(BaseModel):
    user_id: Optional[int] = None
    scopes: list[str] = []

class SecurityService:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._pwd_context = CryptContext(schemes=["bcrypt"])
    
    def create_access_token(
        self, 
        data: dict, 
        expires_delta: timedelta = timedelta(hours=1)
    ) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
    
    def verify_token(self, token: str) -> TokenData:
        payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        return TokenData(**payload)
    
    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)
    
    def verify_password(self, plain: str, hashed: str) -> bool:
        return self._pwd_context.verify(plain, hashed)
```

### 3.2 API Key Authentication (External Services)
```python
# core/api_key.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    # Redis'ten veya DB'den kontrol et
    if not await is_valid_api_key(api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
```

### 3.3 Rate Limiting
```python
# core/rate_limit.py
from fastapi import Request, HTTPException
import redis.asyncio as redis
from functools import wraps

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client
    
    async def check_rate_limit(
        self, 
        key: str, 
        max_requests: int = 100, 
        window_seconds: int = 60
    ) -> bool:
        current = await self._redis.incr(key)
        if current == 1:
            await self._redis.expire(key, window_seconds)
        return current <= max_requests

def rate_limit(max_requests: int = 100, window: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host
            limiter = request.app.state.rate_limiter
            
            if not await limiter.check_rate_limit(
                f"rate:{client_ip}", max_requests, window
            ):
                raise HTTPException(429, "Rate limit exceeded")
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
```

---

## 🐳 FAZ 4: Docker & Kubernetes

### 4.1 Production-Ready Dockerfile
```dockerfile
# docker/api.Dockerfile
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY services/api-service/pyproject.toml .
COPY services/common /common
RUN pip install --no-cache-dir build && \
    pip install --no-cache-dir /common && \
    pip install --no-cache-dir .

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Security: non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Copy only necessary files
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY services/api-service/app ./app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.2 Kubernetes Deployment
```yaml
# k8s/base/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: marketflow-api
  labels:
    app: marketflow-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: marketflow-api
  template:
    metadata:
      labels:
        app: marketflow-api
    spec:
      containers:
      - name: api
        image: marketflow/api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: marketflow-secrets
              key: database-url
```

### 4.3 Horizontal Pod Autoscaler
```yaml
# k8s/base/api-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: marketflow-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: marketflow-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 🧪 FAZ 5: Testing

### 5.1 Unit Tests
```python
# tests/unit/test_symbol_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from domain.services.symbol_service import SymbolService
from domain.entities.symbol import Symbol

@pytest.fixture
def mock_repository():
    return AsyncMock()

@pytest.fixture
def symbol_service(mock_repository):
    return SymbolService(repository=mock_repository)

class TestSymbolService:
    @pytest.mark.asyncio
    async def test_get_symbol_returns_symbol(self, symbol_service, mock_repository):
        # Arrange
        expected = Symbol(id=1, symbol="BTCUSDT", asset_type="crypto")
        mock_repository.get_by_id.return_value = expected
        
        # Act
        result = await symbol_service.get_symbol(1)
        
        # Assert
        assert result == expected
        mock_repository.get_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_create_symbol_raises_on_duplicate(self, symbol_service, mock_repository):
        # Arrange
        mock_repository.get_by_symbol.return_value = Symbol(id=1, symbol="BTCUSDT")
        
        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            await symbol_service.create_symbol(SymbolCreate(symbol="BTCUSDT"))
```

### 5.2 Integration Tests
```python
# tests/integration/test_api_endpoints.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

class TestSymbolsEndpoint:
    @pytest.mark.asyncio
    async def test_get_symbols_returns_list(self, client):
        response = await client.get("/api/v1/symbols")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_get_symbol_not_found(self, client):
        response = await client.get("/api/v1/symbols/99999")
        
        assert response.status_code == 404
```

### 5.3 pytest.ini
```ini
[pytest]
testpaths = tests
asyncio_mode = auto
addopts = -v --cov=app --cov-report=html --cov-report=term-missing
filterwarnings =
    ignore::DeprecationWarning
```

---

## 📊 FAZ 6: Logging & Monitoring

### 6.1 Structured Logging
```python
# core/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "extra"):
            log_obj.update(record.extra)
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    logger = logging.getLogger("marketflow")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
```

### 6.2 Prometheus Metrics
```python
# core/metrics.py
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Request
import time

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)

async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

---

## 🔄 FAZ 7: CI/CD Pipeline

### 7.1 GitHub Actions
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -e services/common
          pip install -e services/api-service[test]
      
      - name: Run linting
        run: |
          pip install ruff
          ruff check .
      
      - name: Run tests
        run: pytest --cov --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker images
        run: |
          docker build -f docker/api.Dockerfile -t marketflow/api:${{ github.sha }} .
          docker build -f docker/etl.Dockerfile -t marketflow/etl:${{ github.sha }} .
```

---

## ☁️ FAZ 8: AWS Deployment

### 8.1 AWS Servisleri
- **ECS/EKS**: Container orchestration
- **RDS**: PostgreSQL
- **ElastiCache**: Redis
- **Amazon MQ**: RabbitMQ
- **S3**: Data lake / backups
- **CloudWatch**: Monitoring
- **ECR**: Container registry
- **Secrets Manager**: Credentials

### 8.2 Terraform (IaC)
```hcl
# terraform/main.tf
provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  name   = "marketflow-vpc"
  cidr   = "10.0.0.0/16"
}

module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  cluster_name    = "marketflow-cluster"
  cluster_version = "1.28"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets
}

module "rds" {
  source     = "terraform-aws-modules/rds/aws"
  identifier = "marketflow-db"
  engine     = "postgres"
  instance_class = "db.t3.medium"
}
```

---

## 📋 Makefile
```makefile
.PHONY: help dev test lint docker-up docker-down migrate

help:
	@echo "Available commands:"
	@echo "  make dev        - Start development environment"
	@echo "  make test       - Run all tests"
	@echo "  make lint       - Run linting"
	@echo "  make docker-up  - Start Docker containers"

dev:
	docker-compose -f docker-compose.dev.yml up -d
	uvicorn services.api-service.app.main:app --reload

test:
	pytest tests/ -v --cov

lint:
	ruff check .
	mypy services/

docker-up:
	docker-compose up -d --build

docker-down:
	docker-compose down -v

migrate:
	alembic upgrade head
```

---

## ✅ Yapılacaklar Checklist

### Faz 1: Proje Yapısı
- [ ] Klasör yapısını yeniden düzenle
- [ ] Makefile oluştur
- [ ] .env.example ekle

### Faz 2: SOLID & Patterns
- [ ] Repository pattern uygula
- [ ] Service layer ekle
- [ ] Factory pattern uygula
- [ ] Dependency Injection ekle

### Faz 3: Security
- [ ] JWT authentication
- [ ] API key authentication
- [ ] Rate limiting
- [ ] CORS configuration

### Faz 4: Docker & K8s
- [ ] Dockerfile'ları doldur
- [ ] Kubernetes manifests
- [ ] HPA configuration

### Faz 5: Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] pytest configuration

### Faz 6: Monitoring
- [ ] Structured logging
- [ ] Prometheus metrics
- [ ] Health checks

### Faz 7: CI/CD
- [ ] GitHub Actions workflow
- [ ] Docker build pipeline
- [ ] Deploy pipeline

### Faz 8: AWS
- [ ] Terraform scripts
- [ ] EKS deployment
- [ ] RDS setup

---

## 📚 Önerilen Öğrenme Kaynakları

1. **Clean Architecture** - Robert C. Martin
2. **Designing Data-Intensive Applications** - Martin Kleppmann
3. **FastAPI Best Practices** - https://github.com/zhanymkanov/fastapi-best-practices
4. **12 Factor App** - https://12factor.net/

---

*Bu yol haritasını takip ederek profesyonel seviyede bir backend projesi oluşturabilirsin. Her fazı tamamladıktan sonra bir sonrakine geç.*

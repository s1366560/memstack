# 架构违规快速修复指南

## 🚨 关键发现

### 严重违规（15 个文件）

所有 15 个路由器都**绕过 Application 层直接访问数据库**：

```bash
auth.py
ai_tools.py
data_export.py
enhanced_search.py
episodes.py
graphiti.py
maintenance.py
memories.py
memos.py
projects.py
recall.py
schema.py
tasks.py
tenants.py
```

### Application 层违规（2 个文件）

```bash
application/services/auth_service.py
application/services/schema_service.py
```

这两文件**直接依赖 Infrastructure 层**，违反依赖倒置原则。

---

## 🎯 5 分钟快速理解

### ❌ 当前错误架构

```python
# memories.py - Router 直接操作数据库 ❌
from src.infrastructure.adapters.secondary.persistence.database import get_db
from src.infrastructure.adapters.secondary.persistence.models import Memory

@router.post("/")
async def create_memory(data: MemoryCreate, db: AsyncSession = Depends(get_db)):
    memory = Memory(**data.dict())
    db.add(memory)
    await db.commit()  # ❌ 绕过 Use Case
```

### ✅ 正确架构

```python
# memories.py - Router 调用 Use Case ✅
from src.application.use_cases.memory.create_memory import CreateMemoryUseCase

@router.post("/")
async def create_memory(
    data: MemoryCreate,
    create_uc: CreateMemoryUseCase = Depends(...)  # ✅ 通过 Use Case
):
    command = CreateMemoryCommand(**data.dict())
    memory = await create_uc.execute(command)
    return MemoryResponse.from_domain(memory)
```

---

## 📋 修复清单

### 阶段 1: 修复 Domain Ports（1 天）

**需要创建的接口**：

```python
# src/domain/ports/repositories/user_repository.py
class UserRepository(ABC):
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]: pass
    @abstractmethod
    async def save(self, user: User) -> None: pass

# src/domain/ports/repositories/memo_repository.py
class MemoRepository(ABC):
    @abstractmethod
    async def find_by_id(self, memo_id: str) -> Optional[Memo]: pass
    @abstractmethod
    async def save(self, memo: Memo) -> None: pass
    @abstractmethod
    async def delete(self, memo_id: str) -> None: pass

# src/domain/ports/repositories/task_repository.py
class TaskRepository(ABC):
    @abstractmethod
    async def find_by_id(self, task_id: str) -> Optional[TaskLog]: pass
    @abstractmethod
    async def save(self, task: TaskLog) -> None: pass
    @abstractmethod
    async def list_recent(self, limit: int) -> List[TaskLog]: pass
```

### 阶段 2: 创建缺失的 Domain Models（1-2 天）

```python
# src/domain/model/auth/user.py
@dataclass(kw_only=True)
class User(Entity):
    email: str
    name: str
    password_hash: str
    is_active: bool = True

# src/domain/model/auth/api_key.py
@dataclass(kw_only=True)
class APIKey(Entity):
    user_id: str
    key_hash: str
    name: str
    is_active: bool = True

# src/domain/model/task/task_log.py
@dataclass(kw_only=True)
class TaskLog(Entity):
    group_id: str
    task_type: str
    status: str
    entity_id: Optional[str] = None
    error_message: Optional[str] = None
```

### 阶段 3: 重构 auth_service.py（1 天）

**步骤**：

1. 创建接口：
```python
# src/domain/ports/services/authentication_port.py
class AuthenticationPort(ABC):
    @abstractmethod
    async def verify_api_key(self, api_key: str) -> Optional[User]: pass
    @abstractmethod
    async def get_current_user(self, api_key: str) -> Optional[User]: pass
```

2. 重构 service：
```python
# application/services/auth_service.py
class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        api_key_repo: APIKeyRepository
    ):
        self._user_repo = user_repo
        self._api_key_repo = api_key_repo

    async def verify_api_key(self, api_key: str) -> Optional[User]:
        key_hash = hash_api_key(api_key)
        api_key = await self._api_key_repo.find_by_hash(key_hash)
        if api_key:
            return await self._user_repo.find_by_id(api_key.user_id)
        return None
```

3. 实现 adapter：
```python
# infrastructure/adapters/secondary/persistence/sql_api_key_repository.py
class SqlAlchemyAPIKeyRepository(APIKeyRepository):
    async def find_by_hash(self, key_hash: str) -> Optional[APIKey]:
        result = await self._session.execute(
            select(DBAPIKey).where(DBAPIKey.key_hash == key_hash)
        )
        db_key = result.scalar_one_or_none()
        return self._to_domain(db_key) if db_key else None
```

### 阶段 4: 重构一个 Router 作为示例（1 天）

**以 `memos.py` 为例**：

1. **创建 Use Case**:
```python
# application/use_cases/memo/create_memo_use_case.py
class CreateMemoUseCase:
    def __init__(self, memo_repo: MemoRepository):
        self._memo_repo = memo_repo

    async def execute(self, command: CreateMemoCommand) -> Memo:
        memo = Memo(
            content=command.content,
            user_id=command.user_id,
            visibility=command.visibility
        )
        await self._memo_repo.save(memo)
        return memo
```

2. **重构 Router**:
```python
# infrastructure/adapters/primary/web/routers/memos.py
from src.application.use_cases.memo.create_memo_use_case import CreateMemoUseCase, CreateMemoCommand

@router.post("/memos")
async def create_memo(
    data: MemoCreate,
    current_user: User = Depends(get_current_user),
    create_uc: CreateMemoUseCase = Depends(...)  # ✅ 从 DI Container 获取
):
    command = CreateMemoCommand(
        content=data.content,
        user_id=current_user.id,
        visibility=data.visibility
    )
    memo = await create_uc.execute(command)
    return MemoResponse.from_domain(memo)
```

3. **更新 DI Container**:
```python
# configuration/container.py
class DIContainer:
    def create_memo_use_case(self, session: AsyncSession) -> CreateMemoUseCase:
        return CreateMemoUseCase(
            memo_repo=SqlAlchemyMemoRepository(session)
        )
```

---

## 🔍 如何验证修复

### 检查违规导入

```bash
# 检查 Application 层是否有 Infrastructure 导入
grep -r "from src.infrastructure" src/application/
# 应该返回空 ✅

# 检查 Routers 是否绕过 Use Cases
grep -r "infrastructure.adapters.secondary.persistence" src/infrastructure/adapters/primary/web/routers/
# 应该返回空 ✅
```

### 检查依赖方向

```bash
# Domain 层不应该依赖其他层
find src/domain/ -name "*.py" -exec grep -l "from src.application\|from src.infrastructure" {} \;
# 应该返回空 ✅

# Application 层应该只依赖 Domain 层
find src/application/ -name "*.py" -exec grep -l "from src.infrastructure" {} \;
# 应该返回空 ✅（除了 adapters 实现类）

# Infrastructure 层可以依赖 Domain 层
find src/infrastructure/ -name "*.py" -exec grep -l "from src.domain" {} \;
# 应该有很多文件 ✅
```

---

## 🚀 自动化检查脚本

创建 pre-commit hook：

```bash
#!/bin/bash
# scripts/check_architecture.sh

echo "🔍 检查架构合规性..."

# 检查 Application 层违规
echo "检查 Application 层违规..."
violations=$(grep -r "from src.infrastructure" src/application/ --include="*.py" | wc -l)
if [ "$violations" -gt 0 ]; then
    echo "❌ 发现 $violations 个 Application 层违规"
    grep -r "from src.infrastructure" src/application/ --include="*.py"
    exit 1
fi

# 检查 Router 违规
echo "检查 Router 违规..."
violations=$(grep -r "infrastructure.adapters.secondary.persistence" src/infrastructure/adapters/primary/web/routers/ --include="*.py" | wc -l)
if [ "$violations" -gt 0 ]; then
    echo "❌ 发现 $violations 个 Router 违规"
    grep -r "infrastructure.adapters.secondary.persistence" src/infrastructure/adapters/primary/web/routers/ --include="*.py"
    exit 1
fi

echo "✅ 架构检查通过！"
```

添加到 `.git/hooks/pre-commit`：
```bash
#!/bin/bash
# .git/hooks/pre-commit
scripts/check_architecture.sh || exit 1
```

---

## 📚 学习资源

**必读**:
1. [六边形架构原文](https://alistair.cockburn.us/hexagonal-architecture/)
2. [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
3. [Domain-Driven Design](https://www.domainlanguage.com/ddd/)

**示例项目**:
1. [Real Python - Architecture Patterns](https://realpython.com/python-application-layouts/)
2. [Awesome Clean Architecture](https://github.com/matthewmcnew/clean-architecture-example)

---

## 💡 快速参考

### 正确的依赖关系

```
Domain ← Application ← Infrastructure
   ↑                      ↑
   └──────────────┘
      (Ports 接口)
```

### 记忆口诀

1. **Domain**: 纯业务，无依赖
2. **Application**: 编排逻辑，依赖接口
3. **Infrastructure**: 实现接口，不包含业务
4. **Primary**: 调用 Application，不跳层

---

## ⚡ 最快修复路径

如果时间紧迫，优先修复这 3 个文件：

1. **memories.py** - 最常用
2. **auth_service.py** - 认证核心
3. **episodes.py** - Episode 创建

修复这 3 个可以覆盖 80% 的使用场景。

---

**更新**: 2024-12-28
**状态**: 🔴 需要修复
**优先级**: 高

# VIP Memory 部署指南

## 部署方式概览

VIP Memory 支持多种部署方式：

1. **Docker Compose** - 推荐用于开发和小规模生产环境
2. **Kubernetes** - 推荐用于大规模生产环境（待完善）
3. **手动部署** - 适合自定义部署场景

## 前置要求

### 最小配置
- **CPU**: 2核
- **内存**: 4GB
- **存储**: 20GB
- **操作系统**: Linux (Ubuntu 20.04+), macOS 10.15+

### 推荐配置
- **CPU**: 4核+
- **内存**: 8GB+
- **存储**: 50GB+ SSD
- **操作系统**: Ubuntu 22.04 LTS

### 软件依赖
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.10+ (手动部署)
- Node.js 18+ (Web开发)

## 方式1: Docker Compose部署 (推荐)

### 1.1 克隆仓库

```bash
git clone https://github.com/yourusername/vip-memory.git
cd vip-memory
```

### 1.2 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置必要配置：

```bash
# Neo4j配置
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password_here

# LLM配置 (选择一个)
LLM_PROVIDER=qwen  # 或 gemini

# 通义千问
QWEN_API_KEY=your_qwen_api_key
DASHSCOPE_API_KEY=your_dashscope_key

# 或 Google Gemini
GEMINI_API_KEY=your_gemini_api_key

# 服务配置
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# 认证配置
REQUIRE_API_KEY=true
```

### 1.3 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 检查状态
docker-compose ps
```

### 1.4 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# 查看API文档
open http://localhost:8000/docs

# 查看Web控制台
open http://localhost:5173
```

### 1.5 获取API Key

查看API服务日志，找到自动生成的API Key：

```bash
docker-compose logs api | grep "Generated default API key"
```

输出示例：
```
INFO:     Generated default API key: vpm_sk_abc123...
```

### 1.6 停止服务

```bash
# 停止服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

## 方式2: 手动部署

### 2.1 安装Python依赖

```bash
# 使用uv (推荐)
uv sync --extra dev

# 或使用pip
pip install -e ".[dev,neo4j,evaluation]"
```

### 2.2 启动数据库服务

```bash
# 启动Neo4j, PostgreSQL, Redis
make docker-up

# 或手动启动
docker-compose up -d neo4j postgres redis
```

### 2.3 配置环境

```bash
cp .env.example .env
# 编辑.env文件
```

### 2.4 启动API服务

```bash
# 开发模式（热重载）
make dev

# 或手动启动
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

### 2.5 启动Web控制台

```bash
cd web

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
npm run preview
```

## 方式3: 独立Web部署

Web应用可以独立部署到静态托管服务。

### 3.1 构建Web应用

```bash
cd web

# 安装依赖
npm install

# 构建
npm run build

# 输出目录: dist/
```

### 3.2 配置API地址

编辑 `web/.env.production`:

```bash
VITE_API_URL=https://api.your-domain.com
```

### 3.3 部署选项

#### 选项A: Nginx

```bash
# 复制构建文件
cp -r dist/* /var/www/vip-memory/

# Nginx配置
sudo nano /etc/nginx/sites-available/vip-memory
```

Nginx配置示例：
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/vip-memory;
    index index.html;

    # SPA路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API代理
    location /api/ {
        proxy_pass http://api-server:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 选项B: Docker

```bash
# 构建镜像
cd web
docker build -t vip-memory-web .

# 运行容器
docker run -d -p 80:80 \
  -e API_URL=http://api:8000 \
  --name vip-memory-web \
  vip-memory-web
```

#### 选项C: Vercel

```bash
# 安装Vercel CLI
npm i -g vercel

# 部署
cd web
vercel --prod
```

#### 选项D: Cloudflare Pages

```bash
# 在Cloudflare Pages控制台:
# 1. 连接GitHub仓库
# 2. 设置构建命令: cd web && npm run build
# 3. 设置输出目录: web/dist
# 4. 添加环境变量: VITE_API_URL
```

## 生产环境配置

### 安全加固

#### 1. 启用HTTPS

使用Let's Encrypt免费证书：

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

#### 2. 配置防火墙

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

#### 3. 限制数据库访问

```yaml
# docker-compose.yml
services:
  neo4j:
    networks:
      - internal
    # 不暴露到主机

networks:
  internal:
    internal: true
```

#### 4. 设置强密码

```bash
# 生成随机密码
openssl rand -base64 32

# 更新环境变量
NEO4J_PASSWORD=<strong-password>
POSTGRES_PASSWORD=<strong-password>
```

### 性能优化

#### 1. 增加Worker数量

```bash
# Uvicorn多进程
uvicorn server.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

或使用Gunicorn:
```bash
gunicorn server.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

#### 2. 配置Nginx缓存

```nginx
# 添加到Nginx配置
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$request_uri";
}
```

#### 3. 启用Redis缓存

```python
# server/config.py
REDIS_ENABLED = True
REDIS_URL = "redis://redis:6379"
CACHE_TTL = 300  # 5分钟
```

#### 4. 数据库连接池

```python
# server/config.py
NEO4J_MAX_CONNECTION_POOL_SIZE = 50
NEO4J_MAX_CONNECTION_LIFETIME = 3600
```

### 监控和日志

#### 1. 配置日志

```python
# server/config.py
LOG_LEVEL = "INFO"
LOG_FORMAT = "json"  # 结构化日志
```

#### 2. 日志收集

使用Docker日志驱动：

```yaml
# docker-compose.yml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

或集成ELK Stack:
```yaml
services:
  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    # ...配置

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    # ...配置

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    # ...配置
```

#### 3. 健康检查

```yaml
# docker-compose.yml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 备份策略

#### 1. Neo4j备份

```bash
# 手动备份
docker exec neo4j neo4j-admin database dump neo4j --to=/backups/neo4j-$(date +%Y%m%d).dump

# 定时备份 (crontab)
0 2 * * * /path/to/backup-script.sh
```

备份脚本示例：
```bash
#!/bin/bash
BACKUP_DIR=/backups
RETENTION_DAYS=7

# 备份
docker exec neo4j neo4j-admin database dump neo4j \
  --to=/backups/neo4j-$(date +%Y%m%d).dump

# 清理旧备份
find $BACKUP_DIR -name "neo4j-*.dump" -mtime +$RETENTION_DAYS -delete

# 上传到对象存储
aws s3 cp $BACKUP_DIR/neo4j-$(date +%Y%m%d).dump \
  s3://your-bucket/backups/
```

#### 2. PostgreSQL备份

```bash
# pg_dump备份
docker exec postgres pg_dump -U postgres vip_memory > backup.sql

# 恢复
docker exec -i postgres psql -U postgres vip_memory < backup.sql
```

## 高可用部署 (HA)

### 架构图

```
                    ┌─────────────┐
                    │   Load      │
                    │  Balancer   │
                    │  (Nginx)    │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
     ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
     │  API    │     │  API    │     │  API    │
     │ Server  │     │ Server  │     │ Server  │
     │   #1    │     │   #2    │     │   #3    │
     └────┬────┘     └────┬────┘     └────┬────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
     ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
     │  Neo4j  │     │ Postgres│     │  Redis  │
     │ Cluster │     │  Primary│     │ Sentinel│
     └─────────┘     └────┬────┘     └─────────┘
                          │
                     ┌────▼────┐
                     │ Postgres│
                     │ Replica │
                     └─────────┘
```

### Nginx负载均衡配置

```nginx
upstream api_backend {
    least_conn;
    server api1:8000 max_fails=3 fail_timeout=30s;
    server api2:8000 max_fails=3 fail_timeout=30s;
    server api3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    
    location /api/ {
        proxy_pass http://api_backend;
        proxy_next_upstream error timeout invalid_header http_500;
        proxy_connect_timeout 5s;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 故障排查

### 常见问题

#### 1. 服务启动失败

```bash
# 查看日志
docker-compose logs api

# 检查端口占用
sudo netstat -tulpn | grep :8000

# 重启服务
docker-compose restart api
```

#### 2. Neo4j连接失败

```bash
# 检查Neo4j状态
docker-compose logs neo4j

# 测试连接
docker exec neo4j cypher-shell -u neo4j -p password "RETURN 1"

# 检查网络
docker network inspect vip-memory_default
```

#### 3. API Key认证失败

```bash
# 查看API日志
docker-compose logs api | grep -i auth

# 验证API Key格式
curl -v http://localhost:8000/api/v1/episodes/ \
  -H "Authorization: Bearer vpm_sk_your_key"
```

#### 4. 内存不足

```bash
# 查看资源使用
docker stats

# 增加内存限制
# docker-compose.yml
services:
  api:
    mem_limit: 2g
  neo4j:
    mem_limit: 2g
```

### 性能诊断

```bash
# API响应时间
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# curl-format.txt内容:
#     time_namelookup:  %{time_namelookup}\n
#        time_connect:  %{time_connect}\n
#     time_appconnect:  %{time_appconnect}\n
#    time_pretransfer:  %{time_pretransfer}\n
#       time_redirect:  %{time_redirect}\n
#  time_starttransfer:  %{time_starttransfer}\n
#                     ----------\n
#          time_total:  %{time_total}\n
```

## 更新和维护

### 滚动更新

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build

# 滚动更新（逐个重启）
docker-compose up -d --no-deps --build api

# 验证
curl http://localhost:8000/health
```

### 数据迁移

```bash
# 导出Neo4j数据
docker exec neo4j neo4j-admin database dump neo4j --to=/tmp/neo4j.dump

# 导入到新实例
docker exec new-neo4j neo4j-admin database load neo4j --from=/tmp/neo4j.dump
```

## 成本估算

### AWS示例 (美国东部)

| 服务 | 配置 | 月费用 |
|-----|------|--------|
| EC2 (API) | t3.medium x 2 | $60 |
| Neo4j (自托管) | t3.large | $70 |
| RDS (PostgreSQL) | db.t3.small | $30 |
| ElastiCache (Redis) | cache.t3.micro | $15 |
| ALB | - | $20 |
| S3 (备份) | 100GB | $3 |
| **总计** | | **$198/月** |

### 使用托管服务

| 服务 | 配置 | 月费用 |
|-----|------|--------|
| Heroku | Standard-2X x 2 | $100 |
| Neo4j Aura | Professional | $200 |
| Heroku Postgres | Standard-0 | $50 |
| Heroku Redis | Premium-0 | $15 |
| **总计** | | **$365/月** |

## 技术支持

- **文档**: https://vip-memory.readthedocs.io
- **Issues**: https://github.com/yourusername/vip-memory/issues
- **讨论**: https://github.com/yourusername/vip-memory/discussions

---

**更新时间**: 2024-12-19  
**文档版本**: 1.0

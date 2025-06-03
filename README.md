

## 系统架构

- **前端**: Vue 3 + TypeScript + Element Plus + Vite
- **后端**: FastAPI + SQLAlchemy + SQLite
- **认证**: JWT令牌认证

## 快速开始

### 前置要求

- Node.js 16+
- Python 3.8+

### 后端启动

1. 进入后端安装依赖,有requirement文件
2. 初始化数据库：
python init_db.py
可以用test文件夹内的脚本查看数据库实时数据

3. 启动后端服务：
```bash
uvicorn app.main:app --reload
```

### 前端启动

1. 进入前端目录并安装依赖：
```bash
cd Frontend
npm install
```

2. 启动开发服务器：
```bash
npm run dev
```

## 访问地址,还没整

- 前端界面: http://localhost:5173
- 后端API文档: http://localhost:8000/docs
- API接口: http://localhost:8000

## 项目结构

```
E-Charge/
├── Frontend/          # Vue 3前端应用
│   ├── src/          # 源代码
│   ├── public/       # 静态资源
│   └── package.json  # 前端依赖配置
├── Backend/          # FastAPI后端服务
│   ├── app/         # 应用代码
│   ├── test/        # 测试文件
│   └── init_db.py   # 数据库初始化
└── README.md        # 项目说明
```

## 开发说明

### 技术栈详情

**前端技术栈:**
- Vue 3 (组合式API)
- TypeScript
- Element Plus (UI组件库)
- Vue Router (路由管理)
- Pinia (状态管理)
- Axios (HTTP客户端)
- Vite (构建工具)

**后端技术栈:**
- FastAPI (异步Web框架)
- SQLAlchemy (ORM)
- SQLite (数据库)
- Pydantic (数据验证)
- JWT (身份认证)

### API接口

主要API端点：

- `POST /users/` - 用户注册
- `GET /users/me` - 获取用户信息
- `POST /charging/request` - 创建充电请求
- `GET /charging/queue/status` - 获取排队状态
- `GET /admin/piles` - 获取充电桩状态

### 构建部署

**前端构建:**
```bash
cd Frontend
npm run build
```

**后端部署:**
```bash
cd Backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 许可证

MIT License

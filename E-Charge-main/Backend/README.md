# 充电站管理系统后端

这是一个基于FastAPI的充电站管理系统后端服务。

## 功能特点

- 用户管理（注册、登录、认证）
- 充电请求管理
- 充电桩调度
- 计费系统
- 管理员功能
- 报表统计

## 系统参数配置

系统支持以下可配置参数：

1. **快充电桩数量 (FastChargingPileNum)** - 系统中快充电桩的数量（默认：2个，名称为A、B）
2. **慢充电桩数量 (TrickleChargingPileNum)** - 系统中慢充电桩的数量（默认：3个，名称为C、D、E）
3. **等候区车位容量 (WaitingAreaSize)** - 等候区可容纳的最大车辆数（默认：6个）
4. **充电桩排队队列长度 (ChargingQueueLen)** - 每个充电桩最多可排队的车辆数（默认为2个车位，只有第一个车位可充电）

### 充电站布局

充电站分为"充电区"和"等候区"两个区域：

1. **等候区**：
   - 最大车位容量为6
   - 电动车到达后通过客户端提交充电请求
   - 根据充电模式分配排队号：快充模式为F类型(如F1、F2)，慢充模式为T类型(如T1、T2)

2. **充电区**：
   - 2个快充电桩(A、B)，功率为30度/小时
   - 3个慢充电桩(C、D、E)，功率为7度/小时
   - 每个充电桩有2个车位的排队队列，只有第一个车位可充电
   
3. **调度策略**：
   - 按照"先来先到"的原则叫号（F类型进入快充桩，T类型进入慢充桩）
   - 当有多个充电桩可选时，选择完成充电所需时长（等待时间+自己充电时间）最短的充电桩

### 配置方法

可以通过以下两种方式配置这些参数：

#### 1. 使用命令行工具

使用项目根目录下的`set_params.py`脚本快速设置系统参数：

```bash
python set_params.py --fast-piles 3 --trickle-piles 5 --waiting-area 8 --queue-len 4
```

参数说明：
- `--fast-piles`: 快充电桩数量 (默认: 2)
- `--trickle-piles`: 慢充电桩数量 (默认: 4)
- `--waiting-area`: 等候区车位容量 (默认: 6)
- `--queue-len`: 充电桩排队队列长度 (默认: 2)

#### 2. 直接设置环境变量

也可以直接在环境中设置以下环境变量：

```bash
# Windows PowerShell
$env:FAST_CHARGING_PILE_NUM=3
$env:TRICKLE_CHARGING_PILE_NUM=5
$env:WAITING_AREA_SIZE=8
$env:CHARGING_QUEUE_LEN=4

# Linux/MacOS
export FAST_CHARGING_PILE_NUM=3
export TRICKLE_CHARGING_PILE_NUM=5
export WAITING_AREA_SIZE=8
export CHARGING_QUEUE_LEN=4
```

#### 3. 创建.env文件

在项目根目录下创建`.env`文件，内容如下：

```
FAST_CHARGING_PILE_NUM=3
TRICKLE_CHARGING_PILE_NUM=5
WAITING_AREA_SIZE=8
CHARGING_QUEUE_LEN=4
```

## 技术栈

- Python 3.8+
- FastAPI
- SQLAlchemy
- SQLite
- JWT认证
- Pydantic

## 安装

1. 确保您使用的是Python 3.8或更高版本（推荐3.9或3.10）：
```bash
python --version
```

2. 创建虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 数据库初始化

系统在首次启动时会自动创建数据库表结构，但您也可以手动初始化数据库：

```bash
# 初始化数据库结构
python init_db.py

# 检查数据库表结构
python check_db_tables.py
```

## 系统参数配置

在启动服务器前，您可以配置系统参数：

```bash
# 使用默认参数
python set_params.py

# 或自定义参数
python set_params.py --fast-piles 3 --trickle-piles 4 --waiting-area 8 --queue-len 3
```

## 依赖项版本兼容性

项目使用的主要依赖版本如下：
- fastapi==0.104.1
- uvicorn==0.24.0
- sqlalchemy==2.0.23
- pydantic==2.5.2

如果遇到以下问题，请尝试相应解决方案：

1. **SQLAlchemy兼容性问题**：如果出现SQLAlchemy相关错误，可尝试降级至1.4.x版本
   ```bash
   pip uninstall sqlalchemy
   pip install sqlalchemy==1.4.47
   ```

2. **Pydantic版本冲突**：如果FastAPI与Pydantic版本不兼容，请尝试：
   ```bash
   pip install "pydantic>=1.10.0,<2.0.0"
   ```

3. **数据库连接错误**：确保SQLite可用，并且有合适的读写权限
   ```bash
   # 验证SQLite安装
   python -c "import sqlite3; print(sqlite3.sqlite_version)"
   ```

## 运行

1. 启动服务器：
```bash
uvicorn app.main:app --reload(
```

2. 访问API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API端点

### 用户相关
- POST /users/ - 创建新用户
- GET /users/me - 获取当前用户信息
- GET /users/{user_id} - 获取指定用户信息

### 充电相关
- POST /charging/request - 创建充电请求
- GET /charging/request/{request_id} - 获取充电请求详情
- PUT /charging/request/{request_id}/cancel - 取消充电请求
- GET /charging/queue/status - 获取排队状态

### 管理员相关
- PUT /admin/pile/{pile_id}/status - 更新充电桩状态
- GET /admin/piles - 获取所有充电桩状态
- GET /admin/pile/{pile_id}/queue - 获取充电桩排队信息
- GET /admin/report - 获取报表数据

## 数据库

系统使用SQLite作为数据库，数据库文件将自动创建在项目根目录下。

## 开发

1. 代码风格遵循PEP 8规范
2. 使用类型注解
3. 编写单元测试
4. 使用Black进行代码格式化

## 部署

1. 修改配置文件中的敏感信息
2. 使用生产级别的数据库（如PostgreSQL）
3. 配置适当的安全措施
4. 使用gunicorn或uvicorn作为生产服务器 
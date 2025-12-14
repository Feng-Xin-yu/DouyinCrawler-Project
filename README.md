# 🎬 DouyinCrawler - 专业抖音数据爬虫

<div align="center">

![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Douyin-red.svg)

**专注于抖音平台的异步数据爬虫，集成签名生成、断点续爬、账号池管理等核心功能**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [项目结构](#-项目结构) • [配置说明](#-配置说明) • [使用示例](#-使用示例)

</div>

---

## 📖 项目简介

DouyinCrawler 是一个专门用于爬取抖音平台数据的 Python 爬虫项目。项目采用异步架构设计，支持关键词搜索、视频详情、创作者主页、首页推荐等多种爬取模式，并提供完善的账号池管理、代理池支持、断点续爬等功能。

## ✨ 功能特性

### 🎬 爬取功能

| 功能 | 说明 |
|------|------|
| 关键词搜索 | 根据关键词搜索视频，支持分页爬取 |
| 视频详情 | 爬取指定视频ID的详细信息，支持批量处理 |
| 创作者主页 | 爬取指定创作者的所有视频 |
| 首页推荐 | 爬取首页推荐内容 |
| 评论数据 | 支持一级和二级评论爬取 |

### 🛠️ 核心功能

- **签名生成**：使用 JavaScript 方式生成请求签名
- **断点续爬**：支持文件和 Redis 两种方式保存爬取进度，中断后可继续爬取
- **账号池管理**：支持多账号轮换，自动状态管理
- **代理IP池**：支持代理提供商集成，IP 验证和轮换
- **异步并发**：基于 asyncio 的异步架构，支持并发爬取
- **数据存储**：支持 CSV 和 JSON 两种存储格式
- **日志系统**：完善的日志输出，便于问题追踪

## 🚀 快速开始

### 📋 前置要求

- **Python**: 3.9.6 或更高版本
- **Node.js**: 16.0+ (用于执行JavaScript签名代码)
- **Redis**: (可选，如果使用 Redis 缓存或断点存储)

### 🔧 安装步骤

#### 1️⃣ 克隆项目

```bash
git clone https://github.com/your-username/DouyinCrawler.git
cd DouyinCrawler
```

#### 2️⃣ 创建 Python 环境

**方式一：使用 Anaconda**

```bash
conda create -n DouyinCrawler python=3.9.6
conda activate DouyinCrawler
```

**方式二：使用 Python venv**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

> 💡 **提示**：两种方式都可以，选择你熟悉的方式即可

#### 3️⃣ 安装依赖

```bash
pip install -r requirements.txt
```


#### 4️⃣ 配置账号

编辑 `config/accounts_cookies.xlsx`，在 `dy` 工作表中添加账号信息：
- `account_name`: 账号名称
- `cookies`: Cookie 字符串

#### 5️⃣ 启动爬虫

```bash
python main.py --type creator
```

## 📁 项目结构

```
DouyinCrawler/
├── main.py                      # 程序入口
├── config/                      # 配置文件目录
│   ├── base_config.py          # 基础配置
│   ├── db_config.py           # Redis配置（可选）
│   └── proxy_config.py        # 代理配置
├── douyin/                      # 抖音爬虫核心实现
│   ├── core.py                # 爬虫核心类
│   ├── client.py               # API 客户端
│   ├── extractor.py            # 数据提取器
│   ├── handlers/              # 处理器
│   │   ├── search_handler.py    # 搜索处理器
│   │   ├── detail_handler.py    # 详情处理器
│   │   ├── creator_handler.py   # 创作者处理器
│   │   └── homefeed_handler.py  # 首页处理器
│   └── processors/            # 数据处理器
│       ├── aweme_processor.py   # 视频处理器
│       └── comment_processor.py # 评论处理器
├── pkg/                        # 公共工具包
│   ├── account_pool/          # 账号池管理
│   ├── proxy/                 # 代理IP池
│   ├── cache/                 # 缓存系统
│   ├── sign/                   # 签名模块
│   │   └── douyin_sign.py     # 签名逻辑
│   ├── js/                     # JavaScript签名代码
│   │   └── douyin.js          # JS逆向代码
│   └── tools/                 # 工具函数
├── repo/                       # 数据存储层
│   ├── accounts_cookies/      # 账号存储管理
│   ├── checkpoint/            # 断点续爬
│   └── platform_save_data/     # 平台数据存储
├── model/                      # 数据模型
└── constant/                   # 常量定义
```

## ⚙️ 配置说明

### 基础配置 (`config/base_config.py`)

```python
# 爬取类型：search / detail / creator / homefeed
CRAWLER_TYPE = "creator"

# 数据存储方式：csv / json
SAVE_DATA_OPTION = "csv"

# 签名类型
SIGN_TYPE = "javascript"

# 是否启用断点续爬
ENABLE_CHECKPOINT = True

# 断点存储方式：file / redis
CHECKPOINT_STORAGE_TYPE = "file"
```

### Redis 配置（可选）

如果使用 Redis 缓存或断点存储，配置 `config/db_config.py`：

```python
REDIS_DB_HOST = "127.0.0.1"
REDIS_DB_PORT = 6379
REDIS_DB_PWD = "your_password"
```

## 📖 使用示例

### 爬取创作者主页

```bash
# 通过命令行参数
python main.py --type creator --user_ids "MS4wLjABAAAA..."

# 通过配置文件
# 编辑 config/base_config.py，设置 DY_CREATOR_ID_LIST
python main.py --type creator
```

### 关键词搜索

```bash
python main.py --type search --keywords "Python编程"
```

### 视频详情

```bash
# 编辑 config/base_config.py，设置 DY_SPECIFIED_ID_LIST
python main.py --type detail
```

### 首页推荐

```bash
python main.py --type homefeed
```

## 📊 数据存储位置

### CSV存储
- 视频数据：`data/douyin/{编号}_{类型}_contents_{日期}.csv`
- 评论数据：`data/douyin/{编号}_{类型}_comments_{日期}.csv`
- 创作者数据：`data/douyin/{编号}_{类型}_creator_{日期}.csv`

### JSON存储
- 视频数据：`data/douyin/json/{类型}_contents_{日期}.json`
- 评论数据：`data/douyin/json/{类型}_comments_{日期}.json`
- 创作者数据：`data/douyin/json/{类型}_creator_{日期}.json`

## 🔧 工作流程

```
1. 初始化
   ├── 加载账号池
   ├── 初始化代理池（可选）
   ├── 初始化签名逻辑
   └── 加载断点（可选）
   ↓
2. 选择处理器
   ├── search_handler: 关键词搜索
   ├── detail_handler: 视频详情
   ├── creator_handler: 创作者主页
   └── homefeed_handler: 首页推荐
   ↓
3. 发送请求
   ├── 构造请求参数
   ├── 生成签名
   └── 发送 HTTP 请求
   ↓
4. 数据处理
   ├── 提取数据
   ├── 处理数据
   └── 保存到文件
```

> 📖 **详细说明**：想了解每一步具体执行哪些代码文件，请查看 [代码运行逻辑详解](docs/代码运行逻辑详解.md)

## ⚠️ 注意事项

1. 合理设置并发数：建议 `MAX_CONCURRENCY_NUM = 1-3`，避免对平台造成压力
2. 控制爬取频率：建议 `CRAWLER_TIME_SLEEP >= 1` 秒
3. 确保账号有效：配置有效的抖音 Cookie
4. 安装依赖：确保已安装 `PyExecJS` 和 Node.js
5. 遵守平台规则：仅供学习研究使用，不得用于商业用途

## 🔗 相关文档

- [环境配置指南](docs/环境配置指南.md) - 详细的环境配置步骤
- [快速开始指南](docs/快速开始.md) - 快速上手使用
- [代码运行逻辑详解](docs/代码运行逻辑详解.md) - 详细的运行流程和代码执行路径
- [代码文件说明](docs/代码文件说明.md) - 每个文件的作用和实现原理
- [开发指南](docs/开发指南.md) - 项目架构和开发相关
- [账号配置说明](config/README_accounts_cookies.md) - 账号配置详细说明

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。详情请查看项目根目录下的 LICENSE 文件。

## 🙏 致谢

本项目在开发过程中参考了 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) 及其衍生项目的部分设计思路，在此表示感谢。

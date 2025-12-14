# 账号Cookie配置文件说明

## 文件位置
`config/accounts_cookies.xlsx`

## 文件格式

### Sheet名称
- 每个Sheet对应一个平台
- 抖音平台使用Sheet名称：`dy`

### 列说明

| 列名 | 是否必填 | 说明 |
|------|---------|------|
| id | 可选 | 账号ID，如果不填写会自动递增（从1开始） |
| account_name | **必填** | 账号名称，用于标识账号（例如：账号1、测试账号等） |
| cookies | **必填** | 账号的Cookie字符串，从浏览器中提取 |

### 示例数据

| id | account_name | cookies |
|----|--------------|---------|
| 1 | 示例账号1 | sessionid=xxx; ms_token=yyy; 请替换为真实的Cookie |

## 如何获取Cookie

### 方法1：使用Cookie-Editor插件（推荐）

1. 安装Chrome插件：[Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm)
2. 在Chrome浏览器中登录抖音账号
3. 点击Cookie-Editor插件图标
4. 点击"Export"按钮，选择"Export as Netscape"
5. 复制导出的Cookie字符串，粘贴到Excel文件的`cookies`列中

### 方法2：手动提取

1. 在Chrome浏览器中登录抖音账号
2. 按F12打开开发者工具
3. 切换到"Application"标签
4. 左侧选择"Cookies" -> 选择抖音网站域名
5. 复制所有Cookie，格式为：`name1=value1; name2=value2; ...`
6. 粘贴到Excel文件的`cookies`列中

## 注意事项

1. **Cookie格式**：Cookie字符串应该使用分号（`;`）分隔各个Cookie项
2. **Cookie有效性**：Cookie可能会过期，如果爬虫提示账号失效，需要重新提取Cookie并更新
3. **多个账号**：可以在Excel中添加多行，每行一个账号，程序会自动轮换使用
4. **Sheet名称**：确保Sheet名称与平台名称一致（抖音使用`dy`）

## 使用示例

### 添加账号步骤

1. 打开`config/accounts_cookies.xlsx`文件
2. 切换到`dy` Sheet（如果没有则创建）
3. 添加一行数据：
   - `id`: 1（或留空，程序会自动分配）
   - `account_name`: 我的抖音账号1
   - `cookies`: sessionid=abc123; ms_token=xyz789; ...
4. 保存文件
5. 重新运行爬虫程序

### 多账号配置示例

| id | account_name | cookies |
|----|--------------|---------|
| 1 | 账号1 | sessionid=xxx1; ms_token=yyy1; ... |
| 2 | 账号2 | sessionid=xxx2; ms_token=yyy2; ... |
| 3 | 账号3 | sessionid=xxx3; ms_token=yyy3; ... |

程序会按照顺序轮换使用这些账号，降低单个账号被封的风险。

## 常见问题

### Q: Cookie过期了怎么办？
A: 重新登录账号，提取新的Cookie，更新Excel文件中的对应行即可。

### Q: 可以添加多少个账号？
A: 理论上没有限制，但建议根据实际需求添加，一般3-5个账号即可。

### Q: 账号被封了怎么办？
A: 程序会自动标记账号为无效状态，如果所有账号都失效，程序会抛出异常。需要添加新的有效账号。

### Q: 如何查看账号状态？
A: 程序运行时会输出日志，显示当前使用的账号信息。如果账号失效，日志中会显示"账号失效"的提示。

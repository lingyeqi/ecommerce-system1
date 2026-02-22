# Simple E-commerce Platform API

基于 Flask 和 SQL Server 的电商平台后端 API，支持消费者、商家、平台管理员三种角色。提供用户注册登录、商家店铺管理、商品管理、订单处理、物流跟踪、销售统计等功能，适用于中小型电商应用的后端服务。

## 技术栈
- **后端**：Python 3.x、Flask
- **数据库**：SQL Server（通过 pyodbc 连接，需安装 ODBC Driver 17）
- **其他**：Flask-CORS（跨域支持）、pyodbc

## 快速开始
### 环境要求
- Python 3.6 或更高版本
- SQL Server（需安装 ODBC Driver 17 for SQL Server）
- pip 包管理工具

### 安装步骤
1. 克隆本仓库到本地。
2. 安装所需 Python 包：
   ```bash
   pip install flask pyodbc flask-cors

运行应用：

bash
python app.py
服务默认运行在 http://127.0.0.1:5001。

数据库设计
主要表结构及作用：

customer：存储消费者信息
字段：customerid、nickname、name、gender、email、phonenumber

merchant：存储商家信息
字段：merchantid、name、password、email、phone

shop：存储店铺信息
字段：shopid、shopname、merchantid、shopaddress、merchantname、licensenumber、idcard、shoptype、sales

product：存储商品信息
字段：productid、productname、category、salenumber、price、status、shopid

product_salenumber：记录商品销量（用于统计）
字段：productid、salenumber、shopid 等

order1：存储订单信息
字段：orderid、customerid、paytime、orderpay、paystatus、orderstatus、paymethod、address、quantity、productid

logistics：存储物流信息
字段：orderid、tracknumber、companyname、telephone

此外，为简化查询创建了若干视图，如 order_product_view、combined_order_view、MerchantShopView，用于订单详情、物流合并、商家店铺信息联合展示。

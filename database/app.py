from flask import Flask, request, jsonify
import pyodbc
import random
from flask_cors import CORS
import datetime
import string

def generate_random_id():
    # 生成十位随机 id，由 26 个大写英文字母和 10 个数字组成
    all_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(random.choices(all_chars, k=10))


app = Flask(__name__)
CORS(app, supports_credentials=True)


# 配置数据库连接
server = 'LAPTOP-7IEPPVOB'
database = 'WORK3'
username ='ZL'
password = '123456ZL'
try:
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
except pyodbc.Error as e:
    print("数据库连接错误: {e}")
    # 这里可以根据需求返回合适的错误信息给客户端
    exit(1)


# 根路由
@app.route('/')
def home():
    return jsonify({"message": "欢迎来到首页!"})

# 用户登录--1.html
@app.route('/login', methods=['GET'])
def login():
    phone = request.args.get('phone')
    password = request.args.get('password')
    if not phone or not password:
        return jsonify({"message": "电话和密码是必需的"}), 400

    try:
        cursor = conn.cursor()
        # 首先从 login 表中获取用户角色
        sql = "SELECT role FROM login WHERE phonenumber =? AND password =?"
        cursor.execute(sql, (phone, password))
        result = cursor.fetchone()

        if not result:
            # 如果没有找到匹配的记录，返回错误信息
            return jsonify({"message": "无效的电话或密码."}), 401

        role = result[0]
        response_data = {"message": "登录成功.", "role": role}

        # 根据角色获取更多信息
        if role == 'Merchant':
            # 从 merchant 表中获取商家名称
            sql = "SELECT name FROM merchant WHERE phone =?"
            cursor.execute(sql, (phone,))
            merchant_result = cursor.fetchone()
            if merchant_result:
                response_data['merchantname'] = merchant_result[0]
        elif role == 'Customer':
            # 从 customer 表中获取消费者昵称等信息（如果有需要）
            sql = "SELECT nickname FROM customer WHERE phonenumber =?"
            cursor.execute(sql, (phone,))
            customer_result = cursor.fetchone()
            if customer_result:
                response_data['nickname'] = customer_result[0]

        return jsonify(response_data)

    except pyodbc.Error as e:
        print("数据库查询错误: {e}")
        return jsonify({"message": "数据库查询错误"}), 500

# 用户注册--1.html
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"message": "请求数据为空"}), 400
    try:
        cursor = conn.cursor()
        if data['role'] == 'Customer':
            # 生成 10 位 customerid
            customerid = generate_random_id()
            sql = "INSERT INTO customer (customerid, nickname, password, name, gender, email, phonenumber) VALUES (?,?,?,?,?,?,?)"
            cursor.execute(sql, (customerid, data['nickname'], data['password'], data['name'], data['gender'], data['email'], data['phone']))
        elif data['role'] == 'Merchant':
            # 生成 10 位 merchantid
            merchantid = generate_random_id()
            sql = "INSERT INTO merchant (merchantid, name, password, email, phone) VALUES (?,?,?,?,?)"
            cursor.execute(sql, (merchantid, data['name'], data['password'], data['email'], data['phone']))
        conn.commit()
        return jsonify({"message": "Registered successfully."})
    except pyodbc.Error as e:
        print("数据库插入错误: {e}")
        conn.rollback()
        return jsonify({"message": "数据库插入错误"}), 500

# 商家注册店铺 -merchant.html
@app.route('/register_shop', methods=['POST'])
def register_shop():
    data = request.get_json()
    if not data:
        return jsonify({"message": "请求数据为空"}), 400
    try:
        cursor = conn.cursor()
        # 生成 10 位 shopid
        shopid = generate_random_id()
        merchantname = data.get('merchantname')
        if not merchantname:
            return jsonify({"message": "商家名称是必需的"}), 400
        # 查询 merchantid 根据 merchantname
        cursor.execute("SELECT merchantid FROM merchant WHERE name =?", (merchantname,))
        merchant_result = cursor.fetchone()
        if not merchant_result:
            return jsonify({"message": "商家名称不存在，请先注册商家"}), 400
        merchantid = merchant_result[0]
        shopname = data.get('shopname')
        if not shopname:
            return jsonify({"message": "店铺名称是必需的"}), 400
        shopaddress = data.get('shopaddress')
        if not shopaddress:
            return jsonify({"message": "店铺地址是必需的"}), 400
        licensenumber = data.get('licensenumber')
        if not licensenumber:
            return jsonify({"message": "营业执照编号是必需的"}), 400
        idcard = data.get('idcard')
        if not idcard:
            return jsonify({"message": "身份证号是必需的"}), 400
        shoptype = data.get('shoptype')
        if not shoptype:
            return jsonify({"message": "店铺类型是必需的"}), 400
        sql = "INSERT INTO shop (shopid, shopname, merchantid, shopaddress, merchantname, licensenumber, idcard, shoptype) VALUES (?,?,?,?,?,?,?,?)"
        cursor.execute(sql, (shopid, shopname, merchantid, shopaddress, merchantname, licensenumber, idcard, shoptype))
        conn.commit()
        return jsonify({"message": "店铺注册成功."})
    except pyodbc.Error as e:
        print("数据库插入错误: {e}")
        conn.rollback()
        return jsonify({"message": "店铺注册时数据库插入错误"}), 500

# 获取商家注册的店铺 -merchant.html（已注册店铺部分）
@app.route('/get_merchant_shops', methods=['GET'])
def get_merchant_shops():
    phone = request.args.get('phone')
    if not phone:
        return jsonify({"message": "电话是必需的"}), 400
    try:
        cursor = conn.cursor()
        # 先根据 phone 获取 merchantid
        cursor.execute("SELECT merchantid FROM merchant WHERE phone =?", (phone,))
        merchant_result = cursor.fetchone()
        if not merchant_result:
            return jsonify({"message": "未找到该商家信息"}), 400
        merchantid = merchant_result[0]
        sql = "SELECT shopname, shopaddress, licensenumber, idcard, shoptype FROM shop WHERE merchantid =?"
        cursor.execute(sql, (merchantid,))
        shops = []
        for row in cursor:
            shop = {
                "shopname": row[0],
                "shopaddress": row[1],
                "licensenumber": row[2],
                "idcard": row[3],
                "shoptype": row[4]
            }
            shops.append(shop)
        return jsonify({"shops": shops})
    except pyodbc.Error as e:
        print(f"数据库查询错误: {e}")
        return jsonify({"message": "数据库查询错误"}), 500

# 销售统计（统计商品销量和店铺销售额） -merchant.html
@app.route('/statistics', methods=['GET'])
def statistics():
    phone = request.args.get('phone')
    if not phone:
        return jsonify({"message": "电话是必需的"}), 400
    try:
        cursor = conn.cursor()
        # 先根据 phone 获取 merchantid
        cursor.execute("SELECT merchantid FROM merchant WHERE phone =?", (phone,))
        merchant_result = cursor.fetchone()
        if not merchant_result:
            return jsonify({"message": "未找到该商家信息"}), 400
        merchantid = merchant_result[0]

        # 获取商品销量统计数据
        sql_product_sales = """
            SELECT p.productid, p.productname, p.category, ps.salenumber, p.price, ps.shopid, s.shopname
            FROM product_salenumber ps
            JOIN shop s ON ps.shopid = s.shopid
            JOIN product p ON ps.productid = p.productid
            WHERE s.merchantid =?
            ORDER BY ps.salenumber DESC
        """
        cursor.execute(sql_product_sales, (merchantid,))
        product_sales = []
        for row in cursor:
            sale = {
                "productid": row[0],
                "productname": row[1],
                "category": row[2],
                "salenumber": row[3],
                "price": row[4],
                "shopid": row[5],
                "shopname": row[6]
            }
            product_sales.append(sale)

        # 获取店铺总销售额统计数据
        sql_shop_sales = """
            SELECT shopid, shopname, sales, merchantname
            FROM shop
            WHERE merchantid =?
            ORDER BY sales DESC
        """
        cursor.execute(sql_shop_sales, (merchantid,))
        shop_sales = []
        for row in cursor:
            sale = {
                "shopid": row[0],
                "shopname": row[1],
                "sales": row[2],
                "merchantname": row[3]
            }
            shop_sales.append(sale)

        return jsonify({
            "product_sales": product_sales,
            "shop_sales": shop_sales
        })

    except pyodbc.Error as e:
        print(f"数据库查询错误: {e}")
        return jsonify({"message": "数据库查询错误"}), 500

# 订单管理（查看订单信息）-- merchant.html
@app.route('/get_merchant_orders', methods=['GET'])
def get_merchant_orders():
    phone = request.args.get('phone')
    if not phone:
        return jsonify({"message": "电话是必需的"}), 400
    try:
        cursor = conn.cursor()
        # 先根据 phone 获取 merchantid
        cursor.execute("SELECT merchantid FROM merchant WHERE phone =?", (phone,))
        merchant_result = cursor.fetchone()
        if not merchant_result:
            return jsonify({"message": "未找到该商家信息"}), 400
        merchantid = merchant_result[0]
        # 从 order_product_view 中根据 merchantid 获取所需的订单信息
        sql_order = "SELECT orderid,customerid,nickname,paytime,productname,price,quantity,orderpay,paymethod,paystatus,orderstatus,address FROM order_product_view WHERE merchantid =?"
        cursor.execute(sql_order, (merchantid,))
        orders = []
        for row in cursor:
            order = {
                "orderid": row[0],
                "customerid": row[1],
                "nickname": row[2],
                "paytime": str(row[3]),  # 将 datetime 对象转换为字符串
                "productname": row[4],
                "price": row[5],
                "quantity": row[6],
                "orderpay": row[7],
                "paymethod": row[8],
                "paystatus": row[9],
                "orderstatus": row[10],
                "address": row[11]
            }
            orders.append(order)
        return jsonify({"orders": orders})
    except pyodbc.Error as e:
        print(f"数据库查询错误: {e}")
        return jsonify({"message": "数据库查询错误"}), 500

# 商品管理（添加商品）-- merchant.html
@app.route('/add_product', methods=['POST'])
def add_product():
    data = request.get_json()
    if not data:
        return jsonify({"message": "请求数据为空"}), 400
    try:
        cursor = conn.cursor()
        productid = generate_random_id()
        productname = data.get('productname')
        category = data.get('category')
        price = data.get('price')
        status = data.get('status')
        shopname = data.get('shopname')

        if not productname or not category or not price or not shopname:
            return jsonify({"message": "商品名称、商品类别、商品单价和店铺名称是必需的"}), 400

        # 查询当前店铺的 shopid
        cursor.execute("SELECT shopid FROM shop WHERE shopname =?", (shopname,))
        shop_result = cursor.fetchone()
        if not shop_result:
            return jsonify({"message": "未找到该店铺信息"}), 400
        shopid = shop_result[0]

        sql = "INSERT INTO product (productid, productname, category, salenumber, price, status, shopid) VALUES (?,?,?,?,?,?,?)"
        cursor.execute(sql, (productid, productname, category, 0, price, status, shopid))
        conn.commit()
        return jsonify({"message": "商品添加成功.", "productId": productid})
    except pyodbc.Error as e:
        print("数据库插入错误: {e}")
        conn.rollback()
        return jsonify({"message": "商品添加时数据库插入错误"}), 500

# 商品管理（删除商品）-- merchant.html
@app.route('/delete_products', methods=['POST'])
def delete_products():
    data = request.get_json()
    if not data:
        return jsonify({"message": "请求数据为空"}), 400
    productIds = data.get('productIds')
    if not productIds:
        return jsonify({"message": "未提供要删除的商品ID"}), 400
    try:
        cursor = conn.cursor()
        for productid in productIds:
            sql = "DELETE FROM product WHERE productid =?"
            cursor.execute(sql, (productid,))
        conn.commit()
        return jsonify({"message": "商品删除成功."})
    except pyodbc.Error as e:
        print(f"数据库删除错误: {e}")
        conn.rollback()
        return jsonify({"message": "商品删除时数据库错误"}), 500

# 商品管理（编辑商品）-- merchant.html
@app.route('/edit_product', methods=['POST'])
def edit_product():
    data = request.get_json()
    if not data:
        return jsonify({"message": "请求数据为空"}), 400
    try:
        cursor = conn.cursor()
        productid = data.get('productId')
        category = data.get('category')
        price = data.get('price')
        status = data.get('status')

        if not productid or not category or not price:
            return jsonify({"message": "商品 ID、商品类别、商品单价是必需的"}), 400

        # 更新商品信息
        sql = "UPDATE product SET category =?, price =?, status =? WHERE productid =?"
        cursor.execute(sql, (category, price, status, productid))
        conn.commit()
        return jsonify({"message": "商品信息更新成功."})
    except pyodbc.Error as e:
        print(f"数据库更新错误: {e}")
        conn.rollback()
        return jsonify({"message": "商品更新时数据库错误"}), 500

# 商品管理（查看商品信息）-- merchant.html
@app.route('/get_merchant_products', methods=['GET'])
def get_merchant_products():
    phone = request.args.get('phone')
    if not phone:
        return jsonify({"message": "电话是必需的"}), 400
    try:
        cursor = conn.cursor()
        # 先根据 phone 获取 merchantid
        cursor.execute("SELECT merchantid FROM merchant WHERE phone =?", (phone,))
        merchant_result = cursor.fetchone()
        if not merchant_result:
            return jsonify({"message": "未找到该商家信息"}), 400
        merchantid = merchant_result[0]
        # 根据 merchantid 获取 shopid
        cursor.execute("SELECT shopid FROM shop WHERE merchantid =?", (merchantid,))
        shop_results = cursor.fetchall()
        if not shop_results:
            return jsonify({"message": "该商家没有注册店铺"}), 400
        shopids = [result[0] for result in shop_results]
        placeholders = ', '.join(['?'] * len(shopids))
        sql = "SELECT p.productid, p.productname, p.category, p.salenumber, p.price, p.status, s.shopname " \
              "FROM product p " \
              "JOIN shop s ON p.shopid = s.shopid " \
              "WHERE s.shopid IN (%s)" % placeholders
        cursor.execute(sql, shopids)
        products = []
        for row in cursor:
            product = {
                "productid": row[0],
                "productname": row[1],
                "category": row[2],
                "salenumber": row[3],
                "price": row[4],
                "status": row[5],
                "shopname": row[6]
            }
            products.append(product)
        return jsonify({"products": products})
    except pyodbc.Error as e:
        print(f"数据库查询错误: {e}")
        return jsonify({"message": "数据库查询错误"}), 500

# 物流信息（生成快递单号） --logistics.html
@app.route('/generate_tracking_number', methods=['GET'])
def generate_tracking_number():
    while True:
        # 定义包含数字和大写字母的字符集
        characters = string.digits + string.ascii_uppercase
        # 从字符集中随机选择 12 个字符
        tracking_number = ''.join(random.choices(characters, k=12))
        cursor = conn.cursor()
        # 检查该单号是否已存在
        sql = "SELECT COUNT(*) FROM [dbo].[logistics] WHERE tracknumber =?"
        cursor.execute(sql, (tracking_number,))
        result = cursor.fetchone()
        if result[0] == 0:  # 如果结果为 0，则该单号不存在
            break
    return tracking_number

# 物流信息（添加物流信息） --logistics.html
@app.route('/add_logistics_info', methods=['POST'])
def add_logistics_info(conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)):
    try:
        data = request.get_json()
        print("Received data:", data)  # 打印接收到的数据
        cursor = conn.cursor()
        sql = """
        INSERT INTO [dbo].[logistics] (orderid, tracknumber, companyname, telephone)
        VALUES (?,?,?,?)
        """
        cursor.execute(sql, (data['orderNumber'], data['trackingNumber'], data['company'], data['contactNumber']))
        conn.commit()
        return jsonify({"message": "物流信息添加成功"})
    except pyodbc.Error as e:
        print("数据库插入错误: {e}")
        conn.rollback()

#物流信息（一键发货） --logistics.html
@app.route('/ship_all_orders', methods=['POST'])
def ship_all_orders():
    try:
        cursor = conn.cursor()
        # 更新 order1 表中 paystatus 为已支付的记录的 orderstatus 为已发货
        sql = "UPDATE order1 SET order1.orderstatus = '已发货' FROM order1 JOIN combined_order_view ON order1.orderid = combined_order_view.orderid;"
        cursor.execute(sql)
        conn.commit()
        return jsonify({"message": "所有订单已发货"})
    except pyodbc.Error as e:
        print("数据库更新错误: {e}")
        conn.rollback()
        return jsonify({"message": "数据库更新错误"}), 500

#物流信息（查看物流信息） --logistics.html
@app.route('/get_all_logistics_info', methods=['GET'])
def get_all_logistics_info():
    try:
        cursor = conn.cursor()
        sql = """
        SELECT orderid, tracknumber, companyname, telephone, orderstatus
        FROM [dbo].[combined_order_view]
        """
        cursor.execute(sql)
        results = cursor.fetchall()
        logistics_info = []
        for row in results:
            item = {
                "orderNumber": row[0],
                "trackingNumber": row[1],
                "company": row[2],
                "contactNumber": row[3],
                "status": row[4]
            }
            logistics_info.append(item)
        return jsonify(logistics_info)
    except pyodbc.Error as e:
        print("数据库查询错误: {e}")
        return jsonify({"message": "数据库查询错误"}), 500

#物流信息（获取已支付的订单） --logistics.html
@app.route('/get_paid_order_ids', methods=['GET'])
def get_paid_order_ids():
    try:
        cursor = conn.cursor()
        # 查询 order1 表中 paystatus 为已支付的 orderid
        sql = "SELECT orderid FROM order1 WHERE paystatus = '已支付'"
        cursor.execute(sql)
        results = cursor.fetchall()
        order_ids = [row[0] for row in results]
        return jsonify(order_ids)
    except pyodbc.Error as e:
        print(f"数据库查询错误: {e}")
        return jsonify({"message": "数据库查询错误"}), 500

#物流信息（获取已支付的订单的订单状态） --logistics.html
@app.route('/get_order_status', methods=['GET'])
def get_order_status():
    order_id = request.args.get('orderId')
    if not order_id:
        return jsonify({"message": "订单号是必需的"}), 400
    try:
        cursor = conn.cursor()
        # 查询 order1 表中指定 orderid 的 orderstatus
        sql = "SELECT orderstatus FROM order1 WHERE orderid =?"
        cursor.execute(sql, (order_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return jsonify({"message": "未找到该订单信息"}), 404
    except pyodbc.Error as e:
        print(f"数据库查询错误: {e}")
        return jsonify({"message": "数据库查询错误"}), 500

#物流信息（删除物流信息） --logistics.html
@app.route('/delete_logistics_info', methods=['POST'])
def delete_logistics_info():
    try:
        data = request.get_json()
        track_number = data.get('trackNumber')
        if not track_number:
            return jsonify({"message": "快递单号是必需的"}), 400
        cursor = conn.cursor()
        sql = "DELETE FROM [dbo].[logistics] WHERE tracknumber = ?"
        cursor.execute(sql, (track_number,))
        conn.commit()
        return jsonify({"message": "物流信息删除成功"})
    except pyodbc.Error as e:
        print("数据库删除错误: {e}")
        conn.rollback()
        return jsonify({"message": "数据库删除错误"}), 500

#购买商品（查看商品信息） --custoemr.html
@app.route('/get_all_products', methods=['GET'])
def get_all_products():
    try:
        with conn.cursor() as cursor:
            # 查询 product 表和 shop 表连接的内容
            sql = """  
            SELECT   
                p.productid,  
                p.productname,  
                p.category,  
                p.shopid,  
                s.shopname,  
                p.salenumber,  
                p.price,  
                p.status   
            FROM   
                product p  
            LEFT JOIN   
                shop s ON p.shopid = s.shopid;  
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            if results:
                products = []
                for row in results:
                    products.append({
                        "productid": row[0],
                        "productname": row[1],
                        "category": row[2],
                        "shopid": row[3],
                        "shopname": row[4],
                        "salenumber": row[5],
                        "price": row[6],
                        "status": row[7]
                    })
                return jsonify({
                    "message": "All products retrieved successfully.",
                    "products": products
                }), 200
            else:
                return jsonify({"message": "No products found."}), 404
    except pyodbc.Error as e:
        print(f"数据库查询错误: {e}")
        return jsonify({"message": "Internal server error."}), 500

#购买商品（确认提交订单） --custoemr.html
@app.route('/place_order', methods=['POST'])
def place_order():
    data = request.get_json()
    if not data:
        return jsonify({"message": "请求数据为空"}), 400
    try:
        cursor = conn.cursor()
        # 从前端接收的数据中获取所需信息
        payment_method = data.get('paymentMethod')
        print(payment_method)
        address = data.get('address')
        price = float(data.get('price'))
        quantity = int(data.get('quantity'))
        shop_name = data.get('shopName')
        phonenumber = data.get('phonenumber')  # 从 JSON 数据中获取手机号
        print(phonenumber)
        productid = data.get('productId')

        # 假设从前端可以获取用户手机号，根据手机号查找 customerid
        if not phonenumber:
            return jsonify({"message": "未找到手机号信息，请检查登录状态。"}), 400
        cursor.execute("SELECT customerid FROM customer WHERE phonenumber =?", (phonenumber,))
        customer_result = cursor.fetchone()
        if not customer_result:
            return jsonify({"message": "未找到用户信息，请检查手机号是否正确。"}), 400
        customer_id = customer_result[0]

        # 生成 orderid，同一家店铺的所有商品为一个订单号，不同店铺订单号不同
        cursor.execute("SELECT shopid FROM shop WHERE shopname =?", (shop_name,))
        shop_result = cursor.fetchone()
        if not shop_result:
            return jsonify({"message": "未找到店铺信息，请检查店铺名称是否正确。"}), 400
        shop_id = shop_result[0]
        order_id = generate_random_id()
        # 获取生成订单的时间
        pay_time = datetime.datetime.now()
        # 计算订单总价
        order_pay = price * quantity
        # 订单状态默认为已支付和未发货
        pay_status = "已支付"
        order_status = "未发货"
        # 插入订单信息到 order1 表
        sql = """
        INSERT INTO order1 (orderid, customerid, paytime, orderpay, paystatus, orderstatus, paymethod, address, quantity, productid)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """
        cursor.execute(sql, (order_id, customer_id, pay_time, order_pay, pay_status, order_status, payment_method, address, quantity,productid))
        conn.commit()
        return jsonify({"message": "订单创建成功。"})
    except pyodbc.Error as e:
        print("数据库插入错误: {e}")
        conn.rollback()
        return jsonify({"message": "订单创建失败，请检查输入数据或联系管理员。"}), 500

#我的订单（查看我的订单） --custoemr.html
@app.route('/get_orders', methods=['GET'])
def get_orders():
    phonenumber = request.args.get('phonenumber')
    if not phonenumber:
        return jsonify({"message": "电话是必需的"}), 400
    try:
        cursor = conn.cursor()
        # 先根据 phonenumber 获取 customerid
        cursor.execute("SELECT customerid FROM customer WHERE phonenumber =?", (phonenumber,))
        customer_result = cursor.fetchone()
        if not customer_result:
            return jsonify({"message": "未找到该商家信息"}), 400
        customerid = customer_result[0]
        # 从 order_product_view 中根据 customerid 获取所需的订单信息
        sql = "SELECT orderid,paytime,productname,price,quantity,orderpay,paymethod,paystatus,orderstatus,address FROM order_product_view WHERE customerid =?"
        cursor.execute(sql, (customerid,))
        orders = []
        for row in cursor:
            order = {
                "orderid": row[0],
                "paytime": str(row[1]),  # 将 datetime 对象转换为字符串
                "productname": row[2],
                "price": row[3],
                "quantity": row[4],
                "orderpay": row[5],
                "paymethod": row[6],
                "paystatus": row[7],
                "orderstatus": row[8],
                "address": row[9]
            }
            orders.append(order)
        return jsonify({"orders": orders})
    except pyodbc.Error as e:
        print(f"数据库查询错误: {e}")
        return jsonify({"message": "数据库查询错误"}), 500

#我的订单（退款） --custoemr.html
@app.route('/refund_order', methods=['POST'])
def refund_order():
    try:
        data = request.get_json()
        print("接收到的请求数据:", data)  # 打印接收到的请求数据
        if not data:
            return jsonify({"message": "请求数据为空"}), 400
        orderid = data.get('orderid')
        print("尝试获取的 orderid:", orderid)  # 明确打印获取 orderid 的操作
        if not orderid:
            return jsonify({"message": "未提供订单 ID"}), 400
        cursor = conn.cursor()
        # 更新订单状态为退款，假设数据库表为 orders，字段为 order_status
        sql = "UPDATE order1 SET paystatus = '已退款' WHERE orderid =?"
        cursor.execute(sql, (orderid,))
        conn.commit()
        return jsonify({"message": "退款成功。"})
    except pyodbc.Error as e:
        print(f"数据库更新错误: {e}")
        conn.rollback()
        return jsonify({"message": "退款时数据库更新错误"}), 500
    except Exception as e:  # 捕获其他异常
        print(f"发生未知错误: {e}")
        return jsonify({"message": "发生未知错误，请检查日志。"}), 500

#我的物流信息（获取物流信息） --custoemr.html
@app.route('/get_logistics_info', methods=['GET'])
def get_logistics_info():
    try:
        cursor = conn.cursor()
        sql = "SELECT o.orderid, l.tracknumber, p.productname, o.address, o.orderpay, l.companyname, l.telephone, o.orderstatus FROM order1 o JOIN logistics l ON o.orderid = l.orderid JOIN product p ON o.productid = p.productid"
        cursor.execute(sql)
        results = cursor.fetchall()
        logistics_list = []
        for row in results:
            logistics = {
                "orderid": row[0],
                "tracknumber": row[1],
                "productname": row[2],
                "address": row[3],
                "orderpay": row[4],
                "companyname": row[5],
                "telephone": row[6],
                "orderstatus": row[7],

            }
            logistics_list.append(logistics)
        return jsonify( logistics_list)
    except pyodbc.Error as e:
        print(f"数据库查询错误: {e}")
        return jsonify({"message": "数据库查询错误"}), 500

#商家-店铺信息（获取商家及其对应的店铺信息） --manager.html
@app.route('/get_merchantshops', methods=['GET'])
def get_merchantshops():
    try:
        with conn.cursor() as cursor:
            # 查询 MerchantShopView 视图
            sql = """
            SELECT merchantid,name,phone,email,shopid,shopname,shopaddress,shoptype,idcard,licensenumber,sales FROM MerchantShopView;
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            if results:
                merchants = []
                for row in results:
                    merchant_data = {
                        'merchantid': row[0],
                        'merchantname': row[1],
                        'merchantphone': row[2],
                        'email': row[3],
                        'shopid': row[4],
                        'shopname': row[5],
                        'shopaddress': row[6],
                        'shoptype': row[7],
                        'idcard': row[8],
                        'licensenumber': row[9],
                        'sales': row[10]
                    }
                    merchants.append(merchant_data)
                # 使用 Python 对数据进行排序
                merchants.sort(key=lambda x: x['merchantid'])
                return jsonify({'merchants': merchants})
            else:
                return jsonify({'error': 'No data found'}), 404
    except pyodbc.Error as e:
        return jsonify({'error': str(e)}), 500

#商家-店铺信息（平台管理员删除店铺） --manager.html
@app.route('/delete_shop/<shopid>', methods=['DELETE'])
def delete_shop(shopid):
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM shop WHERE shopid = ?"
            cursor.execute(sql, (shopid,))
            conn.commit()
            return jsonify({"message": "店铺删除成功"}), 200
    except pyodbc.Error as e:
        print(f"数据库删除错误: {e}")
        return jsonify({"message": "删除失败"}), 500

#商家-店铺信息（搜索） --manager.html
@app.route('/search_merchant_shops', methods=['GET'])
def search_merchant_shops():
    merchantname = request.args.get('merchantname')
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT merchantid, name, phone, email, shopid, shopname, shopaddress, shoptype, idcard, licensenumber,sales
            FROM MerchantShopView
            WHERE name LIKE ?
            """
            cursor.execute(sql, (f'%{merchantname}%',))
            results = cursor.fetchall()
            if results:
                merchants = []
                for row in results:
                    merchant_data = {
                        'merchantid': row[0],
                        'merchantname': row[1],
                        'merchantphone': row[2],
                        'email': row[3],
                        'shopid': row[4],
                        'shopname': row[5],
                        'shopaddress': row[6],
                        'shoptype': row[7],
                        'idcard': row[8],
                        'licensenumber': row[9],
                        'sales': row[10]
                    }
                    merchants.append(merchant_data)
                return jsonify({'merchants': merchants})
            else:
                return jsonify({'error': 'No data found'}), 404
    except pyodbc.Error as e:
        return jsonify({'error': str(e)}), 500

#消费者信息（获取） --manager.html
@app.route('/get_consumers', methods=['GET'])
def get_consumers():
    try:
        with conn.cursor() as cursor:
            # 查询 customer 表的全部内容
            sql = """
            SELECT customerid,nickname,name,gender,phonenumber,email FROM customer;
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            if results:
                consumers = []
                for row in results:
                    consumer_data = {
                        'consumerid': row[0],
                        'nickname': row[1],
                        'name': row[2],
                        'gender': row[3],
                        'phone': row[4],
                        'email': row[5],
                    }
                    consumers.append(consumer_data)
                return jsonify({'consumers': consumers})
            else:
                return jsonify({'error': 'No data found'}), 404
    except pyodbc.Error as e:
        return jsonify({'error': str(e)}), 500

#订单信息（获取平台所有订单信息） --manager.html
@app.route('/get_managerorders', methods=['GET'])
def get_managerorders():
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT orderid, productname, orderpay, paystatus, orderstatus, nickname, merchant_name, shopname FROM order_product_view;
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            if results:
                orders = []
                for row in results:
                    order_data = {
                        'orderid': row[0],
                        'productname': row[1],
                        'orderpay': row[2],  # 确保字段名与数据库查询结果一致
                        'paystatus': row[3],
                        'orderstatus': row[4],
                        'nickname': row[5],
                        'merchantname': row[6],
                        'shopname': row[7]
                    }
                    orders.append(order_data)
                return jsonify({'orders': orders})
            else:
                return jsonify({'error': 'No data found'}), 404
    except pyodbc.Error as e:
        return jsonify({'error': str(e)}), 500

#订单信息（获取平台所有订单的详细信息） --manager.html
@app.route('/get_order_details/<orderid>', methods=['GET'])
def get_order_details(orderid):
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT orderid, productname, price, quantity, orderpay, paymethod, paytime, paystatus, orderstatus, address, customerid, nickname, merchantid, merchant_name, shopname 
            FROM order_product_view
            WHERE orderid = ?
            """
            cursor.execute(sql, (orderid,))
            results = cursor.fetchone()
            if results:
                order_data = {
                    'orderid': results[0],
                    'productname': results[1],
                    'price': results[2],
                    'quantity': results[3],
                    'orderpay': results[4],
                    'paymethod': results[5],
                    # 转换时间对象为字符串
                    'paytime': results[6].strftime('%Y-%m-%d %H:%M:%S') if results[6] else None,
                    'paystatus': results[7],
                    'orderstatus': results[8],
                    'address': results[9],
                    'consumerid': results[10],
                    'nickname': results[11],
                    'merchantid': results[12],
                    'merchantname': results[13],
                    'shopname': results[14]
                }
                return jsonify({'order': order_data})
            else:
                return jsonify({'error': 'Order not found'}), 404
    except pyodbc.Error as e:
        return jsonify({'error': str(e)}), 500

#订单信息（搜索） --manager.html
@app.route('/search_orders', methods=['GET'])
def search_orders():
    paystatus = request.args.get('paystatus')
    try:
        with conn.cursor() as cursor:
            # 根据支付状态搜索订单
            sql = """
            SELECT orderid, productname, orderpay, paystatus, orderstatus, nickname, merchant_name, shopname
            FROM order_product_view
            WHERE paystatus = ?
            """
            cursor.execute(sql, (paystatus,))
            results = cursor.fetchall()
            if results:
                orders = []
                for row in results:
                    order_data = {
                        'orderid': row[0],
                        'productname': row[1],
                        'orderpay': row[2],
                        'paystatus': row[3],
                        'orderstatus': row[4],
                        'nickname': row[5],
                        'merchantname': row[6],
                        'shopname': row[7]
                    }
                    orders.append(order_data)
                return jsonify({'orders': orders})
            else:
                return jsonify({'error': 'No data found'}), 404
    except pyodbc.Error as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
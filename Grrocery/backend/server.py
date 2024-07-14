from flask import Flask, request, render_template, redirect, url_for, session, flash
import base64
from backend import products
from backend.sql_connection import get_sql_connection
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'secret_key'


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        connection = get_sql_connection()
        user = products.get_user_by_username(connection, username)
        connection.close()
        
        if user:
            if password == user["password"]:
        
                session['user_id'] = user["user_id"]
                session['username'] = username
                return redirect(url_for("products_page"))
            else:
                error = "Incorrect password. Please try again."
        else:
            error = "User not found. Please check your username."
            return render_template("login.html", error=error)
    return render_template("login.html")


@app.route("/products/<int:category_id>")
@app.route("/products", defaults={'category_id': None})
def products_page(category_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if category_id is not None:
        connection = products.get_sql_connection()
        products_list = products.get_products_by_category(connection, category_id)
        categories = products.get_all_categories(connection)
        connection.close()
    else:
        
        connection = products.get_sql_connection()
        products_list = products.get_all_products(connection)
        categories = products.get_all_categories(connection)
        connection.close()
    
    for product in products_list:
        if product['image']:
            product['image'] = base64.b64encode(product['image']).decode('utf-8')
    
    return render_template("products.html", products=products_list, categories=categories)


@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    quantity = request.form.get("quantity")
    if quantity is not None:
        quantity = int(quantity)
    else:
        return redirect(url_for("products_page"))

    connection = products.get_sql_connection()
    product = products.get_product_by_id(connection, product_id)
    if product and 'image' in product:
        image_data = product['image']
    else:
        image_data = None
    products.add_to_cart(connection, user_id, product_id, quantity, image_data)
    connection.close()

    return redirect(url_for('cart_page'))

@app.route("/place_order", methods=["POST"])
def place_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    customer_name = session['username']

    connection = products.get_sql_connection()
    cart_items = products.get_cart_items(connection, user_id)
    total = sum(item['quantity'] * item['price_per_unit'] for item in cart_items)

    order_id = products.place_order(connection, customer_name, total, cart_items)
    if order_id:
        for item in cart_items:
            products.add_order_detail(connection, order_id, item['product_id'], item['quantity'], item['price_per_unit'])
        
        products.clear_cart_history(connection, user_id)
        connection.close()

        return redirect(url_for('order_confirmation'))
    else:
        connection.close()
        return "Error placing order"

    
@app.route("/remove_from_cart/<int:product_id>", methods=["GET", "POST"])
def remove_from_cart(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    connection = products.get_sql_connection()
    products.remove_from_cart(connection, user_id, product_id)
    connection.close()
    return redirect(url_for('cart_page'))


@app.route("/filter_by_category", methods=["POST"])
def filter_by_category():
    category = request.form.get("category") 
    connection = products.get_sql_connection()
    filtered_products = products.get_products_by_category(connection, category)
    connection.close()
    
    return render_template("products.html", products=filtered_products)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        connection = products.get_sql_connection()
        cursor = connection.cursor()
        query = "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, password, email))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('products_page'))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))


@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        product_name = request.form["product_name"]
        uom_id = request.form["uom_id"]
        price_per_unit = request.form["price_per_unit"]
        category_id = request.form["category_id"]

        image = request.files['image']
        image_data = image.read() if image else None

        connection = products.get_sql_connection()
        products.insert_new_product(connection, {
            "product_name": product_name,
            "uom_id": uom_id,
            "price_per_unit": price_per_unit,
            "image_data": image_data,
            "category_id": category_id 
        })
        connection.close()

        return redirect(url_for('products_page'))

    else:
        connection = products.get_sql_connection()
        categories = products.get_all_categories(connection)
        connection.close()
        return render_template("add_product.html", categories=categories)



@app.route("/products-list")
def products_list():
    connection = products.get_sql_connection()
    product_list = products.get_all_products(connection)
    connection.close()

    for product in product_list:
        if product['image']:
            product['image'] = base64.b64encode(product['image']).decode('utf-8')

    return render_template("products_list.html", products=product_list)


@app.route("/delete_product", methods=["POST"])
def delete_product():
    product_id = request.form.get("product_id")
    connection = products.get_sql_connection()
    products.delete_product(connection, product_id)
    connection.close()
    return redirect(url_for("products_list"))


@app.route("/edit_product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    connection = products.get_sql_connection()
    if request.method == "POST":
        product_name = request.form["product_name"]
        uom_id = request.form["uom_id"]
        price_per_unit = request.form["price_per_unit"]
        image = request.files['image']
        image_data = image.read() if image else None
        products.update_product(connection, product_id, product_name, uom_id, price_per_unit, image_data)
        connection.close()
        return redirect(url_for("products_list"))
    else:
        product = products.get_product_by_id(connection, product_id)
        connection.close()
        return render_template("edit_product.html", product=product)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category_name = request.form["category_name"]

        connection = products.get_sql_connection()
        products.insert_new_category(connection, category_name)
        connection.close()

        return redirect(url_for('products_page'))

    return render_template("add_category.html")


@app.route("/cart")
def cart_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    connection = products.get_sql_connection()
    cart_items = products.get_cart_items(connection, user_id)
    product_list = products.get_all_products(connection)
    connection.close()

    default_price_per_unit = 10.0  
    for item in cart_items:
        if 'price_per_unit' not in item:
            item['price_per_unit'] = default_price_per_unit
        for product in product_list:
            if product['product_id'] == item['product_id']:
                if product['image']:
                    item['image'] = base64.b64encode(product['image']).decode('utf-8')
                break

    return render_template("cart.html", cart_items=cart_items)

def calculate_total_price():
    total_price = 0
    connection=get_sql_connection()
    cart_items = products.get_cart_items(connection, session['user_id'])
    for item in cart_items:
        total_price += item['quantity'] * item['price_per_unit']
    return total_price

@app.route("/checkout", methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session['user_id']
        connection = get_sql_connection()
        cart_items = products.get_cart_items(connection, user_id)

        total_price = calculate_total_price()  

        order_id = products.process_order(user_id, total_price, cart_items, connection) 

        connection.close()

        if order_id:
            return redirect(url_for('order_confirmation'))
        else:
            flash("Error processing order. Please try again.", "error")
            return redirect(url_for('checkout'))
    else:
        return render_template("checkout.html")

def process_order(user_id, total_price, cart_items, connection):
    try:
        customer_name = session['username'] 

        order_id = place_order(connection, customer_name, total_price, cart_items)
        if order_id:
            products.clear_cart_history(connection, user_id)
            return order_id
        else:
            return None
    except Exception as e:
        print("Error processing order:", e)
        return None




@app.route("/order_history")
def order_history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    connection = products.get_sql_connection()
    user_orders = products.get_order_history(connection, user_id)
    connection.close()

    if user_orders is None:
        user_orders = []  # Handle case when no orders are found

    return render_template("order_history.html", user_orders=user_orders)


@app.route("/order_confirmation")
def order_confirmation():
    return render_template("order_confirmation.html")



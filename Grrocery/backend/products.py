
from mysql.connector import Error
from backend import sql_connection
import datetime
from flask import session

def get_all_products(connection):
    query = ("SELECT products.product_id, products.name, products.uom_id, products.price_per_unit, products.image, "
             "uom.uom_name, products.category_id FROM products INNER JOIN uom ON uom.uom_id = products.uom_id;")
    cursor = connection.cursor()
    cursor.execute(query)
    response = []
    for (product_id, name, uom_id, price_per_unit, image, uom_name, category_id) in cursor:
        response.append({'product_id': product_id, 'name': name, 'uom_id': uom_id, 'price_per_unit': price_per_unit, 'image': image, 'uom_name': uom_name, 'category_id': category_id})
    cursor.close()
    return response

def get_category_id(connection, category_name):
    try:
        cursor = connection.cursor()
        query = "SELECT category_id FROM categories WHERE category_name = %s"
        cursor.execute(query, (category_name,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return result[0]
        else:
            return None 
    except Error as e:
        print("Error fetching category ID:", e)
        return None
    
    
def insert_new_product(connection, product):
    try:
        query = "INSERT INTO products (name, uom_id, price_per_unit, image, category_id) VALUES (%s, %s, %s, %s, %s)"
        cursor = connection.cursor()
        cursor.execute(query, (product['product_name'], product['uom_id'], product['price_per_unit'], product['image_data'], product['category_id']))
        connection.commit()
        cursor.close()
    except Error as e:
        print("Error inserting product:", e)

def get_products_by_category(connection, category_id):
    try:
        query = ("SELECT products.product_id, products.name, products.uom_id, products.price_per_unit, products.image, "
                 "uom.uom_name, products.category_id FROM products "
                 "INNER JOIN uom ON uom.uom_id = products.uom_id "
                 "WHERE products.category_id = %s;")
        cursor = connection.cursor()
        cursor.execute(query, (category_id,))
        response = []
        for (product_id, name, uom_id, price_per_unit, image, uom_name, category_id) in cursor:
            response.append({'product_id': product_id, 'name': name, 'uom_id': uom_id,
                             'price_per_unit': price_per_unit, 'image': image, 'uom_name': uom_name, 'category_id': category_id})
        cursor.close()
        return response
    except Error as e:
        print("Error fetching products by category:", e)
        return None


def update_product(connection, product_id, product_name, uom_id, price_per_unit, image):
    try:
        query = "UPDATE products SET name = %s, uom_id = %s, price_per_unit = %s, image = %s WHERE product_id = %s"
        cursor = connection.cursor()
        cursor.execute(query, (product_name, uom_id, price_per_unit, image, product_id))
        connection.commit()
        cursor.close()
    except Error as e:
        print("Error updating product:", e)


def delete_product(connection, product_id):
    try:
        query = "DELETE FROM products WHERE product_id = %s"
        cursor = connection.cursor()
        cursor.execute(query, (product_id,))
        connection.commit()
        cursor.close()
    except Error as e:
        print("Error deleting product:", e)

def get_product_by_id(connection, product_id):
    try:
        query = "SELECT * FROM products WHERE product_id = %s"
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, (product_id,))
        product = cursor.fetchone()
        cursor.close()
        return product
    except Error as e:
        print("Error fetching product by ID:", e)
        return None

def get_all_product_names(connection):
    try:
        query = "SELECT name FROM products"
        cursor = connection.cursor()
        cursor.execute(query)
        product_names = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return product_names
    except Error as e:
        print("Error fetching product names:", e)
        return None
    
def get_all_categories(connection):
    try:
        query = "SELECT * FROM categories"
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        categories = cursor.fetchall()
        cursor.close()
        return categories
    except Error as e:
        print("Error fetching all categories:", e)
        return None

def insert_new_category(connection, category_name):
    try:
        query = "INSERT INTO categories (category_name) VALUES (%s)"
        cursor = connection.cursor()
        cursor.execute(query, (category_name,))
        connection.commit()
        cursor.close()
        print("Category added successfully!")
    except Error as e:
        print("Error inserting category:", e)

 ########################################################CART######################

def get_cart_item(connection, user_id, product_id):
    query = "SELECT * FROM cart_items WHERE user_id = %s AND product_id = %s"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, (user_id, product_id))
    cart_item = cursor.fetchone()
    cursor.close()
    return cart_item

def add_to_cart(connection, user_id, product_id, quantity, image=None):
    try:
        cursor = connection.cursor()
        query = "INSERT INTO cart_items (user_id, product_id, quantity, image) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (user_id, product_id, quantity, image))
        connection.commit()
        cursor.close()
        print("Product added to cart successfully.")
        return True
    except Error as e:
        print("Error adding product to cart:", e)
        return False


def remove_from_cart(connection, user_id, product_id):
    try:
        cursor = connection.cursor()
        query = "DELETE FROM cart_items WHERE user_id = %s AND product_id = %s"
        cursor.execute(query, (user_id, product_id))
        connection.commit()
        cursor.close()
        return True
    except Error as e:
        print("Error removing product from cart:", e)
        return False


def add_order_detail(connection, order_id, product_id, quantity, price_per_unit):
    try:
        cursor = connection.cursor()
        total_price = quantity * price_per_unit
        query = "INSERT INTO order_detail (order_id, product_id, quantity, total_price, price_per_unit) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (order_id, product_id, quantity, total_price, price_per_unit))
        connection.commit()
        cursor.close()
        return True
    except Error as e:
        print("Error adding order detail:", e)
        return False


def get_order_history(connection, user_id):
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
                SELECT od.order_id, p.name AS product_name, od.quantity, od.total_price, od.price_per_unit
                FROM order_detail od
                INNER JOIN products p ON od.product_id = p.product_id
                WHERE od.order_id = %s
                """
        cursor.execute(query, (user_id,))
        orders = cursor.fetchall()
        cursor.close()
        return orders

    except Exception as e:
        print(f"Error fetching order history for user_id {user_id}: {e}")
        return None



def get_user_by_username(connection, username):
    try:
        query = "SELECT * FROM users WHERE username = %s"
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        cursor.close()
        return user
    except Error as e:
        print("Error fetching user by username:", e)
        return None


def get_cart_items(connection, user_id):
    cursor = connection.cursor(dictionary=True)
    query = """
            SELECT ci.*, p.price_per_unit, p.name AS product_name, p.image
            FROM cart_items ci
            INNER JOIN products p ON ci.product_id = p.product_id
            WHERE ci.user_id = %s
            """
    cursor.execute(query, (user_id,))
    cart_items = cursor.fetchall()
    cursor.close()
    return cart_items



def remove_cart_item(connection, user_id, product_id):
    try:
        cursor = connection.cursor()
        query = "DELETE FROM cart_items WHERE user_id = %s AND product_id = %s"
        cursor.execute(query, (user_id, product_id))
        connection.commit()
        cursor.close()
    except Error as e:
        print("Error removing cart item:", e)


def update_cart_item(connection, cart_item_id, new_quantity):
    try:
        query = "UPDATE cart_items SET quantity = %s WHERE cart_item_id = %s"
        cursor = connection.cursor()
        cursor.execute(query, (new_quantity, cart_item_id))
        connection.commit()
        cursor.close()
    except Error as e:
        print("Error updating cart item:", e)


def clear_cart_history(connection, user_id):
    try:
        cursor = connection.cursor()
        query = "DELETE FROM cart_items WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        connection.commit()
        cursor.close()
    except Exception as e:
        print("Error clearing cart history:", e)

def add_cart_item(connection, user_id, product_id, quantity, image_data):
    try:
        cursor = connection.cursor()
        query = "INSERT INTO cart_items (user_id, product_id, quantity, image) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (user_id, product_id, quantity, image_data))
        connection.commit()
        cursor.close()
        print("Cart item added successfully.")
        return True
    except Exception as e:
        print("Error adding item to cart:", e)
        return False

def place_order(connection, customer_name, total, cart_items):
    try:
        cursor = connection.cursor()
        query = "INSERT INTO orders (customer_name, total) VALUES (%s, %s)"
        cursor.execute(query, (customer_name, total))
        order_id = cursor.lastrowid

        for item in cart_items:
            total_price = item['quantity'] * item['price_per_unit']
            query = "INSERT INTO order_detail (order_id, product_id, quantity, total_price, price_per_unit) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (order_id, item['product_id'], item['quantity'], total_price, item['price_per_unit']))

        connection.commit()
        cursor.close()
        return order_id
    except Exception as e:
        print("Error placing order:", e)
        return None




    
def get_sql_connection():
    return sql_connection.get_sql_connection()

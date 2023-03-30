from flask import Flask, render_template, redirect, request, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

DATABASE = "smile.db"
app = Flask(__name__)

bcrypt = Bcrypt(app)
app.secret_key = "ueuywq9571"

cart = []


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


def get_list(query, execute):
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, execute)
    category_list = cur.fetchall()
    con.close()
    return category_list


def insert_data(query, params):
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, params)
    con.commit()
    con.close()


def summarise_order():
    order = session['order']
    print(order)
    order.sort()
    print(order)
    order = [[x, order.count(x)] for x in set(order)]

    print(order)
    return order


@app.route('/')
def home_page():
    return render_template("home.html", logged_in=is_logged_in())


@app.route('/menu/<cat_id>')
def menu_page(cat_id):
    order_start = request.args.get("order")
    if order_start == "start" and not is_ordering():
        session["order"] = []

    product_list = get_list("SELECT id, name, description, volume, image, price FROM products WHERE cat_id=?", (cat_id, ))

    category_list = get_list("SELECT id, name FROM category", "")

    print(product_list)
    return render_template("menu.html", products=product_list, categories=category_list, logged_in=is_logged_in(),
                           ordering=is_ordering())


@app.route('/add_to_cart/<product_id>')
def add_to_cart(product_id):
    try:
        product_id = int(product_id)
    except ValueError:
        print("{} this is not a number".format(product_id))
        return redirect("/menu/1?invalid+id")

    print("adding to cart product ", product_id)
    order = session["order"]
    print("order before adding ", order)
    order.append(product_id)
    print("order after adding ", order)
    session["order"] = order
    return redirect(request.referrer)


@app.route("/cart", methods=['POST', 'GET'])
def cart_page():
    if request.method == 'POST':
        name = request.form['name']
        if name == "cancel":
            session.pop('order')
            return redirect('/?message=Order+has+been+cancelled')
        else:
            print(name)
            insert_data("INSERT INTO orders VALUES (null, ?, TIME('now'), ?)", (name, 1))
            order_number = get_list("SELECT max(id) FROM orders WHERE name = ?", (name, ))
            print(order_number)
            order_number = order_number[0][0]
            orders = summarise_order()
            for order in orders:
                insert_data("INSERT INTO order_contents VALUES (null, ?, ?, ?)", (order_number, order[0], order[1]))
            session.pop('order')
            return redirect('/?message=Order+has+been+placed+under+' + name)

    else:
        orders = summarise_order()
        total = 0
        for item in orders:
            item_detail = get_list("SELECT name, price FROM products WHERE id = ?", (item[0], ))
            print(item_detail)
            if item_detail:
                item.append(item_detail[0][0])
                item.append(item_detail[0][1])
                item.append(item_detail[0][1] * item[1])
                total += item_detail[0][1] * item[1]
        print(orders)
        return render_template("cart.html", logged_in=is_logged_in(), ordering=is_ordering(), products=orders,
                               total=total)


@app.route('/cancel_order')
def cancel_order():
    session.pop('order')
    return redirect('/?message=Order+has+been+cancelled')


@app.route('/process_orders/<processed>')
def process_orders(processed):
    label = "processed"
    if processed == "1":
        label = "un" + label
    print(label)
    processed = int(processed)
    all_orders = get_list("SELECT orders.id, orders.name, timestamp, products.name, quantity, price FROM orders "
                          "INNER JOIN order_contents ON orders.id = order_contents.order_id "
                          "INNER JOIN products on order_contents.product_id = products.id "
                          "WHERE processed = ?", (processed, ))
    print(all_orders)
    return render_template("orders.html", logged_in=is_logged_in(), orders=all_orders, label=label)


@app.route('/process/<order_id>')
def process_order(order_id):
    insert_data("UPDATE orders SET processed = 0 WHERE id = ?", (order_id, ))
    return redirect(request.referrer)


@app.route('/contact')
def contact_page():
    return render_template("contact.html", logged_in=is_logged_in())


@app.route('/login', methods=['POST', 'GET'])
def login_page():
    if is_logged_in():
        return redirect("/menu/1")
    print("Logging In")
    if request.method == "POST":
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()

        user_data = get_list("SELECT id, fname, password FROM user WHERE email = ?", (email, ))

        try:
            user_id = user_data[0]
            first_name = user_id[1]
            db_password = user_id[2]

        except IndexError:
            return redirect("/login?error=Email+invalid+or+password+incorrect")

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")

        session['email'] = email
        session['user_id'] = user_id
        session['firstname'] = first_name
        session['cart'] = []
        print(session)
        return redirect('/')
    return render_template("login.html")


@app.route('/signup', methods=['POST', 'GET'])
def signup_page():
    if is_logged_in():
        return redirect("/menu/1")
    if request.method == 'POST':
        print(request.form)

        fname = request.form.get('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')

        print(password)
        print(password2)

        if password != password2:
            return redirect("/signup?error=Passwords+do+not+match")

        hashed_password = bcrypt.generate_password_hash(password)

        try:
            insert_data("INSERT INTO user (fname, lname, email, password) VALUES (?, ?, ?, ?)",
                        (fname, lname, email, hashed_password))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')

        return redirect('/login')

    return render_template("signup.html")


@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=See+you+later')


@app.route('/admin')
def admin_page():
    if not is_logged_in():
        return redirect('/?message=Need+to+be+logged+in')
    con = create_connection(DATABASE)
    query = "SELECT * FROM category"
    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()
    con.close()
    return render_template("admin.html", logged_in=is_logged_in(), categories=category_list)


@app.route('/add_category', methods=['POST'])
def add_category():
    if not is_logged_in():
        return redirect('/?message=Need+to+be+logged+in')
    if request.method == "POST":
        print(request.form)
        cat_name = request.form.get('name').lower().strip()
        print(cat_name)
        con = create_connection(DATABASE)
        query = "INSERT INTO category ('name') VALUES (?)"
        cur = con.cursor()
        cur.execute(query, (cat_name,))
        con.commit()
        con.close()
    return redirect('/admin')


@app.route('/delete_category', methods=['POST'])
def delete_category():
    if not is_logged_in():
        return redirect('/?message=Need+to+be+logged+in')
    if request.method == 'POST':
        category = request.form.get('cat_id')
        print(category)
        category = category.split(", ")
        cat_id = category[0]
        cat_name = category[1]
        return render_template("delete_confirm.html", id=cat_id, cat_name=cat_name, type="category")
    return redirect("/admin")


@app.route('/delete_category_confirm/<cat_id>')
def delete_category_confirm(cat_id):
    if not is_logged_in():
        return redirect('/?message=Need+to+be+logged+in')
    con = create_connection(DATABASE)
    query = "DELETE FROM category WHERE id = ?"
    cur = con.cursor()
    cur.execute(query, (cat_id, ))
    con.commit()
    con.close()
    return redirect("/admin")


@app.errorhandler(404)
def page_not_found(error):
    print("error")
    return render_template("error_message.html", message=error)


@app.errorhandler(500)
def page_not_found(error):
    print("error")
    return render_template("error_message.html", message=error)


def is_logged_in():
    if session.get("email") is None:
        print("not logged in")
        return False
    else:
        print(session.get("email"))
        print("logged in")
        return True


def is_ordering():
    if session.get("order") is None:
        return False
    else:
        return True


if __name__ == '__main__':
    app.run()

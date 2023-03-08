from flask import Flask, render_template, redirect, request, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

DATABASE = "smile.db"
app = Flask(__name__)

bcrypt = Bcrypt(app)
app.secret_key = "ueuywq9571"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


@app.route('/')
def home_page():
    return render_template("home.html", logged_in=is_logged_in())


@app.route('/menu/<cat_id>')
def menu_page(cat_id):
    con = create_connection(DATABASE)
    query = "SELECT name, description, volume, image, price FROM products WHERE cat_id=?"
    cur = con.cursor()
    cur.execute(query, (cat_id,))
    product_list = cur.fetchall()
    query = "SELECT id, name FROM category"
    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()
    con.close()
    print(product_list)
    return render_template("menu.html", products=product_list, categories=category_list, logged_in=is_logged_in())


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

        query = """SELECT id, fname, password FROM user WHERE email = ?"""
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

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

        if len(password) < 8:
            return redirect("/signup?error=Password+must+be+at+least+8+characters")

        hashed_password = bcrypt.generate_password_hash(password)
        con = create_connection(DATABASE)
        query = "INSERT INTO user (fname, lname, email, password) VALUES (?, ?, ?, ?)"
        cur = con.cursor()

        try:
            cur.execute(query, (fname, lname, email, hashed_password))
        except sqlite3.IntegrityError:
            con.close()
            return redirect('/signup?error=Email+is+already+used')

        con.commit()
        con.close()

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


def is_logged_in():
    if session.get("email") is None:
        print("not logged in")
        return False
    else:
        print(session.get("email"))
        print("logged in")
        return True


if __name__ == '__main__':
    app.run()

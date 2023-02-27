from flask import Flask, render_template, redirect, request
import sqlite3
from sqlite3 import Error

DATABASE = "smile.db"
app = Flask(__name__)


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
    return None


@app.route('/')
def home_page():
    return render_template("home.html")


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
    return render_template("menu.html", products=product_list, categories=category_list)


@app.route('/contact')
def contact_page():
    return render_template("contact.html")


@app.route('/login', methods=['POST', 'GET'])
def login_page():
    return render_template("login.html")


@app.route('/signup', methods=['POST', 'GET'])
def signup_page():
    if request.method =='POST':
        print(request.form)
        fname = request.form.get('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if password != password2:
            return redirect("/signup?error=Passwords+do+not+match")

        if len(password) < 8:
            return redirect("/signup?error=Password+must+be+at+least+8+characters")

        con = create_connection(DATABASE)
        query = "INSERT INTO user (fname, lname, email, password) VALUES (?, ?, ?, ?)"

        try:
            con.execute(query, (fname, lname, email, password))
        except sqlite3.IntegrityError:
            con.close()
            return redirect('/signup?error=Email+is+already+used')

        con.commit()
        con.close()

    return render_template("signup.html")


if __name__ == '__main__':
    app.run()

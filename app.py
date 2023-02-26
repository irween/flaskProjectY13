from flask import Flask, render_template
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
    cur.execute(query, (cat_id, ))
    product_list = cur.fetchall()
    con.close()
    print(product_list)
    return render_template("menu.html", products=product_list)


@app.route('/contact')
def contact_page():
    return render_template("contact.html")


if __name__ == '__main__':
    app.run()


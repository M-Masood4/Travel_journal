from flask import Flask, render_template, request, session, g, redirect, url_for, flash, send_file, abort
from database import get_db, close_db
from forms import RegistrationForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import io

app = Flask(__name__)
app.teardown_appcontext(close_db)
app.config["SECRET_KEY"] = "Masood2024"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"



@app.before_request
def load_logged_in_user():
    g.user = session.get("user_id", None)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        password2 = form.password2.data
        db = get_db()
        
        conflict_user = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        
        if conflict_user is not None:
            form.user_id.errors.append("Username already taken!!")
        else:
            db.execute("INSERT INTO users (user_id, password) VALUES (?, ?)", (user_id, generate_password_hash(password)))
            db.commit()
            return redirect(url_for("login"))
    
    return render_template("register.html", form=form)



@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE user_id = ?;", (user_id,)
        ).fetchone()
        
        if user is None:
            form.user_id.errors.append("No such username!")
        elif not check_password_hash(user["password"], password):
            form.password.errors.append("Incorrect password!")
        else:
            session.clear()
            session["user_id"] = user_id
            next_page = request.args.get("next")
            if not next_page:
                next_page = url_for("index")
            return redirect(next_page)
        
    return render_template("login.html", form=form)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("login", next=request.url))
        return view(*args, **kwargs)
    return wrapped_view

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route('/premium')
def premium():
    return render_template("premium.html")


def plan(plan_name, user_id):
    db = get_db()
    try:
        db.execute("INSERT INTO PLAN (plan, user_id) VALUES (?, ?)", (plan_name, user_id))
        db.commit() 
    except Exception as e:
        print(f"An error occurred while inserting plan into database: {e}")

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    try:
        item_name = request.form.get('item_name')
        item_price = request.form.get('item_price')

        if 'cart' not in session:
            session['cart'] = []

        session['cart'].append({'name': item_name, 'price': item_price})

        user_id = session.get('user_id')
        if user_id:
            plan("Travel-Lite", user_id)

        return redirect(url_for('cart'))
    except Exception as e:
       return f"An error occurred: {e}"

@app.route('/cart')
def cart():
    return render_template('cart.html', cart=session.get('cart', []))


# this puts image in the database (image type is blob), i think its more optimal to put images in database than store in a static folder..

def image_db(file, entry_text, user_id):
    db = get_db()
    image_data = file.read()
    db.execute("INSERT INTO journals (entry_text, image, user_id) VALUES (?, ?, ?)", (entry_text, image_data, user_id))
    db.commit()

@app.route('/journal', methods=['GET', 'POST'])
def journal_entry():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('file')
        entry_text = request.form.get('text')
        user_id = session['user_id']

        if file and entry_text:
            image_db(file, entry_text, user_id)
            return redirect(url_for('journal_entry'))

    return render_template('journal.html')

@app.route('/myfeed')
def myfeed():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    user_id = session['user_id']
    entries = db.execute("SELECT id, entry_text FROM journals WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    return render_template('myfeed.html', entries=entries)

# https://docs.python.org/3/library/io.html#io.BytesIO turning binary in database to image..

@app.route('/serve_image/<int:id>')
def serve_image(id):
    db = get_db()
    image = db.execute('SELECT image FROM journals WHERE id = ?', (id,)).fetchone()

    if image and image['image']:
        return send_file(io.BytesIO(image['image']), mimetype='image/jpeg')
    else:
        abort(404)


@app.route('/')
def index():
    db = get_db()
    entries = db.execute("SELECT id, entry_text, user_id FROM journals ORDER BY id DESC").fetchall()
    return render_template('index.html', entries=entries)


@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        file = request.files['profile_picture']
        if file:
            image_data = file.read()
            user_id = session['user_id']
            
            db = get_db()
            db.execute('UPDATE users SET profile_picture = ? WHERE user_id = ?', (image_data, user_id))
            db.commit()
            
            flash('Profile picture updated successfully!')
            return redirect(url_for('account'))

    return render_template('account.html')

@app.route('/user/profile_picture')
def profile_picture():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    db = get_db()
    user = db.execute('SELECT profile_picture FROM users WHERE user_id = ?', (user_id,)).fetchone()

# once again the line of code below reads binary and turns it into an image (profile picture)
    if user and user['profile_picture']:
        return send_file(
            io.BytesIO(user['profile_picture']),mimetype='image/jpeg')
    else:
        return 'No profile picture', 404


@app.route('/change_password', methods=['POST'])
def change_password():
    db = get_db()
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    new_password = request.form.get('new_password')
    new_password_hash = generate_password_hash(new_password)
    user_id = session['user_id']
    db.execute('UPDATE users SET password = ? WHERE user_id = ?', (new_password_hash, user_id))
    db.commit()
    return redirect(url_for('account'))

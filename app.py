from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key'
DB_NAME = 'superapp.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_NAME):
        conn = get_db()
        # Создание таблиц для всех модулей
        conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS shopping (id INTEGER PRIMARY KEY, user_id INTEGER, product TEXT, amount TEXT, is_bought INTEGER DEFAULT 0)')
        conn.execute('CREATE TABLE IF NOT EXISTS contacts (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, phone TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, text TEXT, date TEXT)')
        conn.execute('CREATE TABLE IF NOT EXISTS movies (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, genre TEXT, year INTEGER, rating INTEGER)')
        conn.execute('CREATE TABLE IF NOT EXISTS todos (id INTEGER PRIMARY KEY, user_id INTEGER, task TEXT, status TEXT DEFAULT "active", date TEXT)')
        conn.commit()
        conn.close()

# --- AUTH ---
@app.route('/')
def home():
    if 'user_id' in session: return redirect(url_for('notes'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = get_db()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                         (request.form['username'], generate_password_hash(request.form['password'])))
            conn.commit()
            return redirect(url_for('login'))
        except: flash('Логин занят')
        finally: conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (request.form['username'],)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('notes'))
        flash('Ошибка входа')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- NOTES ---
@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        conn.execute('INSERT INTO notes (user_id, content) VALUES (?, ?)', (session['user_id'], request.form['content']))
        conn.commit()
    items = conn.execute('SELECT * FROM notes WHERE user_id = ? ORDER BY id DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('notes.html', items=items, page='notes')

# --- SHOPPING ---
@app.route('/shopping', methods=['GET', 'POST'])
def shopping():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        conn.execute('INSERT INTO shopping (user_id, product, amount) VALUES (?, ?, ?)', 
                     (session['user_id'], request.form['product'], request.form['amount']))
        conn.commit()
    items = conn.execute('SELECT * FROM shopping WHERE user_id = ? ORDER BY is_bought ASC, id DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('shopping.html', items=items, page='shopping')

@app.route('/shopping/toggle/<int:id>')
def shopping_toggle(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    item = conn.execute('SELECT is_bought FROM shopping WHERE id=?', (id,)).fetchone()
    conn.execute('UPDATE shopping SET is_bought = ? WHERE id = ?', (0 if item['is_bought'] else 1, id))
    conn.commit()
    conn.close()
    return redirect(url_for('shopping'))

# --- CONTACTS ---
@app.route('/phonebook', methods=['GET', 'POST'])
def phonebook():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    search = request.args.get('q', '')
    if request.method == 'POST':
        conn.execute('INSERT INTO contacts (user_id, name, phone) VALUES (?, ?, ?)', 
                     (session['user_id'], request.form['name'], request.form['phone']))
        conn.commit()
        return redirect(url_for('phonebook'))
    
    query = 'SELECT * FROM contacts WHERE user_id = ?'
    params = [session['user_id']]
    if search:
        query += ' AND name LIKE ?'
        params.append(f'%{search}%')
        
    items = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('phonebook.html', items=items, page='phonebook', search=search)

# --- BLOG ---
@app.route('/blog', methods=['GET', 'POST'])
def blog():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn.execute('INSERT INTO posts (user_id, title, text, date) VALUES (?, ?, ?, ?)', 
                     (session['user_id'], request.form['title'], request.form['text'], date))
        conn.commit()
    items = conn.execute('SELECT * FROM posts WHERE user_id = ? ORDER BY id DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('blog.html', items=items, page='blog')

# --- MOVIES ---
@app.route('/movies', methods=['GET', 'POST'])
def movies():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        conn.execute('INSERT INTO movies (user_id, title, genre, year, rating) VALUES (?, ?, ?, ?, ?)', 
                     (session['user_id'], request.form['title'], request.form['genre'], request.form['year'], request.form['rating']))
        conn.commit()
    items = conn.execute('SELECT * FROM movies WHERE user_id = ? ORDER BY id DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('movies.html', items=items, page='movies')

# --- TODO ---
@app.route('/todo', methods=['GET', 'POST'])
def todo():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        date = request.form.get('date', '')
        conn.execute('INSERT INTO todos (user_id, task, date) VALUES (?, ?, ?)', 
                     (session['user_id'], request.form['task'], date))
        conn.commit()
    items = conn.execute('SELECT * FROM todos WHERE user_id = ? ORDER BY id DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('todo.html', items=items, page='todo')

@app.route('/todo/toggle/<int:id>')
def todo_toggle(id):
    conn = get_db()
    status = conn.execute('SELECT status FROM todos WHERE id=?', (id,)).fetchone()['status']
    new_status = 'done' if status == 'active' else 'active'
    conn.execute('UPDATE todos SET status = ? WHERE id = ?', (new_status, id))
    conn.commit()
    conn.close()
    return redirect(url_for('todo'))

# --- GLOBAL DELETE ---
@app.route('/delete/<category>/<int:id>')
def delete(category, id):
    if 'user_id' not in session: return redirect(url_for('login'))
    tables = {'notes': 'notes', 'shopping': 'shopping', 'phonebook': 'contacts', 
              'blog': 'posts', 'movies': 'movies', 'todo': 'todos'}
    if category in tables:
        conn = get_db()
        conn.execute(f'DELETE FROM {tables[category]} WHERE id = ? AND user_id = ?', (id, session['user_id']))
        conn.commit()
        conn.close()
    return redirect(url_for(category if category != 'phonebook' else 'phonebook'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
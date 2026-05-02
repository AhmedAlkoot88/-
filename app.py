from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
import hashlib
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

def get_db_connection():
    """إنشاء اتصال آمن بقاعدة البيانات"""
    conn = sqlite3.connect('database.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """تهيئة قاعدة البيانات"""
    conn = get_db_connection()
    
    # جدول المستخدمين
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول المخازن
    conn.execute('''
        CREATE TABLE IF NOT EXISTS warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول الأصناف
    conn.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            carton_number TEXT NOT NULL UNIQUE,
            quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
            min_quantity INTEGER NOT NULL DEFAULT 0 CHECK (min_quantity >= 0),
            warehouse_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE CASCADE
        )
    ''')
    
    # إضافة أدمن افتراضي
    admin_hash = hashlib.sha256('admin123'.encode()).hexdigest()
    try:
        conn.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, 1)", 
                    ('admin', admin_hash))
    except sqlite3.IntegrityError:
        pass
    
    # إندكسات للسرعة
    conn.execute('CREATE INDEX IF NOT EXISTS idx_items_warehouse ON items(warehouse_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_items_carton ON items(carton_number)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
    
    conn.commit()
    conn.close()
    print("✅ قاعدة البيانات جاهزة | admin/admin123")

init_db()

# ديكوريترات
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return render_template('login.html', error='❌ يجب إدخال البيانات')
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?', 
            (username, hash_password(password))
        ).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='❌ اسم المستخدم أو كلمة السر خاطئة')
    
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    is_admin = session.get('is_admin', False)
    success = False
    error = None
    
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        new_password = request.form.get('password', '').strip()
        
        if new_username:
            if len(new_username) < 3 or len(new_username) > 20:
                error = '❌ اسم المستخدم 3-20 حرف'
            else:
                try:
                    conn.execute('UPDATE users SET username = ? WHERE id = ?', 
                               (new_username, session['user_id']))
                    session['username'] = new_username
                except sqlite3.IntegrityError:
                    error = '❌ اسم المستخدم موجود بالفعل'
        
        if new_password:
            if len(new_password) < 4:
                error = '❌ كلمة السر 4 أحرف على الأقل'
            else:
                conn.execute('UPDATE users SET password = ? WHERE id = ?', 
                           (hash_password(new_password), session['user_id']))
        
        if not error:
            conn.commit()
            success = True
            user = conn.execute('SELECT * FROM users WHERE id = ?', 
                              (session['user_id'],)).fetchone()
    
    conn.close()
    return render_template('profile.html', user=user, success=success, error=error, is_admin=is_admin)

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    error = None
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if len(username) < 3 or len(username) > 20:
            error = '❌ اسم المستخدم 3-20 حرف'
        elif len(password) < 4:
            error = '❌ كلمة السر 4 أحرف على الأقل'
        else:
            conn = get_db_connection()
            try:
                conn.execute(
                    'INSERT INTO users (username, password, is_admin) VALUES (?, ?, 0)',
                    (username, hash_password(password))
                )
                conn.commit()
                conn.close()
                return redirect(url_for('index'))
            except sqlite3.IntegrityError:
                error = '❌ اسم المستخدم موجود بالفعل'
                conn.close()
    
    return render_template('add_user.html', error=error)

@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    
    warehouses = conn.execute('''
        SELECT w.*, COUNT(i.id) as item_count 
        FROM warehouses w 
        LEFT JOIN items i ON w.id = i.warehouse_id 
        GROUP BY w.id 
        ORDER BY w.name
    ''').fetchall()
    
    items = conn.execute('''
        SELECT items.*, warehouses.name as warehouse_name 
        FROM items 
        JOIN warehouses ON items.warehouse_id = warehouses.id 
        ORDER BY items.name
    ''').fetchall()
    
    total_items = len(items) if items else 0
    low_stock = len([i for i in items if 0 < i['quantity'] <= i['min_quantity']]) if items else 0
    zero_stock = len([i for i in items if i['quantity'] == 0]) if items else 0
    
    conn.close()
    
    return render_template(
        'index.html', 
        warehouses=warehouses, 
        items=items,
        total_items=total_items, 
        low_stock=low_stock, 
        zero_stock=zero_stock,
        username=session.get('username', 'مستخدم'),
        is_admin=session.get('is_admin', False)
    )

@app.route('/delete_item/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    try:
        conn = get_db_connection()
        result = conn.execute('DELETE FROM items WHERE id = ?', (item_id,)).rowcount
        conn.commit()
        conn.close()
        return jsonify({'success': result > 0, 'message': 'تم الحذف بنجاح'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ خطأ: {str(e)}'})

@app.route('/deduct/<int:item_id>', methods=['POST'])
@login_required
def deduct_item(item_id):
    """خصم كمية من صنف"""
    try:
        data = request.get_json()
        cartons = int(data.get('cartons', 0))
        
        if cartons <= 0:
            return jsonify({'success': False, 'message': 'عدد الكراتين يجب أن يكون أكبر من 0'})
        
        conn = get_db_connection()
        item = conn.execute('SELECT quantity FROM items WHERE id = ?', (item_id,)).fetchone()
        if not item:
            conn.close()
            return jsonify({'success': False, 'message': 'الصنف غير موجود'})
        
        new_quantity = max(0, item['quantity'] - cartons)
        conn.execute('UPDATE items SET quantity = ? WHERE id = ?', (new_quantity, item_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'new_quantity': new_quantity})
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ خطأ: {str(e)}'})

@app.route('/add_quantity/<int:item_id>', methods=['POST'])
@login_required
def add_quantity(item_id):
    """إضافة كمية إلى صنف"""
    try:
        data = request.get_json()
        quantity = int(data.get('quantity', 0))
        
        if quantity <= 0:
            return jsonify({'success': False, 'message': 'الكمية يجب أن تكون أكبر من 0'})
        
        conn = get_db_connection()
        item = conn.execute('SELECT quantity FROM items WHERE id = ?', (item_id,)).fetchone()
        if not item:
            conn.close()
            return jsonify({'success': False, 'message': 'الصنف غير موجود'})
        
        new_quantity = item['quantity'] + quantity
        conn.execute('UPDATE items SET quantity = ? WHERE id = ?', (new_quantity, item_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'new_quantity': new_quantity})
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ خطأ: {str(e)}'})

@app.route('/add_warehouse', methods=['GET', 'POST'])
@login_required
def add_warehouse():
    error = None
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        if not name or len(name) < 2 or len(name) > 100:
            error = '❌ اسم المخزن 2-100 حرف'
        else:
            conn = get_db_connection()
            try:
                conn.execute('INSERT INTO warehouses (name) VALUES (?)', (name,))
                conn.commit()
                conn.close()
                return redirect(url_for('index'))
            except sqlite3.IntegrityError:
                error = '❌ اسم المخزن موجود بالفعل'
                conn.close()
    
    conn = get_db_connection()
    warehouses_count = conn.execute('SELECT COUNT(*) as count FROM warehouses').fetchone()['count']
    conn.close()
    
    return render_template('add_warehouse.html', error=error, warehouses_count=warehouses_count)

@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    conn = get_db_connection()
    warehouses = conn.execute('SELECT * FROM warehouses ORDER BY name').fetchall()
    default_warehouse = request.args.get('warehouse_id') or request.args.get('warehouse')
    error = None
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        carton = request.form.get('carton_number', '').strip()
        quantity = request.form.get('quantity', '0').strip()
        min_qty = request.form.get('min_quantity', '0').strip()
        wh_id = request.form.get('warehouse_id', '').strip()
        
        if not name or len(name) < 2:
            error = '❌ اسم الصنف حرفين على الأقل'
        elif not carton or len(carton) < 3:
            error = '❌ رقم الكرتونة 3 أحرف على الأقل'
        elif not wh_id:
            error = '❌ اختر مخزن'
        else:
            try:
                quantity = int(quantity) if quantity else 0
                min_qty = int(min_qty) if min_qty else 0
                wh_id = int(wh_id)
                
                if quantity < 0 or min_qty < 0:
                    error = '❌ الكمية يجب أن تكون موجبة'
                else:
                    conn.execute(
                        'INSERT INTO items (name, carton_number, quantity, min_quantity, warehouse_id) VALUES (?, ?, ?, ?, ?)',
                        (name, carton, quantity, min_qty, wh_id)
                    )
                    conn.commit()
                    conn.close()
                    return redirect(url_for('index'))
            except ValueError:
                error = '❌ الكمية يجب أن تكون أرقام'
            except sqlite3.IntegrityError:
                error = '❌ رقم الكرتونة موجود بالفعل'
    
    conn.close()
    return render_template('add_item.html', warehouses=warehouses, 
                         default_warehouse=default_warehouse, error=error)

@app.route('/warehouse/<int:wh_id>')
@login_required
def warehouse_details(wh_id):
    conn = get_db_connection()
    warehouse = conn.execute('SELECT * FROM warehouses WHERE id = ?', (wh_id,)).fetchone()
    if not warehouse:
        conn.close()
        return '❌ المخزن غير موجود', 404
    
    items = conn.execute(
        'SELECT * FROM items WHERE warehouse_id = ? ORDER BY name', 
        (wh_id,)
    ).fetchall()
    
    total_items = len(items) if items else 0
    low_stock = len([i for i in items if 0 < i['quantity'] <= i['min_quantity']]) if items else 0
    zero_stock = len([i for i in items if i['quantity'] == 0]) if items else 0
    
    conn.close()
    
    return render_template(
        'warehouse.html', 
        warehouse=warehouse, 
        items=items,
        total_items=total_items, 
        low_stock=low_stock, 
        zero_stock=zero_stock,
        username=session.get('username', 'مستخدم')
    )

@app.route('/deduct')
@login_required
def deduct_page():
    """صفحة تعديل الكميات"""
    conn = get_db_connection()
    items = conn.execute('''
        SELECT items.*, w.name as warehouse_name 
        FROM items 
        JOIN warehouses w ON items.warehouse_id = w.id 
        ORDER BY items.name
    ''').fetchall()
    conn.close()
    
    return render_template('deduct.html', items=items, username=session.get('username', 'مستخدم'))

@app.errorhandler(404)
def not_found(error):
    return '<div style="text-align:center;padding:50px;color:white;font-family:Arial;">❌ الصفحة غير موجودة</div>', 404

@app.errorhandler(500)
def server_error(error):
    return '<div style="text-align:center;padding:50px;color:white;font-family:Arial;">❌ خطأ في الخادم</div>', 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 مدير المخازن v3.3 (نسخة محسّنة)")
    print("="*60)
    print("🌐 الرابط: http://127.0.0.1:5000")
    print("👤 اسم المستخدم: admin")
    print("🔑 كلمة السر: admin123")
    print("="*60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)
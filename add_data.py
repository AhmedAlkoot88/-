import sqlite3
import os
import sys

# إعدادات لدعم العرض في CMD
if os.name == 'nt':  # Windows
    os.system('chcp 65001 >nul')
    sys.stdout.reconfigure(encoding='utf-8')

def get_db():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

print("🔥" * 40)
print("📦 Warehouse Manager Data Entry Tool")
print("🔥" * 40)

def show_menu():
    print("\n1️⃣  Add Warehouses")
    print("2️⃣  Add Items") 
    print("3️⃣  Show Data")
    print("4️⃣  Back to Main Menu")
    print("-" * 40)

while True:
    show_menu()
    choice = input("Choose (1-4): ").strip()
    
    if choice == '1':
        conn = get_db()
        while True:
            name = input("\n🏭 Warehouse Name (Enter=Exit): ").strip()
            if not name: break
            try:
                conn.execute("INSERT INTO warehouses (name) VALUES (?)", (name,))
                conn.commit()
                print(f"✅ [Added] {name}")
            except:
                print(f"❌ {name} already exists!")
        conn.close()
    
    elif choice == '2':
        conn = get_db()
        warehouses = conn.execute("SELECT id,name FROM warehouses").fetchall()
        if not warehouses:
            input("❌ Add warehouses first! (Enter)")
            continue
        
        print("\n🏭 Warehouses:")
        for w in warehouses: print(f"  {w['id']}: {w['name']}")
        
        while True:
            name = input("\n📦 Item Name (Enter=Exit): ").strip()
            if not name: break
            
            carton = input("🆔 Carton Number: ").strip()
            qty = input("📊 Quantity (Enter=0): ") or "0"
            minq = input("⚠️  Minimum Quantity (Enter=10): ") or "10"
            wh = input("🏭 Warehouse ID: ")
            
            try:
                conn.execute("INSERT INTO items VALUES (NULL,?,?,?,?,?,?)", 
                           (name, carton, int(qty), int(minq), int(wh), None))
                conn.commit()
                print(f"✅ [Added] {name}")
            except Exception as e:
                print(f"❌ Error: {e}")
        conn.close()
    
    elif choice == '3':
        conn = get_db()
        print("\n🏭 Warehouses:")
        for w in conn.execute("SELECT * FROM warehouses"):
            print(f"  ID:{w['id']} - {w['name']}")
        
        print("\n📦 Items:")
        for i in conn.execute("SELECT i.*,w.name FROM items i JOIN warehouses w ON i.warehouse_id=w.id"):
            print(f"  {i['name']} | {i['carton_number']} | {i['quantity']}/{i['min_quantity']} | {i['name_1']}")
        conn.close()
        input("\nEnter to continue...")
    
    elif choice == '4':
        break
    
    else:
        print("❌ Invalid choice!")
        input("Enter...")
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = "pantry_key_nozomi"  # ← これを足してくださいまし！
DATABASE = "pantry_track.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# index
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.route("/")
def index():
    conn = get_db_connection()

    # 1. 在庫一覧を取得
    query = """
        SELECT p.*, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.is_active = 1
        ORDER BY p.updated_at DESC
    """
    products = conn.execute(query).fetchall()

    # 2. ：お買い物が必要な商品の件数を数える
    # current_stock が reorder_level（発注点）以下のものをカウントする
    count_query = """
        SELECT COUNT(*) FROM products 
        WHERE is_active = 1 AND current_stock <= reorder_level
    """
    # .fetchone()[0] で、計算結果の「数字」だけを取り出します
    low_stock_count = conn.execute(count_query).fetchone()[0]

    conn.close()

    return render_template(
        "index.html", products=products, low_stock_count=low_stock_count
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    conn = get_db_connection()
    if request.method == "POST":
        name = request.form["name"]
        origin = request.form["origin"]
        category_id = request.form["category_id"]
        current_stock = request.form["current_stock"]
        reorder_level = request.form["reorder_level"]
        unit = request.form["unit"]

        conn.execute(
            """
            INSERT INTO products (name, origin, category_id, current_stock, reorder_level, unit, updated_at, touch_count)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 0)
        """,
            (name, origin, category_id, current_stock, reorder_level, unit),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    categories = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    return render_template("add_product.html", categories=categories)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 出庫
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.route("/reduce/<int:product_id>", methods=["POST"])
def reduce_stock(product_id):
    conn = get_db_connection()
    conn.execute(
        "UPDATE products SET current_stock = MAX(0, current_stock - 1) WHERE id = ?",
        (product_id,),
    )

    # staff_id を NozomiさんのID「1」に設定しますわ！
    conn.execute(
        "INSERT INTO inventory_logs (product_id, staff_id, type, quantity) VALUES (?, ?, ?, ?)",
        (product_id, 1, "出庫", 1.0),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 入庫
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.route("/add_stock/<int:product_id>", methods=["POST"])
def add_stock(product_id):
    conn = get_db_connection()
    conn.execute(
        "UPDATE products SET current_stock = current_stock + 1 WHERE id = ?",
        (product_id,),
    )

    conn.execute(
        "INSERT INTO inventory_logs (product_id, staff_id, type, quantity) VALUES (?, ?, ?, ?)",
        (product_id, 1, "入庫", 1.0),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 廃棄
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.route("/waste/select")
def waste_select():
    conn = get_db_connection()
    products = conn.execute(
        "SELECT * FROM products WHERE is_active = 1 ORDER BY name"
    ).fetchall()
    conn.close()
    return render_template(
        "choose_product.html",
        products=products,
        mode="waste",  # モードをwasteにします
        title="🥀 廃棄の記録",
        bg_color="#ffebee",  # 悲しいけれど大切な記録なので、薄い赤色に
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 商品編集（在庫管理 対象商品）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.route("/edit_product/<int:product_id>")
def edit_product(product_id):
    conn = get_db_connection()
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    categories = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    return render_template("edit_product.html", product=product, categories=categories)


@app.route("/update_product/<int:product_id>", methods=["POST"])
def update_product(product_id):
    # 1. 画面から送られてきたデータを受け取る
    name = request.form["name"]
    origin = request.form["origin"]
    category_id = request.form["category_id"]
    current_stock = request.form["current_stock"]
    reorder_level = request.form["reorder_level"]
    unit = request.form["unit"]

    conn = get_db_connection()

    # 2. データベースの情報を書き換える（Update）
    conn.execute(
        """
        UPDATE products 
        SET name = ?, origin = ?, category_id = ?, current_stock = ?, reorder_level = ?, unit = ?
        WHERE id = ?
    """,
        (name, origin, category_id, current_stock, reorder_level, unit, product_id),
    )

    # 3. ★ここにログを記録するコードを入れますわ！
    # 3. ログを詳しく記録する
    # 名前、在庫、発注点をひとまとめにしてログに刻みますわ
    log_details = (
        f"修正完了 [名前:{name} / 在庫:{current_stock}{unit} / 発注点:{reorder_level}]"
    )

    conn.execute(
        "INSERT INTO inventory_logs (product_id, staff_id, type, quantity) VALUES (?, ?, ?, ?)",
        (product_id, 1, log_details, 0),
    )

    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete_product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    conn = get_db_connection()

    # 1. 論理削除：is_active を 0 に更新（一覧に出なくする）
    conn.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))

    # 2. ★削除したことをログに記録する（NozomiさんのID: 1）
    conn.execute(
        "INSERT INTO inventory_logs (product_id, staff_id, type, quantity) VALUES (?, ?, ?, ?)",
        (product_id, 1, "商品削除", 0),
    )

    conn.commit()
    conn.close()
    return redirect(url_for("index"))


# お買い物リスト
@app.route("/shopping_list")
def shopping_list():
    conn = get_db_connection()
    # 在庫数が発注点（reorder_level）以下のものだけを取得しますわ
    query = """
        SELECT p.*, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.is_active = 1 AND p.current_stock <= p.reorder_level
    """
    items = conn.execute(query).fetchall()
    conn.close()
    return render_template("shopping_list.html", items=items)

    # ログ


@app.route("/logs")
def view_logs():
    conn = get_db_connection()
    # 履歴を、商品名とスタッフ名と一緒に新しい順で取得します
    query = """
        SELECT l.*, p.name AS product_name, s.name AS staff_name
        FROM inventory_logs l
        JOIN products p ON l.product_id = p.id
        JOIN staffs s ON l.staff_id = s.id
        ORDER BY l.created_at DESC
    """
    logs = conn.execute(query).fetchall()
    conn.close()
    return render_template("logs.html", logs=logs)


# --- 入庫（買ってきた） ---
@app.route("/arrival/select")
def arrival_select():
    conn = get_db_connection()
    products = conn.execute(
        "SELECT * FROM products WHERE is_active = 1 ORDER BY name"
    ).fetchall()
    conn.close()
    return render_template(
        "choose_product.html",
        products=products,
        mode="arrival",
        title="何を買いましたか？",
        bg_color="#fff3e0",
    )  # 暖かいオレンジ


# --- 出庫（使い切った） ---
@app.route("/departure/select")
def departure_select():
    conn = get_db_connection()
    products = conn.execute(
        "SELECT * FROM products WHERE is_active = 1 ORDER BY name"
    ).fetchall()
    conn.close()
    return render_template(
        "choose_product.html",
        products=products,
        mode="departure",
        title="なにを使い切りましたか？",
        bg_color="#e3f2fd",
    )  # スッキリしたブルー


# 第2画面を表示するルート（入庫・出庫共通）
@app.route("/<mode>/entry/<int:product_id>")
def entry_quantity(mode, product_id):
    conn = get_db_connection()
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    conn.close()

    # モードに合わせて色と言葉をセットしますわ
    if mode == "arrival":
        title = "✨ 買ってきた登録"
        bg_color = "#fff3e0"
    elif mode == "waste":  # ←ここに廃棄モードを追加しますわ！
        title = "🥀 廃棄の記録"
        bg_color = "#ffebee"  # 廃棄らしい薄い赤色です
    else:
        title = "☕ 使い切った登録"
        bg_color = "#e3f2fd"

    return render_template(
        "entry_quantity.html",
        product=product,
        mode=mode,
        title=title,
        bg_color=bg_color,
    )


@app.route("/<mode>/execute/<int:product_id>", methods=["POST"])
def execute_stock_update(mode, product_id):
    quantity = float(request.form.get("quantity", 0))
    current_staff_id = session.get("staff_id", 1)
    conn = get_db_connection()

    # 修正：現在の在庫だけでなく「発注点（reorder_level）」も一緒に取得しますわ
    product = conn.execute(
        "SELECT name, current_stock, reorder_level FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()

    if mode == "arrival":
        new_stock = product["current_stock"] + quantity
        log_type = "入庫"
    elif mode == "waste":
        new_stock = product["current_stock"] - quantity
        log_type = "廃棄"
    else:
        new_stock = product["current_stock"] - quantity
        log_type = "出庫"

        # ★ここがポイントですわ！
        # 「出庫」した結果、発注点を下回った（かつ、元々は下回っていなかった）場合にメッセージを出します
        if new_stock <= product["reorder_level"]:
            flash(
                f"「{product['name']}」の在庫が残りわずかです。お買い物リストに追加しましたわ！"
            )

    conn.execute(
        """
        UPDATE products 
        SET current_stock = ?, 
            updated_at = CURRENT_TIMESTAMP, 
            touch_count = touch_count + 1
        WHERE id = ?
        """, 
        (new_stock, product_id)
    )

    # （ログの記録などは今のままですわ）
    conn.execute(
        """
        INSERT INTO inventory_logs (product_id, staff_id, type, quantity) 
        VALUES (?, ?, ?, ?)
    """,
        (product_id, current_staff_id, log_type, quantity),
    )

    conn.commit()
    conn.close()

    return redirect(url_for(f"{mode}_select"))


# お買い物リストからの一括入庫を実行するルート
@app.route("/execute_bulk_arrival", methods=["POST"])
def execute_bulk_arrival():
    # フォームから送られてきたすべてのデータを取り出します
    form_data = request.form
    form_data = request.form

    conn = get_db_connection()

    # セッションからスタッフIDを取得（いなければ1:マスター）
    current_staff_id = session.get("staff_id", 1)

    # 送られてきたデータの中から「qty_商品ID」という名前のものを探してループします
    for key, value in form_data.items():
        if key.startswith("qty_"):
            # 名前から商品IDを取り出します（例: 'qty_5' -> 5）
            product_id = int(key.replace("qty_", ""))
            quantity = float(value) if value else 0

            if quantity > 0:
                # 1. 現在の在庫を調べて、新しい在庫を計算します
                product = conn.execute(
                    "SELECT current_stock FROM products WHERE id = ?", (product_id,)
                ).fetchone()
                new_stock = product["current_stock"] + quantity

                # 2. 在庫（productsテーブル）を更新
                conn.execute(
                    "UPDATE products SET current_stock = ? WHERE id = ?",
                    (new_stock, product_id),
                )

                # 3. 履歴（inventory_logsテーブル）に記録
            conn.execute(
                """
                UPDATE products 
                SET current_stock = ?, 
                    updated_at = CURRENT_TIMESTAMP,
                    touch_count = touch_count + 1
                WHERE id = ?
                """,
                (new_stock, product_id),
                            )

    conn.commit()
    conn.close()

    # 終わったら「在庫一覧」へ戻って、更新された数字を見せてあげましょう！
    return redirect(url_for("index"))


@app.route("/stock_list")
def stock_list():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products WHERE is_active = 1").fetchall()
    conn.close()
    return render_template("stock_list.html", products=products)


@app.route("/admin")
def admin_menu():
    # 管理メニュー画面を表示するだけですわ
    return render_template("admin_menu.html")


# --- 2. 商品管理（一覧・編集・削除の入り口） ---
@app.route("/admin/manage_products")
def manage_products():
    conn = get_db_connection()
    # カテゴリ名も一緒に取得しておくと、管理がしやすくなりますわ
    query = """
        SELECT p.*, c.name AS category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.is_active = 1
        ORDER BY p.category_id, p.name
    """
    products = conn.execute(query).fetchall()
    conn.close()
    return render_template("manage_products.html", products=products)


# --- 3. スタッフ登録画面 ---
@app.route("/admin/add_staff", methods=["GET", "POST"])
def add_staff():
    if request.method == "POST":
        name = request.form["name"]
        role = request.form.get(
            "role", "staff"
        )  # roleが送られてこなければ 'staff' にします

        conn = get_db_connection()
        # お写真の構成に合わせて role も含めて保存しますわ
        conn.execute("INSERT INTO staffs (name, role) VALUES (?, ?)", (name, role))
        conn.commit()
        conn.close()

        return redirect(url_for("admin_menu"))

    return render_template("add_staff.html")


# --- スタッフ管理 ---
@app.route("/admin/manage_staffs")
def manage_staffs():
    return "スタッフ管理画面（準備中）"


# --- カテゴリ登録 ---
@app.route("/admin/add_category", methods=["GET", "POST"])
def add_category():
    return "カテゴリ登録画面（準備中）"


# --- カテゴリ管理 ---
@app.route("/admin/manage_categories")
def manage_categories():
    return "カテゴリ管理画面（準備中）"


if __name__ == "__main__":
    app.run(debug=True)

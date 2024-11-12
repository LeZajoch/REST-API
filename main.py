from flask import Flask, jsonify, request,  render_template, g, abort
from flask_mysqldb import MySQL
import MySQLdb.cursors
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)  # Povolení CORS pro celou aplikaci
app.config['DEBUG'] = True
app.config['JSON_SORT_KEYS'] = False


# Mock databáze uživatelů pro autentizaci
users = {
    "admin": generate_password_hash("adminpassword"),
    "user1": generate_password_hash("user1password")
}

# Konfigurace pro MySQL
app.config['MYSQL_HOST'] = 'cit.cna044c44gnm.eu-central-1.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = '5HVSK4U4N'
app.config['MYSQL_DB'] = 'blog_db'
app.config['MYSQL_PORT'] = 3306

mysql = MySQL(app)
auth = HTTPBasicAuth()
#homepage render

# Funkce pro ověření uživatele
@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        g.current_user = username
        return True
    return False

@app.route('/')
def home():
    return render_template("index.html")


#test připojení k mysql
@app.route('/test-db', methods=['GET'])
def test_db():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        cursor.close()
        return jsonify({"tables": tables}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint pro vytvoření nového blogového příspěvku
@app.route('/api/blog', methods=['POST'])
@auth.login_required
def create_blog_post():
    if not g.current_user:
        return jsonify({"message": "Authorization required"}), 403
    author = g.current_user  # Nastavíme autora na aktuálního přihlášeného uživatele
    content = request.json.get('content')
    data = request.get_json()
    author = data.get('author')
    content = data.get('content')

    if not author or not content:
        abort(400, 'Author and content are required.')

    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO blog_post (author, content) VALUES (%s, %s)", (author, content))
    mysql.connection.commit()
    post_id = cursor.lastrowid
    cursor.close()

    return jsonify({"id": post_id, "message": "Blog post created successfully"}), 201

# Endpoint pro zobrazení všech blogových příspěvků
@app.route('/api/blog', methods=['GET']) 
def get_all_blog_posts():
    app.logger.debug("GET /api/blog called")
    return jsonify({"message": "Blog posts retrieved"}), 200
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM blog_post")
    blog_posts = cursor.fetchall()
    cursor.close()


    return jsonify(blog_posts), 200

# Endpoint pro získání jednoho blogového příspěvku podle ID
@app.route('/api/blog/<int:blog_id>', methods=['GET'])
def get_blog_post(blog_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM blog_post WHERE id = %s", (blog_id,))
    blog_post = cursor.fetchone()
    cursor.close()

    if blog_post is None:
        abort(404, 'Blog post not found.')

    return jsonify(blog_post), 200

# Endpoint pro smazání blogového příspěvku podle ID
@app.route('/api/blog/<int:blog_id>', methods=['DELETE'])
def delete_blog_post(blog_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM blog_post WHERE id = %s", (blog_id,))
    mysql.connection.commit()
    cursor.close()

    if cursor.rowcount == 0:
        abort(404, 'Blog post not found.')

    return jsonify({"message": "Blog post deleted successfully"}), 200

# Endpoint pro částečný update blogového příspěvku
@app.route('/api/blog/<int:blog_id>', methods=['PATCH'])
@auth.login_required
def update_blog_post(blog_id):
    data = request.get_json()
    fields = []
    values = []

    # Získání informací o příspěvku z databáze
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT owner_id, visibility FROM blog_post WHERE id = %s", (blog_id,))
    post = cursor.fetchone()
    if not post:
        abort(404, 'Blog post not found.')

    owner_id, visibility = post

    # Kontrola oprávnění - pouze vlastník nebo admin může upravit příspěvek
    if g.current_role != 'admin' and g.current_user != owner_id:
        abort(403, 'You are not authorized to edit this blog post.')

    # Zpracování polí pro aktualizaci
    if 'author' in data:
        fields.append("author = %s")
        values.append(data['author'])
    if 'content' in data:
        fields.append("content = %s")
        values.append(data['content'])
    if 'visibility' in data:
        # Ujisti se, že viditelnost může být pouze 'public' nebo 'private'
        if data['visibility'] not in ['public', 'private']:
            abort(400, 'Invalid visibility value.')
        fields.append("visibility = %s")
        values.append(data['visibility'])

    if not fields:
        abort(400, 'No valid fields to update.')

    values.append(blog_id)
    query = "UPDATE blog_post SET " + ", ".join(fields) + " WHERE id = %s"

    cursor.execute(query, tuple(values))
    mysql.connection.commit()
    cursor.close()

    return jsonify({"message": "Blog post updated successfully"}), 200

# Endpoint pro načtení info o API
@app.route('/api/about', methods=['GET'])
def about():
    """
    Dokumentace API
    ---
    responses:
      200:
        description: Popis všech endpointů
    """
    return jsonify({
        "info": "Toto API umožňuje správu blogových příspěvků.",
        "endpoints": [
	    {"method": "GET", "endpoint": "/test-db", "description": "kontrola funkčnosti db"},
            {"method": "POST", "endpoint": "/api/blog", "description": "Vytvoření nového příspěvku"},
            {"method": "GET", "endpoint": "/api/blog", "description": "Načtení všech příspěvků"},
            {"method": "PATCH", "endpoint": "/api/blog/<id>", "description": "Úprava konkrétního příspěvku"},
            {"method": "DELETE", "endpoint": "/api/blog/<id>", "description": "Smazání konkrétního příspěvku"},
            {"method": "GET", "endpoint": "/api/about", "description": "Zobrazení dokumentace API"}
        ],
        "authorization": "API zatím nevyžaduje autorizaci."
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

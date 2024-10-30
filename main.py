from flask import Flask, jsonify, request, abort, render_template
from flask_mysqldb import MySQL
import MySQLdb.cursors
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Povolení CORS pro celou aplikaci

# Konfigurace pro MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'blog_db'

mysql = MySQL(app)

#homepage render
@app.route('/')
def home():
    return render_template("index.html")


#test připojení k mysql
@app.route('/test-db')
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
def create_blog_post():
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
def update_blog_post(blog_id):
    data = request.get_json()
    fields = []
    values = []

    if 'author' in data:
        fields.append("author = %s")
        values.append(data['author'])
    if 'content' in data:
        fields.append("content = %s")
        values.append(data['content'])

    if not fields:
        abort(400, 'No valid fields to update.')

    values.append(blog_id)
    query = "UPDATE blog_post SET " + ", ".join(fields) + " WHERE id = %s"

    cursor = mysql.connection.cursor()
    cursor.execute(query, tuple(values))
    mysql.connection.commit()
    cursor.close()

    if cursor.rowcount == 0:
        abort(404, 'Blog post not found.')

    return jsonify({"message": "Blog post updated successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)

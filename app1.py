from flask import Flask, request, redirect, jsonify, render_template_string
import sqlite3
import random
import string

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('urls.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS urls (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        short_url TEXT UNIQUE,
                        original_url TEXT
                    )''')
    conn.commit()
    conn.close()

def generate_short_url():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

def store_url_mapping(short_url, original_url):
    conn = sqlite3.connect('urls.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO urls (short_url, original_url) VALUES (?, ?)", (short_url, original_url))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
    finally:
        conn.close()

def get_original_url(short_url):
    conn = sqlite3.connect('urls.db')
    cursor = conn.cursor()
    cursor.execute("SELECT original_url FROM urls WHERE short_url = ?", (short_url,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        original_url = request.form.get('url')
        if not original_url:
            return render_template_string(HTML_TEMPLATE, error='Missing URL')
        
        short_url = generate_short_url()
        while get_original_url(short_url) is not None:
            short_url = generate_short_url()
        
        store_url_mapping(short_url, original_url)
        return render_template_string(HTML_TEMPLATE, short_url=request.host_url + short_url)
    
    return render_template_string(HTML_TEMPLATE)

@app.route('/<short_url>')
def redirect_url(short_url):
    original_url = get_original_url(short_url)
    if original_url:
        return redirect(original_url)
    return jsonify({'error': 'URL not found'}), 404

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>URL Shortener</title>
</head>
<body>
    <h1>URL Shortener</h1>
    <form method="post">
        <input type="text" name="url" placeholder="Enter URL" required>
        <button type="submit">Shorten</button>
    </form>
    {% if short_url %}
        <p>Shortened URL: <a href="{{ short_url }}">{{ short_url }}</a></p>
    {% elif error %}
        <p style="color: red;">{{ error }}</p>
    {% endif %}
</body>
</html>
'''

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
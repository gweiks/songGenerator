from flask import Flask, send_file
import os

app = Flask(__name__)

@app.route('/')
def home():
    return send_file('home.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
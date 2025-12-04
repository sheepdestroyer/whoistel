from flask import Flask, render_template, request, redirect, url_for
from contextlib import closing
import history_manager
import whoistel
from datetime import datetime

app = Flask(__name__)

# Ensure history DB is initialized
history_manager.init_history_db()

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    raw_tel = request.form.get('number')
    if not raw_tel:
        return redirect(url_for('index'))

    # Clean number
    tel = raw_tel.replace(' ', '').replace('.', '').replace('-', '')
    if tel.startswith('+33'):
        tel = '0' + tel[3:]

    return redirect(url_for('view_number', number=tel))

@app.route('/view/<number>', methods=['GET'])
def view_number(number):
    with closing(whoistel.setup_db_connection()) as conn:
        result = whoistel.get_full_info(conn, number)

    # Get stats
    spam_count = history_manager.get_spam_count(number)

    return render_template('result.html', result=result, spam_count=spam_count, number=number)

@app.route('/report', methods=['POST'])
def report():
    number = request.form.get('number')
    date = request.form.get('date')
    is_spam = request.form.get('is_spam') == 'on'
    comment = request.form.get('comment')

    # If date is empty, use today
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')

    if number:
        history_manager.add_report(number, date, is_spam, comment)
        return redirect(url_for('view_number', number=number))
    return redirect(url_for('index'))

@app.route('/history', methods=['GET'])
def history():
    reports = history_manager.get_recent_reports()
    return render_template('history.html', reports=reports)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)

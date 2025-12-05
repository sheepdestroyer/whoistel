from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import CSRFProtect
from contextlib import closing
import os
import history_manager
import whoistel
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("A SECRET_KEY environment variable must be set for security reasons.")
csrf = CSRFProtect(app)

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
    tel = whoistel.clean_phone_number(raw_tel)

    return redirect(url_for('view_number', number=tel))

@app.route('/view/<number>', methods=['GET'])
def view_number(number):
    cleaned_number = whoistel.clean_phone_number(number)
    if cleaned_number != number:
        return redirect(url_for('view_number', number=cleaned_number))

    with closing(whoistel.setup_db_connection()) as conn:
        result = whoistel.get_full_info(conn, cleaned_number)

    # Get stats
    spam_count = history_manager.get_spam_count(cleaned_number)

    return render_template('result.html', result=result, spam_count=spam_count, number=cleaned_number)

@app.errorhandler(whoistel.DatabaseError)
def handle_db_error(e):
    app.logger.error(f"Database error: {e}")
    return render_template('error.html', message="Database error occurred"), 500

@app.route('/report', methods=['POST'])
def report():
    # Clean number before storing
    number = whoistel.clean_phone_number(request.form.get('number'))
    date = request.form.get('date')
    is_spam = request.form.get('is_spam') == 'on'
    comment = (request.form.get('comment') or '')[:1024]

    try:
        # This validates the date format. It will fail for invalid formats,
        # empty strings, or if the date is not provided (None).
        datetime.strptime(date, '%Y-%m-%d')
    except (ValueError, TypeError):
        # If validation fails, store as NULL in the database.
        date = None

    if number:
        history_manager.add_report(number, date, is_spam, comment)
        return redirect(url_for('view_number', number=number))
    return redirect(url_for('index'))

@app.route('/history', methods=['GET'])
def history():
    reports = history_manager.get_recent_reports()
    return render_template('history.html', reports=reports)

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)

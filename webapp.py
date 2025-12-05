from flask import Flask, render_template, request, redirect, url_for, flash, g
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

MAX_COMMENT_LENGTH = 1024

@app.template_filter('format_datetime')
def format_datetime(value, format='%d/%m/%Y %H:%M'):
    if not value:
        return ""

    dt_obj = None
    if isinstance(value, datetime):
        dt_obj = value
    elif isinstance(value, str):
        # Try parsing multiple formats, from most to least specific
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
            try:
                dt_obj = datetime.strptime(value, fmt)
                break
            except ValueError:
                pass
        else:  # No format matched
            app.logger.warning(f"Could not parse datetime string: '{value}'")

    if dt_obj:
        return dt_obj.strftime(format)

    return "" # Return empty string if parsing failed

def get_history_db():
    if 'history_db' not in g:
        g.history_db = history_manager.get_db_connection()
    return g.history_db

def get_main_db():
    if 'main_db' not in g:
        g.main_db = whoistel.setup_db_connection()
    return g.main_db

@app.teardown_appcontext
def close_dbs(error):
    history_db = g.pop('history_db', None)
    if history_db is not None:
        history_db.close()
    
    main_db = g.pop('main_db', None)
    if main_db is not None:
        main_db.close()

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    raw_tel = request.form.get('number')
    if not raw_tel:
        flash("Veuillez saisir un numéro.", "error")
        return redirect(url_for('index'))

    # Clean number
    tel = whoistel.clean_phone_number(raw_tel)

    if not tel.isdigit():
        flash("Le numéro de téléphone est invalide. Il ne doit contenir que des chiffres et des séparateurs courants.", "error")
        return redirect(url_for('index'))

    return redirect(url_for('view_number', number=tel))

@app.route('/view/<number>', methods=['GET'])
def view_number(number):
    cleaned_number = whoistel.clean_phone_number(number)
    
    if not cleaned_number.isdigit():
        return render_template('error.html', message="Le format du numéro est invalide."), 400

    if cleaned_number != number:
        return redirect(url_for('view_number', number=cleaned_number))

    conn = get_main_db()
    result = whoistel.get_full_info(conn, cleaned_number)

    # Get stats
    # Get stats
    spam_count = history_manager.get_spam_count(cleaned_number, conn=get_history_db())

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
    comment = (request.form.get('comment') or '')[:MAX_COMMENT_LENGTH]

    try:
        # This validates the date format. It will fail for invalid formats,
        # empty strings, or if the date is not provided (None).
        datetime.strptime(date, '%Y-%m-%d')
    except (ValueError, TypeError):
        # If validation fails, store as NULL in the database.
        date = None

    if number:
        history_manager.add_report(number, date, is_spam, comment, conn=get_history_db())
        flash("Signalement enregistré.", "success")
        return redirect(url_for('view_number', number=number))
    return redirect(url_for('index'))

@app.route('/history', methods=['GET'])
def history():
    reports = history_manager.get_recent_reports(conn=get_history_db())
    return render_template('history.html', reports=reports)

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)

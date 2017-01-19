from datetime import datetime
from ConfigParser import ConfigParser
import os.path
from flask import flash, Flask, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect
from flask_stormpath import login_required, StormpathManager, user


"""
COnfiguration check
"""
env_files = ['flaskr.ini', 'apiKey.properties']
for file in env_files:
    if not os.path.isfile(file):
        raise IOError('Generate env files before running the application.')


"""
Environment settings.
"""
config = ConfigParser()
config.read('flaskr.ini')


"""
Application settings.
"""
flaskr_credentials = {
    'DEBUG': True,
    'SECRET_KEY': 'travis_secret',
    'STORMPATH_API_KEY_FILE': 'apiKey.properties',
    'STORMPATH_APPLICATION': 'flaskr_travis',
    'STORMPATH_CONFIG_PATH': os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'config', 'default-config' + '.yml'),

    # Social login
    'STORMPATH_SOCIAL': {
        'FACEBOOK': {
            'app_id': config.get('env', 'FACEBOOK_APP_ID'),
            'app_secret': config.get('env', 'FACEBOOK_APP_SECRET')},
        'GOOGLE': {
            'client_id': config.get('env', 'GOOGLE_CLIENT_ID'),
            'client_secret': config.get('env', 'GOOGLE_CLIENT_SECRET')}
    },
    'STORMPATH_ENABLE_FACEBOOK': True,
    'STORMPATH_ENABLE_GOOGLE': True
}

app = Flask(__name__)
csrf = CSRFProtect(app)
app.config.update(flaskr_credentials)
stormpath_manager = StormpathManager(app)


"""
Views
"""


@app.route('/')
@login_required
def index():
    from helpers import development

    flash('Use this view for testing out any flask / python-sdk stuff.')
    params = {
        'login': 'sasabackup@yahoo.com',
        'password': 'Thesouprecha1'
    }
    development(params)
    return render_template('layout.html')


@app.route('/posts')
@login_required
def show_posts():
    posts = []
    for account in stormpath_manager.application.accounts.search(user.email):
        if account.custom_data.get('posts'):
            posts.extend(account.custom_data['posts'])
    posts = sorted(posts, key=lambda k: k['date'], reverse=True)
    return render_template('show_posts.html', posts=posts)


@app.route('/add', methods=['POST'])
@login_required
def add_post():
    if not user.custom_data.get('posts'):
        user.custom_data['posts'] = []

    user.custom_data['posts'].append({
        'date': datetime.utcnow().isoformat(),
        'title': request.form['title'],
        'text': request.form['text'],
    })
    user.save()

    flash('New post successfully added.')
    return redirect(url_for('show_posts'))


@app.route('/invalid_request')
def invalid_request():
    flash('This is how I handle the response.')
    return render_template('show_posts.html', posts=[])

if __name__ == '__main__':
    app.run()

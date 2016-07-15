from datetime import datetime
from flask import (
    abort, flash, Flask, redirect, render_template, request, url_for)
#
import sys
from os import environ
sys.path.insert(0, '/home/sasa/Projects/stormpath/stormpath-flask')
from flask_stormpath import login_required, StormpathManager, user
#


"""
Application settings.
"""
app = Flask(__name__)
app.config.update({
    'DEBUG': True,
    'SECRET_KEY': '365jeproslodana',
    'STORMPATH_API_KEY_FILE': 'apiKey.properties',
    'STORMPATH_APPLICATION': 'flaskr',

    # Social login
    'STORMPATH_SOCIAL': {
        'FACEBOOK': {
            'app_id': '',
            'app_secret': ''},
        'GOOGLE': {
            'client_id': '',
            'client_secret': ''}
    },
    'STORMPATH_ENABLE_FACEBOOK': True,
    'STORMPATH_ENABLE_GOOGLE': True
})
stormpath_manager = StormpathManager(app)


"""
Views
"""
@app.route('/')
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



if __name__ == '__main__':
    app.run()

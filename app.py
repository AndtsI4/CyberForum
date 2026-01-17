import os
from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, request, abort, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_bcrypt import Bcrypt
from sqlalchemy import or_

from models import db, User, Post, Comment
from forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, CommentForm
from utils import save_picture, time_ago

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245' #random iyos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'cyber-info'

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ეს ფუნქცია საშუალებას გვაძლევს ყველა შაბლონში გამოვიყენოთ `time_ago`
@app.context_processor
def inject_utilities():
    return dict(time_ago=time_ago)

@app.context_processor
def inject_now():
    return {'date_now': datetime.utcnow().strftime('%Y-%m-%d %H:%M')}

# ადმინის დეკორატორი
from functools import wraps
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# "ბოლო აქტივობის" განახლება ყოველ მოთხოვნაზე
@app.before_request
def update_last_seen():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

#errorebis martva
@app.errorhandler(404)
def error_404(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def error_403(error):
    return render_template('errors/403.html'), 403

@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    category_filter = request.args.get('category', '')

    query = Post.query

    # dzebnis logika
    if search_query:
        query = query.filter(
            or_(
                Post.title.contains(search_query),
                Post.content.contains(search_query)
            )
        )
    
    # kategoriis filtri
    if category_filter:
        query = query.filter_by(category=category_filter)

    # yvelaze axalit dasortva
    posts = query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    
    return render_template('index.html', posts=posts, q=search_query, cat=category_filter)

#authentikacia
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw, bio=form.bio.data)
        
        # pirveli momxmarebeli (me) avtomaturad xdeba admini websaitis
        if User.query.count() == 0:
            user.is_admin = True
            
        db.session.add(user)
        db.session.commit()
        flash('სისტემაში რეგისტრაცია წარმატებულია! გაიარეთ ავტორიზაცია.', 'cyber-success')
        return redirect(url_for('login'))
    return render_template('register.html', title='ინიციალიზაცია', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'მოგესალმებით, {user.username}. წვდომა დაშვებულია.', 'cyber-success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('წვდომა უარყოფილია. შეამოწმეთ მონაცემები.', 'cyber-danger')
    return render_template('login.html', title='ავტორიზაცია', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

#postebi da damatebiti funqciebi
@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        pic_file = None
        if form.image.data:
            pic_file = save_picture(form.image.data, folder_name='post_pics')
            
        post = Post(title=form.title.data, content=form.content.data, 
                    category=form.category.data, author=current_user, image_file=pic_file)
        db.session.add(post)
        db.session.commit()
        flash('მონაცემი ატვირთულია სერვერზე!', 'cyber-success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='ახალი პოსტი', form=form, legend='ახალი პოსტი')

@app.route("/post/<int:post_id>", methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    
    #naxvebis logika
    if 'viewed_posts' not in session:
        session['viewed_posts'] = []

    # თუ ამ სესიაში ეს პოსტი ჯერ არ უნახავს, მოუმატოს ნახვა
    if post_id not in session['viewed_posts']:
        post.views += 1
        db.session.commit()
        session['viewed_posts'].append(post_id)
        session.modified = True
    
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('კომენტარისთვის შედით სისტემაში.', 'cyber-info')
            return redirect(url_for('login'))
        comment = Comment(content=form.content.data, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        flash('კომენტარი დაემატა.', 'cyber-success')
        return redirect(url_for('post', post_id=post.id))
        
    return render_template('post_detail.html', title=post.title, post=post, form=form)

# laikebis funqcionireba
@app.route("/post/<int:post_id>/like")
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post in current_user.liked_posts:
        current_user.liked_posts.remove(post) # Unlike
    else:
        current_user.liked_posts.append(post) # Like
    db.session.commit()
    return redirect(url_for('post', post_id=post.id))

#profilebi da admini
@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data, folder_name='profile_pics', output_size=(150, 150))
            current_user.image_file = picture_file
        
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('პროფილი განახლებულია!', 'cyber-success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
        
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='ანგარიში', image_file=image_file, form=form)

@app.route("/admin_panel")
@admin_required
def admin_panel():
    users = User.query.all()
    posts = Post.query.all()
    return render_template('admin_panel.html', users=users, posts=posts)

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    # მხოლოდ ავტორს ან ადმინს შეუძლია წაშლა
    if post.author != current_user and not current_user.is_admin:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('პოსტი განადგურებულია!', 'cyber-success')
    return redirect(url_for('home'))

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user and not current_user.is_admin:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.category = form.category.data
        if form.image.data:
             post.image_file = save_picture(form.image.data, folder_name='post_pics')
        db.session.commit()
        flash('პოსტი განახლდა!', 'cyber-success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form.category.data = post.category
    return render_template('create_post.html', title='რედაქტირება', form=form, legend='რედაქტირება')

#gashveba
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
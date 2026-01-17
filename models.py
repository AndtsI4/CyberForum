from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


# დამხმარე ცხრილი ლაიქებისთვის. არ სჭირდება ცალკე კლასი
post_likes = db.Table('post_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True)
)

#momxmareblis identifikacia
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    
    # quality of life funqciebi
    bio = db.Column(db.String(200), nullable=True)  # მოკლე აღწერა პროფილისთვის
    is_admin = db.Column(db.Boolean, default=False, nullable=False) # Admin Status
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) # რეგისტრაციის დრო
    last_seen = db.Column(db.DateTime, default=datetime.utcnow) # აქტივობის სტატუსისთვის

    # Relationships (კავშირები)
    # cascade="all, delete-orphan" -> თუ User წაიშლება, მისი Post-ებიც თან მიყვება.
    posts = db.relationship('Post', backref='author', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='author', lazy=True, cascade="all, delete-orphan")
    
    #მომხმარებლის მიერ დალაიქებული პოსტები
    liked_posts = db.relationship('Post', secondary=post_likes, backref=db.backref('liked_by', lazy='dynamic'))

    @property
    def rank(self):
        """
        tamashis nairi rankebis sistema
        ითვლის მომხმარებლის პოსტების რაოდენობას და ანიჭებს კიბერ-რანგს.
        """
        if self.is_admin:
            return "ROOT_USER 🛡️" # ადმინისტრატორი
        
        post_count = len(self.posts)
        
        if post_count >= 15:
            return "LEGENDARY_ROOT 💀" # ელიტარული ჰაკერი
        elif post_count >= 5:
            return "CYBER_OPERATIVE 🕵️" # გამოცდილი
        else:
            return "SCRIPT_KIDDIE 👶" # დამწყები

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.rank}')"


#forumis postebi
class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True) # თუ პოსტი დარედაქტირდა
    
    #damatebiti funqciebi
    category = db.Column(db.String(50), nullable=False, default='General')
    image_file = db.Column(db.String(20), nullable=True) # პოსტის სურათი
    views = db.Column(db.Integer, default=0) # ნახვების მთვლელი
    
    # Foreign Keys & Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")

    @property
    def reading_time(self):
        """
        Algorithm:
        ითვლის პოსტის წასაკითხად საჭირო დროს.
        საშუალო სიჩქარე: 200 სიტყვა/წუთში.
        """
        word_count = len(self.content.split())
        minutes = round(word_count / 200)
        return max(1, minutes) # მინიმუმ 1 წუთს აბრუნებს

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}', Views: {self.views})"


#momxmareblis komentarebii
class Comment(db.Model):
    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    def __repr__(self):
        return f"Comment('{self.content[:20]}...', User: {self.user_id})"
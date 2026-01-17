from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp
from models import User

#authentikatori
class RegistrationForm(FlaskForm):
    username = StringField('Username', 
                           validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', 
                        validators=[DataRequired(), Email()])
    bio = TextAreaField('Bio / Status')
    
    # განახლებული პაროლის ვალიდაცია
    password = PasswordField('Password', 
                             validators=[
                                 DataRequired(), 
                                 Length(min=8, max=20, message='პაროლი უნდა იყოს 8-დან 20 სიმბოლომდე!')
                             ])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[
                                         DataRequired(), 
                                         EqualTo('password', message='პაროლები არ ემთხვევა!')
                                     ])
    submit = SubmitField('SYSTEM_INITIALIZE')

    #შემოწმება ბაზაში უნიკალურობაზე
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('ეს იდენტიფიკატორი უკვე სისტემაშია. სცადეთ სხვა.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('ამ მეილით რეგისტრაცია უკვე არსებობს.')


class LoginForm(FlaskForm):
    email = StringField('ელ-ფოსტა', validators=[DataRequired(), Email()])
    password = PasswordField('პაროლი', validators=[DataRequired()])
    remember = BooleanField('სესიის დამახსოვრება')
    submit = SubmitField('ACCESS_GRANT')


#momxmareblis profili da interactions
class UpdateAccountForm(FlaskForm):
    username = StringField('იდენტიფიკატორი', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('ელ-ფოსტა', validators=[DataRequired(), Email()])
    
    # QoL: სურათის ატვირთვა ვალიდაციით
    picture = FileField('პროფილის სურათი', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'მხოლოდ სურათებია დაშვებული!')
    ])
    bio = TextAreaField('მოკლე ბიოგრაფია', validators=[Length(max=200)])
    
    submit = SubmitField('UPDATE_IDENTITY')

    #მოწმდება მხოლოდ მაშინ, თუ მომხმარებელმა შეცვალა მონაცემი
    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('ეს სახელი დაკავებულია.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('ეს მეილი დაკავებულია.')


class PostForm(FlaskForm):
    title = StringField('სათაური / Subject', validators=[DataRequired()])
    content = TextAreaField('შინაარსი / Content', validators=[DataRequired()])
    
    #kategoriebi
    category = SelectField('კატეგორია / Category', choices=[
        ('Software Engineering', 'Software Engineer 💻'),
        ('Web Developing', 'Web Developer 🌐'),
        ('Exploiting', 'Exploiter 💣'),
        ('Ethical Hacking', 'Ethical Hacking 🛡️'),
        ('Linux', 'Linux Mastery 🐧'),
        ('Cybersecurity', 'Cybersecurity 🔐'),
        ('Coding', 'General Coding ☕'),
        ('General Discussion', 'General Discussion 🦜'),
        ('Malware', 'Malware 🦠')
    ], validators=[DataRequired()])

    image = FileField('სურათის მიმაგრება (Optional)', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('TRANSMIT DATA')


class CommentForm(FlaskForm):
    content = TextAreaField('კომენტარი', validators=[DataRequired(), Length(min=2, max=500)])
    submit = SubmitField('SEND_PACKET')
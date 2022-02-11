import json
import random
import string
import urllib.request
from datetime import datetime, timedelta
from email.mime.multipart import MIMEBase, MIMEMultipart
from functools import wraps

from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for)
from flask_mail import Mail, Message
from flask_mysqldb import MySQL
from flask_swagger_ui import get_swaggerui_blueprint
from passlib.handlers.sha2_crypt import sha256_crypt
from wtforms import Form, StringField, TextAreaField, validators

from api import *
from flask_session import Session
from models import *

sess = Session()
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(minutes=30)
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'qwallityapp@gmail.com'
app.config['MAIL_PASSWORD'] = 'Abc@123123'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

SWAGGER_URL = '/swagger'
authorizations = '"Bearer": {"type": "Bearer Token", "in": "header", "name": "Authorization"}'
API_URL = '/static/swagger.json'
SWAGGER_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "app_name": "QwallityApp API"
    }
)
app.register_blueprint(blueprint=SWAGGER_BLUEPRINT, url_prefix=SWAGGER_URL, authorizations=authorizations)
key =''.join(random.choices(string.ascii_uppercase +
                             string.digits, k = 10))
app.config['SECRET_KEY'] = key
sess.init_app(app)
api_key = '3d22940be1eb70fcfe47f0fc0de9a7fa'


admin = False
# About us page funtion
@app.route('/about')
def about():
    return render_template('about.html')


# User registration
@app.route('/register', methods=['GET','POST'])
def user_register():
    form=RegisterForm(request.form)

    if request.method == 'POST' and form.validate():
        first_name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        role_id = 2
        account = 100
        #Create Users object
        new_user = Users(first_name=first_name, email=email, username=username, password=password, role_id=role_id, account=account)
        existing_email = Users.query.filter_by(email=email).first()            #return top 1 email
        existing_username = Users.query.filter_by(username=username).first()   #return top 1 username
        if existing_email:
            flash('User with this email is already exists', 'error')
            return (render_template('register.html', form=form))
            
        elif existing_username:    
            flash('User with this username is already exists', 'error')   
            return (render_template('register.html', form=form))         
        else:
            db.session.add(new_user)
            db.session.commit()
    
            flash('Your account has been successfully registered.', 'success')
            return redirect(url_for('login'))
    return(render_template('register.html', form=form))


@app.route('/login', methods=['GET','POST'])
def login():

    if request.method=='POST':
    
        #get form fields
        username = request.form['username']
        password_candidate = request.form['password']
        print(request.form)
        #get username from db
        result = Users.query.filter_by(username=username).first()
        if result:
            # return redirect(url_for('index'))
            password = result.password
            
            #compare password
            if sha256_crypt.verify(password_candidate, password):
              
                session['logged_in'] = True
                session['username'] = username   
                flash('You are now logged in', 'success') 
              
                return redirect(url_for('index'))
            else:
                error = 'Invalid username or password'
                return render_template('login.html', error=error)                             
        else:
            error = 'Username is not found'
            return render_template('login.html', error=error)  
           
    return render_template('login.html')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
 
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized user. Please register or log in.', 'danger')
            return redirect(url_for('login'))
    return wrap

@is_logged_in
def get_role():   
    try:
        role = Users.query.with_entities(Users.role_id).filter_by(username=session['username']).first()[0]
    except:
        print('user not found')
    return role   


@is_logged_in
@app.route('/profile', methods=['Get', 'Post'])
def profile():
    username = Users.query.filter_by(username=session['username']).first()
    form1 = Account(request.form)
    form1.account_balance.data = (db.session.query(Users.account).filter_by(username=session['username'])).first()[0]
    form2 = Admin(request.form)
    roles = ['admin', 'non_admin']
    if get_role() == 2:
        if request.method == 'POST' and form1.validate():
           
            if not form1.amount.data.isdigit():
                flash('Amount accept only digits', 'error')
            else:
                amount = int(form1.amount.data)
                form1.amount.data = 0
                username.account = form1.account_balance.data + amount
                db.session.commit()
                form1.account_balance.data = (db.session.query(Users.account).filter_by(username=session['username'])).first()[0]
                flash('Your changes are done', 'success')
            return render_template('profile.html', form1=form1)
            
        return render_template('profile.html', form1=form1)
    else:
        if request.method == 'POST':
     
            if request.form.get('roles') == 'admin':
                Users.query.filter(Users.username == form2.username.data).\
                update({Users.role_id: 1})
            else:
                Users.query.filter(Users.username == form2.username.data).\
                update({Users.role_id: 2})
            db.session.commit()
            flash('Role is changed', 'success') 
            return render_template('profile_admin.html', form2=form2, roles=roles)
        return render_template('profile_admin.html', form2=form2, roles=roles)        

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


#Homepage
@app.route('/')
def index():
    courses = Courses.query.order_by(Courses.id.desc()).all()
    if get_role() == 1:
        return render_template('home.html', courses=courses)
    else:
         return render_template('home_nonadmin.html', courses=courses)
# -----------------------------------------------courses--------------------------------

# create course form
class courseForm(Form):
    title       = StringField('Title', [validators.Length(min=1, max=200)])
    body        = TextAreaField('Description')
    course_type = StringField('Type')
    price = StringField('Price')

# insert new course
@app.route('/add_course', methods=['GET','POST'])
def add_course():
    form=courseForm(request.form)
    if request.method=='POST' and form.validate():
        title       = form.title.data
        body        = form.body.data
        coursetype  = request.form.get('type')
        price = form.price.data
        new_course=Courses(title=title, body=body, coursetype=coursetype, author=session['username'], price=price)
        db.session.add(new_course)
        db.session.commit()
        return redirect(url_for('index'))

    return(render_template('add_course.html', form=form))


# edit course page
@app.route('/edit_course/<string:id>', methods=['GET','POST'])
@is_logged_in
def edit_course(id):
    course=Courses.query.get(id)
    return(render_template("edit_course.html", course=course))

# update course details
@app.route('/course/<int:id>/update', methods=["POST","GET"])
def course_update(id):
    course=Courses.query.get(id)

    form=courseForm(request.form)
    form.title.data=(db.session.query(Courses.title).filter(Courses.id==id).first())[0]
    form.body.data=(db.session.query(Courses.body).filter(Courses.id==id).first())[0]

    if request.method=="POST":
        course.title=request.form['title']
        course.body=request.form['body']
        try:
            db.session.commit()
            flash('Your changes are done', 'success')
            
            return redirect('/courses') 
            
        except:
            return "Something went wrong"
    else:
        
        return(render_template("edit_course.html", form=form))

@app.route('/course/<int:id>/details')
def course_details(id):
    course=Courses.query.get(id)

    form=courseForm(request.form)
    form.title.data=(db.session.query(Courses.title).filter(Courses.id==id).first())[0]
    form.body.data=(db.session.query(Courses.body).filter(Courses.id==id).first())[0]

    return(render_template("course_details.html", form=form))
          

# delete course
@app.route('/course/<int:id>/delete')
def course_delete(id):
    course=Courses.query.get_or_404(id)

    try:
        db.session.delete(course)
        db.session.commit()
        flash('Course is deleted', 'success')
        return redirect('/courses')
    except:
        return "Something went wrong"


# get article detail
@app.route('/courses/course/<int:id>', methods=['GET', 'POST'])
def art_detail(id):
    course = Courses.query.get(id)
    users = [user.user_id for user in UserCourses.query.filter_by(course_id=id)]
    user_id = db.session.query(Users.id).filter_by(username=session['username']).first()[0]
    if get_role() == 1:
        return(render_template("art_details.html", course=course))
    elif get_role() == 2 and request.method == 'POST' or user_id in users:
        if request.method == 'POST':
            user_course = UserCourses(user_id=user_id, course_id=id)
            db.session.add(user_course)
            username = Users.query.filter_by(username=session['username']).first()
            username.account = db.session.query(Users.account).filter_by(username=session['username']).first()[0] - course.price
            showbuy = False
            if username.account < 0:
                flash('Account balance insufficient ', 'error')
                return(render_template("art_details_nonadmin.html", course=course))
            db.session.commit()
      
        return redirect(url_for('my_courses'))
    else:
        return(render_template("art_details_nonadmin.html", course=course))

# display all courses in courses page
@app.route('/courses')
@is_logged_in
def courses():
    return render_template('courses.html')

# foundamental courses page
@app.route('/courses/fundamental')
@is_logged_in
def fundamental_courses():
    user_id = db.session.query(Users.id).filter_by(username=session['username']).first()[0]
    course_id = [course.course_id for course in UserCourses.query.filter_by(user_id=user_id)]
    courses = db.session.query(Courses).filter((Courses.id.notin_(course_id))).filter_by(coursetype=1)
    if get_role()==2:

        return render_template('fundamental_courses.html', courses=courses)
    else:
        return render_template('fundamental_courses_admin.html', courses=courses)



@app.route('/mycourses')
@is_logged_in
def my_courses():
    user_id = db.session.query(Users.id).filter_by(username=session['username']).first()[0]
    course_id = [course.course_id for course in UserCourses.query.filter_by(user_id=user_id)]
    courses = db.session.query(Courses).filter((Courses.id.in_(course_id)))
    return render_template('my_courses.html', courses=courses)


# advanced courses page
@app.route('/courses/advanced')
@is_logged_in
def advanced_courses():
    user_id = db.session.query(Users.id).filter_by(username=session['username']).first()[0]
    course_id = [course.course_id for course in UserCourses.query.filter_by(user_id=user_id)]
    courses = db.session.query(Courses).filter((Courses.id.notin_(course_id))).filter_by(coursetype=2)
    if get_role()==2:
        return render_template('advanced_courses.html', courses=courses)
    else:
        return render_template('advanced_courses_admin.html', courses=courses)

# display course by id
@app.route('/courses/course/<int:id>')
def course_detail(id):
    course=Courses.query.get(id)
    return(render_template("course.html", course=course))



@app.route('/sendmail', methods=["POST","GET"])
def send_pass():
    form=Forgot(request.form)
    existing_email=Users.query.filter_by(email=form.email.data).first() 
    if request.method=='POST' and form.validate():
        if existing_email:
            msg = MIMEMultipart()
            code = ''.join(random.choice(string.digits) for i in range(7))
            msg = Message('Code', sender = 'qwallityapp@gmail.com', recipients = [form.email.data])
            msg.body = code
            mail.send(msg)
            flash('Secret code sent to your email', 'success') 
            new_code=Codes(email=form.email.data, gen_code=code, is_used=0)
            db.session.add(new_code)
            db.session.commit()
        else:
            flash('Email is not registered, try registered email', 'error')
    return render_template('sendmail.html', form=form)


@app.route('/resetpass', methods=["POST","GET"])
def reset_pass():
    form=Reset(request.form)
    if request.method=='POST' and form.validate():
        users=Users.query.get(id)
        try:
            code_usage = Codes.query.with_entities(Codes.is_used).filter_by(gen_code=form.code.data).first()[0]
            code_email = Codes.query.with_entities(Codes.email).filter_by(gen_code=form.code.data).first()[0]
            if code_usage==0:
                Codes.query.filter(Codes.gen_code==form.code.data).\
                update({Codes.is_used: 1}, synchronize_session=False)
                Users.query.filter(Users.email==code_email).\
                update({Users.password:sha256_crypt.encrypt(str(form.new_password.data)) })
                db.session.commit()
                flash('Your password is changed', 'success') 
            else:
                flash('Code is expired', 'error')
        except:
            flash('Code is not valid', 'error')
    return render_template('resetpass.html', form=form)

    
# After each request check response, if response is 404, redirect to main page
@app.after_request
def after_request_func(response):
    response_code=response.status_code
    if response_code==404:
        url_list=request.url.split('/')
        redirect_url=url_list[0]+'//'+url_list[2]+'/'+url_list[-1]
        return redirect(redirect_url)
 
    return response

@app.route('/calculator', methods=["POST","GET"])
def calculate():
    form = Calculator(request.form)
    output=0
    thing = ''
    if request.method=='POST' and form.validate():
        if request.form.get('Calculate'):
            thing = request.form.get('thing','')
            num1     = float(form.number1.data.replace(',','.'))
            num2     = float(form.number2.data.replace(',','.'))
            if request.form.get('thing')=='addition':
                output=num1+num2
            elif request.form.get('thing')=='subtraction':
                 output=num1-num2
            elif request.form.get('thing')=='multiplication':
                if num1==0 or num2==0:
                    output == 0
                else:
                    output=num1*num2           
            elif request.form.get('thing')=='division':
                if num2==0:
                    flash('Can not devide by zero', 'error')
                elif  num1==0:
                    output == 0.0
                else:
                    output=float(num1/num2)
        elif request.form.get('Reset'):
            form.number1.data = 0
            form.number2.data = 0
    return render_template('calculator.html', form=form, output=output, thing=thing)

@app.route('/exercises')
def exercises():
    return render_template('exercises.html')

@app.route('/blackbox', methods=["POST","GET"])
def blackbox():
    form = Blackbox(request.form)
    if request.method=='POST' :
        if request.form.get('Reset'):
            form.name.data = ''
            form.address.data = ''
            form.phone.data = ''
        elif request.form.get('Check') and form.validate():
            flash('Information is correct', 'success')              
    return render_template('blackbox.html', form=form)


if __name__=='__main__':
    app.secret_key='secret'
    app.run(debug=True)

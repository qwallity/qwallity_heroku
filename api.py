from flask import Flask, render_template, flash, redirect, url_for, session,\
     logging, request, jsonify, make_response
from passlib.handlers.sha2_crypt import sha256_crypt
from datetime import datetime
from functools import wraps
import jwt
from flask_session import Session
from datetime import timedelta
from models import *



# Check if user logged in
def is_logged_in_api(f):
    @wraps(f)
    def login_decorator(*args, **kwargs):
        token = None
        try:
            token = request.headers['Authorization'].split('Bearer')[1].strip()
        except:
            return jsonify({'message':'Token is missing'}),403
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms="HS256")
        except:
            return jsonify({'message': 'Token is invalid'}),403
        return f(*args, **kwargs)
    return login_decorator

# check if user is admin
def is_admin_api(f):
    @wraps(f)
    def admin_decorator(*args, **kwargs):
        token = request.headers['Authorization'].split('Bearer')[1].strip()
        data = jwt.decode(token,  app.config['SECRET_KEY'], algorithms="HS256")
        if data['role'] != 1:
            return jsonify({'message': 'Unauthorized'}),401
        return f(*args, **kwargs)
    return admin_decorator
    
#User login
@app.route('/login/api', methods=['POST'])
def login_api():
    if request.method=='POST':
        auth = request.authorization
        #get form fields
        username = auth.username
        password_candidate = auth.password
          #get username from db
        result = Users.query.filter_by(username=username).first()
        if result and sha256_crypt.verify(password_candidate, result.password):
            token = jwt.encode({'username': username, 'id': result.id, 'role': result.role_id, 'exp': datetime.utcnow()+timedelta(minutes=30)},\
                    app.config['SECRET_KEY'])
            return jsonify({'token' : token})
        else:
            return make_response('Could not Verify',403, {'WWW-Authenticate' : 'Basic realm=Login Required'})     
        
    return render_template('login.html')

@app.route('/register/api', methods=['POST'])
def user_register_api():

        first_name     = request.json['first_name']
        email          = request.json['email']
        username       = request.json['username']
        password       = sha256_crypt.encrypt(request.json['password'])
        role_id        = 2
        account        = 100
        #Create Users object
        new_user=Users(first_name=first_name,email=email, username=username, password=password, role_id=role_id, account=account)
        existing_email=Users.query.filter_by(email=email).first()            #return top 1 email
        existing_username=Users.query.filter_by(username=username).first()   #return top 1 username
        
        if existing_email:
            return jsonify({'message': 'User with this email is already exists'})
            
        elif existing_username:    
            return jsonify({'message': 'User with this username is already exists'})
        else:
            db.session.add(new_user)
            db.session.commit()
            result = Users.query.filter_by(username=username).first()
            session['logged_in'] = True
            return jsonify({'message': 'User is created'})

class TaskSchema(ma.Schema):
    class Meta:
        fields=('id','title', )

task_schema=TaskSchema()
tasks_schema=TaskSchema(many=True)


# get advanced courses
@app.route('/courses/advanced/api')
@is_logged_in_api
def advanced_courses_api():
    count_result=Courses.query.filter_by(coursetype=2).count()
    courses=Courses.query.filter_by(coursetype=2).order_by(Courses.id.desc())
    result=tasks_schema.dump(courses)
    payload = {
    "count":count_result,
    "result":result
}
    return jsonify(payload)
     

# get fundamental courses
@app.route('/courses/fundamental/api')
@is_logged_in_api
def fundamental_courses_api():
    count_result=Courses.query.filter_by(coursetype=1).count()
    courses=Courses.query.filter_by(coursetype=1).order_by(Courses.id.desc())

    result=tasks_schema.dump(courses)
    result=tasks_schema.dump(courses)
    
    payload = {
    "count":count_result,
    "result":result
    
}
    return jsonify(payload)

# add new article
@app.route('/add_course/api', methods=['POST'])
@is_logged_in_api
@is_admin_api
def add_course_api():

    if request.method=='POST':
        title       = request.json['title']
        body        = request.json['body']
        coursetype  = request.json['coursetype']
        author      =  request.json['author']

        new_course=Courses(title=title, body=body, coursetype=coursetype, author=author)
        if coursetype not in ("1","2"):
            return (f"Course type should be 1 or 2")
        db.session.add(new_course)
        db.session.commit()
        return  task_schema.jsonify(new_course)

# add amount 
@app.route('/add_account_balance/<string:username>/api', methods=["POST"])
@is_logged_in_api
def add_account_balance_api(username):

    if request.method=="POST":
       # get form fields
        username_db = Users.query.filter_by(username=username).first()
        account_balance = db.session.query(Users.account).filter_by(username=username).first()[0]
        username_db.account = request.json['amount'] + account_balance
        try:
            db.session.commit()
            
            return (f'Account Balance is '+ str(username_db.account))
            
        except:
            return "Something went wrong"
# delete article

@app.route('/courses/course/<int:id>', methods=['DELETE'])
@is_logged_in_api
@is_admin_api
def course_delete_api(id):
    if request.method=='DELETE':
        course=Courses.query.get_or_404(id)
        db.session.delete(course)
        db.session.commit()
        return (f"The course with id {id} is deleted")

# buy course
@app.route('/buy_course/api/<int:id>/<string:user>', methods=['POST'])
@is_logged_in_api
def buy_course_api(id, user):
    course = Courses.query.get(id)
    users = [user.user_id for user in UserCourses.query.filter_by(course_id=id)]
    user_id = db.session.query(Users.id).filter_by(username=user).first()[0]
    if user_id not in users:
        user_course = UserCourses(user_id=user_id, course_id=id)
        db.session.add(user_course)
        username = Users.query.filter_by(username=user).first()
        print(db.session.query(Users.account).filter_by(username=user).first()[0])
        print(course.price)
        username.account = db.session.query(Users.account).filter_by(username=user).first()[0] - course.price
        if username.account < 0:
            return('Account Balance is depleted')
        db.session.commit()
        return('Successfully Done')
    else:
        return('You already bought this course')

# get account balance
@app.route('/balance/api/<string:user>', methods=['GET'])
@is_logged_in_api
def get_user_balance( user):  
    balance = db.session.query(Users.account).filter_by(username=user).first()[0] 
    return('User balance is ' + str(balance))


@app.route('/course/<int:id>/update/', methods=["PATCH"])
@is_logged_in_api
@is_admin_api
def course_update_api(id):
    course=Courses.query.get(id)
    if request.method=="PATCH":
        course.title=request.json['title']
        course.body=request.json['body']
        try:
            db.session.commit()
            flash('Your changes are done', 'success')
            
            return (f"The course with id {id} is updated") 
            
        except:
            return "Something went wrong"



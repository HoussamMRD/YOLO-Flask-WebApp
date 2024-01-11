from flask import Flask, render_template, Response,jsonify,request,session ,redirect,url_for

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

#FlaskForm--> it is required to receive input from the user
# Whether uploading a video file  to our object detection model

from flask_wtf import FlaskForm


from wtforms import FileField, SubmitField,StringField,DecimalRangeField,IntegerRangeField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired,NumberRange
import os


# Required to run the YOLOv8 model
import cv2

# YOLO_Video is the python file which contains the code for our object detection model
#Video Detection is the Function which performs Object Detection on Input Video
from YOLO_Video import video_detection
app = Flask(__name__)

app.config['SECRET_KEY'] = 'houssamMRD'
app.config['UPLOAD_FOLDER'] = 'static/files'




app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable Flask-SQLAlchemy modification tracking

db = SQLAlchemy(app)

class Passenger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_passengers = db.Column(db.Integer, nullable=False)







#Use FlaskForm to get input video file  from user
class UploadFileForm(FlaskForm):
    #We store the uploaded video file path in the FileField in the variable file
    #We have added validators to make sure the user inputs the video in the valid format  and user does upload the
    #video when prompted to do so
    file = FileField("File",validators=[InputRequired()])
    submit = SubmitField("Run")


def generate_frames(path_x = ''):
    yolo_output = video_detection(path_x)
    for detection_ in yolo_output:
        ref,buffer=cv2.imencode('.jpg',detection_)

        frame=buffer.tobytes()
        yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame +b'\r\n')

def generate_frames_web(path_x):
    yolo_output = video_detection(path_x)
    for detection_ in yolo_output:
        ref,buffer=cv2.imencode('.jpg',detection_)

        frame=buffer.tobytes()
        yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame +b'\r\n')

@app.route('/', methods=['GET','POST'])



@app.route('/home', methods=['GET','POST'])
def home():
    session.clear()
    return render_template('indexproject.html')
# Rendering the Webcam Rage
#Now lets make a Webcam page for the application
#Use 'app.route()' method, to render the Webcam page at "/webcam"
@app.route("/webcam", methods=['GET','POST'])
def webcam():
    session.clear()
    return render_template('ui.html')
@app.route('/FrontPage', methods=['GET','POST'])
def front():
    # Upload File Form: Create an instance for the Upload File Form
    form = UploadFileForm()
    if form.validate_on_submit():
        # Our uploaded video file path is saved here
        file = form.file.data
        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'],
                               secure_filename(file.filename)))  # Then save the file
        # Use session storage to save video file path
        session['video_path'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'],
                                             secure_filename(file.filename))
    return render_template('videoprojectnew.html', form=form)
@app.route('/video')
def video():
    #return Response(generate_frames(path_x='static/files/bikes.mp4'), mimetype='multipart/x-mixed-replace; boundary=frame')
    return Response(generate_frames(path_x = session.get('video_path', None)),mimetype='multipart/x-mixed-replace; boundary=frame')

# To display the Output Video on Webcam page
@app.route('/webapp')
def webapp():
    #return Response(generate_frames(path_x = session.get('video_path', None),conf_=round(float(session.get('conf_', None))/100,2)),mimetype='multipart/x-mixed-replace; boundary=frame')
    return Response(generate_frames_web(path_x=0), mimetype='multipart/x-mixed-replace; boundary=frame')













@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the credentials are correct
        if username == 'admin' and password == 'admin':
            # Redirect to the dashboard (replace 'dashboard' with your actual dashboard route)
            return redirect(url_for('dashboard'))

    # Render the login page if the credentials are incorrect or it's a GET request
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    # Perform any logout logic here (if needed)
    # For now, let's just redirect to the home page
    return redirect(url_for('home'))















@app.route('/passenger_list')
def passenger_list():
    passengers = Passenger.query.all()
    return render_template('Passenger/passenger_list.html', passengers=passengers)


@app.route('/add_passenger', methods=['GET', 'POST'])
def add_passenger():
    if request.method == 'POST':
        datetime_val = datetime.utcnow()  # You can modify this based on your form data
        total_passengers_val = int(request.form['total_passengers'])  # Assuming 'total_passengers' is the input name in your form

        new_passenger = Passenger(datetime=datetime_val, total_passengers=total_passengers_val)
        db.session.add(new_passenger)
        db.session.commit()

        return redirect(url_for('passenger_list'))

    return render_template('Passenger/add_passenger.html')

@app.route('/edit_passenger', methods=['GET', 'POST'])
def edit_passenger():
    passenger_id = request.args.get('id')
    passenger = Passenger.query.get(passenger_id)

    if request.method == 'POST':
        passenger.datetime = datetime.utcnow()
        passenger.total_passengers = int(request.form['total_passengers'])

        db.session.commit()

        return redirect(url_for('passenger_list'))

    return render_template('Passenger/edit_passenger.html', passenger=passenger)

@app.route('/delete_passenger/<int:id>', methods=['GET', 'POST'])
def delete_passenger(id):
    passenger = Passenger.query.get_or_404(id)

    if request.method == 'POST':
        db.session.delete(passenger)
        db.session.commit()
        return redirect(url_for('passenger_list'))





























if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)





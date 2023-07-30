from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_uploads import UploadSet, configure_uploads
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.utils import secure_filename 
import hashlib
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Thay thế bằng một secret key bất kỳ
app.config['UPLOADED_VIDEOS_DEST'] = 'static/uploads'
app.config['UPLOADED_VIDEOS_URL'] = '/static/uploads/videos/'
#app.config['UPLOADED_VIDEOS_URL'] = '/static/uploads/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db' 
app.config['SQLALCHEMY_BINDS'] = {
    'teachers': 'sqlite:///teachers.db',
    'students': 'sqlite:///students.db'
}   # Sử dụng SQLite database, bạn có thể thay đổi thành database khác nếu muốn

app.config['UPLOAD_FOLDER'] = 'static/uploads'
videos = UploadSet('videos', extensions=('mp4', 'avi', 'mov'))
configure_uploads(app, videos)
db = SQLAlchemy(app)

def create_tables():
    with app.app_context():
        db.create_all()

class User(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    def hash_password(self, password):
        # Hàm mã hóa mật khẩu sử dụng hashlib (SHA256)
        return hashlib.sha256(password.encode()).hexdigest()
    def check_password(self, input_password):
        # Hàm kiểm tra mật khẩu
        return self.password == self.hash_password(input_password)

    #def get_related_content(self):
        # Tìm các nội dung liên quan dựa trên các thẻ tag đã chọn
        #related_content = Content.query.filter(Content.tags.contains(self.tags)).all()
        #return related_content
class Students(User):
    __bind_key__ = 'students'
    tags = db.Column(db.String(200))
    report = db.Column(db.Text)
    def get_tags(self):
        if self.tags:
            tags_json = self.tags
            tags_list = json.loads(tags_json)  # Chuyển đổi chuỗi JSON thành list
            return tags_list
        else:
            return []
    
"""def get_videos_by_tag(tag):
    # Hàm này trả về danh sách các video dựa trên thẻ tag đã chọn
    courses = Courses.query.filter(Courses.tag == tag).all()
    return courses"""
#playlist_video_association = db.Table('playlist_video_association',
    #db.Column('course_id', db.Integer, db.ForeignKey('courses.id'), primary_key=True),
    #db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id'), primary_key=True)
#)
          
class Teachers(User):
    __bind_key__ = 'teachers'
    courses = db.relationship('Courses', backref='teacher', lazy=True)
    playlists = db.relationship('Playlist', backref='teacher', lazy=True)
    
    
class Courses(db.Model):
    __bind_key__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    video_url = db.Column(db.String(200))
    #video_filename = db.Column(db.String(200))  # Thêm thuộc tính mới để lưu tên tệp video đã tải lên
    tag = db.Column(db.String(100))
    playlist = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    teacher_name = db.Column(db.String(80), nullable=False)
    
    
class Playlist(db.Model):
    __bind_key__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)

    
    
def get_teacher_playlists():
    teacher_playlists = []

    for teacher in Teachers.query.all():
        playlists = Playlist.query.filter_by(teacher_id=teacher.id).all()
        for playlist in playlists:
            video_urls = []
            tags = []
            for course in Courses.query.filter_by(teacher_id=teacher.id, playlist=playlist.id).all():
                video_urls.append(course.video_url)
                tags.append(course.tag)

            teacher_playlist = {
                'id': playlist.id,
                'teacher_id': teacher.id,
                'name': playlist.name,
                'playlist_videos': video_urls,
                'tags': tags,
                'num_videos': len(video_urls)
            }
            teacher_playlists.append(teacher_playlist)

    return teacher_playlists
    
def tag_list():
    try:
        with open('tags list.txt', encoding='utf-8') as tep:
            tags = list(map(str.strip, tep.readlines()))
    except FileNotFoundError:
        tags = []

    return tags



def get_unique_filename(filename, upload_folder):
    """
    Trả về tên file duy nhất bằng cách thêm số thứ tự vào tên file nếu trùng lặp.
    Ví dụ: Nếu filename đã tồn tại, trả về 'filename(1).ext'.
    """
    name, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(os.path.join(upload_folder, filename)):
        filename = f"{name}({counter}){ext}"
        counter += 1
    return filename
    
@app.route('/')
def home():
    return render_template("viewpage.html")

#def check_admin(name, password):
    data_admin = (
    ("An", {"password": "28082005"}),
    ("VietQuang", {"password": "456789"}),
    ("Hoàng", {"password": "123456"}),
    ("Tuệ_Mẫn", {"password": "Tuệ_Mẫn"})
)
    for admin_name, admin_password in data_admin:
        if admin_name == name:
            if admin_password["password"] == password:
                return True
            else:
                return False
    return False

#@app.route('/admin')
#def admin_login():
    error_message=None
    if request.method == "POST":
        name_admin_request = request.form['admin_name'] 
        name_admin_request =  request.form['password']     
        if check_admin(name_admin_request, name_admin_request):
            return redirect(url_for('admin_sys'))
        else:
            return render_template('home', error_message = "Tiễn vong")
        
#@app.route('/admin/sys', methods=['GET', 'POST'])
#def admin_sys():
    if request.method == "POST":
        video_id = request.form.get("video_id")
        video = Courses.query.get(video_id)  # Fetch the video from the 'Courses' table
        #general_content = Content.query.get(content_id)  # Fetch the general content from the 'Content' table

        if video:
            db.session.delete(video)
            db.session.commit()
            flash("Video đã được xóa thành công!")
        elif general_content:
            db.session.delete(general_content)
            db.session.commit()
            flash("Nội dung đã được xóa thành công!")
        else:
            flash("Không tìm thấy bài viết!")
        return redirect(url_for("admin_sys"))

    # Fetching both teacher videos and general content
    teachers_videos = Courses.query.all()  # Fetch teacher videos from the 'Courses' table
    general_content = Content.query.all()  # Fetch general user content from the 'Content' table

    teachers_videos.reverse()
    general_content.reverse()

    return render_template("admin.html", teachers_videos=teachers_videos, general_content=general_content)
 
@app.route('/logout')
def logout():
    # Clear the user's session data to log them out
    session.clear()
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    if request.method == 'POST':
        # Xử lý thông tin đăng nhập
        username_or_email = request.form['username_or_email']
        password = request.form['password']
        role = request.form.get('role')

        # Kiểm tra tên đăng nhập hoặc email
        if role == "hocvien":
            user = Students.query.filter((Students.username == username_or_email) | (Students.email == username_or_email)).first()
        elif role == "giaovien":
            user = Teachers.query.filter((Teachers.username == username_or_email) | (Teachers.email == username_or_email)).first()

        if user and user.check_password(password):
            # Đăng nhập thành công, chuyển hướng đến trang cá nhân của người dùng
            if role == "hocvien":
                return redirect(url_for('student_profile', username=user.username))
            elif role == "giaovien":
                return redirect(url_for('teacher_profile', username=user.username))
        else:
            error_message = "Tên đăng nhập hoặc mật khẩu không đúng!"

    return render_template('login.html', error_message=error_message)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Xử lý thông tin đăng ký
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role')

        # Kiểm tra xem tên đăng nhập hoặc email đã tồn tại trong cơ sở dữ liệu chưa
        if role == "hocvien":
            if Students.query.filter((Students.username == username) | (Students.email == email)).first():
                return "Tên đăng nhập hoặc email đã tồn tại!"
            new_student = Students(username=username, email=email, password=User().hash_password(password))
            with app.app_context():
                db.session.add(new_student)
                db.session.commit()
        elif role == "giaovien":
            if Teachers.query.filter((Teachers.username == username) | (Teachers.email == email)).first():
                return "Tên đăng nhập hoặc email đã tồn tại!"
            new_teacher = Teachers(username=username, email=email, password=User().hash_password(password))
            with app.app_context():
                db.session.add(new_teacher)
                db.session.commit()

        # Chuyển hướng đến trang chủ sau khi đăng ký thành công
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/select_tags/<username>', methods=['GET', 'POST'])
def select_tags(username):
    tags = tag_list()
    user = Students.query.filter_by(username=username).first()
    if not user:
        return "User not found"
    if request.method == 'POST':
        tags_selected = request.form.getlist('tags')
        tags_json = json.dumps(tags_selected)  # Chuyển đổi list thành chuỗi JSON
        user.tags = tags_json
        db.session.commit()
        return redirect(url_for('student_profile', username=username))
    else:
        current_tags = user.get_tags()
        return render_template('select_tags.html', tags=tags, current_tags=current_tags, user=user)

@app.route('/playlist/<int:playlist_id>')
def playlist_page(playlist_id):
    # Lấy thông tin về playlist dựa trên playlist_id
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        abort(404)  # Playlist không tồn tại, có thể thay bằng xử lý tùy ý

    return render_template('playlist.html', playlist=playlist)
    
@app.route('/student/<username>')
def student_profile(username):
    user = Students.query.filter_by(username=username).first()
    tags = user.get_tags()  # Gọi hàm tags() của Students để lấy danh sách tags đã chọn
    
    if not tags:
        # Xử lý trường hợp phương thức get_tags() trả về None, có thể chuyển hướng đến trang select_tags
        return redirect(url_for('select_tags', username=username))
    
    # Tạo danh sách các điều kiện 'or_' cho mỗi thẻ tag đã chọn
    tag_conditions = [Courses.tag.in_(tags)]
    # Truy vấn danh sách video dựa trên các thẻ tag đã chọn
    videos_by_tags = Courses.query.filter(or_(*tag_conditions)).all()
    
    teacher_playlists = get_teacher_playlists()
 
    return render_template('user_profile.html', username=username, tags=tags, videos_by_tags=videos_by_tags, teacher_playlists=teacher_playlists)

#@app.route('/view_content/<content_id>')
#def view_content(content_id):
    course = Courses.query.get(content_id)
    if Courses:
        if Courses.pla == 'playlist':
            playlist = Playlist.query.get(content.playlist_id)
            if playlist:
                return render_template('view_playlist.html', playlist=playlist)
            else:
                return "Playlist not found"
        elif content.content_type == 'video':
            video = Courses.query.get(content.video_id)
            if video:
                return render_template('view_video.html', video_id=course.id)
            else:
                return "Video not found"
        else:
            return "Invalid content type"
    else:
        return "Content not found"
    
#@app.route('/playlist/<int:playlist_id>')
#def playlist_details(playlist_id):
    playlist = Playlist.query.get(playlist_id)
    if not playlist:
        # Handle the case where the playlist doesn't exist
        return "Playlist not found."

    # Fetch videos associated with the playlist
    videos = playlist.videos

    return render_template('playlist_details.html', playlist=playlist, videos=videos)    

@app.route('/Teachers/<username>')
def teacher_profile(username):
    teacher = Teachers.query.filter_by(username=username).first()
    if not teacher:
        return "Teacher not found"

    courses = Courses.query.filter_by(teacher_id=teacher.id).all()
    courses.reverse()
    return render_template('teacher_profile.html', teacher=teacher, courses=courses, username=username, )

@app.route('/Teachers/<username>/upload_video', methods=['GET', 'POST'])
def upload_video(username):
    teacher = Teachers.query.filter_by(username=username).first()
    teacher_playlists = teacher.playlists if teacher else []
    
    #teacher_playlists = teacher.courses
    print("Debug: ",teacher_playlists)
    if not teacher:
            return "Teacher not found"
    if request.method == 'POST':
        video_file = request.files.get('video') 
        title = request.form['title']
        description = request.form['description']
        tag = request.form['tag']
        playlist = request.form.get('playlist')
        
  
        
        if not playlist:
            playlist_text = None
        elif playlist == 'new':
            new_playlist_name = request.form.get('newPlaylist')
            if new_playlist_name:
                new_playlist = Playlist(name=new_playlist_name, teacher_id=teacher.id)
                db.session.add(new_playlist)
                db.session.commit()
                playlist_text = new_playlist.name
        else:
            playlist_text = playlist
                

        
        if video_file and videos.file_allowed(video_file, video_file.filename):
            filename = secure_filename(video_file.filename)
            filename = get_unique_filename(filename, app.config["UPLOAD_FOLDER"])
            video_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            # Save the video to the server
            video_file.save(video_path)
            #video_url = f"{app.config['UPLOADED_VIDEOS_URL']}{filename}"  # Get the URL for the video
            # Get the relative URL for the video within the /static/uploads/videos/ directory
            video_url = url_for('uploaded_videos', filename=filename, _external=True) 
            print('debug url: ',video_url)
            new_video = Courses(title=title, 
                                description=description,
                                video_url=video_url, 
                                tag=tag, 
                                teacher_id=teacher.id, 
                                teacher_name=teacher.username, 
                                playlist=playlist_text
                                )
            
            db.session.add(new_video)
            db.session.commit()
            return redirect(url_for('teacher_profile', username=teacher.username))
    tags = tag_list()
    return render_template('upload_video.html', tags=tags, username=username, teacher_playlists=teacher_playlists)

@app.route('/uploads/videos/<filename>')
def uploaded_videos(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    create_tables()
    app.run(debug=True, port=5000)

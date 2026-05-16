from flask import Flask, request, redirect, render_template, url_for, flash, session
from flask_jwt_extended import JWTManager, create_access_token
import os, requests, random
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
jwt = JWTManager(app)

app.secret_key="chupa_pijas"

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["MYSQL_USER"]= os.environ.get("user")
app.config["MYSQL_HOST"]= os.environ.get("host")
app.config["MYSQL_DB"] = os.environ.get("base_d")
app.config["MYSQL_PASSWORD"] = os.environ.get("password")
app.config["MYSQL_CURSORCLASS"]= "DictCursor"

conexion = MySQL(app)

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.errorhandler(404)
def error(error):
    return render_template('error.html'), 404

@app.route('/auth')
def auth():
    return render_template('auth.html')
    
    

@app.route("/register")
def do_register():
    if not session.get('token'):
        return render_template('register.html')
    
    return redirect(url_for('do_favorito'))
        
@app.route("/login")
def do_login():
    if not session.get('token'):
        return render_template('login.html')
    
    return redirect(url_for('do_favorito'))

@app.route("/favoritos")
def do_favorito():
    if not session.get('token'):
        return render_template('login.html')
    
    cursor = conexion.connection.cursor()
    query = "SELECT nombre, genero, imagen FROM favoritos WHERE user_id=%s"
    cursor.execute(query, (session['id'],))
    favo= cursor.fetchall()
    cursor.close()
    return render_template('favoritos.html', favoritos=favo)

@app.route("/logout")
def logout():
    if session:
        session.clear()
        return render_template("inicio.html")

@app.route('/register', methods=["POST"]) 
def register() :
    cursor = None
    
    try:
        cursor = conexion.connection.cursor()
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash("Rellena los campos")
            return redirect(url_for('do_register'))
        
        query = "SELECT email FROM users WHERE email=%s"
        cursor.execute(query,(email,))
        comprobar = cursor.fetchone()
        
        if comprobar:
            flash("Ya estas registrado")
            return redirect(url_for('do_register'))
        
        if email == "admin@admin.com":
            query = "INSERT INTO users(email, password, rol) VALUES(%s, %s, 'Admin')"
        else:
            query = "INSERT INTO users (email, password) VALUES(%s, %s)"
            
        password_hash = generate_password_hash(password)
        cursor.execute(query,(email, password_hash))
        conexion.connection.commit()
        
        query = "SELECT * FROM users WHERE email=%s"
        cursor.execute(query,(email,))
        usuario_completo = cursor.fetchone()
        
        if email != 'admin@admin.com':
            url = 'https://futuramaapi.com/api/characters'
            data = requests.get(url)
            datos = data.json()
            personajes = datos["items"]
            
            numeros = []
            lista_personajes = []
            
            while len(numeros) != 5:
                n = random.randint(0,49)
                if n not in numeros:
                    numeros.append(n)
            
            for i in numeros:
                lista_personajes.append(personajes[i])
                
            query = "INSERT INTO favoritos(user_id, nombre, genero, imagen) VALUES(%s, %s, %s, %s)"
            
            for p in lista_personajes:
                cursor.execute(query, (usuario_completo['id'], p['name'], p['gender'], p['image']))
                
            conexion.connection.commit()
        
        
        token = create_access_token(identity=email)
        session['id'] = usuario_completo['id']
        session['rol'] = usuario_completo['rol']
        session['token'] = token
        
        return redirect(url_for('do_favorito'))
    
    except Exception as e:
        flash(str(e))
        return redirect(url_for("do_register"))

    finally:
        if cursor:
            cursor.close()

@app.route("/login", methods=["POST"])    
def login():
    cursor = None
    
    try:
        cursor = conexion.connection.cursor()  
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash("Rellena los campos")
            return redirect(url_for('do_login'))    
        
        query = "SELECT * FROM users WHERE email=%s"
        cursor.execute(query,(email,))
        resultado = cursor.fetchone()
        
        if not resultado:
            flash("No estar registrado, puta")
            return redirect(url_for("do_register"))
        
        comprobar = check_password_hash(resultado["password"], password)
        
        if not comprobar:
            flash("error en la contraseña")
            return redirect(url_for("do_login"))
        
        else:
            token = create_access_token(identity=email)
            session['id'] = resultado['id']
            session['rol'] = resultado['rol']
            session['token'] = token
            
            flash('Login correcto')
            return redirect(url_for('do_favorito'))
        
    except Exception as e:
        flash(str(e))
        return redirect(url_for("do_login"))

    finally:
        if cursor:
            cursor.close()
            
            
if __name__ == "__main__":
    app.run(debug=True)
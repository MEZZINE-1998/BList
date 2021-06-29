import os
from flask import Flask,request, url_for, redirect, render_template, jsonify, session, flash, send_file
import pandas as pd
from werkzeug.utils import secure_filename
from IPython.display import HTML






 
#  --------------------------------------- configurations :

app = Flask(__name__)

app.secret_key = "abdellatif"

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

path = os.getcwd()

try:
    user_df = pd.read_csv(path+'/static/users.csv')
except:
    user_df = pd.DataFrame(columns = ['name', 'email', 'password'])  
    user_df.to_csv(path+'/static/users.csv', index=False ,header=True)


ALLOWED_EXTENSIONS = set(['csv', 'xls', 'xlsx', 'ets'])





# ---------------------------------------- simple methods :

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def getHistorique():
    try:
        df = pd.read_csv(path+'/static/download/actions_'+str(session['network'])+'.csv', dtype=str)
    except:
        df = pd.DataFrame(columns = ['NCLI', 'status', 'created_at']) 
    return df



def make_action_meth(file, action):

    # this_month = pd.to_datetime("today").month
    # this_year = pd.to_datetime("today").year

    hist = getHistorique()

    # make dataframe based on file extension ...
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    if file_extension == "csv":
        df_action = pd.read_csv(file, usecols=[0])
    elif file_extension == "ets":
        df_action = pd.read_csv(file, usecols=[0], sep=" ", dtype=str)
    elif file_extension == "xls" or file_extension == "xlsx":
        df_action = pd.read_excel(file, usecols=[0])

    df_action = df_action.rename(lambda x: 'NCLI', axis=1) 

    df_action['status'] = action
    df_action['created_at'] = pd.to_datetime("today")

    df_appended = hist.append(df_action, sort=False)

    # here we need to makes update inside our CSV file ....
    df_appended.to_csv(path+'/static/download/actions_'+str(session['network'])+'.csv', index=False, header=True)


def get_customers_by_NCLI(NCLI):
    df_cust = pd.read_csv(path+'/static/all_customers.csv')
    return  df_cust.loc[(df_cust['NCLI'] == NCLI)]







# ------------------------------------------ applying methods for user:


@app.route("/")
def home():
    if session.get("auth"):
        return redirect("/login")
    return render_template("home.html")



@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "GET":
        if session.get("auth"):
            return render_template('main.html')
        else:
            return render_template('home.html', message = "you are note authenticated")

    if request.method == "POST":
        email = request.form['email']
        pwd = request.form['pwd']
        if email and pwd:
            try:
                user = user_df.loc[(user_df['email'] == str(email)) & (user_df['password'] == str(pwd))].values
                if len(user) != 0:
                    session['email'] = str(email)
                    session['password'] = str(pwd)
                    session['name'] = user[0][0]
                    session['auth'] = True
                    session['network'] = 'mobile'
                    return render_template('main.html')
                else:
                    message = 'Incorrect username/password!'
            except Exception as exception:
                message = str(exception)
    return render_template('home.html', message= message)



@app.route('/settings', methods=["GET"])
def settings():
    return render_template('setting.html', user=session)



@app.route('/updateProfile', methods=["POST"])
def updateProfile():

    global user_df

    email = request.form['email']
    oldPassword = request.form['oldPassword']
    password = request.form['password']
    passwordConfirm = request.form['passwordConfirm']

    if str(oldPassword) != str(session['password']):
        message = "your old password is incorrect"
        return render_template('setting.html', message= message)
    
    if str(password) != str(passwordConfirm):
        message = "password and password-conform not matched"
        return render_template('setting.html', message= message)

    user_df.loc[(user_df['email'] == session['email']), 'email'] = email
    user_df.loc[(user_df['email'] == session['email']), 'password'] = password

    session['email'] = str(email)
    session['password'] = str(password)

    user_df.to_csv(path+'/static/users.csv', index=False)

    return redirect('/login')
    



@app.route('/logout', methods=["GET"])
def logout():
    session['auth'] = False
    session.clear()
    return render_template('home.html')






# ------------------------------------------- applying methods for files 

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        action = request.form['action']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            make_action_meth(file, action)
            return render_template('main.html', value = "Action maked successfully")
        else:
            return render_template('main.html', value = "Allowed file types are csv, xls and xlsx")




@app.route('/reviewandexportbl', methods=["POST", "GET"])
def reviewandexportbl():

    if request.method == 'POST':

        date = request.form['date']
        action = request.form['action']

        if date and action:

            # df = pd.read_csv(path+'/static/download/actions_'+str(session['network'])+'.csv', dtype=str)
            date = pd.to_datetime(date)
            month = date.month
            year = date.year

            if action == "review":
                try:
                    df = pd.read_csv(path+'/static/download/blist_'+str(session['network'])+'_'+str(month)+'_'+str(year)+'.csv', as_attachment=True)
                except:
                    df = pd.read_csv(path+'/static/download/actions_'+str(session['network'])+'.csv', dtype=str)
                    df = df[pd.to_datetime(df['created_at']) < date]
                    df = df.drop_duplicates(subset=['NCLI'], keep='last')
                    df = df[df['status'] == "added"]
                    # df = get_customers_by_NCLI(df['NCLI'])
                    return render_template('main.html', blackList=HTML(df.to_html(classes='table')))

            else:
                try:
                    send_file(path+'/static/download/blist_'+str(session['network'])+'_'+str(month)+'_'+str(year)+'.csv', as_attachment=True)
                except:
                    df = pd.read_csv(path+'/static/download/actions_'+str(session['network'])+'.csv', dtype=str)
                    df = df[pd.to_datetime(df['created_at']) < date]
                    df = df.drop_duplicates(subset=['NCLI'], keep='last')
                    df = df[df['status'] == "added"]
                    # df = get_customers_by_NCLI(df['NCLI'])
                    df.to_csv(path+'/static/download/blist_'+str(session['network'])+'_'+str(month)+'_'+str(year)+'.csv', index=False, header=True)
                    return send_file(path+'/static/download/blist_'+str(session['network'])+'_'+str(month)+'_'+str(year)+'.csv', as_attachment=True)
                
    return redirect('/login')
    
    


@app.route('/netMobile', methods=['GET'])
def netMobile():
    session['network'] = "mobile"
    return redirect('/login')


@app.route('/netFixe', methods=['GET'])
def netFixe():
    session['network'] = "fixe"
    return redirect('/login')








# @app.route('/seeBlackList', methods=['GET'])
# def seeBlackList():
#     df = getHistorique()[0:15]
#     df = df.drop_duplicates(subset=['NCLI'], keep='last')
#     df = df[df['status'] == "added"]
    
#     # df = get_customers_by_NCLI(df['NCLI'])
#     return render_template('main.html', blackList=HTML(df.to_html(classes='table')))



# @app.route('/exportcsv', methods=['GET'])
# def exportcsv():
#     this_month = pd.to_datetime("today").month
#     this_year = pd.to_datetime("today").year

#     df = getHistorique(this_year, this_month)
#     df = df[df['status'] == "added"]
#     df = df.drop_duplicates(subset=['NCLI'], keep='last')
#     # df = get_customers_by_NCLI(df['NCLI'])
#     df.to_csv(path+'/static/download/BList_'+str(session['network'])+'.csv', index=False, header=True)

#     return send_file(path+'/static/download/BList_'+str(session['network'])+'.csv', as_attachment=True)


# @app.route('/exporthistcsv', methods=['GET'])
# def exporthistcsv():
#     this_month = pd.to_datetime("today").month
#     this_year = pd.to_datetime("today").year
    
#     return send_file(path+'/static/download/actions_'+str(session['network'])+'.csv', as_attachment=True)



# @app.route('/historique', methods=['GET'])
# def historique():
#     files = []
#     for file in os.listdir(path+'/static/download/'):
#         if file.lower().endswith(".csv"):
#             files.append(file)
#     return render_template('historique.html', files = files)








      
if __name__ == "__main__":
    app.run(host="0.0.0.0", port="8080")

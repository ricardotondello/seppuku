from logging.handlers import RotatingFileHandler
from flask import Flask, flash, redirect, render_template, request, session, abort
import json
import subprocess
import os
import os.path
import routes.gestor_dump_file
from routes import *
import sys
from pathlib import Path
import logging
import webbrowser
from time import strftime

app = Flask(__name__)
app.register_blueprint(routes)

@app.after_request
def after_request(response):
    """ Logging after every request. """
    # This avoids the duplication of registry in the log,
    # since that 500 is already logged via @app.errorhandler.
    if response.status_code != 500:
        ts = strftime('[%Y-%b-%d %H:%M]')
        logger.error('%s %s %s %s %s %s',
                      ts,
                      request.remote_addr,
                      request.method,
                      request.scheme,
                      request.full_path,
                      response.status)
    return response

@app.errorhandler(Exception)
def exceptions(e):
    """ Logging after every Exception. """
    ts = strftime('[%Y-%b-%d %H:%M]')
    tb = traceback.format_exc()
    logger.error('%s %s %s %s %s 5xx INTERNAL SERVER ERROR\n%s',
                  ts,
                  request.remote_addr,
                  request.method,
                  request.scheme,
                  request.full_path,
                  tb)
    return "Internal Server Error", 500

@app.route('/')
def home():
    if not session.get('initialized'):
        inicializar()

    ler_argumentos()
    return render_template('main.html')

@app.route('/getconfig', methods = ["POST"])
def get_config():

    compare_tool_full_path = request.form.get('compare_tool_full_path')
    source_monitor_full_path = request.form.get('source_monitor_full_path')

    if compare_tool_full_path:
        session['compare_tool_path'] = compare_tool_full_path
    if source_monitor_full_path:
        session['source_monitor_path'] = source_monitor_full_path
        
    data = {"compare_tool_path" : session.get('compare_tool_path'),
            "source_monitor_path" : session.get('source_monitor_path')}
    
    with open(session.get('settings_path'), 'w') as f:
        json.dump(data, f)
 
    return redirect('/')

@app.route('/open_compare_tool')
def open_compare_tool():
    validar_compare_tool()
    return redirect('/')

@app.route('/open_compare_tool_no_redirect')
def open_compare_tool_no_redirect():
    validar_compare_tool()
    return redirect('/report')

def validar_compare_tool():
    if gestor_dump_file.validar():
        subprocess.Popen(session.get('compare_tool_path') + " " + session.get('file_old') + " " + session.get('file_new'))
        
def load_config():
    path = Path().absolute()
    session['settings_path'] = str(path) + '\\settings.json'

    if not validar_file(session.get('settings_path')):
        return
    
    config                         = json.load(open( session.get('settings_path')))
    session['compare_tool_path']   = config["compare_tool_path"]
    session['source_monitor_path'] = config["source_monitor_path"]
    session['has_config']          = validar_file(session.get('compare_tool_path')) and validar_file(session.get('source_monitor_path'))

def validar_file(ps_file):
    if not ps_file:
        return False
    return (os.path.isfile(ps_file) and os.access(ps_file, os.R_OK))
        
def ler_argumentos():
    file_old = request.args.get('file_old')
    file_new = request.args.get('file_new')
    
    if not file_old or not file_new:
        return
    
    session['valid_files'] = (validar_file(file_old) and validar_file(file_new))
    session['file_new']    = file_new
    session['file_old']    = file_old
    
def inicializar():   
    sARQUIVO_NAO_LOCALIZADO = 'Arquivo não localizado!'
    session['initialized'] = True
    session['valid_files'] = False
    session['has_config']  = False
    session['file_new']    = sARQUIVO_NAO_LOCALIZADO
    session['file_old']    = sARQUIVO_NAO_LOCALIZADO
    
    load_config()

##Parte client - deve ser refatorado futuramente
if (len(sys.argv) == 3):
    path_tmp_tfs = 'TFSTemp'
    file_old_temp = sys.argv[1] + '_temp'
    file_new_temp = sys.argv[2]
    
    if path_tmp_tfs in file_new_temp:
        file_new_temp = sys.argv[2] + '_temp'
        os.popen('copy "' + sys.argv[2] + '" "' + file_new_temp + '"')
        
    url = "http://127.0.0.1:5000?file_old={file_old}&file_new={file_new}".format(file_old=file_old_temp, file_new=file_new_temp)

    os.popen('copy "' + sys.argv[1] + '" "' + file_old_temp + '"')
    logging.info(url)
    webbrowser.open_new_tab(url)

if ((len(sys.argv) == 1) and (__name__ == "__main__")):
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    logger.addHandler(handler)
    
    app.secret_key = os.urandom(12)
    app.run(host='127.0.0.1', port=5000)
    
   


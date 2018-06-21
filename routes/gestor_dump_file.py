import xmltodict
from flask import render_template, session, flash, redirect
from . import routes
import os
import os.path
import subprocess

metodos_new = []
metodos_old = []
metodos_geral_alterado = []
metodos_geral_nao_alterado = []
SEPARADOR = ' | '
metodos_totalizador = []

path_compare        = ''
path_command_export = ''
path_dump_file      = ''
path_project_file   = ''
path_file_old       = ''
path_file_new       = ''

class arquivo:
    kind = 'Checkpoint File'
    
    def __init__(self):
        self.method_name  = ''
        self.complexity   = ''
        self.statements   = ''
        self.depth        = ''
        self.nivel        = 0
        self.termometro   = ''
        self.hash         = ''


@routes.route('/report')
def report():
    
    if not validar():
        return redirect('/')
    
    metodos_geral_alterado_tmp, metodos_geral_nao_alterado_tmp, metodos_totalizador_tmp = get_report()
    
    return render_template('report.html',
                           metodos_geral_alterado = metodos_geral_alterado_tmp,
                           metodos_geral_nao_alterado = metodos_geral_nao_alterado_tmp,
                           metodos_totalizador = metodos_totalizador_tmp)

def get_report():
    gerar_dump()
    MostrarResultado(path_dump_file)    
    metodoordenado = sorted(metodos_geral_alterado, key=lambda arquivo: arquivo.nivel, reverse=True)
    
    metodos_geral_nao_alterado_sorted = sorted(metodos_geral_nao_alterado, key=lambda arquivo: arquivo.complexity, reverse=True)
    return metodoordenado, metodos_geral_nao_alterado_sorted, metodos_totalizador

def validar():

    if not session.get('has_config'):
        flash("Configuração não localizada!")
        return False
    if not session.get('valid_files'):
        flash("Não foi possível acessar os arquivos!")
        return False
    return True

def criar_estrutura_pastas():
    dir_compare = '\\Compare\\'
    global path_compare
    global path_command_export
    global path_dump_file
    global path_project_file
    global path_file_old
    global path_file_new

    head, tail = os.path.split(session.get('source_monitor_path'))
    path_compare =  head + dir_compare
    
    if not os.path.exists(path_compare):
        os.makedirs(path_compare)
      
    path_command_export = path_compare + 'CommandExportData.xml'
    path_dump_file      = path_compare + 'dump.xml'
    path_project_file   = path_compare + 'MyProject.smproj'
    path_file_old       = path_compare + 'FileOld.pas'
    path_file_new       = path_compare + 'FileNew.pas'
    
def criar_arquivo_command():

    if os.path.isfile(path_command_export):
        os.remove(path_command_export)
        
    arq = open(path_command_export, 'w')
    texto = """<?xml version="1.0" encoding="UTF-8" ?>
<sourcemonitor_commands>
<command>
  <project_file>{path_project_file}</project_file>
  <project_language>Delphi</project_language>
  <modified_complexity>true</modified_complexity>
  <ignore_headers_footers>3 Ignore both ordinary and DOC comments</ignore_headers_footers>
  <source_directory>{path_compare}</source_directory>
  <parse_utf8_files>True</parse_utf8_files>
 <export>
    <export_type>1 (Export project summary in XML format.)</export_type>
    <export_type>5 (Export method metrics in XML format)</export_type>
    <export_option>4 Export metrics totals in a line at the end of each checkpoint</export_option>
    <export_insert>xml-stylesheet type=''text/xsl'' href=''SourceMonitor.xslt''</export_insert>
    <export_file>{path_dump_file}</export_file>
 </export>
 </command>
</sourcemonitor_commands>"""
    arq.write(texto.replace('{path_compare}', path_compare).replace('{path_dump_file}',path_dump_file).replace('{path_project_file}',path_project_file))
    arq.close()    

    

def deletar_arquivos_temporarios():
    if os.path.isfile(path_project_file):
        os.remove(path_project_file)
        
    if os.path.isfile(path_dump_file):
        os.remove(path_dump_file)
        
    if os.path.isfile(path_file_old):
        os.remove(path_file_old)
        
    if os.path.isfile(path_file_new):
        os.remove(path_file_new)

def copiar_arquivos_para_raiz():
    os.popen('copy "' + session.get('file_old') + '" "' + path_file_old + '"')
    os.popen('copy "' + session.get('file_new') + '" "' + path_file_new + '"')
    
def executar_estatistica():
    some_command = session.get('source_monitor_path') + " /C " + path_command_export

    p = subprocess.Popen(some_command, stdout=subprocess.PIPE, shell=True)

    (output, err) = p.communicate()  

    #This makes the wait possible
    p_status = p.wait()

def gerar_dump():
    criar_estrutura_pastas()
    criar_arquivo_command()
    deletar_arquivos_temporarios()
    copiar_arquivos_para_raiz()
    executar_estatistica()
    
def MostrarResultado(sDumpFile):
    loadXmlDump(sDumpFile)

def loadXmlDump(sDumpFile):
    global metodos_new
    global metodos_old
    
    metodos_new.clear()
    metodos_old.clear()
    metodos_geral_alterado.clear()
    metodos_geral_nao_alterado.clear()

    if not os.path.isfile(sDumpFile):
        return
    
    with open(sDumpFile) as fd:
        doc = xmltodict.parse(fd.read())

    for arq in doc['sourcemonitor_metrics']['project']['checkpoints']['checkpoint']['files']['file']:
        
        file_name = arq['@file_name']
                
        for method in arq['method']:
            method_name = method['@name']
            complexity  = method['complexity']
            statements  = method['statements']
            depth       = method['maximum_depth']
            
            auxarquivo = arquivo()
            auxarquivo.method_name = method_name
            auxarquivo.complexity  = complexity
            auxarquivo.statements  = statements
            auxarquivo.depth       = depth
                        
            if file_name == "FileNew.pas":
                metodos_new.append(auxarquivo)
            else:
                metodos_old.append(auxarquivo)
                
    MontarDiferencas()

def retorna_metodo_correspondente(method_to_find, method_name):
    for m_temp in method_to_find:
        if m_temp.method_name == method_name:
            return m_temp
        
    ##se for funcao adicionada
    tmp_method = arquivo()
    tmp_method.method_name = method_name
    tmp_method.complexity  = '0'
    tmp_method.statements  = '0'
    tmp_method.depth       = '0'
    tmp_method.hash        = 'NL'
            
    return tmp_method

def CalcularNivelETermometro(complexity_old, complexity_new, statements_old, statements_new, depth_old, depth_new):
    nivel_complexity = int(complexity_old) - int(complexity_new)
    nivel_statements = int(statements_old) - int(statements_new)
    nivel_depth      = int(depth_old)      - int(depth_new)

    termometro = ''
    nivel      = 0
    
    if (nivel_complexity < 0 or nivel_statements < 0 or nivel_depth < 0):
        termometro = 'danger'
        nivel = 3
    if (termometro == 'danger') and (nivel_complexity > 0 or nivel_statements > 0 or nivel_depth > 0):
        termometro = 'warning'
        nivel = 2
    if (termometro == '') and (nivel_complexity > 0 or nivel_statements > 0 or nivel_depth > 0):
        termometro = 'success'
        nivel = 1
    return termometro, nivel  
    
def MontarDiferencas():
    old_complexity = 0
    old_statements = 0
    old_depth      = 0
    
    new_complexity = 0
    new_statements = 0
    new_depth      = 0
    
    for mold in metodos_old:
        aux_new = retorna_metodo_correspondente(metodos_new, mold.method_name)

        ##armazena o totalizador
        old_complexity += int(mold.complexity)
        old_statements += int(mold.statements)
        old_depth      += int(mold.depth)
        
        new_complexity += int(aux_new.complexity)
        new_statements += int(aux_new.statements)
        new_depth      += int(aux_new.depth)

        aux = arquivo()
        aux.method_name = mold.method_name
        aux.complexity  = mold.complexity + SEPARADOR + aux_new.complexity
        aux.statements  = mold.statements + SEPARADOR + aux_new.statements
        aux.depth       = mold.depth      + SEPARADOR + aux_new.depth
        
        aux.termometro, aux.nivel = CalcularNivelETermometro(mold.complexity, aux_new.complexity, mold.statements, aux_new.statements, mold.depth, aux_new.depth)

        ##joga para uma lista unica
        if aux.nivel == 0:
            metodos_geral_nao_alterado.append(aux)
        else:
            metodos_geral_alterado.append(aux)

    ##métodos adicionados
    for mnew in metodos_new:
        aux_new.hash = ''
        aux_new = retorna_metodo_correspondente(metodos_old, mnew.method_name)
        
        if aux_new.hash == 'NL':
            aux = arquivo()
            aux.method_name = mnew.method_name
            aux.complexity  = '0' + SEPARADOR + mnew.complexity
            aux.statements  = '0' + SEPARADOR + mnew.statements
            aux.depth       = '0' + SEPARADOR + mnew.depth
            aux.termometro  = 'info'
            aux.nivel       = 4
            metodos_geral_alterado.append(aux)
            
            new_complexity += int(mnew.complexity)
            new_statements += int(mnew.statements)
            new_depth      += int(mnew.depth)
            
    
    ##Totalizador
    aux = arquivo()
    aux.method_name = 'Totalizador'
    aux.complexity  = str(old_complexity) + SEPARADOR + str(new_complexity)
    aux.statements  = str(old_statements) + SEPARADOR + str(new_statements)
    aux.depth       = str(old_depth)      + SEPARADOR + str(new_depth)
    aux.termometro, aux.nivel = CalcularNivelETermometro(old_complexity, new_complexity, old_statements, new_statements, old_depth, new_depth)

    metodos_totalizador.clear()
    metodos_totalizador.append(aux) 

##@routes.route('/report2')
##def testar_dump():
##    path = "C:\Seppuku\compare\dump.xml"
##    loadXmlDump(path)    
##    metodoordenado = sorted(metodos_geral_alterado, key=lambda arquivo: arquivo.nivel, reverse=True)
##    return render_template('report.html', metodos_geral_alterado=metodoordenado, metodos_geral_nao_alterado=metodos_geral_nao_alterado, metodos_totalizador=metodos_totalizador)


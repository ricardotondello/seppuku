# seppuku
Ferramenta para análise de métricas de projetos Delphi (Complexidade ciclomatica).

## Requirements

  * Python 3.5.x
  * PyInstaller 3.3.1
  * Flask 0.12.2
  * XmlToDict 0.11.0
  * PyPiWin32 219
  * [Source Monitor 3.5](http://www.campwoodsw.com/sourcemonitor.html)

## Build 1

    (env)$ setup/compilar.bat
    - Transforma Python files em um único .exe
    - Gera um setup de instalação
   
## Build 2
    - Execute seppuku.py pelo prompt.
    - Utilize passando 2 argumentos (seppuku.py c:\temp\fileOld.pas c:\temp\fileNew.pas)
    - Automáticamente abrirá o browser mostrando as métricas comparando os arquivos.
    

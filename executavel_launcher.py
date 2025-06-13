import sys
import os
import subprocess
import webbrowser
import time
import threading
import socket
import psutil

def get_free_port(start_port=8501):
    """Encontra uma porta livre a partir da porta inicial"""
    port = start_port
    while port < start_port + 10:  # Testa até 10 portas
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            port += 1
    raise Exception("Nenhuma porta disponível encontrada")

def is_streamlit_running(port):
    """Verifica se já existe um processo Streamlit rodando na porta"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', port))
            return result == 0
    except:
        return False

def kill_streamlit_processes():
    """Mata processos Streamlit existentes para evitar conflitos"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'streamlit' in ' '.join(proc.info['cmdline']).lower():
                proc.kill()
                time.sleep(1)
    except:
        pass

def open_browser(port):
    """Abre o navegador após delay"""
    time.sleep(5)  # Aguarda mais tempo
    if not is_streamlit_running(port):
        return
    webbrowser.open(f'http://localhost:{port}')

if __name__ == "__main__":
    print("🔄 Iniciando Localizador de Desenhos...")
    
    # Mata processos Streamlit existentes
    kill_streamlit_processes()
    
    # Localiza o script no executável
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    script_path = os.path.join(base_path, "Legacy_Searcher.py")
    
    if not os.path.exists(script_path):
        print(f"❌ Script não encontrado: {script_path}")
        input("Pressione Enter para sair...")
        sys.exit(1)

    # Encontra porta livre
    try:
        port = get_free_port(8501)
        print(f"🌐 Usando porta: {port}")
    except Exception as e:
        print(f"❌ Erro ao encontrar porta: {e}")
        input("Pressione Enter para sair...")
        sys.exit(1)

    # Verifica se já não está rodando
    if is_streamlit_running(port):
        print(f"⚠️ Streamlit já rodando na porta {port}, abrindo navegador...")
        webbrowser.open(f'http://localhost:{port}')
        input("Pressione Enter para sair...")
        sys.exit(0)

    # Abre browser automaticamente
    browser_thread = threading.Thread(target=open_browser, args=(port,), daemon=True)
    browser_thread.start()
    
    try:
        # Configurações mais restritivas para evitar loops
        env = os.environ.copy()
        env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        env['STREAMLIT_SERVER_HEADLESS'] = 'true'
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", script_path,
            f"--server.port={port}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false",
            "--browser.serverAddress=localhost"
        ], env=env)
    except KeyboardInterrupt:
        print("\n🛑 Aplicação encerrada pelo usuário")
    except Exception as e:
        print(f"❌ Erro: {e}")
        input("Pressione Enter para sair...")
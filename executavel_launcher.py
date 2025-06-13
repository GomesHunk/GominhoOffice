import sys
import os
import subprocess
import webbrowser
import time
import threading
import socket

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

def open_browser(port):
    time.sleep(4)  # Aguarda mais tempo para garantir que o Streamlit iniciou
    webbrowser.open(f'http://localhost:{port}')

if __name__ == "__main__":
    print("🔄 Iniciando Localizador de Desenhos...")
    
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

    # Abre browser automaticamente
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", script_path,
            f"--server.port={port}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--server.enableCORS=false"
        ])
    except Exception as e:
        print(f"❌ Erro: {e}")
        input("Pressione Enter para sair...")

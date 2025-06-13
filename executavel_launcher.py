import sys
import os
import subprocess

if __name__ == "__main__":
    print("🔄 Iniciando o Localizador de Desenhos Técnicos Legacy...")
    print("⏳ Aguarde... A primeira execução pode demorar alguns segundos.")
    print("⚠️ Por favor, não feche esta janela enquanto estiver utilizando o programa.")
    print("✅ Quando quiser encerrar o uso, basta fechar esta janela.\n")

    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_path, "Legacy_Searcher.py")

    print(f"📁 Verificando script: {script_path}")
    if not os.path.exists(script_path):
        print(f"❌ Erro: Script não encontrado em {script_path}")
        sys.exit(1)

    # Executa o script Streamlit como subprocesso
    subprocess.run([
        sys.executable,
        "-m", "streamlit",
        "run", script_path,
        "--server.port=8501"
    ])

import json
import os
import socket
import subprocess
import pyautogui
import sys

HOST = "0.0.0.0"
PORT = 5555

# --- LÓGICA DE DIRETÓRIO PARA DISTRIBUIÇÃO (PORTABLE) ---
if getattr(sys, 'frozen', False):
    # Se estiver rodando como .exe (congelado pelo PyInstaller)
    # O BASE_DIR será a pasta onde o .exe está localizado
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Se estiver rodando como script .py normal
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
# -------------------------------------------------------

STATE = {"current_page": 1, "pages": {}}

def load_config():
    global STATE
    print(f"Buscando configuracoes em: {CONFIG_PATH}")
    
    if not os.path.exists(CONFIG_PATH):
        print(f"AVISO: config.json nao encontrado em: {CONFIG_PATH}")
        print("Certifique-se de que o Configurator gerou o arquivo na mesma pasta deste executavel.")
        return
    
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            STATE = json.load(f)
        print("Configuracoes carregadas com sucesso!")
    except Exception as e:
        print(f"Erro critico ao ler o arquivo JSON: {e}")

def run_action(page, button_id):
    try:
        # Busca os dados da página e do botão no dicionário STATE
        page_data = STATE.get("pages", {}).get(f"p{page}", {})
        action = page_data.get(f"b{button_id}")
        
        if not action:
            print(f"Nenhuma acao definida para Pagina {page}, Botao {button_id}")
            return

        at_type = action.get("type")
        print(f"Executando: {at_type} (Pag: {page}, Botao: {button_id})")

        if at_type == "open_app":
            # os.path.normpath garante que caminhos do Windows funcionem independente das barras
            app_path = os.path.normpath(action["path"])
            if os.path.exists(app_path):
                os.startfile(app_path)
            else:
                print(f"Erro: Aplicativo nao encontrado em: {app_path}")
                
        elif at_type == "open_url":
            # Abre o navegador padrão no Windows
            subprocess.Popen(["cmd", "/c", "start", "", action["url"]])
            
        elif at_type == "hotkey":
            # Executa a combinação de teclas (ex: CTRL+C)
            pyautogui.hotkey(*[k.lower() for k in action["keys"]])
            
    except Exception as e:
        print(f"Erro ao executar acao: {e}")

def serve():
    load_config()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # SO_REUSEADDR permite reiniciar o servidor imediatamente sem erro de 'porta ocupada'
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((HOST, PORT))
        except Exception as e:
            print(f"Erro ao iniciar servidor na porta {PORT}: {e}")
            return

        s.listen(1)
        print(f"======================================================")
        print(f"SERVIDOR ATIVO (Ouvindo em {HOST}:{PORT})")
        print(f"Seu IP Local atual e: {socket.gethostbyname(socket.gethostname())}")
        print(f"======================================================")
        
        while True:
            conn, addr = s.accept()
            print(f"Switch conectado por: {addr}")
            try:
                with conn:
                    # Lê as mensagens enviadas pelo Nintendo Switch
                    f = conn.makefile("r", encoding="utf-8")
                    for line in f:
                        if "BTN_PRESS" in line:
                            parts = line.split()
                            if len(parts) == 3:
                                run_action(parts[1], parts[2])
            except Exception as e:
                print(f"Conexao com o Switch perdida ou erro: {e}")

if __name__ == "__main__":
    try:
        serve()
    except KeyboardInterrupt:
        print("\nServidor encerrado pelo usuário.")
    except Exception as e:
        print(f"CRASH NO SERVIDOR: {e}")
        input("Pressione Enter para fechar...")
import json
import os
import socket
import subprocess
import pyautogui
import sys

HOST = "0.0.0.0"
PORT = 5555
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

STATE = {"current_page": 1, "pages": {}}

def load_config():
    global STATE
    if not os.path.exists(CONFIG_PATH):
        print(f"ERRO: config.json não encontrado em: {CONFIG_PATH}")
        return
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        STATE = json.load(f)
    print("Configurações carregadas com sucesso!")

def run_action(page, button_id):
    try:
        # Lê a página com o novo prefixo 'p' e o botão com 'b'
        page_data = STATE.get("pages", {}).get(f"p{page}", {})
        action = page_data.get(f"b{button_id}")
        
        if not action:
            print(f"Nenhuma ação definida para Página {page}, Botão {button_id}")
            return

        at_type = action.get("type")
        print(f"Executando: {at_type} (Pág: {page}, Botão: {button_id})")

        if at_type == "open_app":
            os.startfile(action["path"])
        elif at_type == "open_url":
            subprocess.Popen(["cmd", "/c", "start", "", action["url"]])
        elif at_type == "hotkey":
            pyautogui.hotkey(*[k.lower() for k in action["keys"]])
    except Exception as e:
        print(f"Erro ao executar ação: {e}")

def serve():
    load_config()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        print(f"SERVIDOR ATIVO (Ouvindo em 0.0.0.0:{PORT})")
        print(f"Seu IP Local atual é: {socket.gethostbyname(socket.gethostname())}")
        
        while True:
            conn, addr = s.accept()
            print(f"Switch conectado por: {addr}")
            with conn:
                f = conn.makefile("r", encoding="utf-8")
                for line in f:
                    if "BTN_PRESS" in line:
                        parts = line.split()
                        if len(parts) == 3:
                            run_action(parts[1], parts[2])

if __name__ == "__main__":
    try:
        serve()
    except Exception as e:
        print(f"CRASH NO SERVIDOR: {e}")
        input("Pressione Enter para fechar...")
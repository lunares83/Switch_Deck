🎮 Switch Deck

English
💡 The Concept

Switch Deck turns your Nintendo Switch into a wireless "Stream Deck" for your computer. Using the console's touchscreen, you can launch apps, execute hotkeys, or open URLs on your PC over your local Wi-Fi network.

The project consists of three main components:

NRO (Switch): The visual frontend that sends commands via TCP.

Configurator (PC): A Python GUI tool to map buttons, icons, and pages.

Receiver (PC): A lightweight background server that listens for Switch commands and executes actions on Windows.

🚀 How to Use

On your Computer:

Install requirements: pip install PySide6 pyautogui.

Run configurator.py to set up your PC IP, button actions, and icons.

Click "SAVE TO SWITCH" and select your app's folder on the SD Card.

Launch receiver.py to start listening for commands.

On your Switch:

Ensure both Switch and PC are on the same Wi-Fi network.

Open the app via the Homebrew Menu.

If the background is green, you are connected! If it's red, double-check the IP in config.json.

The video below shows a step-by-step tutorial of the app in action; only the subtitles are currently in English.:
https://www.youtube.com/watch?v=F54bT5_ek4Y

-------------------------------------------------------------------------------------------------------------------------------------------------------

Português
💡 O Conceito

O Switch Deck transforma seu Nintendo Switch em um "Stream Deck" sem fio para o seu computador. Através de uma interface por toque no console, você pode abrir aplicativos, executar atalhos de teclado (hotkeys) ou abrir URLs no seu PC via rede Wi-Fi local.

O projeto é dividido em três partes:

NRO (Switch): A interface visual que envia comandos via TCP.

Configurator (PC): Uma ferramenta gráfica em Python para mapear botões, ícones e páginas.

Receiver (PC): Um servidor leve que escuta o Switch e executa as ações no Windows.

🚀 Como Usar

No Computador:

Instale as dependências: pip install PySide6 pyautogui.

Execute o configurator.py para definir seu IP, botões e ícones.

Clique em "SAVE TO SWITCH" e selecione a pasta onde o app está no seu Cartão SD.

Inicie o receiver.py para que ele fique aguardando os comandos.

No Switch:

Certifique-se de que o Switch e o PC estão na mesma rede Wi-Fi.

Abra o app via Homebrew Menu.

Se o fundo estiver verde, você está conectado! Se estiver vermelho, verifique o IP no config.json.

O video abaixo mostra um passo a passo do app funiconando.:
https://www.youtube.com/watch?v=F54bT5_ek4Y


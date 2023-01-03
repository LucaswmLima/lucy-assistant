import psycopg2
import regex as re
import os
import requests
from playsound import playsound
from gtts import gTTS
import random
import speech_recognition as sr
import datetime
import json
import unicodedata
from bs4 import BeautifulSoup
from threading import Thread
from tkinter import *
import num2words
import pathlib
import psutil

# Usado para fechar o programa
current_system_pid = os.getpid()
ThisSystem = psutil.Process(current_system_pid)
# Usado para encontrar o desktop
desktop = pathlib.Path.home() / 'Desktop'

# Variaveis Globais
global nome, link
activationFunction = 0
start = 0
inputedSlot = ''
inputedItemName = ''
inputedItemQuantity = ''
inputedItemMinQuantity = ''

# Conecta ao banco de dados
conn = psycopg2.connect(dbname="db_lucy", user="postgres",
                        password="admin", host="localhost")
print('Conexão com o banco de dados bem sucedida!')
cur = conn.cursor()

# Dados do usuario
with open("user_data.json") as jsonFile:
    dados = json.load(jsonFile)
nick = dados['name']
idade = dados['age']
local = dados['local']

# Função de fala
def fala(text):
    global file1
    tts = gTTS(text, lang='pt')
    file1 = str("lucy_audio.mp3")
    tts.save(file1)
    playsound(file1, True)
    os.remove(file1)

# Função para normalizar textos
def normalize_text(text):
    normalizedText = unicodedata.normalize('NFD', text)
    return re.sub(r'[\u0300-\u036f]', '', normalizedText).casefold()

# Função para converter numeros em letras para numeros em digitos
def convertWordToDigits(text):
    words = ['zero', 'uma', 'um', 'duas', 'dois', 'tres', 'três', 'quatro',
             'cinco', 'seis', 'ses', 'sete', 'oito', 'nove', 'dez', 'des']
    tradeWords = ['0', '1', '1', '2', '2', '3', '3',
                  '4', '5', '6', '6', '7', '8', '9', '10', '10']

    for words, tradeWords in zip(words, tradeWords):
        convertedText = re.sub(r"(?i){}".format(words), tradeWords, text)
    return convertedText

# Função para confirmar na tela quando a função de star foi ativa
def activeCheck(activationFunction):
    if activationFunction == 1:
        print('//////////Função Ativa!//////////')
    else:
        print('//////////Função não ativa...//////////')

# Função principal da assistente
def lucy():
    global says
    global start

    # Listas
    activationAdvice = ['pois não', 'o que deseja', 'ao seu dispor']

    # Loop principal da assistente
    while True:
        if start == 0:
            fala('Olá, sou a lúci, estou a sua disposição!')
            start = 1
        # Iniciando o reconhecimento de fala
        r = sr.Recognizer()

        try:
            with sr.Microphone() as source:
                # Ajusta o ruido ambiente
                r.energy_threshold = 4000
                # "Escutando" o arquivo
                audio_data = r.listen(source)                
                # Convertendo de audio para texto                
                says = r.recognize_google(audio_data, language='pt-BR')
                # Escrevendo o que foi dito.
                print('Você disse:' + says.lower())
                texto = says.lower()

                # ////////// FUNÇÕES DE CONTROLE DE ESTOQUE //////////

                # Função de ativação
                if 'lucy' in texto or 'luz' in texto or 'lúcia' in texto or 'ok google' in texto:
                    fala(random.choice(activationAdvice))
                    activationFunction = 1
                    activeCheck(activationFunction)

                # Items em falta
                elif ('em falta' in texto or 'faltando' in texto or 'acabando' in texto):
                    cur.execute(f"SELECT item_name, item_quantity , min_item_quantity FROM slots WHERE item_quantity < min_item_quantity;")
                    result = cur.fetchall()
                    print(f'Os itens que estão em falta são:')
                    fala(f'Os itens que estão em falta são:')
                    for x in result: 
                        print(f'{x[0]}, Quantidade atual: {x[1]}, Quantidade mínima: {x[2]}, {(x[2]-x[1])} abaixo do ideal')
                        fala(f'{x[0]}, Quantidade atual: {x[1]}, Quantidade mínima: {x[2]}, {(x[2]-x[1])} abaixo do ideal')

                # Alterar quantidade mínima de um item #1
                elif ('quantidade minima' in texto or 'quantidade mínima' in texto):
                    fala('De qual item deseja alterar a quantidade mínima?')
                    activationFunction = 3.1
                # Alterar quantidade mínima de um item #2
                elif activationFunction == 3.1:
                    inputedItemName = texto
                    fala('Para qual quantidade mínima?')
                    activationFunction = 3.2
                # Alterar quantidade mínima de um item #3
                elif activationFunction == 3.2:
                    inputedItemMinQuantity = texto
                    inputedItemMinQuantityInt = int(inputedItemMinQuantity)
                    cur.execute(f"UPDATE slots SET min_item_quantity = {inputedItemMinQuantityInt} WHERE item_name = '{normalize_text(inputedItemName)}';")
                    conn.commit()
                    fala('Ok alterado')       
                    inputedItemName,inputedItemMinQuantity = '',''   
                    activationFunction = 0  

                # Alterar quantidade de um item #1
                elif ('quantidade' in texto and('muda' in texto or 'mudar' in texto or 'alterar' in texto or 'altera' in texto or 'trocar' in texto or 'troca' in texto)):
                    fala('De qual item deseja alterar a quantidade?')
                    activationFunction = 4.1
                # Alterar quantidade de um item #2
                elif activationFunction == 4.1:
                    inputedItemName = texto
                    fala('Para qual quantidade?')
                    activationFunction = 4.2
                # Alterar quantidade de um item #3
                elif activationFunction == 4.2:
                    inputedItemQuantity = texto
                    inputedItemQuantityInt = int(inputedItemQuantity)
                    cur.execute(f"UPDATE slots SET item_quantity = {inputedItemQuantityInt} WHERE item_name = '{normalize_text(inputedItemName)}';")
                    conn.commit()
                    fala('Ok alterado')       
                    inputedItemName,inputedItemQuantity = '',''   
                    activationFunction = 0
                
                # Excluir gaveta #1
                elif ('excluir' in texto or 'deletar' in texto):
                    fala('Qual gaveta deseja excluir?')
                    activationFunction = 10.1
                # Excluir gaveta #2
                elif activationFunction == 10.1:
                    inputedSlot = texto
                    cur.execute(
                        f"SELECT item_quantity FROM slots WHERE slot_name = '{normalize_text(inputedSlot)}';")
                    result = cur.fetchall()
                    if (result == []):
                        fala('A gaveta requisitada não existe, para adicionar uma nova gaveta utilize o comando configurar gaveta')
                        activationFunction = 0
                    else:                 
                        try:
                            cur.execute(
                                f"DELETE FROM slots WHERE slot_name = '{normalize_text(inputedSlot)}';")
                            conn.commit()
                            # Imprime e fala o resultado
                            print(
                                f'A gaveta nomeada {normalize_text(inputedSlot)} foi excluida da base de dados')
                            fala(
                                f'A gaveta nomeada {normalize_text(inputedSlot)} foi excluida da base de dados')
                        except:
                            print(
                                f'Algo está errado, verifique o nome da gaveta e tente novamente')
                            fala(
                                f'Algo está errado, verifique o nome dda gaveta e tente novamente')
                        inputedSlot,inputedItemName,inputedItemQuantity,inputedItemMinQuantity = '','','',''
                        activationFunction = 0   

                # Alterar nome de uma gaveta #1
                elif ('nome da gaveta' in texto or 'nome de gaveta' in texto):
                    fala('De qual gaveta deseja alterar o nome?')
                    activationFunction = 6.1
                # Alterar nome de uma gaveta #2
                elif activationFunction == 6.1:
                    inputedSlot = texto
                    fala('Para qual nome?')
                    activationFunction = 6.2
                # Alterar nome de uma gaveta #3
                elif activationFunction == 6.2:
                    newSlotName = texto
                    cur.execute(f"UPDATE slots SET slot_name = '{normalize_text(newSlotName)}' WHERE slot_name = '{normalize_text(inputedSlot)}';")
                    conn.commit()
                    fala('Ok alterado')       
                    inputedSlot,newSlotName = '',''   
                    activationFunction = 0 

                # Alterar nome de um item #1
                elif ('nome' in texto and('muda' in texto or 'mudar' in texto or 'alterar' in texto or 'altera' in texto or 'trocar' in texto or 'troca' in texto)):
                    fala('De qual item deseja alterar o nome?')
                    activationFunction = 5.1
                # Alterar nome de um item #2
                elif activationFunction == 5.1:
                    inputedItemName = texto
                    fala('Para qual nome?')
                    activationFunction = 5.2
                # Alterar nome de um item #3
                elif activationFunction == 5.2:
                    newName = texto
                    cur.execute(f"UPDATE slots SET item_name = '{normalize_text(newName)}' WHERE item_name = '{normalize_text(inputedItemName)}';")
                    conn.commit()
                    fala('Ok alterado')       
                    inputedItemName,newName = '',''   
                    activationFunction = 0  

                # Cancelar comando 
                elif ('cancelar' in texto):
                    fala('Ok cancelado')
                    inputedItemName,newName,inputedItemMinQuantity,inputedSlot,inputedItemQuantity = '','','','',''
                    activationFunction = 0  

                # Adicionar item #1
                elif ('adicionar' in texto or 'adicione' in texto or 'coloque' in texto or 'colocar' in texto or 'inserir' in texto):
                    fala('Qual item?')
                    activationFunction = 7.1
                # Adicionar item #2
                elif activationFunction == 7.1:
                    inputedItemName = texto
                    cur.execute(
                        f"SELECT item_quantity FROM slots WHERE item_name = '{normalize_text(inputedItemName)}';")
                    result = cur.fetchall()
                    if (result == []):
                        fala('Não há nenhuma gaveta com o item requisitado, para adicionar novos itens por favor utilize a função adicionar novo item')
                        activationFunction = 0
                    else:
                        fala('Qual a quantidade que deseja adicionar?')
                        activationFunction = 7.2
                # Adicionar item #3
                elif activationFunction == 7.2:
                    inputedItemQuantityAdd = texto
                    inputedItemQuantityAddInt = int(inputedItemQuantityAdd)
                    cur.execute(
                        f"UPDATE slots SET item_quantity=item_quantity + {inputedItemQuantityAddInt} WHERE item_name='{normalize_text(inputedItemName)}'")
                    conn.commit()
                    cur.execute(
                        f"SELECT item_quantity FROM slots WHERE item_name = '{normalize_text(inputedItemName)}';")
                    result = cur.fetchall()
                    # Imprime e fala o resultado
                    print(
                        f'Ok, adicionando {inputedItemQuantityAddInt} {normalize_text(inputedItemName)}, a quantidade atual é {result}')
                    fala(
                        f'Ok, adicionando {inputedItemQuantityAddInt} {normalize_text(inputedItemName)}, a quantidade atual é {result}')
                    inputedSlot,inputedItemName,inputedItemQuantity,inputedItemMinQuantity = '','','',''
                    activationFunction = 0    
                
                # Retirar item #1
                elif ('retirar' in texto or 'remover' in texto or 'remove' in texto or 'remova' in texto or 'tirar' in texto or 'tira' in texto or 'tire' in texto) and activationFunction == 1:
                    fala('Qual item?')
                    activationFunction = 8.1
                # Retirar item #2
                elif activationFunction == 8.1:
                    inputedItemName = texto
                    cur.execute(
                        f"SELECT item_quantity FROM slots WHERE item_name = '{normalize_text(inputedItemName)}';")
                    result = cur.fetchall()
                    if (result == []):
                        fala('Não há nenhuma gaveta com o item requisitado')
                        activationFunction = 0
                    else:
                        fala('Qual a quantidade que deseja retirar?')
                        activationFunction = 8.2
                # Retirar item #3
                elif activationFunction == 8.2:
                    inputedItemQuantityRemove = texto
                    inputedItemQuantityRemoveInt = int(inputedItemQuantityRemove)
                    cur.execute(
                        f"UPDATE slots SET item_quantity=item_quantity - {inputedItemQuantityRemoveInt} WHERE item_name='{normalize_text(inputedItemName)}'")
                    conn.commit()
                    cur.execute(
                        f"SELECT item_quantity FROM slots WHERE item_name = '{normalize_text(inputedItemName)}';")
                    result = cur.fetchall()
                    # Imprime e fala o resultado
                    print(
                        f'Ok, retirando {inputedItemQuantityRemoveInt} {normalize_text(inputedItemName)}, a quantidade atual é {result}')
                    fala(
                        f'Ok, retirando {inputedItemQuantityRemoveInt} {normalize_text(inputedItemName)}, a quantidade atual é {result}')
                    inputedSlot,inputedItemName,inputedItemQuantity,inputedItemMinQuantity = '','','',''
                    activationFunction = 0   

                # Procurar item #1
                elif ('procurar' in texto or 'encontrar' in texto or 'onde está' in texto) and activationFunction == 1:
                    fala('Qual item?')
                    activationFunction = 9.1
                # Procurar item #2
                elif activationFunction == 9.1:
                    inputedItemName = texto
                    cur.execute(
                        f"SELECT item_quantity FROM slots WHERE item_name = '{normalize_text(inputedItemName)}';")
                    result = cur.fetchall()
                    if (result == []):
                        fala('Não há nenhuma gaveta com o item requisitado, para adicionar o item utilize o comando adicionar novo item')
                        activationFunction = 0
                    else:                        
                        try:
                            cur.execute(
                                f"SELECT slot_name FROM slots WHERE item_name = '{normalize_text(inputedItemName)}';")
                            result = cur.fetchall()
                            cur.execute(
                                f"SELECT item_quantity FROM slots WHERE item_name = '{normalize_text(inputedItemName)}';")
                            result2 = cur.fetchall()

                            # Imprime e fala o resultado
                            print(
                                f'O item {normalize_text(inputedItemName)} está na gaveta nomeada {result}, e sua quantidade atual é: {result2}')
                            fala(
                                f'O item {normalize_text(inputedItemName)} está na gaveta nomeada {result}, e sua quantidade atual é: {result2}')
                        except:
                            print(
                                f'Algo está errado, verifique o nome do item e tente novamente')
                            fala(
                                f'Algo está errado, verifique o nome do item e tente novamente')
                        activationFunction = 0
                        inputedSlot,inputedItemName,inputedItemQuantity,inputedItemMinQuantity = '','','',''
                        activationFunction = 0   

                # Configurar novo item #1
                elif ('configurar' in texto or 'novo item' in texto) and activationFunction == 1:
                    fala('Qual o nome da gaveta?')
                    
                    activationFunction = 2.1
                # Configurar novo item #2
                elif activationFunction == 2.1:
                    inputedSlot = texto
                    fala('Qual o nome do item?')
                    activationFunction = 2.2                
                # Configurar novo item #3
                elif activationFunction == 2.2:
                    inputedItemName = texto
                    fala('Qual a quantidade do item?')
                    activationFunction = 2.3
                # Configurar novo item #4
                elif activationFunction == 2.3:
                    inputedItemQuantity = texto
                    fala('Qual a quantidade mínima do item?')
                    activationFunction = 2.4
                # Configurar novo item #5
                elif activationFunction == 2.4:                    
                    inputedItemMinQuantity = texto
                    activationFunction = 2.5
                    print(f'Será configurada a gaveta nomeada {inputedSlot}, com o item {inputedItemName}, sua quantidade atual é {inputedItemQuantity} e mínima de {inputedItemMinQuantity}')
                    fala(f'Será configurada a gaveta nomeada {inputedSlot}, com o item {inputedItemName}, sua quantidade atual é {inputedItemQuantity} e mínima de {inputedItemMinQuantity}')
                    fala('Confirma essa operação?')
                # Configurar novo item #6
                elif activationFunction == 2.5:
                    inputedItemQuantityInt = int(inputedItemQuantity)
                    inputedItemMinQuantityInt = int(inputedItemMinQuantity)
                                     
                    if 'sim' in texto or 'confirmar' in texto or 'confirmo' in texto:
                        fala('Ok, adicionado')
                        cur.execute(
                        f"INSERT INTO slots(slot_name, item_name, item_quantity, min_item_quantity)VALUES ('{inputedSlot}', '{inputedItemName}',{inputedItemQuantityInt} , {inputedItemMinQuantityInt})")
                        conn.commit()
                    if 'nao' in texto or 'cancelar' in texto or 'não' in texto:
                        fala('ok, operação cancelada')                    
                    inputedSlot,inputedItemName,inputedItemQuantity,inputedItemMinQuantity = '','','',''
                    activationFunction = 0       
                    
                # Exportar tabela para CSV
                elif ('imprimir' in texto or 'exportar' in texto or 'excel' in texto or 'csv' in texto) and activationFunction == 1:
                    cur.execute(f"COPY (SELECT * FROM slots) TO '{desktop}\complete_table.csv' WITH (FORMAT CSV, HEADER)")
                    fala(f'ok, a base de dados completa foi exportada para sua area de trabalho em: {desktop}')
                    activationFunction = 0  
                # ////////// FUNÇÕES BASICAS DE ASSISTENTES VIRTUAIS //////////

                # Desligar
                elif ('desligar' in texto or 'descansar' in texto or 'encerrar' in texto or 'fechar' in texto) and activationFunction == 1:
                    fala('Ok! Desligando')
                    start = 0
                    ThisSystem.terminate()
                    break

                # Funcão para falar a data
                elif ('data' in texto or 'dia' in texto) and activationFunction == 1:
                    monthList = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                                 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
                    currentDate = (datetime.datetime.now()).strftime("%d/%m/%y")
                    day, month, year = currentDate.split('/')
                    currentDate = 'Hoje é %s de %s de 2000 e %s' % (
                        num2words.num2words(day, lang='pt_BR'), monthList[int(month)-1], num2words.num2words(year, lang='pt_BR'))
                    fala(currentDate)
                    activationFunction = 0

                # Funcão para falar as horas
                elif ('hora' in texto or 'horas' in texto) and activationFunction == 1:
                    hora = datetime.datetime.now().strftime('%H:%M')
                    fala('Agora são' + hora)
                    activationFunction = 0


                # Previsão do tempo
                elif (('clima' in texto or 'previsão' in texto or 'tempo' in texto) and activationFunction == 1):
                    busca = f"A Previsão do tempo em {local} é:"
                    url = f"https://www.google.com/search?q={busca}"
                    r = requests.get(url)
                    s = BeautifulSoup(r.text, "html.parser")
                    update = s.find("div", class_="BNeawe").text
                    weather = (busca + update)
                    fala(f'{weather}')
                    activationFunction = 0

                # Jogar moeda
                elif ('jogue uma moeda' in texto) and activationFunction == 1:
                    moeda = ['cara', 'coroa']
                    fala(random.choice(moeda))
                    activationFunction = 0

                # Respostas simples
                elif ('bom dia' in texto) and activationFunction == 1:
                    fala(f'Bom dia {nick}"')
                    activationFunction = 0

                elif ('boa noite' in texto) and activationFunction == 1:
                    fala(f'Boa noite {nick}"')
                    activationFunction = 0

                elif ('boa tarde' in texto) and activationFunction == 1:
                    fala(f'Ba tarde {nick}"')
                    activationFunction = 0

                elif ('idade' in texto) and activationFunction == 1:
                    fala(f'Você tem {idade} anos')
                    activationFunction = 0                    

                elif ('moro' in texto) and activationFunction == 1:
                    fala(f'Você mora no {local}')
                    activationFunction = 0                    

        # Se ocorrer algum erro, retornará:
        except Exception as e:
            print('Ocorreu algum erro.')
            print('Erro:')
            print(e)

# Inicia a Thread da lucy
def main_thread():
    Thread(target=lucy).start()

# Cria a tela
def ui_screen():

    w = 900  # width for the Tk root
    h = 600  # height for the Tk root

    root = Tk()

    canvas = Canvas(root, bg="white", width=900, height=600)
    canvas.pack()

    # Fundo
    background = PhotoImage(file="assets/main_frame.png")
    canvas.create_image(450, 300, image=background)

    '''
    # Entrada do comando
    input = PhotoImage(file="assets/command_input.png")
    canvas.create_image(635, 360, image=input)

    # Botão de executar comando
    button_img = PhotoImage(file="assets/execute_command_button.png")
    execute = Button(root, image=button_img, borderwidth=0, bg='#02B3F9',
                     fg='#02B3F9', activebackground='#02B3F9', command=command_input)
    execute.place(x=407, y=430)

    # Entrada
    entry = Entry(root, width=24, bg='white',
                  font=('Verdana 20'), borderwidth=0)
    entry.place(x=430, y=360)
    '''

    # Botão de iniciar
    button_img2 = PhotoImage(file="assets/start_button.png")
    execute2 = Button(root, image=button_img2, borderwidth=0, bg='#02B3F9',
                      fg='#02B3F9', activebackground='#02B3F9', command=main_thread)
    execute2.place(x=470, y=300)

    # Pega o tamanho da tela
    ws = root.winfo_screenwidth()  # width
    hs = root.winfo_screenheight()  # height

    # Calcula o meio da tela
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)

    root.title('Lucy - Assistente virtual para controle de estoque')
    root.iconbitmap('assets/icon.ico')
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    root.resizable(width=0, height=0)

    root.mainloop()

# inicia a tela
ui_screen()

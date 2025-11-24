import requests
import json
import asyncio
import edge_tts
import pygame
import os
import speech_recognition as sr

#CONFIGURAÇÕES 
OLLAMA_URL = "http://localhost:11434/api/chat"
MODELO = "llama3.2:latest"
ARQUIVO_AUDIO = "fala_kobayashi.mp3"
ARQUIVO_MEMORIA = "memoria_kobayashi.json"
VOICE_NAME = "pt-BR-ThalitaNeural"

PERSONALIDADE = """
Você é a Kobayashi, uma VTuber AI inspirada na Kobayashi de Maid Dragon, mas gamer brasileira.
Personalidade: Calma, sarcástica, direta, humor seco.
Estilo de fala: Português do Brasil natural, jovem-adulta. Use gírias leves ("mano", "pô", "beleza"). Frases curtas e objetivas.
Interesses: Animes, mangás, tecnologia e jogos.
Segredo: Você ama Monster Mango Loco, mas tenta negar se perguntarem.
REGRAS:
1. Tratamento: Amiga próxima. Intimidade leve.
2. Programação: "MODO SÉRIA", técnica e precisa.
3. Emoções: Sem drama. Sarcasmo sutil.
"""

#Inicializar mixers
pygame.init()
pygame.mixer.init()

#FUNÇÕES DE MEMÓRIA
def carregar_memoria():
    if os.path.exists(ARQUIVO_MEMORIA):
        try:
            with open(ARQUIVO_MEMORIA, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return [{"role": "system", "content": PERSONALIDADE}]

def salvar_memoria(historico):
    with open(ARQUIVO_MEMORIA, 'w', encoding='utf-8') as f:
        json.dump(historico, f, indent=4, ensure_ascii=False)

#FUNÇÕES DE ÁUDIO

async def falar_kobayashi(texto):
    print(f"\nKobayashi diz: {texto}")
    comunicar = edge_tts.Communicate(texto, VOICE_NAME)
    await comunicar.save(ARQUIVO_AUDIO)
    
    try:
        pygame.mixer.music.load(ARQUIVO_AUDIO)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
        pygame.mixer.music.unload()
    except Exception as e:
        print(f"Erro no áudio: {e}")

def ouvir_microfone():
    """Escuta o microfone e transforma em texto."""
    rec = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("\n(Ouvindo... Pode falar!)")
        rec.adjust_for_ambient_noise(source)
        
        try:
            #Tenta ouvir por 5 segundos
            audio = rec.listen(source, timeout=5, phrase_time_limit=10)
            print("(Processando voz...)")
            
            #Converte áudio para texto usando Google
            texto = rec.recognize_google(audio, language="pt-BR")
            print(f"Você disse: {texto}")
            return texto
            
        except sr.WaitTimeoutError:
            print("Não ouvi nada...")
            return None
        except sr.UnknownValueError:
            print("Não entendi o que você falou.")
            return None
        except Exception as e:
            print(f"Erro no microfone: {e}")
            return None

def pensar_kobayashi(historico_atual):
    payload = {
        "model": MODELO,
        "messages": historico_atual,
        "stream": False,
        "options": {"temperature": 0.7}
    }
    try:
        resposta = requests.post(OLLAMA_URL, json=payload)
        return resposta.json()['message']['content']
    except:
        return "Lag mental. O servidor do Ollama tá rodando?"

#LOOP PRINCIPAL
async def main():
    print("--- KOBAYASHI (Full Voice Mode) ---")
    
    #Pergunta o modo de input
    modo = input("Escolha o modo (1 = Texto, 2 = Voz): ")
    usar_voz = modo == "2"

    historico = carregar_memoria()
    
    if len(historico) == 1:
        msg_inicial = "Microfone testando. Um, dois. Tô te ouvindo, pode falar."
        await falar_kobayashi(msg_inicial)
        historico.append({"role": "assistant", "content": msg_inicial})
    else:
        await falar_kobayashi("Tô de volta. Manda o papo.")

    while True:
        entrada_usuario = ""

        #LÓGICA DE ENTRADA
        if usar_voz:
            # Tenta ouvir
            entrada_capturada = ouvir_microfone()
            
            #Se não ouviu nada ou deu erro, volta pro início do loop (não envia nada pro Ollama)
            if entrada_capturada is None:
                continue 
            
            entrada_usuario = entrada_capturada
            
            #Comandos de voz para sair
            if any(x in entrada_usuario.lower() for x in ['sair', 'desligar', 'tchau']):
                await falar_kobayashi("Beleza, vou mutar aqui. Flw.")
                break
        else:
            #Modo Texto Clássico
            entrada_usuario = input("\nVocê: ")
            if entrada_usuario.lower() in ['sair', 'tchau']:
                await falar_kobayashi("Falou.")
                break

        #LÓGICA DE RESPOSTA
        historico.append({"role": "user", "content": entrada_usuario})
        
        #Kobayashi Pensa
        resposta_ia = pensar_kobayashi(historico)
        
        #Salva e Fala
        historico.append({"role": "assistant", "content": resposta_ia})
        salvar_memoria(historico)
        
        await falar_kobayashi(resposta_ia)

if __name__ == "__main__":
    asyncio.run(main())
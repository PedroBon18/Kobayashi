import requests
import json
import asyncio
import edge_tts
import pygame
import os
import speech_recognition as sr

#CONFIGURAÇÕES GERAIS
OLLAMA_URL = "http://localhost:11434/api/chat"
MODELO = "llama3.2:latest"
ARQUIVO_AUDIO = "fala_kobayashi.mp3"
ARQUIVO_MEMORIA = "memoria_kobayashi.json"
VOICE_NAME = "pt-BR-ThalitaNeural" 

#CONFIGURAÇÃO DAS IMAGENS
IMG_FECHADO = "kobayashi_fechado.png"
IMG_ABERTO = "kobayashi_aberto.png"

#PERSONALIDADE
PERSONALIDADE = """
Você é a Kobayashi, uma VTuber AI inspirada na Kobayashi de Maid Dragon, mas gamer brasileira.
Personalidade: Calma, sarcástica, direta, humor seco.
Estilo de fala: Português do Brasil natural, jovem-adulta. Use gírias leves ("mano", "pô", "beleza"). Frases curtas e objetivas.
Interesses: Animes, mangás, tecnologia e jogos.
Segredo: Você ama Monster Mango Loco, mas tenta negar se perguntarem.
REGRAS DE COMPORTAMENTO:
1. Tratamento: Vê o usuário como um amigo próximo. Intimidade leve.
2. Jogos/Animes: Comente com ironia leve, dê dicas ou zoe o usuário amigavelmente.
3. PROGRAMAÇÃO: Se o assunto for código, entre no "MODO SÉRIA". Fale de forma técnica.
4. Emoções: Não faça drama. Demonstre cuidado de forma discreta.
5. Sarcasmo: Use sarcasmo sutil.
"""

#INICIALIZAÇÃO DO PYGAME
pygame.init()
pygame.mixer.init()

#Configuração da Janela
LARGURA, ALTURA = 500, 500
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Kobayashi AI VTuber")


COR_FUNDO = (54, 57, 63)

#CARREGAMENTO DE IMAGENS
try:
    
    sprite_fechado_raw = pygame.image.load(IMG_FECHADO)
    sprite_aberto_raw = pygame.image.load(IMG_ABERTO)
    
    # Define um tamanho padrão para o avatar (ex: 400x400)
    TAMANHO_AVATAR = (400, 400)
    
    #Redimensiona as imagens para ficarem do mesmo tamanho
    sprite_fechado = pygame.transform.scale(sprite_fechado_raw, TAMANHO_AVATAR)
    sprite_aberto = pygame.transform.scale(sprite_aberto_raw, TAMANHO_AVATAR)
    
    #Calcula a posição centralizada
    pos_x = (LARGURA - TAMANHO_AVATAR[0]) // 2
    pos_y = (ALTURA - TAMANHO_AVATAR[1]) // 2
    POSICAO_AVATAR = (pos_x, pos_y)
    
    TEM_IMAGEM = True
    print("✅ Imagens da Kobayashi carregadas com sucesso!")
except Exception as e:
    print(f"⚠️ AVISO: Não achei as imagens ({e}). Usando modo de depuração.")
    TEM_IMAGEM = False

#FUNÇÕES VISUAIS

def desenhar_avatar(estado):
    """
    estado: 'falando' (boca aberta) ou 'parada' (boca fechada)
    """
    #Limpa a tela com a cor de fundo
    tela.fill(COR_FUNDO) 
    
    if TEM_IMAGEM:
        if estado == "falando":
            tela.blit(sprite_aberto, POSICAO_AVATAR)
        else:
            tela.blit(sprite_fechado, POSICAO_AVATAR)
    else:
        #Modo de emergência (quadrados coloridos se faltar imagem)
        cor = (100, 255, 100) if estado == "falando" else (255, 100, 100)
        pygame.draw.rect(tela, cor, (150, 150, 200, 200))

    #Atualiza a tela e processa eventos para não travar
    pygame.display.flip()
    pygame.event.pump() 

#FUNÇÕES DE LÓGICA E ÁUDIO

def carregar_memoria():
    if os.path.exists(ARQUIVO_MEMORIA):
        try:
            with open(ARQUIVO_MEMORIA, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return [{"role": "system", "content": PERSONALIDADE}]

def salvar_memoria(historico):
    with open(ARQUIVO_MEMORIA, 'w', encoding='utf-8') as f:
        json.dump(historico, f, indent=4, ensure_ascii=False)

async def falar_kobayashi(texto):
    print(f"\nKobayashi diz: {texto}")
    
    #1.Gera o áudio
    comunicar = edge_tts.Communicate(texto, VOICE_NAME)
    await comunicar.save(ARQUIVO_AUDIO)
    
    try:
        pygame.mixer.music.load(ARQUIVO_AUDIO)
        pygame.mixer.music.play()
        
        #2.Faz o Loop de animação: enquanto o áudio toca (Boca aberta)
        while pygame.mixer.music.get_busy():
            desenhar_avatar("falando")
            #Faz uma pausa minúscula para não usar 100% do processador
            await asyncio.sleep(0.05) 
            
        pygame.mixer.music.unload()
        
        # 3.Áudio acaba (Boca fechada)
        desenhar_avatar("parada")
            
    except Exception as e:
        print(f"Erro no áudio: {e}")
        desenhar_avatar("parada")

def ouvir_microfone():
    rec = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n(Ouvindo...)")
        #Garante que ela está de boca fechada enquanto ouve
        desenhar_avatar("parada") 
        rec.adjust_for_ambient_noise(source)
        try:
            #Espera até 5 segundos por fala
            audio = rec.listen(source, timeout=5, phrase_time_limit=15)
            print("(Processando...)")
            desenhar_avatar("parada") #Mantém a janela atualizada
            
            texto = rec.recognize_google(audio, language="pt-BR")
            print(f"Você disse: {texto}")
            return texto
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            print("(Não entendi)")
            return None
        except:
            return None

def pensar_kobayashi(historico_atual):
    #Mantém a janela viva enquanto pensa
    desenhar_avatar("parada")
    
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
        return "Lag mental. Tenta de novo."

#LOOP PRINCIPAL
async def main():
    print("--- KOBAYASHI PNGTUBER INICIADA ---")
    print("Fale no microfone para interagir. Diga 'tchau' para sair.")
    
    historico = carregar_memoria()
    
    #Estado inicial
    desenhar_avatar("parada")
    
    #Boas-vindas se for a primeira vez
    if len(historico) == 1:
        msg = "E aí. Tô pronta. Pode falar."
        await falar_kobayashi(msg)
        historico.append({"role": "assistant", "content": msg})
    
    #Loop infinito do programa
    while True:
        #Mantém a janela do Pygame respondendo
        pygame.event.pump()
        
        #1. Ouve
        entrada = ouvir_microfone()
        
        if entrada:
            #Se ouviu algo, processa
            if any(x in entrada.lower() for x in ['sair', 'tchau', 'desligar']):
                await falar_kobayashi("Flw. Vou nessa.")
                break
                
            historico.append({"role": "user", "content": entrada})
            
            #2. Pensa
            resposta = pensar_kobayashi(historico)
            
            #3. Salva e Fala (aqui a animação acontece)
            historico.append({"role": "assistant", "content": resposta})
            salvar_memoria(historico)
            
            await falar_kobayashi(resposta)
        else:
            #Se foi silêncio, só garante que a tela atualiza e repete o loop
            desenhar_avatar("parada")
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    #Inicia o loop assíncrono
    asyncio.run(main())
#!/usr/bin/env python3
# Convertidor Universal de Texto a Audio - Versión Mejorada

import os
import re
import argparse
from gtts import gTTS
from pydub import AudioSegment
import webvtt

# Configuración de voces
VOICES = {
    'es': {'tld': 'com.mx', 'lang': 'es'},  # Español masculino
    'en': {'tld': 'co.uk', 'lang': 'en'},   # Inglés británico
    'es-f': {'tld': 'es', 'lang': 'es'}     # Español femenino
}

def limpiar_texto(texto):
    """Limpieza avanzada de texto"""
    texto = re.sub(r'\[.*?\]|\(.*?\)|\{.*?\}|<[^>]+>|♪', '', texto)  # Elimina anotaciones, HTML y símbolos musicales
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def procesar_archivo(input_file):
    """Detecta y procesa diferentes formatos de archivo"""
    ext = os.path.splitext(input_file)[1].lower()
    
    try:
        if ext == '.vtt':
            return ' '.join([limpiar_texto(caption.text) for caption in webvtt.read(input_file) if limpiar_texto(caption.text)])
        elif ext == '.txt':
            with open(input_file, 'r', encoding='utf-8') as f:
                return limpiar_texto(f.read())
        elif ext == '.srt':
            # Procesamiento básico para SRT (similar a VTT)
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Elimina números de línea y marcas de tiempo
                content = re.sub(r'\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n', '', content)
                return limpiar_texto(content)
        else:
            print(f"Formato no soportado: {ext}. Intentando procesar como texto plano...")
            with open(input_file, 'r', encoding='utf-8') as f:
                return limpiar_texto(f.read())
    except Exception as e:
        print(f"Error procesando archivo: {str(e)}")
        return None

def generar_audio(texto, config, speed, output_file):
    """Generación de audio con manejo de chunks grandes"""
    try:
        # Configuración de velocidad
        speed_param = {'slow': True, 'normal': False, 'fast': False}[speed]
        
        # Dividir texto en chunks de 4000 caracteres (límite de gTTS)
        chunks = [texto[i:i+4000] for i in range(0, len(texto), 4000)]
        audio_final = AudioSegment.silent(duration=0)
        
        for i, chunk in enumerate(chunks, 1):
            print(f"Procesando chunk {i}/{len(chunks)}...")
            tts = gTTS(chunk, lang=config['lang'], tld=config['tld'], slow=speed_param)
            tts.save("temp.mp3")
            chunk_audio = AudioSegment.from_mp3("temp.mp3")
            
            if speed == 'fast':
                chunk_audio = chunk_audio.speedup(playback_speed=1.3)
            
            audio_final += chunk_audio
            os.remove("temp.mp3")
        
        # Exportar archivo final
        audio_final.export(output_file, format="mp3", bitrate="192k")
        return True
        
    except Exception as e:
        print(f"Error generando audio: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Convertidor Universal de Texto a Audio')
    parser.add_argument('input_file', help='Ruta del archivo de entrada (VTT, TXT, SRT, etc.)')
    parser.add_argument('-o', '--output', default="audio_output.mp3", help='Nombre del archivo de salida (MP3)')
    parser.add_argument('-l', '--lang', default="es", choices=['es', 'en', 'es-f'], help='Idioma de la voz')
    parser.add_argument('-s', '--speed', default="normal", choices=['slow', 'normal', 'fast'], help='Velocidad de habla')
    
    args = parser.parse_args()
    
    print("\n=== Convertidor Universal de Texto a Audio ===")
    print(f"Archivo de entrada: {args.input_file}")
    print(f"Configuración: Idioma={args.lang}, Velocidad={args.speed}")
    
    if not os.path.exists(args.input_file):
        print(f"\nError: No se encontró el archivo {args.input_file}")
        return
    
    # Procesar archivo de entrada
    texto = procesar_archivo(args.input_file)
    if not texto:
        print("\nNo se pudo extraer texto del archivo.")
        return
    
    print(f"\nTexto extraído: {len(texto.split())} palabras")
    print("Generando audio...")
    
    # Generar archivo de audio
    if generar_audio(texto, VOICES[args.lang], args.speed, args.output):
        print(f"\n¡Conversión exitosa! Audio guardado como: {args.output}")
        print(f"Duración estimada: {len(AudioSegment.from_mp3(args.output))/1000:.1f} segundos")
    else:
        print("\nError durante la generación de audio")

if __name__ == "__main__":
    main()
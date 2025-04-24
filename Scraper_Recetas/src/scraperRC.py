import requests
from bs4 import BeautifulSoup
import json
import time 
import os
from datetime import datetime
import hashlib

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9"
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'receitas.json')
LOG_FILE = os.path.join(OUTPUT_DIR, 'receitas_log.json')

def calculate_hash(content):
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode('utf-8')).hexdigest()

def log_change():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "file": OUTPUT_FILE,
        "action": "modified"
    }
    
    log_data = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except:
            pass
    
    log_data.append(log_entry)
    
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

def save_if_changed(new_data):
    current_hash = calculate_hash(new_data)
    
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            existing_hash = calculate_hash(existing_data)
            
            if current_hash == existing_hash:
                print("ℹ️ Nenhuma alteração detectada no conteúdo.")
                return False
        except:
            pass
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    log_change()
    return True

def get_links_recetas(limit):
    url = "https://www.recetasgratis.net/"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()  
        soup = BeautifulSoup(response.text, 'html.parser')

        links = []
        count = 0
        for a in soup.find_all('a', class_='titulo titulo--bloque'):
            href = a.get('href')
            if href:
                links.append(href)
                count += 1
                if count >= limit:
                    break
                time.sleep(1)   
        
        return links
    except Exception as e:
        print(f"Erro ao buscar links em {url}: {e}")
        return []

def scrape_receta(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        titulo = soup.find('h1', class_='titulo').text.strip()
        imagem = soup.find('img', class_='imagen')
        imagem_url = imagem['src'] if imagem else None

        ingredientes = []
        ingredientes_section = soup.find('div', class_='ingredientes')
        if ingredientes_section:
            for li in ingredientes_section.find_all('li', class_='ingrediente'):
                ingrediente = li.find('label').text.strip() if li.find('label') else None
                if ingrediente:
                    ingredientes.append(ingrediente)

        passos = []
        passos_section = soup.find_all('div', class_='apartado')
        for sec in passos_section:
            if sec.find('div', class_='orden'):
                p = sec.find('p')
                if p:
                    passos.append(p.get_text(strip=True))

        nutricion = {}
        nutricion_section = soup.find('div', id='nutritional-info')
        if nutricion_section:
            for li in nutricion_section.find_all('li'):
                texto = li.get_text(strip=True)
                if ':' in texto:
                    chave, valor = texto.split(':', 1)
                    nutricion[chave.strip()] = valor.strip()

        return {
            "titulo": titulo,
            "imagem": imagem_url,
            "ingredientes": ingredientes,
            "nutricion": nutricion,
            "passos": passos
        }
    except Exception as e:
        print(f"Erro ao coletar dados de {url}: {e}")
        return None

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("\n\t==={ SCRAPPER RECETAS }===\n")
    
    while True:
        try:
            limit = int(input("Digite o número de receitas a coletar (exemplo: 5): "))
            print("\n\t==={ Scrapping in proccess, please be pacient. It may take some time, big numbers are equivalent to bigger delays. }===\n")
            if limit > 0:
                break
            print("Por favor, insira um número maior que 0.")
        except ValueError:
            print("Por favor, insira um número válido.")
    
    links = get_links_recetas(limit)
    if links:
        todas_receitas = []
        for link in links:
            print(f"📥 Coletando dados de: {link}")
            dados = scrape_receta(link)
            if dados:
                todas_receitas.append(dados)

        if save_if_changed(todas_receitas):
            print(f"✅ Dados das receitas salvos com sucesso em: {OUTPUT_FILE}")
        else:
            print(f"ℹ️ Dados não salvos, pois não houve alterações.")
    else:
        print("❌ Nenhum link encontrado para as receitas.")

if __name__ == "__main__":
    main()
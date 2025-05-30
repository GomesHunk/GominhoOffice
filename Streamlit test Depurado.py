import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

def get_latest_drawing_url(base_url, drawing_code):
    parts = drawing_code.split('-')
    if len(parts) != 3:
        raise ValueError("Formato inválido. Use: 'xxx-xxx-xxx'")

    response = requests.get(base_url)
    if response.status_code != 200:
        raise Exception(f"Erro ao acessar a pasta raiz: {base_url}")

    soup = BeautifulSoup(response.content, 'html.parser')

    first_level_pattern = re.compile(f"^{parts[0]}\\b.*")
    first_level_folder = None
    for link in soup.find_all('a', href=True):
        folder_name = link.text.strip('/')
        if first_level_pattern.match(folder_name):
            first_level_folder = link['href']
            break

    if not first_level_folder:
        raise Exception(f"Nenhuma pasta encontrada para o prefixo: {parts[0]}")

    first_level_url = base_url.rstrip('/') + '/' + first_level_folder

    response = requests.get(first_level_url)
    if response.status_code != 200:
        raise Exception(f"Erro ao acessar a subpasta: {first_level_url}")

    soup = BeautifulSoup(response.content, 'html.parser')

    second_level_pattern = re.compile(f"^{parts[0]}-{parts[1]}\\b.*")
    second_level_folder = None
    for link in soup.find_all('a', href=True):
        folder_name = link.text.strip('/')
        if second_level_pattern.match(folder_name):
            second_level_folder = link['href']
            break

    if not second_level_folder:
        raise Exception(f"Nenhuma subpasta encontrada para: {parts[0]}-{parts[1]}")

    second_level_url = first_level_url.rstrip('/') + '/' + second_level_folder

    response = requests.get(second_level_url)
    if response.status_code != 200:
        raise Exception(f"Erro ao acessar a subpasta final: {second_level_url}")

    soup = BeautifulSoup(response.content, 'html.parser')

    file_pattern = re.compile(f"{drawing_code}(-[A-Z])?\\.tif$")
    file_links = [link['href'] for link in soup.find_all('a', href=True) if file_pattern.match(link['href'])]

    if not file_links:
        raise Exception(f"Nenhum arquivo encontrado para: {drawing_code}")

    def revision_key(filename):
        match = re.search(r'-(\w)\.tif$', filename)
        return match.group(1) if match else ''

    file_links = sorted(file_links, key=revision_key, reverse=True)
    latest_file_url = second_level_url.rstrip('/') + '/' + file_links[0]

    return latest_file_url

# Interface Streamlit
st.set_page_config(page_title="Localizador de Desenhos Técnicos", layout="centered")
st.title("🔍 Localizador de Desenhos Técnicos")

if "drawing_code" not in st.session_state:
    st.session_state.drawing_code = ""

drawing_code = st.text_input("Digite o código do desenho (ex: 180-570-542):", value=st.session_state.drawing_code)

col1, col2 = st.columns(2)

with col1:
    if st.button("Buscar desenho"):
        if drawing_code:
            st.session_state.drawing_code = drawing_code
            try:
                url = get_latest_drawing_url(
                    "http://rio1web.net.fmcti.com/ipd/fmc_released_legacy/Desenhos/Produtos",
                    drawing_code
                )
                st.success("✅ Link do desenho mais recente encontrado:")
                st.write(url)  # Apenas exibe o link clicável uma vez
            except Exception as e:
                st.error(f"❌ Erro: {e}")
        else:
            st.warning("Por favor, insira um código de desenho.")

with col2:
    if st.button("Limpar"):
        st.session_state.drawing_code = ""
        st.rerun()

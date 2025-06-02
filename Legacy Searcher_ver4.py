import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import os
import zipfile
from io import BytesIO

# Função para formatar o código de desenho para a pasta Desativados
def format_drawing_code_desativados(drawing_code):
    parts = drawing_code.split('-')
    formatted_parts = [parts[0].zfill(3)] + parts[1:]
    return '-'.join(formatted_parts)

# Função para formatar o código de desenho para a pasta FMC (sem formatação)
def format_drawing_code_fmc(drawing_code):
    return drawing_code

# Busca na web
def get_latest_drawing_urls(base_url, drawing_code):
    drawing_code = format_drawing_code_desativados(drawing_code)
    parts = drawing_code.split('-')
    if len(parts) != 3:
        raise ValueError("Formato inválido. Use: 'xxx-xxx-xxx'")

    response = requests.get(base_url)
    if response.status_code != 200:
        raise Exception(f"Erro ao acessar a pasta raiz: {base_url}")
    soup = BeautifulSoup(response.content, 'html.parser')

    # Primeiro nível
    first_level_pattern = re.compile(f"^{parts[0]}\\b.*")
    first_level_folder = next((link['href'] for link in soup.find_all('a', href=True)
                               if first_level_pattern.match(link.text.strip('/'))), None)
    if not first_level_folder:
        raise Exception(f"Nenhuma pasta encontrada para o prefixo: {parts[0]}")
    first_level_url = base_url.rstrip('/') + '/' + first_level_folder

    # Segundo nível
    response = requests.get(first_level_url)
    if response.status_code != 200:
        raise Exception(f"Erro ao acessar a subpasta: {first_level_url}")
    soup = BeautifulSoup(response.content, 'html.parser')
    second_level_pattern = re.compile(f"^{parts[0]}-{parts[1]}\\b.*")
    second_level_folder = next((link['href'] for link in soup.find_all('a', href=True)
                                if second_level_pattern.match(link.text.strip('/'))), None)
    if not second_level_folder:
        raise Exception(f"Nenhuma subpasta encontrada para: {parts[0]}-{parts[1]}")
    second_level_url = first_level_url.rstrip('/') + '/' + second_level_folder

    # Arquivos
    response = requests.get(second_level_url)
    if response.status_code != 200:
        raise Exception(f"Erro ao acessar a subpasta final: {second_level_url}")
    soup = BeautifulSoup(response.content, 'html.parser')

    # Padrão para arquivos com múltiplas páginas e revisões
    file_pattern = re.compile(f"{drawing_code}(-\\d+)?-([A-Z])\\.tif$")
    file_links = [link['href'] for link in soup.find_all('a', href=True) if file_pattern.match(link['href'])]

    if not file_links:
        raise Exception(f"Nenhum arquivo encontrado para: {drawing_code}")

    # Agrupar por revisão
    grouped = {}
    for file in file_links:
        match = re.search(rf"{drawing_code}(-\d+)?-([A-Z])\.tif$", file)
        if match:
            revision = match.group(2)
            if revision not in grouped:
                grouped[revision] = []
            grouped[revision].append(second_level_url.rstrip('/') + '/' + file)

    # Selecionar a revisão mais recente (ordem alfabética reversa)
    latest_revision = sorted(grouped.keys(), reverse=True)[0]
    return grouped[latest_revision], latest_revision

# Busca na rede local
def get_latest_drawing_paths(base_path, drawing_code, format_code_func):
    drawing_code = format_code_func(drawing_code)
    parts = drawing_code.split('-')
    if len(parts) < 2:
        raise ValueError("Formato inválido. Use: 'xxx-xxx' ou 'xxx-xxx-xxx'")

    file_pattern = re.compile(f"{drawing_code}(-\\d+)?-?([A-Z])?\\.tif$")

    found_files = []

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file_pattern.search(file):
                found_files.append(os.path.join(root, file))

    if not found_files:
        raise Exception(f"Nenhum arquivo encontrado para: {drawing_code}")

    return found_files

# Função para agrupar arquivos por versão e página
def group_files_by_version_and_page(files):
    grouped_files = {}
    for file in files:
        match = re.search(r'-(\d+)?-?([A-Z])?\.', file)
        if match:
            page = match.group(1) if match.group(1) else 'single'
            version = match.group(2) if match.group(2) else ''
            if version not in grouped_files:
                grouped_files[version] = {}
            if page not in grouped_files[version]:
                grouped_files[version][page] = []
            grouped_files[version][page].append(file)
    return grouped_files

# Função para criar um arquivo zip com os arquivos fornecidos
def create_zip(files):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for file in files:
            zip_file.write(file, os.path.basename(file))
    buffer.seek(0)
    return buffer

# Função para criar um arquivo zip a partir de URLs
def create_zip_from_urls(urls):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for url in urls:
            response = requests.get(url)
            if response.status_code == 200:
                filename = url.split('/')[-1]
                zip_file.writestr(filename, response.content)
    buffer.seek(0)
    return buffer

# Interface Streamlit
st.set_page_config(page_title="🔍 Localizador de Desenhos Técnicos Legacy", layout="centered")
st.title("🔍 Localizador de Desenhos Técnicos Legacy")

if "drawing_code" not in st.session_state:
    st.session_state.drawing_code = ""

if "stop_search" not in st.session_state:
    st.session_state.stop_search = False

drawing_code = st.text_input("Digite o código do desenho (ex: 180-570-542):", value=st.session_state.drawing_code)

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("Buscar desenho", use_container_width=True):
        if drawing_code:
            st.session_state.drawing_code = drawing_code
            st.session_state.stop_search = False

            # Busca na web
            try:
                with st.spinner("Buscando na web..."):
                    urls, latest_revision = get_latest_drawing_urls(
                        "http://rio1web.net.fmcti.com/ipd/fmc_released_legacy/Desenhos/Produtos",
                        drawing_code
                    )
                    st.success(f"✅ Arquivos da revisão mais recente (Web): {latest_revision}")
                    for url in urls:
                        st.write(url)
                    if len(urls) > 1:
                        zip_buffer = create_zip_from_urls(urls)
                        st.download_button(label=f"📦 Baixar todas as páginas (Web) - Revisão {latest_revision}", data=zip_buffer, file_name=f"{drawing_code}-web-{latest_revision}.zip")
                    st.session_state.stop_search = True
            except Exception as e:
                st.warning(f"⚠️ Web: {e}")

            # Busca na rede local - Desativados
            if not st.session_state.stop_search:
                try:
                    with st.spinner("Buscando na rede local..."):
                        network_path_desativados = r"\\rio-data-srv\arquivo\Desativados"
                        local_files_desativados = get_latest_drawing_paths(network_path_desativados, drawing_code, format_drawing_code_desativados)
                        grouped_files = group_files_by_version_and_page(local_files_desativados)
                        latest_version = sorted(grouped_files.keys(), reverse=True)[0]
                        st.success(f"✅ Arquivos da versão mais recente: {latest_version}")
                        for page, files in grouped_files[latest_version].items():
                            st.write(f"Página {page}:")
                            for file_path in files:
                                st.write(file_path)
                                with open(file_path, "rb") as file:
                                    st.download_button(label=f"📥 Baixar {os.path.basename(file_path)}", data=file, file_name=os.path.basename(file_path))
                            if len(files) > 1:
                                zip_buffer = create_zip(files)
                                st.download_button(label=f"📦 Baixar todas as páginas - Página {page} - Versão {latest_version}", data=zip_buffer, file_name=f"{drawing_code}-versao-{latest_version}.zip")
                        st.session_state.stop_search = True
                except Exception as e:
                    st.warning(f"⚠️ Rede: {e}")

            # Busca na rede local - FMC
            if not st.session_state.stop_search:
                try:
                    with st.spinner("Buscando na rede local..."):
                        network_path_fmc = r"\\rio-data-srv\arquivo\FMC"
                        local_files_fmc = get_latest_drawing_paths(network_path_fmc, drawing_code, format_drawing_code_fmc)
                        grouped_files = group_files_by_version_and_page(local_files_fmc)
                        latest_version = sorted(grouped_files.keys(), reverse=True)[0]
                        st.success(f"✅ Arquivos da versão mais recente: {latest_version}")
                        for page, files in grouped_files[latest_version].items():
                            st.write(f"Página {page}:")
                            for file_path in files:
                                st.write(file_path)
                                with open(file_path, "rb") as file:
                                    st.download_button(label=f"📥 Baixar {os.path.basename(file_path)}", data=file, file_name=os.path.basename(file_path))
                            if len(files) > 1:
                                zip_buffer = create_zip(files)
                                st.download_button(label=f"📦 Baixar todas as páginas - Página {page} - Versão {latest_version}", data=zip_buffer, file_name=f"{drawing_code}-versao-{latest_version}.zip")
                        st.session_state.stop_search = True
                except Exception as e:
                    st.warning(f"⚠️ Rede: {e}")
        else:
            st.warning("Por favor, insira um código de desenho.")

with col2:
    if st.button("Limpar", use_container_width=True):
        st.session_state.drawing_code = ""
        st.rerun()

with col3:
    if st.button("Parar busca", use_container_width=True):
        st.session_state.stop_search = True


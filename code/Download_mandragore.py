import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from pathlib import Path

def url_to_soup(query:str, page_num) -> BeautifulSoup:
    """
    Envoie une requête GET à l'URL de recherche de Mandragore pour le mot-clé donné.
    Retourne le contenu HTML sous forme d'objet BeautifulSoup.
    
    Paramètres :
    - query (str) : le mot-clé de recherche
    - page_num : numéro de page à récupérer (pagination Mandragore)

    Retour :
    - BeautifulSoup : le contenu HTML parsé, ou None en cas d'erreur réseau/HTTP
    """
    
    # URL de recherche Mandragore construite à partir du mot-clé (query) et de la page demandée
    url = 'https://mandragore.bnf.fr/recherche/avancee?searchData={"formField"%3A[{"critere"%3A"UD_DESCRIPTEUR"%2C"value"%3A"'+query+'"%2C"exactValue"%3Atrue}]%2C"formType"%3A"UD"}&page='+str(page_num)
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup
    
    except requests.exceptions.RequestException as e:
        print(f"Erreur de requête pour l'URL: {url}\n→ {e}")
        return None
    
def get_total_pages(query:str) -> int:
    """
    Détermine dynamiquement le nombre total de pages de résultats pour une requête Mandragore.
    Gère les cas d'absence de résultat, ou de structure HTML variable.

    Paramètres :
    - query (str) : le mot-clé de recherche

    Retour :
    - int : nombre de pages de résultats (0 si aucun)
    """

    soup = url_to_soup(query, page_num=1)
    if soup is None:
        print("❌ Erreur : impossible de charger la page.")
        return 0
    
    # --- Si aucun résultat de recherche ---
    no_result = soup.find("p", id="error-no-result")
    if no_result:
        print(f"🚫 Aucun résultat trouvé pour la requête : '{query}'")
        return 0
    
    # --- Si résultats ---
    try: 
        last_page = soup.find('a', title="Dernière page")
        if last_page:
            onclick = last_page.get("onclick", "")
            last_page_number = re.search(r"changePagination\('(\d+)',", onclick)
            if last_page_number:
                return int(last_page_number.group(1))
        else:
            # Aucun lien "Dernière page" → probablement une seule page
            return 1
    
    except Exception as e:
        print(f"⚠️ Erreur lors de l'analyse de la pagination : {e}")
        return 1  # Retourner au moins une page par défaut

def clean_text(text:str) -> str:
    """
    Nettoie une chaîne de texte en supprimant les caractères de contrôle
    (tabulations, retours à la ligne, retours chariot) et les espaces multiples.

    Paramètres :
    - text (str) : chaîne de texte brute à nettoyer

    Retour :
    - str : texte nettoyé avec un seul espace entre les mots et sans caractères parasites
    """
    
    if not text:
        return ''
    # --- Remplacer les tabulations, retours à la ligne, retour chariot, etc. par un espace ---
    text = re.sub(r'[\t\r\n]+', ' ', text)
    
    # --- Supprimer les espaces en double ou multiples ---
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def retrieve_img_data(query:str, page_num:int) -> list[list[str]]:
    """
    Extrait les données IIIF et les métadonnées associées à chaque image sur une page de résultats.
    Nettoie le texte tout en conservant les caractères spéciaux, et sécurise chaque extraction.

    Paramètres :
    - query (str) : mot-clé de recherche
    - page_num (int) : numéro de page de résultats à analyser

    Retour :
    - list[list[str]] : liste de lignes contenant
      [img_url, manuscrit, folio, légende, texte enluminé, artiste, lieu, date]
    """

    soup = url_to_soup(query, page_num)
    if soup is None:
        print('Impossible d’analyser le contenu de la page : https://mandragore.bnf.fr/recherche/avancee?searchData={"formField"%3A[{"critere"%3A"UD_DESCRIPTEUR"%2C"value"%3A"'+query+'"%2C"exactValue"%3Atrue}]%2C"formType"%3A"UD"}&page='+str(page_num))
        return []

    # --- Récupérer les résultats structurés en deux blocs ---
    # Accès à la ressource image / IIIF
    result_imgs = soup.find_all("div", id="result-img")
    # Accès aux métadonnées textuelles
    result_infos = soup.find_all("div", id="result-infos")

    print(f"🔍 Images trouvées : {len(result_imgs)}")
    print(f"📝 Infos trouvées  : {len(result_infos)}")


    all_data = []

    for idx, (img, info) in enumerate(zip(result_imgs, result_infos)):
        try:
            # --- Image URL ---
            img_target = img.find("input", id=lambda x: x and x.startswith("mirador-"))
            img_iiif = img_target.get('value') if img_target else None

            if not img_iiif:
                print(f"⚠️ Image non disponible pour l’entrée #{idx+1}")
                img_url = "Image non disponible"
            else:
                img_url = f'https://gallica.bnf.fr/iiif/{img_iiif}/full/max/0/default.jpg'

                # HIC SUNT DRACONES
                # Zone instable : stratégie de fallback réseau Gallica → Mandragore
                # (désactivée pour l'instant à cause des limitations de l'API BnF)
                """gallica_url = f'https://gallica.bnf.fr/iiif/{img_iiif}/full/max/0/default.jpg'
                mandragore_url = f'https://mandragore.bnf.fr/iiif/{img_iiif}/full/max/0/default.jpg'

                try:
                    response = requests.get(gallica_url)
                    if response.status_code == 200:
                        img_url = gallica_url
                    else:
                        # Essai Mandragore
                        response_alt = requests.get(mandragore_url)
                        if response_alt.status_code == 200:
                            img_url = mandragore_url
                        else:
                            print(f"⚠️ Image non disponible pour l’entrée #{idx+1}")
                            img_url = "Image non disponible"
                except Exception as e:
                    print(f"❌ Erreur réseau pour l’image #{idx+1} : {e}")
                    img_url = "Image non disponible"""


            # --- Folio + Caption ---
            img_name_tag = info.find_all('a', href=True)
            img_name_raw = img_name_tag[0].text if img_name_tag else ''
            img_name_clean = clean_text(img_name_raw)
            parts = [p.strip() for p in img_name_clean.split(',')]
            img_folio = parts[0].strip() if len(parts) > 0 else ''
            img_caption = parts[1].strip() if len(parts) > 1 else ''

            # --- Métadonnées manuscrit ---
            ms_name = artist = place = date = ''
            img_data = info.find_all('a', href=True)

            # Récupération du nom du manuscrit depuis le <li>
            ms_li = info.find("li", string=lambda s: s and "Manuscrit" in s)
            if ms_li:
                ms_text = ms_li.get_text(" ", strip=True)
                ms_name = re.sub(r"^Manuscrit\s*:\s*", "", ms_text).strip()

            # Récupération du bloc contenant artiste, lieu, date
            if len(img_data) > 1:
                img_detail_raw = img_data[1].text.strip()
                lines = img_detail_raw.splitlines()

                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("-"):
                        cleaned_lines.append(line.lstrip("-").strip())
                    else:
                        if cleaned_lines:
                            cleaned_lines[-1] += " " + line

                # Attribution des champs si disponibles
                artist = cleaned_lines[0] if len(cleaned_lines) > 0 else ''
                place  = cleaned_lines[1] if len(cleaned_lines) > 1 else ''
                date   = cleaned_lines[2] if len(cleaned_lines) > 2 else ''



            # --- Texte enluminé ---
            target_tags = info.find_all('a', href="#")
            if target_tags:
                target_text = clean_text(target_tags[0].get_text(strip=True))
            else:
                target_text = ''

            #  --- Ajout final ---
            all_data.append([img_url, ms_name, img_folio, img_caption, target_text,  artist, place, date])

        except Exception as e:

            print(f"Erreur lors du traitement de l’entrée #{idx} sur la page :" + 'https://mandragore.bnf.fr/recherche/avancee?searchData={"formField"%3A[{"critere"%3A"UD_DESCRIPTEUR"%2C"value"%3A"'+query+'"%2C"exactValue"%3Atrue}]%2C"formType"%3A"UD"}&page='+str(page_num) + f'\n→ {e}')

    return all_data

def browse_results(query: str, output_folder:str) -> None:
    """
    Lance une recherche sur Mandragore, récupère toutes les pages de résultats pour un mot-clé donné,
    extrait les métadonnées des images, puis exporte le tout dans un fichier CSV.

    Paramètres :
    - query (str) : le mot-clé de recherche
    - output_folder (str) : dossier de sortie pour le CSV

    Effets :
    - Affiche les progrès dans la console
    - Crée un fichier CSV nommé 'gallica_data_<query>.csv'
    """
    
    all_data = []

    total_pages = get_total_pages(query)
    if total_pages == 0:
        print(f"Aucun résultat pour la requête : '{query}'. Aucune donnée à exporter.")
        return
    
    print(f"🔍 {total_pages} page(s) trouvée(s) pour la recherche : {query}")

    # Boucle de pagination (1..total_pages inclus)
    for page_num in range(1, total_pages+1):
        print(f"➡️  Traitement de la page {page_num}/{total_pages}.")
        
        try:
            # Extraction des lignes (une ligne par image)
            page_data = retrieve_img_data(query, page_num)
            if page_data:
                all_data.extend(page_data)
            else:
                print(f"⚠️ Aucune donnée extraite sur la page {page_num}")
        
        except Exception as e:
            print(f"❌ Erreur lors du traitement de la page {page_num}: {e}")


    if not all_data:
        print(f"🚫 Aucune donnée récupérée pour la requête '{query}'. Fichier non généré.")
        return


    # --- Export CSV ---
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    output_file = Path(output_folder) / (f'gallica_data_{query}.csv')
    columns = ['img_url', 'manuscrit', 'folio', 'caption', 'texte',  'artiste', 'lieu', 'date']
    df = pd.DataFrame(all_data, columns=columns)
    df.to_csv(output_file, index=False, encoding='utf-8')

    print(f"✅ {len(all_data)} enregistrement(s) exporté(s) dans '{output_file}")

def download_from_list(list_mandragore_file, output_folder) -> None:
    
    with open(list_mandragore_file, 'r') as kw_file:
        for kw in kw_file:
            browse_results(kw.strip(), output_folder)

list_mandragore_file = None
output_folder = None
download_from_list(list_mandragore_file, output_folder)
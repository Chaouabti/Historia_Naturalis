from typing import Any, Iterable
from pathlib import Path
import pandas as pd
import re



# ---------------------------------------
#           Regex compilées
# ---------------------------------------

# Exemple : "XIVe siècle (3e quart)" -> capture "XIV"
RE_ROMAN_CENTURY = re.compile(
    r"\b([IVXLCDM]+)e(?:\s*-\s*[IVXLCDM]+e)?\s+siècle[s]?\b"
)


# Détection explicite "avant Jésus Christ" / "av. J.-C."
RE_BEFORE_CHRIST = re.compile(
    r"(avant\s+J(é|e)sus\s+Christ|av\.\s*J\.-?C\.)",
    flags=re.IGNORECASE
)

# Priorité : prendre l'année après "=" (conversion vers l'ère commune)
# Ex : "Ère séleucide 1957 = 1646" -> capture 1646
RE_EQUALS_YEAR = re.compile(r"=\s*(\d{3,4})")

# Sinon, on prend la première année rencontrée (3 ou 4 chiffres)
# Ex : "1059-1060", "Vers 1250-1275", "Entre 1006 et 1031" -> capture la 1ère année
RE_ANY_YEAR = re.compile(r"\b(\d{3,4})\b")

corrected_dates = {'Copte 2 A': '1375',
 'Français 1': 'Vers 1366-1370',
 'Français 105': '1301-1325',
 'Français 12558': 'XIIIe siècle (mileu ou 3/4 quart)',
 'Français 1281': '1401-1500',
 'Français 1433': '1301-1350',
 'Français 1444': '1201-1300',
 'Français 1463': 'Vers 1273-1300',
 'Français 14649': '1250-1275',
 'Français 156': '1320-1350',
 'Français 157': '1320-1340',
 'Français 161': 'Vers 1200-1399',
 'Français 162': 'Vers 1200-1399',
 'Français 172': '1375-1399',
 'Français 173': '1407',
 'Français 183': '1320-1330',
 'Français 184': '1402-1415',
 'Français 1847': '1401-1500',
 'Français 2': 'XIVe siècle (3e quart)',
 'Français 208': '1370-1399',
 'Français 22533': 'Vers 1372-1499',
 'Français 235': 'XVe siècle',
 'Français 236': 'XVe siècle',
 'Français 24383': '1401-1500',
 'Français 2634': '1310-1325',
 'Français 264': '1405-1415',
 'Français 2823': '1501-1600',
 'Français 290': '1405-1410',
 'Français 296': '1401-1500',
 'Français 297': '1401-1500',
 'Français 298': '1401-1500',
 'Français 299': '1401-1500',
 'Français 302': '1401-1500',
 'Français 303': '1401-1500',
 'Français 339': 'Vers 1250',
 'Français 377': '1401-1500',
 'Français 387': '1401-1500',
 'Français 400': '1301-1400',
 'Français 402': '1401-1500',
 'Français 405': 'XVe siècle',
 'Français 406': 'XVe siècle',
 'Français 55': '1467-1475',
 'Français 56': 'XVe siècle',
 'Français 57': 'XVe siècle',
 'Français 5715': '1520-1522',
 'Français 58': 'XVe siècle',
 'Français 726': 'XIIIe siècle',
 'Français 773': 'Vers 1250-1275',
 'Français 78': 'XVe-XVIe siècles',
 'Français 79': 'XVe siècle',
 'Français 87': 'XVe siècle',
 'Français 9083': '1325-1350',
 'Grec 2180': '1401-1500',
 'Italien 1698': '1471-1500',
 'Italien 543': '1325-1370',
 'Latin 10526': 'XIIIe siècle (début ou 1er quart)',
 'Latin 10603': 'XIIe siècle',
 'Latin 1079': '1101-1200',
 'Latin 1121': '1401-1500',
 'Latin 11249': '1701-1800',
 'Latin 1152': 'Vers 842-869',
 'Latin 11565': 'XIIe siècle',
 'Latin 12610': 'Vers 1030-1060',
 'Latin 13152': 'XIIIe siècle',
 'Latin 14389': 'Vers 1375-1400',
 'Latin 14390': 'Vers 1300',
 'Latin 14513, F. 1-152': 'XIIe siècle',
 'Latin 14693, F. 53-104': 'XIVe siècle',
 'Latin 14786': 'Vers 1175-1200',
 'Latin 15211': 'XIIIe siècle',
 'Latin 15675': '1175-1200',
 'Latin 16': '1275-1400',
 'Latin 16187': '1150-1199',
 'Latin 16386': 'XIIIe siècle (3e quart)',
 'Latin 1651': 'XIIe siècle (3e quart)',
 'Latin 16724': '1623',
 'Latin 16794': '1601-1700',
 'Latin 16895': '1601-1700',
 'Latin 16896': '1201-1300',
 'Latin 16913': '1275-1300',
 'Latin 17155': '1301-1325',
 'Latin 17246': '1160-1180',
 'Latin 17950': '1225-1250',
 'Latin 2232': '1401-1500',
 'Latin 226': 'Vers 1415-1420',
 'Latin 2288': 'Vers 1150-1175',
 'Latin 232': 'XIIIe siècle',
 'Latin 2422': '822-847',
 'Latin 312': '1101-1200',
 'Latin 3903': '1301-1400',
 'Latin 3908': '1301-1400',
 'Latin 4535': 'Vers 1375-1400',
 'Latin 458': '1401-1500',
 'Latin 4594': '1280-1340',
 'Latin 5302': 'Vers 1175-1200',
 'Latin 5304, F. 1-60': 'XIe siècle',
 'Latin 5304, F. 164-267': 'XIe-XIIe siècles',
 'Latin 6 (3)': 'Vers 1035-1100',
 'Latin 6322': '1301-1400',
 'Latin 667': '1470-1490',
 'Latin 7544': '1201-1300',
 'Latin 760': '1301-1400',
 'Latin 7732': '1201-1260',
 'Latin 8055, pp. 1-140': 'XIe siècle',
 'Latin 9716': 'Vers 1101-1200',
 'Latin 9740': '1101-1200',
 'Mexicain 46-58': 'XVIe siècle (3e quart)',
 'Mexicain 59-64': '1501-1600',
 'Ms-3325': 'Vers 1250-1299',
 'NAL 299': 'Vers 1225-1275',
 'NAL 3099': '1401-1500',
 'NAL 779': 'XIVe siècle',
 'Persan 257': 'Vers 1515-1575',
 'Smith-Lesouëf 3': 'XIe siècle',
 'Supplément Persan 1962': 'XVIe siècle (3e quart)'
 }

dates_to_clean = [
'1er-2e quart',
'1re moitié-milieu',
'2e moitié-fin',
'2e quart-milieu',
'2e-3e quart',
'3e-4e quart',
'3e-4e quart du XVe siècle',
'4e quart-fin',
'Début-1er quart',
'Début-1re moitié',
'Milieu-2e moitié',
'Milieu-3e quart'
]

egyptian_dynasty =  {'19e dynastie égyptienne' : '1296/92–1188 avant Jésus Christ',
  '20e dynastie égyptienne' : '1188–1069 avant Jésus Christ',
  '21e dynastie égyptienne' : '1069–943 avant Jésus Christ'}

def clean_kw(file: str | Path) -> None:
    """
    Nettoie un fichier texte de mots-clés en remplaçant les '+' par des espaces.
    Réécrit le même fichier (overwrite).

    Paramètres :
    - file : chemin du fichier contenant 1 mot-clé par ligne (str ou Path)

    Effets :
    - Remplace tous les '+' par ' ' dans le fichier
    - Écrase le fichier d'origine avec la version nettoyée
    """
    new_kw_list = []
    with open(file, 'r') as kws:
        for kw in kws:
            new_kw = kw.replace('+', ' ')
            new_kw_list.append(new_kw)

    with open(file, 'w') as kw_cleaned:
        kw_cleaned.writelines(new_kw_list)

def clean_csv(nh_folder: str | Path) -> None:

    """
    Parcourt tous les fichiers du dossier et remplace les ';' par ':' dans leur contenu.
    Réécrit chaque fichier sur place.

    Paramètres :
    - nh_folder : dossier contenant les fichiers à nettoyer (str ou Path)

    Effets :
    - Pour chaque fichier du dossier : remplace ';' par ':' puis écrase le fichier
    - Affiche l'avancement dans la console
    """
    
    nh_folder = Path(nh_folder)
    csv_files = [f for f in nh_folder.iterdir() if f.suffix.lower() == '.csv']

    for file in csv_files:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()

        # Remplace les ; par :
        content = content.replace(";", ":")

        # Réécrit le fichier propre
        with open(file, "w", encoding="utf-8") as f:
            f.write(content)
            print(f"Fichier nettoyé: {file}")

    print("Nettoyage terminé : tous les ';' ont été remplacés par ':'")

def merge_csv(nh_folder: str | Path) -> None:
    """
    Fusionne tous les fichiers CSV d'un dossier en un seul fichier, en ajoutant :
    - une colonne 'mot_cle' (dérivée du nom de fichier)
    - une colonne 'ms_folio' = manuscrit + ':' + folio

    Paramètres :
    - nh_folder : dossier contenant les CSV d'entrée (str ou Path)

    Effets :
    - Crée un fichier "mandragore_nh_global.csv" dans le dossier nh_folder
    - Écrit le CSV fusionné avec séparateur ';'
    """
    
    nh_folder = Path(nh_folder)
    output_file =  nh_folder / "mandragore_nh_global.csv"
    csv_list = []

    for file in nh_folder.iterdir():
        if file.suffix.lower() != '.csv':
            continue
        
        df = pd.read_csv(file, sep=',')
        mot_cle = file.stem.split('_')[-1]
        df['mot_cle'] = mot_cle
        df['ms_folio'] = df.manuscrit + ':' + df.folio

        csv_list.append(df)

    # Concatène tous les DataFrames
    df_merged = pd.concat(csv_list, ignore_index=True)

    # Sauvegarde en un seul CSV
    df_merged.to_csv(output_file, index=False, sep=';')
    print(f"Fichier fusionné créé : {output_file}")

def fill_empty_cells(nh_folder: str | Path) -> None:
    """
    Lit le fichier CSV global et normalise les cellules vides.
    Réécrit le fichier sur place avec les valeurs par défaut.

    Paramètres :
    - nh_folder : dossier contenant le fichier CSV global (str ou Path)

    Effets :
    - Remplace les valeurs vides ou manquantes dans certaines colonnes
    - Affecte des valeurs par défaut (lieu, date, artiste)
    - Écrase le fichier CSV d’origine avec la version corrigée
    - Affiche un message de confirmation dans la console
    """

    csv = Path(nh_folder) / "mandragore_nh_global.csv"

    df = pd.read_csv(csv, sep=';')

    # Valeurs à considérer comme vides
    EMPTY_VALUES = ["", " ", "  ", "nan", "NaN", "None"]

    # Remplacements par colonne
    FILL_VALUES = {
        "lieu": "Origine inconnue",
        "date": "Date inconnue",
        "artiste": "Artiste non identifié",
    }

    for col, fill_value in FILL_VALUES.items():
        df[col] = (
            df[col]
            .replace(EMPTY_VALUES, pd.NA)
            .fillna(fill_value)
        )

    df.to_csv(csv, index=False, sep=";")
    print(f"Fichier mis à jour : {csv}")

def fix_dates(corrected_dates: dict[str, str],
              dates_to_clean: list[str],
              egyptian_dynasty: dict[str, str],
              nh_folder: str | Path) -> None:
   """
    Nettoie et normalise la colonne 'date' du fichier CSV global.
    Réécrit le fichier sur place avec les dates corrigées.

    Paramètres :
    - corrected_dates : dictionnaire associant un manuscrit à une date corrigée (dict)
    - dates_to_clean : liste des valeurs de date à remplacer (list)
    - egyptian_dynasty : dictionnaire des dynasties égyptiennes et de leurs périodes (dict)
    - nh_folder : dossier contenant le fichier CSV global (str ou Path)

    Effets :
    - Transforme les dynasties égyptiennes en "dynastie = période"
    - Remplace certaines dates imprécises à partir du manuscrit correspondant
    - Écrase le fichier CSV d’origine avec la version corrigée
    - Affiche un message de confirmation dans la console
    """

    
   csv_path = Path(nh_folder) / "mandragore_nh_global.csv"
   df = pd.read_csv(csv_path, sep=";")

   # --- 1) Ajout des chronologies pour dynasties égyptiennes ---
   mask_egypt = df["date"].isin(egyptian_dynasty.keys())

   df.loc[mask_egypt, "date"] = (
      df.loc[mask_egypt, "date"]
      + " = "
      + df.loc[mask_egypt, "date"].map(egyptian_dynasty)
   )

   # --- 2) Remplacement des dates "à nettoyer" via le manuscrit ---
   mask_clean = df["date"].isin(dates_to_clean)

   df.loc[mask_clean, "date"] = df.loc[mask_clean, "manuscrit"].map(corrected_dates)

   df.to_csv(csv_path, index=False, sep=";")
   print(f"Dates corrigées dans : {csv_path}")

   # return df

def int_to_roman(n: int) -> str:
    """
    Convertit un entier en chiffres romains.

    Paramètres :
    - n : nombre entier positif à convertir (int)

    Retour :
    - Chaîne représentant le nombre en chiffres romains (str)
    """

    vals = [1000,900,500,400,100,90,50,40,10,9,5,4,1]
    syms = ["M","CM","D","CD","C","XC","L","XL","X","IX","V","IV","I"]
    out = []
    for v, s in zip(vals, syms):
        while n >= v:
            n -= v
            out.append(s)
    return "".join(out)

def year_to_century_ec(year: int) -> str:
    """
    Convertit une année de l’ère commune en siècle exprimé en chiffres romains.

    Paramètres :
    - year : année en ère commune (int)

    Retour :
    - Chaîne représentant le siècle correspondant, au format « XVe siècle » (str)
    """

    # 1-100 -> I, 101-200 -> II, etc.
    century = (year - 1) // 100 + 1
    return f"{int_to_roman(century)}e siècle"

def extract_century(date_value: Any) -> str:
    """
    Extrait et normalise un siècle à partir d'une date textuelle hétérogène.

    Paramètres :
    - date_value : valeur de la colonne 'date' (str, NaN, etc.)

    Retour :
    - "XIVe siècle" : siècle normalisé (sans quart, tiers ou précision)
    - "AEC" : si la date est explicitement avant l’ère commune
    - "Date inconnue" : si la valeur est absente ou non exploitable

    Règles :
    - Conserve "Date inconnue" tel quel
    - Détecte explicitement les dates avant Jésus-Christ
    - Priorise un siècle déjà exprimé en chiffres romains
    - Priorise une conversion explicite de type "= 1591"
    - À défaut, utilise la première année rencontrée pour calculer le siècle
    """


    # 0) Cas des vraies valeurs manquantes pandas (NaN)
    if pd.isna(date_value):
        return "Date inconnue"

    # 1) On normalise la valeur en chaîne et on enlève les espaces superflus
    s = str(date_value).strip()

    # 2) "Date inconnue" doit rester tel quel
    if "Date inconnue" in s:
        return "Date inconnue"

    # 3) Si c'est explicitement avant l'ère commune -> "AEC"
    #    (ex : "XIIe-XIe siècles avant Jésus Christ" ou dynasties égyptiennes)
    if RE_BEFORE_CHRIST.search(s):
        return "AEC"

    # 4) Si la chaîne contient déjà un siècle romain, on le garde (sans précision)
    #    Ex : "XIVe siècle (3e quart)" -> "XIVe siècle"
    m = RE_ROMAN_CENTURY.search(s)
    if m:
        return f"{m.group(1)}e siècle"

    # 5) Priorité à l'année après "="
    #    Ex : "Hégire 1000 = 1591-1592" -> 1591 -> XVIe siècle
    m = RE_EQUALS_YEAR.search(s)
    if m:
        year = int(m.group(1))
        return year_to_century_ec(year)

    # 6) Sinon on prend la première année trouvée
    #    Ex : "1101-1200" -> 1101 -> XIIe siècle
    #         "Entre 779 et 797" -> 779 -> VIIIe siècle
    m = RE_ANY_YEAR.search(s)
    if m:
        year = int(m.group(1))
        return year_to_century_ec(year)

    # 7) Sinon, rien d'exploitable
    return "Date inconnue"

def clean_century(nh_folder: str | Path) -> None:
    """
    Ajoute une colonne 'siecle' calculée à partir de la colonne 'date',
    insérée immédiatement après celle-ci.

    Paramètres :
    - nh_folder : dossier contenant le fichier CSV Mandragore (str ou Path)

    Effets :
    - Calcule le siècle pour chaque ligne à partir de la colonne 'date'
    - Insère la colonne 'siecle' juste après la colonne 'date'
    - Réécrit le fichier CSV avec la colonne ajoutée
    """


    csv_path = Path(nh_folder) / "mandragore_nh_global.csv"
    df = pd.read_csv(csv_path, sep=";")

    # 1) Calcul des siècles à partir de la colonne date
    siecles = df["date"].apply(extract_century)

    # 2) Si la colonne existe déjà, on la supprime pour réinsérer au bon endroit
    if "siecle" in df.columns:
        df = df.drop(columns=["siecle"])

    # 3) Trouver l'index de la colonne date
    date_idx = df.columns.get_loc("date")

    # 4) Insérer juste après
    df.insert(date_idx + 1, "siecle", siecles)

    df.to_csv(csv_path, index=False, sep=";")
    print(f"Colonne 'siecle' ajoutée dans : {csv_path.name}")
    # return df

def build_parent_country_map(lieux: Iterable[Any]) -> dict[str, str]:
    """
    Construit un dictionnaire de correspondance lieu → pays/région
    à partir des formes explicites de type « X (Y) » présentes dans le corpus.

    Paramètres :
    - lieux : ensemble des valeurs de la colonne 'lieu' (itérable de str)

    Retour :
    - Dictionnaire associant un lieu de base à un pays ou une région (dict[str, str])

    Règles :
    - Ignore les parenthèses non informatives (directions, « et al. »)
    - Conserve la première association rencontrée pour un même lieu
    """

    mapping = {}

    for lieu in lieux:
        if pd.isna(lieu):
            continue

        s = str(lieu).strip()

        # on ignore les cas sans parenthèses
        if "(" not in s:
            continue

        lieu_base, parenthese = s.split("(", 1)
        lieu_base = lieu_base.strip()
        contenu_parenthese = parenthese.split(")", 1)[0].strip()

        contenu_parenthese_min = contenu_parenthese.lower()

        # ignorer les parenthèses non informatives
        if contenu_parenthese_min in {"et al.", "et al"}:
            continue

        if contenu_parenthese_min in {
            "sud", "nord", "est", "ouest", "centre",
            "sud-est", "nord-est", "sud-ouest", "nord-ouest"
        }:
            continue

        # cas "région, pays"
        if "," in contenu_parenthese:
            pays = contenu_parenthese.split(",")[-1].strip()
        else:
            pays = contenu_parenthese

        # on n’écrase pas une valeur déjà existante
        mapping.setdefault(lieu_base, pays)

    return mapping

def extract_country(lieux: Iterable[Any], parent_map: dict[str, str]) -> list[str]:
    """
    Extrait un pays ou une région à partir d'une liste de lieux,
    en s'appuyant sur un référentiel interne lieu → pays/région.

    Paramètres :
    - lieux : valeurs de la colonne 'lieu' (itérable de str)
    - parent_map : dictionnaire de correspondance lieu → pays/région

    Retour :
    - Liste des pays ou régions extraits, dans le même ordre que les lieux (list[str])

    Règles :
    - Utilise en priorité l'information contenue dans les parenthèses
    - Ignore les parenthèses non informatives (directions, « et al. »)
    - À défaut, applique le référentiel interne construit à partir du corpus
    """

    out = []

    for lieu in lieux:
        if pd.isna(lieu):
            out.append("Origine inconnue")
            continue

        s = str(lieu).strip()

        # enlever un éventuel suffixe "(et al.)"
        s = re.sub(r"\s*\(et al\.\)\s*$", "", s, flags=re.IGNORECASE)

        # --- CAS 1 : parenthèses présentes ---
        if "(" in s:
            lieu_base, parenthese = s.split("(", 1)
            lieu_base = lieu_base.strip()
            contenu_parenthese = parenthese.split(")", 1)[0].strip()

            contenu_parenthese_min = contenu_parenthese.lower()

            # directions → on garde ce qu’il y a lieu_base
            if contenu_parenthese_min in {
                "sud", "nord", "est", "ouest", "centre",
                "sud-est", "nord-est", "sud-ouest", "nord-ouest"
            }:
                out.append(lieu_base)
                continue

            # "région, pays"
            if "," in contenu_parenthese:
                out.append(contenu_parenthese.split(",")[-1].strip())
            else:
                out.append(contenu_parenthese)
            continue

        # --- CAS 2 : pas de parenthèses ---
        racine = s.split(",", 1)[0].strip()

        # si le référentiel interne connaît ce lieu
        if racine in parent_map:
            out.append(parent_map[racine])
        else:
            out.append(racine)

    return out

def clean_places(nh_folder: str| Path) -> None:
    """
    Lit le fichier CSV Mandragore et ajoute une colonne 'pays_region'
    extraite de la colonne 'lieu', insérée immédiatement après celle-ci.

    Paramètres :
    - nh_folder : dossier contenant le fichier CSV Mandragore (str ou Path)

    Effets :
    - Construit un référentiel interne lieu → pays/région
    - Calcule la colonne 'pays_region' à partir de la colonne 'lieu'
    - Réécrit le fichier CSV avec la colonne ajoutée
    """

    csv_path = Path(nh_folder) / "mandragore_nh_global.csv"
    df = pd.read_csv(csv_path, sep=";")

    # construction du référentiel interne
    parent_map = build_parent_country_map(df["lieu"])

    # extraction finale
    pays = extract_country(df["lieu"], parent_map)

    # suppression si la colonne existe déjà
    if "pays_region" in df.columns:
        df = df.drop(columns=["pays_region"])

    # insertion juste après 'lieu'
    idx = df.columns.get_loc("lieu")
    df.insert(idx + 1, "pays_region", pays)


    df.to_csv(csv_path, index=False, sep=";")
    print(f"Colonne 'pays_region' ajoutée dans : {csv_path.name}")
    # return df




if __name__ == "__main__":
    nh_folder = Path(input("Entrez le chemin : ").strip())
    
    if not nh_folder.exists():
        raise FileNotFoundError(f"Dossier introuvable : {nh_folder}")
    
    clean_csv(nh_folder)
    merge_csv(nh_folder)
    fill_empty_cells(nh_folder)
    fix_dates(corrected_dates, dates_to_clean, egyptian_dynasty, nh_folder)
    clean_century(nh_folder)
    clean_places(nh_folder)
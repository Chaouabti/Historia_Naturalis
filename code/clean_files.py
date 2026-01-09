from pathlib import Path
import pandas as pd

def clean_kw(file):
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

    with open(file, 'w') as clean_kw:
        clean_kw.writelines(new_kw_list)

def clean_csv(nh_folder):
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
    csv_files = [file for file in nh_folder.iterdir()]

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

def merge_csv(nh_folder):
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
    
    output_file = Path(nh_folder) / "mandragore_nh_global.csv"
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


nh_folder = None
merge_csv(nh_folder)
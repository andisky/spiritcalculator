import streamlit as st
import pandas as pd
import re
import urllib.error
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# Seiten-Layout einstellen
st.set_page_config(page_title="Spirit Calculator", layout="wide")

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("Spirit Calculator")

# Eingabefeld für den Link
sheet_url = st.text_input("Google Sheets Link:", placeholder="enter Link")

if sheet_url:
    # 1. IDs aus dem Link extrahieren (mit Regular Expressions)
    sheet_id_match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
    gid_match = re.search(r"gid=([0-9]+)", sheet_url)

    if not sheet_id_match:
        st.error("Konnte keine gültige Sheet-ID im Link finden. Bitte überprüfe den Link.")
    else:
        sheet_id = sheet_id_match.group(1)
        gid = gid_match.group(1) if gid_match else "0" 

        # 2. Export-URL für Pandas zusammenbauen
        csv_export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

        try:
            with st.spinner("Calculating..."):
                # 3. Daten laden
                spirit_scores_df = pd.read_csv(csv_export_url)

                # Zur Sicherheit: Nur die ersten 9 Spalten nehmen, falls das Sheet extra Spalten am Ende hat
                spirit_scores_df = spirit_scores_df.iloc[:, :9]
                
                # Deine Spalten-Zuweisung
                spirit_scores_df.columns = ["Zeitstempel", "Your Team", "Your Opponent", "Rules Knowledge and Use", "Fouls and Body Contact", "Positive Attitute and Self-Control", "Fair-Mindedness", "Communication", "Comments"]
                spirit_scores_df = spirit_scores_df.drop("Zeitstempel", axis=1)

                # Robustheits-Check: Falls im Formular "2 - Good" statt nur "2" steht, 
                # extrahieren wir automatisch nur die Zahl, damit '.mean()' nicht abstürzt.
                score_columns = ["Rules Knowledge and Use", "Fouls and Body Contact", "Positive Attitute and Self-Control", "Fair-Mindedness", "Communication"]
                for col in score_columns:
                    spirit_scores_df[col] = pd.to_numeric(spirit_scores_df[col].astype(str).str.extract(r'(\d+)')[0], errors='coerce')

                # Deine Berechnungs-Logik
                spirit_scores_ranking = spirit_scores_df.groupby(["Your Opponent"]).agg(
                    Rules_Knowledge_and_Use=pd.NamedAgg(column="Rules Knowledge and Use", aggfunc="mean"),
                    Fouls_and_Body_Contact=pd.NamedAgg(column="Fouls and Body Contact", aggfunc="mean"),
                    Positive_Attitute_and_Self_Control=pd.NamedAgg(column="Positive Attitute and Self-Control", aggfunc="mean"),
                    Fair_Mindedness=pd.NamedAgg(column="Fair-Mindedness", aggfunc="mean"),
                    Communication=pd.NamedAgg(column="Communication", aggfunc="mean")
                )

                spirit_scores_ranking["Spirit Gesamt"] = spirit_scores_ranking[["Rules_Knowledge_and_Use", "Fouls_and_Body_Contact", "Positive_Attitute_and_Self_Control", "Fair_Mindedness", "Communication"]].sum(axis=1)
                
                spirit_scores_ranking = spirit_scores_ranking[["Spirit Gesamt", "Rules_Knowledge_and_Use", "Fouls_and_Body_Contact", "Positive_Attitute_and_Self_Control", "Fair_Mindedness", "Communication"]].sort_values("Spirit Gesamt", ascending=False).reset_index()
                spirit_scores_ranking.columns = [col.replace("_", " ") for col in spirit_scores_ranking.columns]
                spirit_scores_ranking = spirit_scores_ranking.rename(columns={"Your Opponent": "Team Name"}).set_index("Team Name")

                # 4. Erfolgsmeldung und Ausgabe
                st.success("Results:")
                
                # Tabelle schön formatiert ausgeben (Werte auf 2 Nachkommastellen runden)
                st.dataframe(
                    spirit_scores_ranking.style.format("{:.2f}"), 
                    use_container_width=True,
                    height=500
                )

        except urllib.error.HTTPError as e:
            if e.code in [401, 403]:
                st.error("Google Sheet is private")
            elif e.code == 404:
                st.error("Link not correct")
            else:
                st.error(f"HTTP Fehler: {e}")
        except Exception as e:
            st.error(f"Error: Are to column names correct?")

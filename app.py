import requests
from bs4 import BeautifulSoup
import pandas as pd
import psycopg2
import streamlit as st
import plotly.express as px
import time
from datetime import datetime
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os
import base64
from pathlib import Path
from streamlit.components.v1 import html
from pyngrok import ngrok


# Configuration Ngrok
public_url = ngrok.connect(8501)  # Ouvre un tunnel vers votre port Streamlit
st.write(f"## Lien public temporaire : [{public_url}]({public_url})")

# Votre application normale...
st.title("KTRIX - Tableau de Bord")
# ... (le reste de votre code)
# Configuration de la page
st.set_page_config(layout="wide", page_title="KTRIX - Scraping de Données Livresques", page_icon="📚")

# CSS personnalisé
st.markdown("""
<style>
.metric-card {
    background-color: #262730;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 20px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
.progress-text {
    font-size: 18px;
    text-align: center;
    margin-top: 10px;
    color: #4CAF50;
}
.presentation-header {
    color: #4CAF50;
    font-weight: bold;
}
.logo-container {
    text-align: center;
    margin-bottom: 20px;
}
.founder-card {
    background-color: #2E2E3A;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 15px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
.sidebar-logo {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 15px;
}
.sidebar-logo img {
    border-radius: 10px;
    box-shadow: 0px 2px 4px rgba(255,255,255,0.1);
    margin-bottom: 5px;
}
.sidebar-title {
    color: #4A00E0;
    font-weight: bold;
    text-align: center;
    margin-bottom: 5px;
}
.sidebar-subtitle {
    color: #CCCCCC;
    font-size: 12px;
    font-style: italic;
    text-align: center;
    margin-top: -5px;
}
.founder-img {
    border-radius: 10px;
    border: 2px solid #4A00E0;
    margin-bottom: 10px;
}
.founder-container {
    display: flex;
    margin-bottom: 20px;
    align-items: center;
}
</style>
""", unsafe_allow_html=True)

# Logo KTRIX dans la sidebar
def display_logo():
    """Affiche le logo KTRIX dans la sidebar"""
    chemin_logo = Path(__file__).parent / "KTRIX.jpg"
    
    if chemin_logo.exists():
        with open(chemin_logo, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()
        
        st.sidebar.markdown(
            f"""
            <div class="sidebar-logo">
                <img src="data:image/jpg;base64,{img_base64}" width="120">
                <div class="sidebar-title">KTRIX</div>
                <div class="sidebar-subtitle">Data Scraping Intelligent</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.sidebar.error("⚠ Logo non trouvé")

# Variables globales pour la progression
progress_bar = None
status_container = None

# Fonction pour afficher la progression du scraping
def display_scraping_progress(current, total, start_time):
    progress = current / total
    elapsed_time = time.time() - start_time
    estimated_time = (elapsed_time / current) * (total - current) if current > 0 else 0
    
    progress_bar.progress(progress)
    
    with status_container:
        col1, col2, col3 = st.columns(3)
        col1.metric("Pages traitées", f"{current}/{total}")
        col2.metric("Progression", f"{progress*100:.1f}%")
        col3.metric("Temps estimé", f"{estimated_time:.1f}s restantes")
        
        time.sleep(0.01)

# Fonction de web scraping
def webscraping():
    base_url = "https://books.toscrape.com/catalogue/category/books_1/page-{}.html"
    total_pages = 50
    books_data = []
    start_time = time.time()
    
    global progress_bar, status_container
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    for page_number in range(1, total_pages + 1):
        try:
            response = requests.get(base_url.format(page_number))
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            books = soup.find_all('article', class_='product_pod')
            
            for book in books:
                name = book.h3.a['title']
                price = book.find('p', class_='price_color').text.strip()
                stock_status = book.find('p', class_='instock availability').text.strip()
                
                books_data.append({
                    'Nom': name,
                    'Prix': price.replace('£', ''),
                    'État': stock_status,
                    'Date Scraping': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            
            display_scraping_progress(page_number, total_pages, start_time)
            time.sleep(0.1)
            
        except Exception as e:
            st.error(f"Erreur page {page_number}: {str(e)}")
            continue
    
    progress_bar.empty()
    status_container.empty()
    
    if books_data:
        df = pd.DataFrame(books_data)
        df["Prix"] = df["Prix"].astype(float)
        st.session_state['df'] = df
        st.success(f"Scraping terminé! {len(df)} livres extraits.")
        return df
    else:
        st.error("Aucune donnée n'a pu être récupérée.")
        return None

# Fonction tableau de bord
def tableau_de_bord(df):
    st.title("📊 Tableau de Bord")

    # Section 1 : Indicateurs Clés
    st.header("📌 Indicateurs Clés")
    col1, col2, col3 = st.columns(3)
    col1.metric("📖 Livres Totaux", len(df))
    col2.metric("💰 Prix Moyen (£)", f"£{df['Prix'].mean():.2f}")
    col3.metric("✅ En Stock", df[df['État'] == 'In stock'].shape[0])

    # Section 2 : Graphiques
    st.header("📊 Visualisations")
    onglet1, onglet2, onglet3, onglet4, onglet5 = st.tabs(
        ["📉 Répartition des prix", "🏆 Top Livres", "📦 Stock", "📈 Évolution", "☁ Nuage de Mots"]
    )

    with onglet1:
        fig1 = px.histogram(df, x="Prix", nbins=20, title="Répartition des Prix des Livres")
        st.plotly_chart(fig1, use_container_width=True)

    with onglet2:
        top_books = df.sort_values("Prix", ascending=False).head(10)
        fig2 = px.bar(top_books, x="Nom", y="Prix", color="Prix", title="Top 10 des Livres les Plus Chers")
        st.plotly_chart(fig2, use_container_width=True)

    with onglet3:
        stock_status = df['État'].value_counts().reset_index()
        fig3 = px.pie(stock_status, values='count', names='État', title="Stock Disponible et Épuisé")
        st.plotly_chart(fig3, use_container_width=True)

    with onglet4:
        df['Date Scraping'] = pd.to_datetime(df['Date Scraping'])
        df_trend = df.groupby(df['Date Scraping'].dt.date)['Prix'].mean().reset_index()
        fig4 = px.line(df_trend, x='Date Scraping', y='Prix', markers=True, title="Évolution des Prix Moyens")
        st.plotly_chart(fig4, use_container_width=True)

    with onglet5:
        text = ' '.join(df['Nom'])
        wordcloud = WordCloud(width=800, height=400, background_color="black", colormap="coolwarm").generate(text)
        fig5, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig5)

    # Section 3 : Filtrage et Recherche (CORRIGÉ)
    st.header("🔍 Recherches et Filtres")
    titre_recherche = st.text_input("Rechercher un titre :", "")
    
    # Correction du slider
    prix_range = st.slider(
        "Filtrer par prix (£)",
        float(df['Prix'].min()),
        float(df['Prix'].max()),
        (float(df['Prix'].min()), float(df['Prix'].max()))
    )
    prix_min, prix_max = prix_range

    df_filtré = df[(df['Prix'] >= prix_min) & (df['Prix'] <= prix_max)]
    if titre_recherche:
        df_filtré = df_filtré[df_filtré['Nom'].str.contains(titre_recherche, case=False)]
    st.dataframe(df_filtré)

    # Section 4 : Tableau des Données
    st.header("📜 Données Complètes")
    st.dataframe(df.sort_values("Prix", ascending=False), use_container_width=True)

# Fonction PostgreSQL
def connect_to_postgresql(df, host, database, user, password):
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id SERIAL PRIMARY KEY,
                Nom VARCHAR(255),
                Prix FLOAT,
                État VARCHAR(255),
                date_scraping TIMESTAMP
            )
        """)
        conn.commit()

        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO books (Nom, Prix, État, date_scraping)
                VALUES (%s, %s, %s, %s)
            """, (row['Nom'], row['Prix'], row['État'], row['Date Scraping']))

        conn.commit()
        cur.close()
        conn.close()

        st.success("Données sauvegardées dans PostgreSQL avec succès!")
        return True

    except Exception as e:
        st.error(f"Erreur PostgreSQL: {str(e)}")
        return False

# Fonction pour afficher les fondateurs avec leurs photos (CORRIGÉE)
def display_founders():
    st.header("📸 Présentation des Fondateurs")
    
    # Chemin absolu sécurisé
    BASE_DIR = Path(__file__).parent
    PHOTOS_DIR = BASE_DIR / "photos"
    
    founders = [
        {
            "name": "Adou Brin Jean Marc", 
            "tel": "0758922534", 
            "mail": "jeanmarcadou1@gmail.com",
            "profession": "Data Science student at INSSEDS",
            "photo": "jean_marc.jpg"
        },
        {
            "name": "Dadie Zihon Jeanne Emmanuella", 
            "tel": "0506137884", 
            "mail": "emmanuellada30@gmail.com",
            "profession": "Data Science student at INSSEDS", 
            "photo": "jeanne_emmanuella.jpg"
        },
        {
            "name": "N'dri Abo Onesim", 
            "tel": "0768059887", 
            "mail": "ndriablatie123@gmail.com",
            "profession": "Data Science student at INSSEDS", 
            "photo": "onesim.jpg"
        },
        {
            "name": "Sie Esmel Aicha Meliane", 
            "tel": "0503360203", 
            "mail": "sieesmelaicha@gmail.com",
            "profession": "Data Science student at INSSEDS", 
            "photo": "aicha_meliane.jpg"
        },
        {
            "name": "Hie Yagba Beranger", 
            "tel": "0777457755", 
            "mail": "Yagbaberangerh@gmail.com",
            "profession": "Data Science student at INSSEDS", 
            "photo": "beranger.jpg"
        },
        {
            "name": "Dembele Kassoum", 
            "tel": "0558320743", 
            "mail": "Dkasso7991@gmail.com",
            "profession": "Data Science student at INSSEDS", 
            "photo": "kassoum.jpg"
        },
    ]

    for founder in founders:
        with st.container():
            col1, col2 = st.columns([1, 3])
            
            # Chemin corrigé
            photo_path = PHOTOS_DIR / founder['photo']
            
            if photo_path.exists():
                col1.image(str(photo_path), width=150)
            else:
                col1.error(f"❌ Photo non trouvée : {photo_path}")
            
            col2.markdown(
                f"""
                <div class='founder-card'>
                    <h4>{founder['name']}</h4>
                    <p>📞 Tel : {founder['tel']}</p>
                    <p>📧 Mail : {founder['mail']}</p>
                    <p>👨‍🎓 Profession : {founder['profession']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.markdown("---")

# Page À propos
def about_page():
    st.title("À propos")
    display_founders()

# Page Présentation
def presentation_page():
    st.title("PRÉSENTATION DE « KTRIX »", anchor=False)
    
    st.markdown("""
    <div class='presentation-header'>
    KTRIX est une application web intuitive conçue pour simplifier l'extraction automatisée de données livresques à partir de sources en ligne.
    </div>
    
    Développée avec Streamlit, elle permet même aux non-techniciens d'effectuer du scraping, de visualiser des analyses et d'exporter les résultats 
    en quelques clics, le tout sans écrire une seule ligne de code.
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.header("Fonctionnalités Principales")
    
    with st.expander("1. Scraping Automatisé en Temps Réel", expanded=True):
        st.markdown("""
        - **Simple et rapide** : Lancement en un clic
        - **Progression visuelle** :
        - Barre de progression (%)
        - Compteur de pages traitées (ex: 25/50)
        - Temps restant estimé
        - **Données extraites** :
        - Titres
        - Prix
        - Disponibilité
        - Horodatage automatique
        """)
    
    with st.expander("2. Tableau de Bord Analytique"):
        st.markdown("""
        Visualisez les données scrapées via :
        - **KPI clés** :
        - Nombre de livres
        - Prix moyen
        - Taux de disponibilité
        - **Graphiques interactifs** :
        - Histogramme des prix
        - Top 10 des livres les plus chers
        - Répartition du stock (disponible/épuisé)
        - **Tableau triable** pour explorer les données brutes
        """)
    
    with st.expander("3. Export Vers PostgreSQL"):
        st.markdown("""
        Sauvegardez les résultats dans une base de données :
        - **Configuration facile** : Interface intuitive
        - **Structure optimisée** : Métadonnées incluses
        """)
    
    with st.expander("4. Interface Utilisateur Conviviale"):
        st.markdown("""
        - **Navigation simplifiée** : Menu latéral clair
        - **Design moderne** : Interface épurée
        - **Accessible** : Compatible tous navigateurs
        """)
    
    st.markdown("---")
    st.header("Avantages Clés")
    
    col1, col2 = st.columns(2)
    with col1:
        st.success("✅ Économie de temps")
        st.success("✅ Pas de compétences techniques requises")
    with col2:
        st.success("✅ Transparence")
        st.success("✅ Extensibilité")
    
    st.markdown("*Export possible vers d'autres bases de données (SQLite, MySQL, etc.)*")
    
    st.markdown("---")
    st.header("Cas d'Usage")
    
    st.markdown("""
    - **Éditeurs** : Surveillez les prix et la disponibilité des livres concurrents
    - **Bibliothèques** : Gestion automatisée des stocks
    - **Étudiants** : Recherche académique sur les tendances du marché
    - **Data Scientists** : Collecte de données pour analyses avancées
    """)

# Interface principale
def main():
    # Logo dans la sidebar
    display_logo()
    
        # CSS pour l'interactivité (ajoutez cette partie)
    st.markdown("""
    <style>
    .stRadio > div[role="radiogroup"] > label[data-baseweb="radio"] div {
        transition: all 0.3s ease;
        padding: 8px 12px;
        border-radius: 5px;
    }
    .stRadio > div[role="radiogroup"] > label[data-baseweb="radio"] div:hover {
        background-color: #4A00E0 !important;
        color: white !important;
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Navigation
    menu = st.sidebar.radio("Navigation", 
        ["Présentation", "Scraping", "Dashboard", "Analyse", "PostgreSQL", "À propos"])
    
    if menu == "Présentation":
        presentation_page()
    
    elif menu == "Scraping":
        st.header("Scraping de Données Livresques")
        if st.button("Lancer le Scraping"):
            with st.spinner("Extraction en cours..."):
                webscraping()
    
    elif menu == "Dashboard":
        st.markdown("## DASHBOARD")
        st.markdown("##### WELCOME ADMIN")
        
        if "df" in st.session_state:
            df = st.session_state['df']
            col1, col2, col3 = st.columns(3)
            col1.metric("Livres", len(df))
            col2.metric("Prix Moyen", f"£{df['Prix'].mean():.2f}")
            col3.metric("En Stock", f"{len(df[df['État']=='In stock'])}")
        else:
            st.warning("Aucune donnée disponible. Veuillez effectuer un scraping d'abord.")
    
    elif menu == "Analyse":
        if "df" in st.session_state:
            tableau_de_bord(st.session_state['df'])
        else:
            st.warning("Veuillez d'abord effectuer un scraping de données")
    
    elif menu == "PostgreSQL":
        st.header("Export vers PostgreSQL")
        
        if "df" not in st.session_state:
            st.warning("Veuillez d'abord effectuer un scraping de données")
            return
            
        st.subheader("Paramètres de connexion")
        host = st.text_input("Hôte", "localhost")
        database = st.text_input("Base de données", "postgres")
        user = st.text_input("Utilisateur", "postgres")
        password = st.text_input("Mot de passe", type="password")
        
        if st.button("Exporter vers PostgreSQL"):
            with st.spinner("Export en cours..."):
                if connect_to_postgresql(st.session_state['df'], host, database, user, password):
                    st.balloons()
    
    elif menu == "À propos":
        about_page()

if __name__ == "__main__":
    main()
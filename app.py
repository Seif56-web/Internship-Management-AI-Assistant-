import streamlit as st

st.title("Gestion des stagiaires")

st.write("Formulaire d'ajout de stagiaire")

nom = st.text_input("Nom")
prenom = st.text_input("Prénom")
ecole = st.text_input("École")

if st.button("Enregistrer"):
    st.success("Stagiaire enregistré !")

    st.write("### Informations")
    st.write(f"Nom : {nom}")
    st.write(f"Prénom : {prenom}")
    st.write(f"École : {ecole}")

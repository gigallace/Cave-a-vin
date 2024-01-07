# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 13:31:19 2023

@author: user
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
from psycopg2 import extras

app = Flask(__name__)
app.secret_key = '1' 



class Utilisateur:
    def __init__(self, identifiant=None, nom=None, email=None, mot_de_passe=None):
        self.identifiant = identifiant
        self.nom = nom
        self.email = email
        self.mot_de_passe = mot_de_passe
        self.caves = []

    @staticmethod
    def verifier_identifiants(email, mot_de_passe):
        with psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme") as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id_utilisateur FROM utilisateur WHERE email = %s AND mdp = %s", (email, mot_de_passe))
                user_row = cur.fetchone()
                return user_row[0] if user_row else None
    
    @staticmethod
    def creer(nom, email, mdp):
        with psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme") as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO utilisateur (nom, email, mdp) VALUES (%s, %s, %s) RETURNING id_utilisateur", (nom, email, mdp))
                id_utilisateur = cur.fetchone()[0]
                conn.commit()
                return id_utilisateur
            
            


         
class Cave:
    def __init__(self, id_cave, nom, proprietaire_id):
        self.id_cave = id_cave
        self.nom = nom
        self.proprietaire_id = proprietaire_id
        self.etageres = []

    def load_etageres(self):
        conn = psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme")  
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Etagere WHERE Cave_ID = %s", (self.id_cave,))
            etageres_data = cursor.fetchall()
            for etagere_row in etageres_data:
                self.etageres.append(Etagere(*etagere_row))
        conn.close()

    @staticmethod
    def get_caves_by_user(user_id):
       caves = []
       conn = psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme")  
       with conn.cursor() as cursor:
           cursor.execute("SELECT * FROM Cave WHERE Proprietaire_ID = %s", (user_id,))
           caves_data = cursor.fetchall()
           for cave_row in caves_data:
               caves.append(Cave(*cave_row))
       conn.close()
       return caves

    
    def add_etagere(self, region):
        conn = psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme")
        with conn.cursor() as cursor:
            # Compter le nombre total d'étagères déjà présentes dans la cave
            cursor.execute("SELECT COUNT(*) FROM Etagere WHERE Cave_ID = %s", (self.id_cave,))
            count = cursor.fetchone()[0]

            # Le nouveau numéro d'étagère est le nombre total d'étagères plus un
            numero = f"E{count + 1}"
            nb_place = 50

            # Insérer la nouvelle étagère dans la base de données
            cursor.execute("""
                INSERT INTO Etagere (numero, region, nb_place, Cave_ID) 
                VALUES (%s, %s, %s, %s)
            """, (numero, region, nb_place, self.id_cave))
            conn.commit()
        conn.close()

        # Recharger les étagères pour mettre à jour l'instance de Cave
        self.load_etageres()

    def remove_etagere(self, etagere_id):
        conn = psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme")
        with conn.cursor() as cursor:
            # Vérifier si l'étagère contient des bouteilles
            cursor.execute("SELECT COUNT(*) FROM Bouteille WHERE Etagere_ID = %s", (etagere_id,))
            if cursor.fetchone()[0] == 0:
                # Aucune bouteille, on peut supprimer l'étagère
                cursor.execute("DELETE FROM Etagere WHERE id_etagere = %s AND Cave_ID = %s", (etagere_id, self.id_cave))
                conn.commit()
                return True  # Retourne True si l'étagère a été supprimée
            else:
                # Il y a des bouteilles dans l'étagère, on ne peut pas la supprimer
                return False  # Retourne False pour indiquer l'échec de la suppression
        conn.close()

    @staticmethod
    def creer(nom_cave, id_utilisateur):
        with psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme") as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO cave (nom_cave, proprietaire_id) VALUES (%s, %s) RETURNING id_cave", (nom_cave, id_utilisateur))
                id_cave = cur.fetchone()[0]
                conn.commit()
                return id_cave





class Etagere:
    def __init__(self, id_etagere, numero, region, nb_emplacements, cave_id):
        self.id_etagere = id_etagere
        self.numero = numero
        self.region = region
        self.nb_emplacements = nb_emplacements
        self.cave_id = cave_id
        self.bouteilles = []

    def load_bouteilles(self):
        self.bouteilles = []  
        conn = psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme") 
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Bouteille WHERE Etagere_ID = %s", (self.id_etagere,))
            bouteilles_data = cursor.fetchall()
            for bouteille_row in bouteilles_data:
                
                # Créer un objet Bouteille
                bouteille = Bouteille(*bouteille_row)
                # Charger le template pour cet objet Bouteille
                bouteille.load_template()  # Cela définit l'attribut template de la bouteille
                # Ajouter l'objet Bouteille à la liste des bouteilles de l'étagère
                self.bouteilles.append(Bouteille(*bouteille_row))
        conn.close()
        
    @staticmethod
    def add_bouteille(etagere_id, template_id):
        conn = psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme")
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO Bouteille (Template_ID, Etagere_ID) 
                    VALUES (%s, %s)
                """, (template_id, etagere_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Erreur lors de l'ajout de la bouteille: {e}")
            return False
        finally:
            conn.close()





class Bouteille:
    def __init__(self, id_bouteille, note_perso, etagere_id, template_id):
        self.id_bouteille = id_bouteille   
        self.note_perso = note_perso
        self.etagere_id = etagere_id
        self.template_id = template_id
        self.template = TemplateBouteille.get_template_by_id(template_id)

    def load_template(self):
        # Chargez le template en utilisant l'ID du template déjà présent dans l'instance
        self.template = TemplateBouteille.get_template_by_id(self.template_id)
        
    
    @staticmethod
    def delete(bouteille_id):
        conn = psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme")
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM Bouteille WHERE id_bouteille = %s", (bouteille_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Erreur lors de la suppression de la bouteille: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def update_note(bouteille_id, nouvelle_note):
        conn = psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme")
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE Bouteille SET note_perso = %s WHERE id_bouteille = %s", (float(nouvelle_note), bouteille_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la note: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def get_bouteille_by_id(bouteille_id):
        conn = psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme")
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id_bouteille, note_perso, etagere_id, template_id FROM Bouteille WHERE id_bouteille = %s", (bouteille_id,))
                bouteille_data = cursor.fetchone()
                if bouteille_data:
                    return Bouteille(*bouteille_data)
        except Exception as e:
            print(f"Erreur lors de la récupération de la bouteille: {e}")
        finally:
            conn.close()
        return None







class TemplateBouteille:
    def __init__(self, id_template, domaine, nom, type_bouteille, annee, region, note_moyenne, photo, prix):
        self.id_template = id_template
        self.domaine = domaine
        self.nom = nom
        self.type_bouteille = type_bouteille
        self.annee = annee
        self.region = region
        self.note_moyenne = note_moyenne
        self.photo = photo
        self.prix = prix

    @staticmethod
    def get_template_by_id(template_id):
        conn = None
        template = None
        try:
            conn = psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme")
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM templatebouteille WHERE id_template = %s", (template_id,))
                template_data = cursor.fetchone()
                if template_data:
                    template = TemplateBouteille(*template_data)
                else:
                    print(f"Aucun template trouvé pour l'id {template_id}")
        except Exception as e:
            print(f"Une erreur s'est produite: {e}")
        finally:
            if conn:
                conn.close()

        return template
    
    def recalculer_note_moyenne(self):
            """Recalcule la note moyenne basée sur les notes personnelles des bouteilles."""
            conn = None
            try:
                conn = psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme")
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute("SELECT note_perso FROM bouteille WHERE template_id = %s", (self.id_template,))
                    bouteilles = cursor.fetchall()
                    if not bouteilles:
                        return self.note_moyenne  # Retourne la note moyenne actuelle s'il n'y a pas de bouteilles
                    somme_des_notes = sum(bouteille['note_perso'] for bouteille in bouteilles)
                    self.note_moyenne = somme_des_notes / len(bouteilles)
                    # Mettre à jour la base de données avec la nouvelle note moyenne
                    cursor.execute("UPDATE templatebouteille SET note_moyenne = %s WHERE id_template = %s", (self.note_moyenne, self.id_template))
                    conn.commit()
            except Exception as e:
                print(f"Une erreur s'est produite: {e}")
            finally:
                if conn:
                    conn.close()

            return self.note_moyenne

    @staticmethod
    def get_all_templates():
        conn = psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme")
        templates = []
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM templatebouteille")
                for template_data in cursor.fetchall():
                    templates.append(TemplateBouteille(*template_data))
        except Exception as e:
            print(f"Erreur lors de la récupération des templates: {e}")
        finally:
            conn.close()
        return templates





@app.route('/')
def index():
    # Afficher la page de connexion
    return render_template('index.html')



@app.route('/login', methods=['POST', 'GET'])
def login():
    email = request.form.get('email')
    mot_de_passe = request.form.get('password')
    
    user_id = Utilisateur.verifier_identifiants(email, mot_de_passe)
    if Utilisateur.verifier_identifiants(email, mot_de_passe):
        session['utilisateur_id'] = user_id  # Définir l'ID de l'utilisateur dans la session
        return redirect(url_for('dashboard'))  # Rediriger vers le tableau de bord
    else:
        return "Identifiants incorrects", 401



@app.route('/creer_compte')
def creer_compte():
    return render_template('creer_compte.html')

@app.route('/enregistrer_compte', methods=['POST'])
def enregistrer_compte():
    nom = request.form['nom']
    email = request.form['email']
    mdp = request.form['mdp']
    nom_cave = request.form['nom_cave']

    id_utilisateur = Utilisateur.creer(nom, email, mdp)
    if id_utilisateur:
        Cave.creer(nom_cave, id_utilisateur)
        return redirect(url_for('dashboard'))
    else:
        return "Erreur lors de la création du compte", 400




@app.route('/dashboard')
def dashboard():
    if 'utilisateur_id' not in session:
        return redirect(url_for('login'))

    user_id = session['utilisateur_id']
    print("ID de l'utilisateur:", user_id)

    # Utiliser la classe Cave pour récupérer les informations
    caves = Cave.get_caves_by_user(user_id)  # Vous devez implémenter cette méthode dans la classe Cave

    templates_debug = []
    caves_with_etageres_and_bouteilles = []
    for cave in caves:
        # Pour chaque cave, charger les étagères et les bouteilles
        cave.load_etageres()  # Une méthode dans la classe Cave
        for etagere in cave.etageres:
            etagere.load_bouteilles()  # Charger les bouteilles pour chaque étagère
            for bouteille in etagere.bouteilles:
                bouteille.load_template()  # charger le template pour chaque bouteille
                
                if bouteille.template is not None:  # Vérifiez que le template n'est pas None
                    templates_debug.append(bouteille.template.__dict__)  # Ajoute les propriétés du template
                else:
                    # Si le template est None, ajoutez un message de débogage
                    templates_debug.append({'error': f'Template not found for bouteille ID {bouteille.id_bouteille}, for template ID {bouteille.template_id}, for etagere ID {bouteille.etagere_id}, for note-perso ID {bouteille.note_perso}'})
    

                
        caves_with_etageres_and_bouteilles.append({'cave': cave, 'etageres': cave.etageres})

    return render_template('dashboard.html', 
                           caves_with_etageres_and_bouteilles=caves_with_etageres_and_bouteilles, 
                           templates_debug=templates_debug)





@app.route('/add_etagere', methods=['POST'])
def add_etagere():
    if 'utilisateur_id' not in session:
        return redirect(url_for('login'))

    user_id = session['utilisateur_id']
    region = request.form['region']

    caves = Cave.get_caves_by_user(user_id)

    if caves:
        cave = caves[0] 
        cave.add_etagere(region)
        flash('Nouvelle étagère ajoutée avec succès !', 'success')
    else:
        flash('Aucune cave trouvée pour cet utilisateur.', 'error')

    return redirect(url_for('dashboard'))





@app.route('/delete_etagere/<int:etagere_id>', methods=['POST'])
def delete_etagere(etagere_id):
    if 'utilisateur_id' not in session:
        return redirect(url_for('login'))

    user_id = session['utilisateur_id']
    
    # Récupérez l'instance de la cave de l'utilisateur
    cave = Cave.get_caves_by_user(user_id)[0]

    if cave.remove_etagere(etagere_id):
        flash('L\'étagère a été supprimée avec succès.', 'success')
    else:
        flash('Suppression impossible : l\'étagère contient des bouteilles.', 'error')

    return redirect(url_for('dashboard'))




@app.route('/add_bouteille')
def add_bouteille():
    if 'utilisateur_id' not in session:
        return redirect(url_for('login'))

    user_id = session['utilisateur_id']
    cave = Cave.get_caves_by_user(user_id)[0]
    cave.load_etageres()

    # Chargez les templates de bouteille disponibles
    templates = TemplateBouteille.get_all_templates()  

    return render_template('add_bouteille.html', etageres=cave.etageres, templates=templates)




@app.route('/submit_bouteille', methods=['POST'])
def submit_bouteille():
    if 'utilisateur_id' not in session:
        return redirect(url_for('login'))

    user_id = session['utilisateur_id']
    etagere_id = request.form['etagere_id']
    template_id = request.form['template_id']

    if Etagere.add_bouteille(etagere_id, template_id):  
        flash("La bouteille a été ajoutée avec succès.", "success")
    else:
        flash("Impossible d'ajouter la bouteille.", "error")

    return redirect(url_for('dashboard'))




@app.route('/delete_bouteille/<int:bouteille_id>', methods=['POST'])
def delete_bouteille(bouteille_id):
    if 'utilisateur_id' not in session:
        return redirect(url_for('login'))

    if Bouteille.delete(bouteille_id): 
        flash("La bouteille a été supprimée avec succès.", "success")
    else:
        flash("Impossible de supprimer la bouteille.", "error")

    return redirect(url_for('dashboard'))




@app.route('/modifier_note/<int:bouteille_id>', methods=['POST'])
def modifier_note(bouteille_id):
    if 'utilisateur_id' not in session:
        return redirect(url_for('login'))

    nouvelle_note = request.form['nouvelle_note']

    if Bouteille.update_note(bouteille_id, nouvelle_note): 
        # Recalculer la note moyenne après la mise à jour de la note
        bouteille = Bouteille.get_bouteille_by_id(bouteille_id)
        if bouteille and bouteille.template:
            bouteille.template.recalculer_note_moyenne()

        flash("La note a été mise à jour et la note moyenne recalculée.", "success")
    else:
        flash("Impossible de mettre à jour la note.", "error")

    return redirect(url_for('dashboard'))


@app.route('/supprimer_compte', methods=['POST'])
def supprimer_compte():
    user_id = session['utilisateur_id']  

    try:
        with psycopg2.connect(host="185.207.251.192", dbname="caveavin", user="mharony", password="CompoteDeP0mme") as conn:
            with conn.cursor() as cur:
                # Supprime les bouteilles associées aux étagères de l'utilisateur
                cur.execute("DELETE FROM bouteille WHERE etagere_id IN (SELECT id_etagere FROM etagere WHERE cave_id IN (SELECT id_cave FROM cave WHERE proprietaire_id = %s))", (user_id,))
                # Supprime les étagères associées à la cave de l'utilisateur
                cur.execute("DELETE FROM etagere WHERE cave_id IN (SELECT id_cave FROM cave WHERE proprietaire_id = %s)", (user_id,))
                # Supprime la cave de l'utilisateur
                cur.execute("DELETE FROM cave WHERE proprietaire_id = %s", (user_id,))
                # Supprime l'utilisateur
                cur.execute("DELETE FROM utilisateur WHERE id_utilisateur = %s", (user_id,))
                conn.commit()
    except Exception as e:
        print(f"Erreur lors de la suppression du compte : {e}")
        return "Une erreur s'est produite", 500

    session.pop('utilisateur_id', None)
    return redirect(url_for('index'))




if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)


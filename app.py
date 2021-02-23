
import sqlalchemy, pymysql
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from sqlalchemy import create_engine
from jinja2 import Environment, FileSystemLoader 
from jinja2.ext import Extension
import hashlib
import pdfkit
from datetime import datetime
import plotly.figure_factory as ff
import plotly.graph_objects as go
import plotly.express as px
import plotly, json
from flask import * 
from werkzeug.security import generate_password_hash, check_password_hash
import os
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay
import numpy as np
import calendar
from datetime import *

#Définition de la variable d'Application Flask
app = Flask(__name__)

#variable de configuration
app.config.update(SECRET_KEY  = 'ma cle secrete')

#Connexion à la Base de Données
engine = create_engine('mysql+pymysql://simplon:Simplon2020@localhost:3306/perrenot')
con=engine.connect()

#Fonction pour calculer le nombre de jours de semaine (sans weekend)
def nbreJourSemaine(date1,date2):
    us_bd = CustomBusinessDay(calendar=USFederalHolidayCalendar())
    return len(pd.bdate_range(start=date1,end=date2))

#Fonction qui calcule nombre de jour ouvrable entre deux dates 
def jourOuvrable(date1,date2) :
    datedif=con.execute(text("select datediff(:date2,:date1)"),{'date1':date1,'date2':date2})  .fetchone()
    datediff=datedif[0]+1
    tmp=date1
    tmp=datetime.strptime(tmp,"%Y-%m-%d")
    date2=datetime.strptime(date2,"%Y-%m-%d")
    while tmp<date2:
        MJ=con.execute(text("select month(:tmp),day(:tmp)"),{'tmp':tmp}).fetchone()
        if tmp.weekday()==6:
            datediff=datediff-1
        elif str(MJ[0])+'-'+str(MJ[1]) in ("1-1","4-13","5-1","5-8","5-21","6-1","7-14","8-15","11-1","11-11","12-25"):
            datediff=datediff-1
        tmp =tmp+ timedelta(days=1) #on incrémente d'un jour
    return datediff       
#Fonction pour calculer nombre de jours ouvrables par mois de chaque date d une période; sans dimanche et jours fériés    
def nbreJourOuvrable(L_date_trinome):
    jour_ouvrable=[]
    for date in L_date_trinome:
        jourOuvr = np.array(calendar.monthcalendar(date[3],date[2]))
        # enlever les dimanches et les jours qui n'appartiennent pas au mois de la date https://www.quennec.fr/trucs-astuces/langages/python/python-compter-le-nombre-de-jours-ouvr%C3%A9s-dans-un-mois
        nbre_jour_ouvrable=len(jourOuvr[np.where(jourOuvr[:,:-1] > 0)])
        if date[2]==1 and datetime.strptime(str(date[3])+"-01-01", "%Y-%m-%d").weekday()!=6:
            nbre_jour_ouvrable=nbre_jour_ouvrable-1
        elif date[2]==4 and datetime.strptime(str(date[3])+"-04-13", "%Y-%m-%d").weekday()!=6:
            nbre_jour_ouvrable=nbre_jour_ouvrable-1
        elif date[2]==5:
            if datetime.strptime(str(date[3])+"-05-01", "%Y-%m-%d").weekday()!=6:
                nbre_jour_ouvrable=nbre_jour_ouvrable-1
            if datetime.strptime(str(date[3])+"-05-08", "%Y-%m-%d").weekday()!=6:
                nbre_jour_ouvrable=nbre_jour_ouvrable-1
            if datetime.strptime(str(date[3])+"-05-21", "%Y-%m-%d").weekday()!=6:
                nbre_jour_ouvrable=nbre_jour_ouvrable-1        
        elif date[2]==6 and datetime.strptime(str(date[3])+"-06-01", "%Y-%m-%d").weekday()!=6:
            nbre_jour_ouvrable=nbre_jour_ouvrable-1    
        elif date[2]==7 and datetime.strptime(str(date[3])+"-07-14", "%Y-%m-%d").weekday()!=6:
            nbre_jour_ouvrable=nbre_jour_ouvrable-1
        elif date[2]==8 and datetime.strptime(str(date[3])+"-08-15", "%Y-%m-%d").weekday()!=6:
            nbre_jour_ouvrable=nbre_jour_ouvrable-1
        elif date[2]==11 :
            if datetime.strptime(str(date[3])+"-11-01", "%Y-%m-%d").weekday()!=6:
                nbre_jour_ouvrable=nbre_jour_ouvrable-1
            if datetime.strptime(str(date[3])+"-11-11", "%Y-%m-%d").weekday()!=6:
                nbre_jour_ouvrable=nbre_jour_ouvrable-1
        elif date[2]==12 and datetime.strptime(str(date[3])+"-12-25", "%Y-%m-%d").weekday()!=6:
            nbre_jour_ouvrable=nbre_jour_ouvrable-1    
        jour_ouvrable.append((date[0],nbre_jour_ouvrable, datetime.strptime(str(date[0]), "%Y-%m-%d").strftime("%d-%m-%Y")))
    return jour_ouvrable



#URL pour la page d'accueil
@app.route('/', methods=['GET','post'])
def home():
    
    return render_template('pages/index.html')

 
        
#*************************************************************************************************IDENTIFICATION***************************************************************        
@app.route('/Accueil', methods=['post', 'get'])
def identification():
    
    pseudo,nom,prenom='', '', ''
    data={
            'nom': nom ,
            'prenom': prenom,
            'pseudo':pseudo
        }
    if request.method== 'POST':
        mot_de_pass=request.form['mdp']
        pseudo=request.form['pseudo']
        data['pseudo']=str(pseudo)
        test_pseudo=con.execute(text("select utilisateur_pseudo, utilisateur_MDP, role_id from utilisateur where utilisateur_pseudo=:pseudo"),{'pseudo':pseudo}).fetchone()
        mot_de_pass= str(mot_de_pass)
        if test_pseudo and check_password_hash(str(test_pseudo[1]),mot_de_pass)==True:
            
            if test_pseudo[2]==1:
                session['login']=pseudo
                session['role']=1
                session['connexion'] = True
                return render_template('pages/accueil_admin.html',**data)
            elif test_pseudo[2]==2:
                session['login']=pseudo
                session['role']=2
                session['connexion'] = True
                return render_template('pages/accueil_agent.html',**data)

        flash(' pseudo et mot de passe ne correspondent pas, Veuillez vérifier votre saisie','danger')
        return render_template('pages/index.html',**data)
         
    return render_template('pages/accueil_admin.html',**data)       

    #*************************************************************************************************************************FEUILLE DE ROUTE*****************************************

@app.route('/Feuille-de-route', methods=['GET','post'])
def feuille_route():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    date=request.form['date_tour']  
    date_test=con.execute(text("select date from camion_magasin where date=:date"),{'date':date}).fetchall()
    if len(date_test)==0:
        flash("Pas de tournées enregistrées à cette date",'danger')
        return redirect(url_for('identification'))
    L_chauf_cam=con.execute(text("select chauffeur_camion.chauf_id, chauf_nom, chauf_prenom, ligne ,chauffeur_camion.camion_id, camion_mat  from chauffeur join chauffeur_camion on chauffeur_camion.chauf_id=chauffeur.chauf_id and chauffeur_camion.date =:date join camion on camion.camion_id=chauffeur_camion.camion_id group by chauffeur_camion.chauf_id,chauffeur_camion.camion_id,chauffeur_camion.ligne"),{'date':date}).fetchall()
    path_wkhtmltopdf = r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    rendered=''
    for chauf in L_chauf_cam : 
        L_mag=con.execute(text("select camion_magasin.magasin_id, magasin_code,magasin_heure_livr, magasin_adresse, nbre_rolls, nbre_palette from camion_magasin join magasin on magasin.magasin_id=camion_magasin.magasin_id and ligne=:ligne and camion_id=:cam and date=:date  order by magasin_heure_livr"),{'ligne':chauf[3],'cam':chauf[4],'date':date}) 
        dateConvert=datetime.strptime(date, "%Y-%m-%d").strftime("%d-%m-%Y")
        data={'chauffeur':chauf,
            'camion':L_mag,
            'date':dateConvert}    
        rendered+=render_template('pages/feuille_route.html', **data)
        pdf =pdfkit.from_string(rendered, False, configuration=config)
        
    response=make_response(pdf)
    response.headers['Content-Type']='application/pdf'
    response.headers['Content-Disposition']='attachment; filename=feuille_route.pdf'
        
    return response
    
#************************************************************************************************************************IMPRESSION FACTURATION*****************************************

@app.route('/impresion_facturation_recap', methods=['GET','post'])
def impression_facturation():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    L_ens=con.execute(text("select enseigne_id, enseigne_intitulé from enseigne where enseigne_actif=1")).fetchall()
    data={'L_ens':L_ens}    
    if request.method=='POST':
        date_deb=request.form.getlist('date_debut') 
        date_fin=request.form.getlist('date_fin')
        enseigne_select=request.form.getlist('liste_ens')
        casino_ens_id=con.execute(text("select enseigne_id from enseigne where enseigne_intitulé='CASINO'")).fetchone()
        #facturation navette pour toutes les enseignes
        L_tot_navette=con.execute(text("SELECT info_tarification_id, intitule_tarif, type_tarif, tarif FROM info_tarification join enseigne on enseigne.enseigne_id = info_tarification.enseigne_id and enseigne.enseigne_id =:enseigne_select where type_tarif ='navette' "),{'enseigne_select':enseigne_select[0]}).fetchall()
        L_date_facturation=con.execute(text("select distinct date(date),DATE_FORMAT(date, '%d%-%m%-%Y') from tarification where date between :date_deb and :date_fin order by date"), {'date_deb':date_deb[0], 'date_fin':date_fin[0]}).fetchall()
        L_navette=con.execute(text("select tarification.info_tarification_id, intitule_tarif, date(date), valeur from info_tarification join tarification on tarification.info_tarification_id=info_tarification.info_tarification_id join enseigne on enseigne.enseigne_id=info_tarification.enseigne_id and enseigne.enseigne_id =:enseigne_select where date between :date_deb and :date_fin and type_tarif='navette'"), {'date_deb':date_deb[0], 'date_fin':date_fin[0],'enseigne_select':enseigne_select[0]}).fetchall()
        dateDebConvert=datetime.strptime(date_deb[0], "%Y-%m-%d").strftime("%d-%m-%Y")
        dateFinConvert=datetime.strptime(date_fin[0], "%Y-%m-%d").strftime("%d-%m-%Y")
            
        if int(enseigne_select[0])==int(casino_ens_id[0]):
            test_enseigne='casino'
            #facturation distribution
            L_tot_rolls=con.execute(text("select distinct magasin_tarif_rolls from magasin where enseigne_id=:enseigne_select and magasin_tarif_rolls<>0 and magasin_actif=1"),{'enseigne_select':enseigne_select[0]}).fetchall()
            L_tot_pal=con.execute(text("select distinct magasin_tarif_palette from magasin where enseigne_id=:enseigne_select and magasin_tarif_palette<>0 and magasin_actif=1"),{'enseigne_select':enseigne_select[0]}).fetchall()
            L_date_distribution=con.execute(text("select distinct date, DATE_FORMAT(date, '%d%-%m%-%Y') from camion_magasin where date between :date_deb and :date_fin order by date"), {'date_deb':date_deb[0], 'date_fin':date_fin[0]}).fetchall()
            nbre_rolls_secteur=con.execute(text("select  magasin.magasin_tarif_rolls, camion_magasin.date, sum(nbre_rolls) from camion_magasin join magasin on magasin.magasin_id=camion_magasin.magasin_id and magasin_facturé=1 join camion on camion.camion_id= camion_magasin.camion_id and camion_type <> 'CAISSE_MOBILE' and camion_type <> 'VL' join enseigne on enseigne.enseigne_id=magasin.enseigne_id and enseigne.enseigne_id =:enseigne_select group by magasin.magasin_tarif_rolls, date having date between :date_deb and :date_fin"), {'enseigne_select':enseigne_select[0],'date_deb':date_deb[0], 'date_fin':date_fin[0]}).fetchall()
            nbre_pal_secteur=con.execute(text("select  magasin.magasin_tarif_palette, camion_magasin.date, sum(nbre_palette) from camion_magasin join magasin on magasin.magasin_id=camion_magasin.magasin_id and magasin_facturé=1 join camion on camion.camion_id= camion_magasin.camion_id  and camion_type <> 'CAISSE_MOBILE' and camion_type <> 'VL' join enseigne on enseigne.enseigne_id=magasin.enseigne_id and enseigne.enseigne_id =:enseigne_select group by magasin.magasin_tarif_palette, date having date between :date_deb and :date_fin"), {'enseigne_select':enseigne_select[0],'date_deb':date_deb[0], 'date_fin':date_fin[0]}).fetchall()
            nbre_rls_pal_trinome=con.execute(text(" select  date, sum(nbre_rolls+(nbre_palette)) from camion_magasin join magasin on magasin.magasin_id=camion_magasin.magasin_id AND date between :date_deb and :date_fin and magasin_facturé=1 join camion on camion.camion_id= camion_magasin.camion_id and camion_type ='VL' join enseigne on enseigne.enseigne_id=magasin.enseigne_id and enseigne.enseigne_intitulé='CASINO'  group by date "), {'date_deb':date_deb[0], 'date_fin':date_fin[0]}).fetchall()
            #cout tri emballage
            cout_triEmb=con.execute(text("select tarif from info_tarification where type_tarif='tri_emb' and enseigne_id=:casino_ens_id"),{'casino_ens_id':casino_ens_id[0]}).fetchone()   
            #cout passage à quai
            cout_PàQ=con.execute(text("select tarif from info_tarification where type_tarif='passage_a_quai'and enseigne_id=:casino_ens_id "),{'casino_ens_id':casino_ens_id[0]}).fetchone()
            # cout trinome
            L_date_trinome=con.execute(text("select distinct date,day(last_day(date)),MONTH(date), YEAR(date),DAYOFWEEK(date) from tarification join camion on camion.camion_id = tarification.camion_id and camion.camion_type='VL'where date between :date_deb and :date_fin order by date"), {'date_deb':date_deb[0], 'date_fin':date_fin[0]}).fetchall()
            jour_ouvrable=nbreJourOuvrable(L_date_trinome)
            
            L_tot_vl=con.execute(text("select distinct tarification.camion_id, camion_mat, camion.camion_loyer from tarification join camion on camion.camion_id=tarification.camion_id and camion.camion_type='VL' where date between :date_deb and :date_fin"), {'date_deb':date_deb[0], 'date_fin':date_fin[0]}).fetchall()
            km_trinome=con.execute(text("select tarif, info_tarification_id from info_tarification where type_tarif='trinome' and intitule_tarif='km' and enseigne_id= :casino_ens_id  "), {'casino_ens_id':casino_ens_id[0]}).fetchone()
            heure_trinome=con.execute(text("select tarif, info_tarification_id from info_tarification where type_tarif='trinome' and intitule_tarif='heure' and enseigne_id= :casino_ens_id  "), {'casino_ens_id':casino_ens_id[0]}).fetchone()
            maj_heure_nuit_trinome=con.execute(text("select tarif, info_tarification_id from info_tarification where type_tarif='trinome' and intitule_tarif='maj_heure_nuit' and enseigne_id= :casino_ens_id  "), {'casino_ens_id':casino_ens_id[0]}).fetchone()
            nbre_km_trinome=con.execute(text("select tarification.camion_id, date, sum(valeur) from tarification join camion on camion.camion_id=tarification.camion_id and camion_type='VL' where tarification.info_tarification_id=:km_trinome and date between :date_deb and :date_fin group by tarification.camion_id, date"),{'date_deb':date_deb[0], 'date_fin':date_fin[0], 'km_trinome':km_trinome[1] }).fetchall()
            nbre_heure_trinome=con.execute(text("select tarification.camion_id, date, sum(valeur) from tarification join camion on camion.camion_id=tarification.camion_id and camion_type='VL' where tarification.info_tarification_id=:heure_trinome and date between :date_deb and :date_fin group by tarification.camion_id, date"),{'date_deb':date_deb[0], 'date_fin':date_fin[0], 'heure_trinome':heure_trinome[1] }).fetchall()
            nbre_maj_hN_trinome=con.execute(text("select tarification.camion_id, date, sum(valeur) from tarification join camion on camion.camion_id=tarification.camion_id and camion_type='VL' where tarification.info_tarification_id=:maj_heure_nuit_trinome and date between :date_deb and :date_fin group by tarification.camion_id, date"),{'date_deb':date_deb[0], 'date_fin':date_fin[0], 'maj_heure_nuit_trinome':maj_heure_nuit_trinome[1] }).fetchall()
            # TK
            L_date_TK= con.execute(text("select distinct date, DATE_FORMAT(date, '%d%-%m%-%Y') from tarification join camion on camion.camion_id = tarification.camion_id and camion.camion_type='CAISSE_MOBILE'where date between :date_deb and :date_fin order by date"), {'date_deb':date_deb[0], 'date_fin':date_fin[0]}).fetchall()
            km_TK=con.execute(text("select tarif, info_tarification_id from info_tarification where type_tarif='TK' and intitule_tarif='km' and enseigne_id= :casino_ens_id  "), {'casino_ens_id':casino_ens_id[0]}).fetchone()
            km_trc_TK=con.execute(text("select tarif, info_tarification_id from info_tarification where type_tarif='TK' and intitule_tarif='traction' and enseigne_id= :casino_ens_id  "), {'casino_ens_id':casino_ens_id[0]}).fetchone()
            
            traction_TK=con.execute(text("select tarif, info_tarification_id from info_tarification where type_tarif='TK' and intitule_tarif='traction' and enseigne_id= :casino_ens_id  "), {'casino_ens_id':casino_ens_id[0]}).fetchone()
            L_tot_CM=con.execute(text("select distinct tarification.camion_id, camion_mat, camion.camion_loyer from tarification join camion on camion.camion_id=tarification.camion_id and camion.camion_type='CAISSE_MOBILE' where date between :date_deb and :date_fin"), {'date_deb':date_deb[0], 'date_fin':date_fin[0]}).fetchall()
            nbre_km_TK= con.execute(text("select tarification.camion_id, date, sum(valeur) from tarification join camion on camion.camion_id=tarification.camion_id and camion_type='CAISSE_MOBILE' where tarification.info_tarification_id=:km_TK and date between :date_deb and :date_fin group by tarification.camion_id, date"),{'date_deb':date_deb[0], 'date_fin':date_fin[0], 'km_TK':km_TK[1] }).fetchall()
            nbre_kmTrc_TK=con.execute(text("select date, valeur from tarification where tarification.info_tarification_id=:km_trc_TK and date between :date_deb and :date_fin order by date"),{'date_deb':date_deb[0], 'date_fin':date_fin[0], 'km_trc_TK':km_trc_TK[1] }).fetchall()
            date_traction=con.execute(text("select distinct date from tarification where tarification.info_tarification_id=:km_trc_TK and date between :date_deb and :date_fin order by date"),{'date_deb':date_deb[0], 'date_fin':date_fin[0], 'km_trc_TK':km_trc_TK[1] }).fetchall()
            tot_traction=[0 for i in range(len(L_tot_CM)//2)]
            for date in date_traction:
                compteur=0
                for trc in nbre_kmTrc_TK:
                    if trc[0]==date[0]:
                        tot_traction[compteur]=tot_traction[compteur]+trc[1]
                        compteur+=1
            data={'L_tot_navette':L_tot_navette,
            'L_date_facturation':L_date_facturation,
            'L_navette':L_navette,
            'date_debut': dateDebConvert,
            'date_fin':dateFinConvert,
            'L_tot_rolls':L_tot_rolls, 
            'L_tot_pal':L_tot_pal,
            'nbre_rolls_secteur':nbre_rolls_secteur,
            'nbre_pal_secteur':nbre_pal_secteur,
            'L_date_distribution':L_date_distribution,
            'cout_PàQ':cout_PàQ[0],
            'nbre_rls_pal_trinome':nbre_rls_pal_trinome,
            'L_tot_vl':L_tot_vl, 
            'jour_ouvrable':jour_ouvrable,
            'km_trinome':km_trinome,
            'heure_trinome':heure_trinome,
            'maj_hN_trinome':maj_heure_nuit_trinome,
            'L_date_trinome': L_date_trinome,
            'nbre_km_trinome':nbre_km_trinome,
            'nbre_heure_trinome':nbre_heure_trinome,
            'nbre_maj_hN_trinome':nbre_maj_hN_trinome,
            'L_date_TK':L_date_TK,
            'km_TK':km_TK,
            'traction_TK':traction_TK,
            'L_tot_CM':L_tot_CM,
            'tot_traction':tot_traction,
            'nbre_km_TK':nbre_km_TK,
            'nbre_kmTrc_TK':nbre_kmTrc_TK,
            'nbre_tot_CM':len(L_tot_CM),
            'km_trc_TK':km_trc_TK,
            'cout_triEmb':cout_triEmb[0],
            'test_ens':test_enseigne
            }
        else:
            test_enseigne='autre'
            enseigne_intitulé=con.execute(text("select enseigne_intitulé from enseigne where enseigne_id=:ens"),{'ens':enseigne_select}).fetchone()
            #facturation distribution
            L_tot_rolls=con.execute(text("select distinct magasin_tarif_rolls from magasin where enseigne_id=:enseigne_select and magasin_tarif_rolls<>0 and magasin_actif=1"),{'enseigne_select':enseigne_select[0]}).fetchall()
            L_tot_pal=con.execute(text("select distinct magasin_tarif_palette from magasin where enseigne_id=:enseigne_select and magasin_tarif_palette<>0 and magasin_actif=1"),{'enseigne_select':enseigne_select[0]}).fetchall()
            L_date_distribution=con.execute(text("select distinct date, DATE_FORMAT(date, '%d%-%m%-%Y') from camion_magasin where date between :date_deb and :date_fin order by date"), {'date_deb':date_deb[0], 'date_fin':date_fin[0]}).fetchall()
            nbre_rolls_secteur=con.execute(text("select  magasin.magasin_tarif_rolls, camion_magasin.date, sum(nbre_rolls) from camion_magasin join magasin on magasin.magasin_id=camion_magasin.magasin_id and magasin_facturé=1 join  enseigne on enseigne.enseigne_id=magasin.enseigne_id and enseigne.enseigne_id =:enseigne_select group by magasin.magasin_tarif_rolls, date having date between :date_deb and :date_fin"), {'enseigne_select':enseigne_select[0],'date_deb':date_deb[0], 'date_fin':date_fin[0]}).fetchall()
            nbre_pal_secteur=con.execute(text("select  magasin.magasin_tarif_palette, camion_magasin.date, sum(nbre_palette) from camion_magasin join magasin on magasin.magasin_id=camion_magasin.magasin_id and magasin_facturé=1 join enseigne on enseigne.enseigne_id=magasin.enseigne_id and enseigne.enseigne_id =:enseigne_select group by magasin.magasin_tarif_palette, date having date between :date_deb and :date_fin"), {'enseigne_select':enseigne_select[0],'date_deb':date_deb[0], 'date_fin':date_fin[0]}).fetchall()
            data={'L_tot_rolls':L_tot_rolls,
                  'L_tot_pal':L_tot_pal,
                  'L_date_distribution':L_date_distribution,
                  'nbre_rolls_secteur':nbre_rolls_secteur,
                  'nbre_pal_secteur':nbre_pal_secteur,
                  'L_tot_navette':L_tot_navette,
                  'L_date_facturation':L_date_facturation,
                  'L_navette':L_navette,
                  'test_ens':test_enseigne,
                  'date_debut': dateDebConvert,
                  'date_fin':dateFinConvert,
                  'enseigne_intitulé':enseigne_intitulé[0]
            }
        #crréation pdf
        path_wkhtmltopdf = r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe'
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        #pdfkit.from_url("http://google.com", "out.pdf", configuration=config)
        rendered=render_template('pages/fact_navette_casino.html',**data)
        rendered=rendered
        pdf =pdfkit.from_string(rendered, False, configuration=config)
        response=make_response(pdf)
        response.headers['Content-Type']='application/pdf'
        response.headers['Content-Disposition']='attachment; filename=Facturation_casino.pdf'
        return response
    return render_template('pages/formulaire_facturation_recap.html', **data)       
            
               
    #*************************************************************************************************************************FORMULAIRE FACTURATION*****************************************

@app.route('/facturation', methods=['GET','post'])
def form_facturation():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    if request.method=='POST':
        date=request.form['date']
        date_test_distribution=con.execute(text("select date from camion_magasin where date=:date"),{'date':date}).fetchall()
        if len(date_test_distribution)==0:
            flash("Pas de tournées enregistrées à cette date!",'warning')
            
        date_test=con.execute(text("select date from tarification where date=:date"),{'date':date}).fetchall()
        casino_id=con.execute(text("select enseigne_id from enseigne where enseigne_intitulé='CASINO'")).fetchone()
        L_enseigne=con.execute(text("select enseigne_id, enseigne_intitulé from enseigne where enseigne_intitulé<>'CASINO' and enseigne_actif=1")).fetchall()
        L_VL=con.execute(text("select distinct camion_mat, camion.camion_id from camion where camion.camion_type='VL' and camion_actif=1")).fetchall()
        L_CM=con.execute(text("select distinct camion_mat ,camion.camion_id from  camion  where camion.camion_type='CAISSE_MOBILE' and camion.camion_actif=1")).fetchall()
        L_CM_complete=con.execute(text("select camion_mat ,camion_id from camion where camion_type='CAISSE_MOBILE' and camion_actif=1")).fetchall()
        L_camion=con.execute(text("select camion_mat ,camion_id, camion_type from camion where (camion_type='CAISSE_MOBILE' or camion_type='SEMI-REMORQUE' ) and camion_etat=1 and camion_actif=1")).fetchall()
        L_navette=con.execute(text("select intitule_tarif, info_tarification_id from info_tarification where type_tarif ='navette' and enseigne_id =:casino_id and  tarification_actif=1"),{'casino_id':casino_id[0]}).fetchall()
        
        L_navette_ens=[con.execute(text("select info_tarification_id, intitule_tarif, enseigne_id from info_tarification where enseigne_id=:ens_id and tarification_actif=1 and type_tarif='navette' "),{'ens_id':L_enseigne[j][0]}).fetchall() for j in range(len(L_enseigne))]
        nbre_vl=len(L_VL)
        date_converti=datetime.strptime(date, "%Y-%m-%d").strftime("%d-%m-%Y")
        data={'L_enseigne':L_enseigne,
                'nbre_ens':len(L_enseigne),
                'L_VL':L_VL,
                'L_CM':L_CM,
                'L_CM_complete':L_CM_complete,
                'nbre_vl':nbre_vl,
                'nbre_cm':len(L_CM_complete),
                'L_navette': L_navette,
                'L_camion':L_camion,
                'date':date,
                'date_converti':date_converti,
                'L_navette_ens':L_navette_ens}
        if len(date_test)>0:
            test_fact=1
            flash("Des données ont déjà été renseignées à cette date, vous avez la possibilité de les modifier",'success')    
            km_trinome=con.execute(text("select valeur, camion_id from tarification  join info_tarification on info_tarification.info_tarification_id=tarification.info_tarification_id and intitule_tarif='km' and type_tarif='trinome' and date=:date"),{'date':date}).fetchall()
            heure_trinome=con.execute(text("select valeur, camion_id from tarification  join info_tarification on info_tarification.info_tarification_id=tarification.info_tarification_id and intitule_tarif='heure' and type_tarif='trinome' and date=:date"),{'date':date}).fetchall()
            MHN_trinome=con.execute(text("select valeur, camion_id from tarification  join info_tarification on info_tarification.info_tarification_id=tarification.info_tarification_id and intitule_tarif='maj_heure_nuit' and type_tarif='trinome' and date=:date"),{'date':date}).fetchall()

            km_TK=con.execute(text("select valeur, camion_id from tarification join info_tarification on info_tarification.info_tarification_id=tarification.info_tarification_id and type_tarif='TK' and intitule_tarif='km' and date=:date"),{'date':date}).fetchall()
            traction_TK=con.execute(text("select valeur, tarification.camion_id, camion_mat,camion_type from tarification join camion on camion.camion_id= tarification.camion_id join info_tarification on info_tarification.info_tarification_id=tarification.info_tarification_id and type_tarif='TK' and intitule_tarif='traction' and date=:date"),{'date':date}).fetchall()
          
            navette_casino=con.execute(text("select valeur, tarification.info_tarification_id from tarification  join info_tarification on tarification.info_tarification_id = info_tarification.info_tarification_id and date=:date and enseigne_id=:casino_id and type_tarif='navette' and tarification_actif=1"),{'date':date,'casino_id':casino_id[0]}).fetchall()

            navette_ens=con.execute(text("select valeur, tarification.info_tarification_id, enseigne_id from tarification  join info_tarification on tarification.info_tarification_id = info_tarification.info_tarification_id and date=:date and enseigne_id<>:casino_id and type_tarif='navette' and tarification_actif=1"),{'date':date,'casino_id':casino_id[0]}).fetchall()

            data['test_fact']=test_fact
            data['km_trinome']=km_trinome
            data['heure_trinome']=heure_trinome
            data['MHN_trinome']=MHN_trinome
            data['km_TK']=km_TK
            data['traction_TK']=traction_TK
            data['navette_casino']=navette_casino
            data['navette_ens']=navette_ens
            data['nbre_traction']=len(traction_TK)
            data['nbre_trinome']=len(km_trinome)
            data['nbre_TK']=len(km_TK)
            
        return render_template('pages/facturation_globale.html', **data)

 
    #*************************************************************************************************************************ENREGISTRER FORMULAIRE FACTURATION*****************************************

@app.route('/enregistrement_facturation', methods=['GET','post'])
def enregistrer_facturation():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    if request.method=='POST':
        vl_cam_id=request.form.getlist('vl_mat')
        vl_km=request.form.getlist('vl_km')
        vl_heure=request.form.getlist('vl_heure')
        vl_heure_nuit=request.form.getlist('vl_heure_nuit')
        
        trc_km=request.form.getlist('trc_km')
        traction_mat=request.form.getlist('traction_mat')
        csn_nvt_type=request.form.getlist('csn_nvt_type')
        csn_nvt_nbre=request.form.getlist('csn_nvt_nbre')
        ens_nvt=request.form.getlist('ens_nvt')
        ens_nvt_nbre=request.form.getlist('ens_nvt_nbre')
        cm_id=request.form.getlist('cm_id')
        cm_km=request.form.getlist('cm_km')
        date=request.form.getlist('date')
        
        #enregistrer facturation Casino
        casino_id=con.execute(text("select enseigne_id from enseigne where enseigne_intitulé='CASINO'")).fetchone()
        trinome_km=con.execute(text("select info_tarification_id from info_tarification where type_tarif='trinome' and intitule_tarif='km' and enseigne_id =:casino_id"),{'casino_id':casino_id[0]}).fetchone()
        trinome_heure= con.execute(text("select info_tarification_id from info_tarification where type_tarif='trinome' and intitule_tarif='heure' and enseigne_id =:casino_id"),{'casino_id':casino_id[0]}).fetchone()
        trinome_heure_nuit= con.execute(text("select info_tarification_id from info_tarification where type_tarif='trinome' and intitule_tarif='maj_heure_nuit' and enseigne_id =:casino_id "),{'casino_id':casino_id[0]}).fetchone()
        tk_traction= con.execute(text("select info_tarification_id from info_tarification where type_tarif='TK' and intitule_tarif='traction' and enseigne_id =:casino_id "),{'casino_id':casino_id[0]}).fetchone()
        tk_km=con.execute(text("select info_tarification_id from info_tarification where type_tarif='TK' and intitule_tarif='km' and enseigne_id =:casino_id "),{'casino_id':casino_id[0]}).fetchone()
        L_nvt_casino=con.execute(text("select info_tarification_id from info_tarification where type_tarif='navette' and enseigne_id =:casino_id "),{'casino_id':casino_id[0]}).fetchall()
        semi_navette=con.execute(text("select camion_id from camion where camion_type ='SEMI_NAVETTE'")).fetchone()

        #au cas de modification supprimer tous les anciens enregstrements
        con.execute(text("delete from tarification where date=:date"),{'date':date})
        for cpt in range(len(vl_cam_id)):
            con.execute(text("insert into tarification (info_tarification_id, camion_id,date,valeur) values(:trinome_km, :vl_cam_id, :date, :valeur )"),  {'trinome_km': trinome_km[0], 'vl_cam_id': vl_cam_id[cpt],'date':date, 'valeur':vl_km[cpt] })
            con.execute(text("insert into tarification (info_tarification_id, camion_id,date,valeur) values(:trinome_heure, :vl_cam_id, :date, :valeur )"),  {'trinome_heure': trinome_heure[0], 'vl_cam_id': vl_cam_id[cpt],'date':date, 'valeur':vl_heure[cpt] })
            con.execute(text("insert into tarification (info_tarification_id, camion_id,date,valeur) values(:trinome_heure_nuit, :vl_cam_id, :date, :valeur )"),  {'trinome_heure_nuit': trinome_heure_nuit[0], 'vl_cam_id': vl_cam_id[cpt],'date':date, 'valeur':vl_heure_nuit[cpt] })
        for cpt in range(len(cm_id)):
            con.execute(text("insert into tarification (info_tarification_id, camion_id,date,valeur) values(:tk_km, :cm_id, :date, :valeur )"),  {'tk_km': tk_km[0], 'cm_id': cm_id[cpt],'date':date, 'valeur':cm_km[cpt] })
        for cpt in range(len(traction_mat)):
            if float(trc_km[cpt]) !=0:
                con.execute(text("insert into tarification (info_tarification_id, camion_id,date,valeur) values(:tk_traction, :cm_id, :date, :valeur )"),  {'tk_traction': tk_traction[0], 'cm_id': traction_mat[cpt],'date':date, 'valeur':trc_km[cpt] })
        for cpt in range(len(csn_nvt_type)):
            if int(csn_nvt_nbre[cpt]) !=0:
                con.execute(text("insert into tarification (info_tarification_id, camion_id, date,valeur) values(:csn_nvt_type, :semi_navette,  :date, :valeur )"),  {'csn_nvt_type': csn_nvt_type[cpt],'semi_navette':semi_navette[0], 'date':date, 'valeur':csn_nvt_nbre[cpt] })

        # enregistrer navette autre enseigne que Casino 
        L_nvt_saisi=request.form.getlist('ens_nvt_nbre')      
        L_enseigne=con.execute(text("select enseigne_id, enseigne_intitulé from enseigne where enseigne_intitulé<>'CASINO' and enseigne_actif=1")).fetchall()
        L_navette_ens=[con.execute(text("select info_tarification_id, intitule_tarif, enseigne_id from info_tarification where enseigne_id=:ens_id and tarification_actif=1 and type_tarif='navette' "),{'ens_id':L_enseigne[j][0]}).fetchall() for j in range(len(L_enseigne))]
        nvt_saisi=0
        for cpt_ens in range(len(L_enseigne)):
            for nvt in L_navette_ens[cpt_ens]:
                if int(L_nvt_saisi[nvt_saisi])!=0:
                   con.execute(text("insert into tarification (info_tarification_id, camion_id, date,valeur)values(:tarif_id,:semi_navette,:date,:valeur)"),{'tarif_id':nvt[0],'semi_navette':semi_navette[0], 'date':date,'valeur':L_nvt_saisi[nvt_saisi]})
                nvt_saisi+=1   
      
        data={'vl_cam_id':vl_cam_id,
              'vl_km':vl_km,
              'vl_heure':vl_heure,
              'vl_heure_nuit':vl_heure_nuit,
              'trc_km':trc_km,
              'csn_nvt_type':csn_nvt_type,
              'csn_nvt_nbre':csn_nvt_nbre,
              'ens_nvt':ens_nvt,
              'ens_nvt_nbre':ens_nvt_nbre
              }
        flash("le formualaire de la facturation a été bien enregistré",'success')
        return render_template('pages/accueil_admin.html', **data)
 #*************************************************************************************************************************AJOUTER NAVETTE************************************************
@app.route('/editer_tarif_casino',methods=['GET','POST'])    
def editer_tarif_casino():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    casino_id=con.execute(text("select enseigne_id from enseigne where enseigne_intitulé='CASINO' ")).fetchone()
    #récupération les tarifi de tous les types de tarification
    km_trinome=con.execute(text("select tarif from info_tarification where type_tarif='trinome' and intitule_tarif ='km' and enseigne_id=:casino_id"),{'casino_id':casino_id[0]}).fetchone()
    heure_trinome=con.execute(text("select tarif from info_tarification where type_tarif='trinome' and intitule_tarif ='heure' and enseigne_id=:casino_id"),{'casino_id':casino_id[0]}).fetchone()
    MAJ_HN_trinome=con.execute(text("select tarif from info_tarification where type_tarif='trinome' and intitule_tarif ='maj_heure_nuit' and enseigne_id=:casino_id"),{'casino_id':casino_id[0]}).fetchone()
   
    km_TK=con.execute(text("select tarif from info_tarification where type_tarif='TK' and intitule_tarif ='km' and enseigne_id=:casino_id"),{'casino_id':casino_id[0]}).fetchone()
    traction_TK=con.execute(text("select tarif from info_tarification where type_tarif='TK' and intitule_tarif ='traction' and enseigne_id=:casino_id"),{'casino_id':casino_id[0]}).fetchone()
    
    tri_emb_casino=con.execute(text("select tarif from info_tarification where type_tarif='tri_emb' and intitule_tarif ='tri_emb' and enseigne_id=:casino_id"),{'casino_id':casino_id[0]}).fetchone()
    passage_a_quai_casino=con.execute(text("select tarif from info_tarification where type_tarif='passage_a_quai' and intitule_tarif ='passage_a_quai' and enseigne_id=:casino_id"),{'casino_id':casino_id[0]}).fetchone()
   
    
    data={
                'km_trinome':km_trinome[0],
                'heure_trinome':heure_trinome[0],
                'MAJ_HN_trinome':MAJ_HN_trinome[0],
                'km_TK':km_TK[0],
                'traction_TK':traction_TK[0],
                'tri_emb_casino':tri_emb_casino[0],
                'passage_a_quai_casino':passage_a_quai_casino[0]
         }
    if request.method =='POST':
        km_trinome=request.form['km_trinome']
        heure_trinome=request.form['heure_trinome']
        MAJ_HN_trinome=request.form['MAJ_HN_trinome']
        km_TK=request.form['km_TK']
        traction_TK=request.form['traction_TK']
        tri_emb_casino=request.form['tri_emb_casino']
        passage_a_quai_casino=request.form['passage_a_quai_casino']
        con.execute(text("update  info_tarification set tarif=:km where enseigne_id=:casino_id and type_tarif='trinome' and intitule_tarif='km' "), {'km':km_trinome,'casino_id':casino_id[0]}) 
        con.execute(text("update  info_tarification set tarif=:heure where enseigne_id=:casino_id and type_tarif='trinome' and intitule_tarif='heure' "), {'heure':heure_trinome,'casino_id':casino_id[0]}) 
        con.execute(text("update  info_tarification set tarif=:MHN where enseigne_id=:casino_id and type_tarif='trinome' and intitule_tarif='maj_heure_nuit' "), {'MHN':MAJ_HN_trinome,'casino_id':casino_id[0]}) 
        con.execute(text("update  info_tarification set tarif=:km where enseigne_id=:casino_id and type_tarif='TK' and intitule_tarif='km' "), {'km':km_TK,'casino_id':casino_id[0]}) 
        con.execute(text("update  info_tarification set tarif=:traction where enseigne_id=:casino_id and type_tarif='TK' and intitule_tarif='traction' "), {'traction':traction_TK,'casino_id':casino_id[0]}) 
        con.execute(text("update  info_tarification set tarif=:paq where enseigne_id=:casino_id and type_tarif='passage_a_quai' and intitule_tarif='passage_a_quai' "), {'paq':passage_a_quai_casino,'casino_id':casino_id[0]}) 
        con.execute(text("update  info_tarification set tarif=:tri where enseigne_id=:casino_id and type_tarif='tri_emb' and intitule_tarif='tri_emb' "), {'tri':tri_emb_casino,'casino_id':casino_id[0]}) 
        flash('Les modifications ont été bien enregistrées','success')
        data['km_trinome'],data['heure_trinome'],data['MAJ_HN_trinome'],data['km_TK'],data['traction_TK'],data['tri_emb_casino'],data['passage_a_quai_casino']='','','','','','',''
    return render_template('pages/edit_tarif_casino.html', **data)     
            
#*************************************************************************************************************************AJOUTER NAVETTE************************************************
@app.route('/ajout_navette',methods=['GET','POST'])    
def ajouter_navette():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    navette, tarif='', ''
    requete_ens="select enseigne_id, enseigne_intitulé from enseigne where enseigne_actif=1"
    enseigne=con.execute(text(requete_ens)).fetchall()
    data={
                'navette':navette,
                'tarif':tarif,
                'enseigne':enseigne
         }
    if request.method =='POST':
        navette=request.form['navette']
        tarif=request.form['tarif']
        enseigne=request.form['liste_ens']
        test_navette=con.execute(text("select intitule_tarif from info_tarification where enseigne_id=:ens_id and type_tarif='navette' and intitule_tarif=:navette"),{'ens_id':enseigne,'navette':navette}).fetchone()
        
        if test_navette:
            flash('cet intitulé de navette existe déjà pour cette enseigne, veuillez le changer!', 'danger')
            if request.form['test_ens']!="":
                return render_template('pages/mag_nvt_nvl_ens.html', **data)

        else:
            requete_ajout="INSERT INTO info_tarification (intitule_tarif, type_tarif, tarif, enseigne_id) VALUES (:navette, 'navette', :tarif, :ens_id)"
            con.execute(text(requete_ajout),{'navette': navette, 'tarif':tarif, 'ens_id':enseigne})
            flash("la navette a été bien enregistrée", 'success')
            navette,tarif='',''
            if request.form['test_ens']!="": # revoyer le template nouveau magasin et navette cas ajout nouvelle enseigne
                data['navette']=navette
                data['tarif']  =tarif 
                data['ens_intitulé']=request.form['enseigne_intitule']
                data['nvl_ens_id']=enseigne
                data['test_ajout_mag']=0
                return render_template('pages/mag_nvt_nvl_ens.html', **data)
            return redirect(url_for('ajouter_navette'))
        data['navette']=navette
        data['tarif']  =tarif 
    return render_template('pages/ajouter_navette.html', **data)   

    
 #************************************************************************************************************************EDITER NAVETTE********************************************************************************************************************************************
@app.route('/modification_navette', methods=['GET','post'])
def edit_navette():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    rech_nvt=''
    nvt_select=''
    nvt_info=[ '' for i in range(3)]
    L_nvt= con.execute(text("select intitule_tarif, tarif, enseigne_intitulé, info_tarification.enseigne_id, info_tarification_id from info_tarification  join  enseigne on enseigne.enseigne_id=info_tarification.enseigne_id and tarification_actif=1 where enseigne_actif=1 and type_tarif='navette'")).fetchall()
    L_ens=con.execute(text("select enseigne_id, enseigne_intitulé from enseigne where enseigne_actif=1")).fetchall()
    
    data={ 'L_nvt': L_nvt,
            'rech_nvt':rech_nvt, 
            'nvt_info':nvt_info,
            'L_ens': L_ens,
          }
    if request.method=='POST':
        # Si l utilisateur a tapé un nom dans la bare de recherche:
        #nvt_select=request.form.getlist('nvt_select')
        if request.form['rech_nvt']:
            rech_nvt=request.form['rech_nvt']
            liste_nvt_rech=con.execute(text("select intitule_tarif, tarif, enseigne_intitulé, info_tarification.enseigne_id, info_tarification_id   from info_tarification join  enseigne on enseigne.enseigne_id=info_tarification.enseigne_id and enseigne_actif=1 and tarification_actif=1 where type_tarif='navette' and (intitule_tarif LIKE :intitule_tarif or enseigne_intitulé LIKE :rech_nvt )"), {'intitule_tarif':rech_nvt+'%','rech_nvt':rech_nvt+'%' }).fetchall()
            if liste_nvt_rech:
                data['L_nvt']=liste_nvt_rech
            else:
                flash('Aucune navette ne correspond à votre recherche!','danger')
            return render_template('pages/edit_navette.html', **data)   
        # si l utilisateur a coché un nom:
                   
        if request.form['nvt_select']!='':
            #nvt_select=request.form['nvt_select']
            nvt_select=request.form.getlist('nvt_select')
            nvt_info=con.execute(text("select intitule_tarif, tarif, enseigne_intitulé, info_tarification.enseigne_id, info_tarification_id   from info_tarification join  enseigne on enseigne.enseigne_id=info_tarification.enseigne_id and tarification_actif=1 where info_tarification_id=:nvt_select  "), {'nvt_select':nvt_select[0]}).fetchone()
            data['nvt_info']=nvt_info
            
    return render_template('pages/edit_navette.html', **data)             
 #**************************************************************************************************************VALIDER SUPPRESSION NAVETTE**********************************************************************
@app.route('/navette_supprimée', methods=['GET','post'])
def navette_supprimée():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    info_tarif_id=request.form['info_tarif_id']
    
    con.execute(text("update info_tarification set tarification_actif=0 where info_tarification_id=:tarif_id"),{'tarif_id':info_tarif_id})
    flash('Cette Navette a été bien suppirmée pour cette Enseigne', 'success')
    return redirect(url_for('edit_navette'))

#*********************************************************************************************************************AJOUTER CAMION***************************************************************************
@app.route('/Ajouter_Camion', methods=['GET','post'])
def ajout_camion():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    if request.method=='POST':
        Immatriculation=request.form['immatriculation']
        capacite=request.form['capacite']
        type_cam=request.form.getlist('liste_type')
        tonnage=request.form['tonnage']
        fonction=request.form.getlist('liste_fonction')
        assurance=request.form['assurance']
        loyer=request.form['loyer']
        entretient=request.form['entretient']
        pneu=request.form['pneu']
        consommation=request.form['consommation']
        test_matActif=con.execute(text("select camion_mat from camion where camion_mat=:mat_cam and camion_actif=1" ),{'mat_cam':Immatriculation}).fetchone()
        test_matNonActif= con.execute(text("select camion_mat from camion where camion_mat=:mat_cam and camion_actif=0"),{'mat_cam':Immatriculation}).fetchone()
        if test_matActif:
           flash('Ce matricule existe déjà, Veuillez le changer', 'danger')
        elif  test_matNonActif: 
            flash('Ce camion existait déjà a été récupéré', 'success')
            con.execute(text("update camion set camion_actif=1 where camion_mat=:mat_cam and camion_actif=0"),{'mat_cam':Immatriculation})
        else:
            con.execute(text("insert into camion (camion_mat,camion_cap,camion_type,camion_tonnage,camion_fonction, camion_assurance, camion_loyer, camion_entretien, camion_pneus, camion_conso) values(:cam_mat, :cam_cap,:cam_type, :cam_tonnage,:cam_fonc, :cam_assur,:cam_loyer, :cam_entret, :cam_pneu, :cam_cons)"), {'cam_mat':Immatriculation,'cam_cap':capacite, 'cam_type':type_cam[0] , 'cam_tonnage': tonnage ,'cam_fonc':fonction[0] , 'cam_assur': assurance,'cam_loyer': loyer, 'cam_entret': entretient, 'cam_pneu':pneu ,'cam_cons':consommation   })      
            flash('Ce camion a été bien ajouté', 'success')
        return render_template('pages/ajouter_camion.html')

    return render_template('pages/ajouter_camion.html')

   #************************************************************************************************************************EDITER CAMION********************************************************************
@app.route('/modification_camion', methods=['GET','post'])
def edit_camion():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    rech_cam=''
    cam_select=''
    cam_info=[ '' for i in range(9)]
    liste_camion= con.execute(text("select camion_id, camion_mat, camion_cap, camion_etat, camion_type, camion_tonnage, camion_fonction, camion_assurance, camion_loyer, camion_entretien, camion_pneus, camion_conso   from camion  where camion_actif=1")).fetchall()
    data={ 'liste_camion': liste_camion,
            'rech_cam':rech_cam, 
            'cam_info':cam_info
         }
       
    if request.method=='POST':
        # Si l utilisateur a tapé un nom dans la bare de recherche:
        if request.form['rech_cam']:
            rech_cam=request.form['rech_cam']
            liste_cam_rech=con.execute(text("select camion_id, camion_mat, camion_cap, camion_etat, camion_type, camion_tonnage, camion_fonction, camion_assurance, camion_loyer, camion_entretien, camion_pneus, camion_conso from camion  where  (camion_mat LIKE :cam or camion_type LIKE :cam)  and camion_actif=1 "), {'cam': rech_cam +'%'}).fetchall()
            if liste_cam_rech:
                data['liste_camion']=liste_cam_rech
            else:
                flash(' aucun camion avec cette Immatriculation','danger')
            return render_template('pages/edit_camion.html', **data)   
        # si l utilisateur a coché un nom:
                   
        if request.form['cam_select']!='':
            cam_select=request.form['cam_select']
            cam_info=con.execute(text("select camion_id, camion_mat, camion_cap, camion_etat, camion_type, camion_tonnage, camion_fonction, camion_assurance, camion_loyer, camion_entretien, camion_pneus, camion_conso from camion  where camion_id=:cam and  camion_actif=1"), {'cam':cam_select}).fetchone()
            data['cam_info']=cam_info
            
        
    return render_template('pages/edit_camion.html', **data) 
    #*************************************************************************************************************VALIDER MODIFICATION CAMION*****************************************************************

@app.route('/camion_supprimé', methods=['GET','post'])
def camion_supprime():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    camion_id=request.form['camion_id']
    con.execute(text("update camion set camion_actif=0 where camion_id=:camion_id"),{'camion_id':camion_id})
    flash('Le camion coché a été bien supprimé', 'success')   
     
    return redirect(url_for('edit_camion'))  

#***************************************************************************************************************VALIDER MODIFICATION CAMION*****************************************************************

@app.route('/camion_modifié', methods=['GET','post'])
def camion_modifie():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    mat_anc=request.form['mat_anc']
    cam_id=request.form['cam_id']
    mat=request.form['mat']
    cap=request.form['cap']
    etat=request.form.getlist('etat')
    typeC=request.form.getlist('liste_type')
    tonnage=request.form['tonnage']
    fonction=request.form.getlist('fonction')
    assurance=request.form['assurance'] 
    loyer=request.form['loyer']
    entretien=request.form['entretien'] 
    pneus=request.form['pneus']
    consomation=request.form['consomation']
    test_nv_mat=con.execute(text("select camion_mat from camion where camion_mat=:mat and camion_mat<>:mat_anc"),{"mat":mat,'mat_anc':mat_anc}).fetchone()
    if test_nv_mat:
        flash('La nouvelle immatriculation que vous venez de taper existe déjà, veuillez la modifier!', 'danger')
    else: 
        con.execute(text("update camion set camion_mat=:mat, camion_cap=:cap,camion_etat=:etat,camion_type=:typeC,camion_tonnage=:tonnage,camion_fonction=:fonction,camion_assurance=:assurance,camion_loyer=:loyer, camion_entretien=:entretien, camion_pneus=:pneus,camion_conso=:conso where camion_id=:cam_id"),{'mat':mat,"cap":cap, 'etat':int(etat[0]), 'typeC':typeC[0],'tonnage':tonnage, 'fonction':fonction[0], 'assurance':assurance, 'loyer':loyer, 'entretien': entretien,'pneus':pneus, 'conso':consomation, 'cam_id':cam_id[0]})
        flash('les  modifications ont été bien prises en compte', 'success')   
     
    return redirect(url_for('edit_camion'))  
    

#*************************************************************************************************Espace Enseigne***************************************************************
#**********AJOUTER enseigne**********
@app.route('/Ajouter_Enseigne', methods=['GET','post'])
def ajout_enseigne():
    enseigne=con.execute(text("select enseigne_intitulé from enseigne where enseigne_actif=1")).fetchall()
    data={ 'enseigne':enseigne, 'nbre_ens':len(enseigne)}
    if request.method=='POST':
        intitule=request.form['intitulé']
        test_ens1=con.execute(text("select enseigne_id from enseigne where enseigne_intitulé=:ens and enseigne_actif=1"),{'ens':intitule}).fetchone()
        test_ens2=con.execute(text("select enseigne_id from enseigne where enseigne_intitulé=:ens and enseigne_actif=0"),{'ens':intitule}).fetchone()
       
        if test_ens1:
            flash("cette enseigne existe déjà, veuillez changer l'intitulé", 'danger')
        elif test_ens2:
            con.execute(text("update enseigne set enseigne_actif=1 where enseigne_intitulé=:ens"),{'ens':intitule})
            con.execute(text("update magasin set magasin_actif=1 where enseigne_id=:ens_id"),{'ens_id':test_ens2[0]})
            flash("l'enseigne existait déjà et a été récupérée avec tous ses magasins",'success')
        else:
            con.execute(text("insert into enseigne (enseigne_intitulé) value (:ens)"),{'ens':intitule})
            nvl_ens_id=con.execute(text("select enseigne_id from enseigne where enseigne_intitulé=:ens"),{'ens':intitule}).fetchone()
            data['ens_intitulé']=intitule
            data['test_ens']=1
            data['nvl_ens_id']=nvl_ens_id[0]
            data['test_ajout_mag']=0
            flash("l'enseigne a été bien enregistrée, veuillez lui ajouter magasins et tarif navette",'success')
            return render_template('pages/mag_nvt_nvl_ens.html', **data)

    return render_template('pages/ajouter_enseigne.html', **data)

#**********MODIFIER enseigne**********
@app.route('/modification_enseigne', methods=['GET','post'])
def modifier_enseigne(): 
    rech_ens=''
    ens_select=''
    ens_info=[ '' for i in range(2)]

    liste_ens=con.execute(text("select enseigne_intitulé, enseigne_id from enseigne where enseigne_actif=1")).fetchall()
    data={ 'liste_ens': liste_ens,
            'rech_ens':rech_ens, 
            'ens_info':ens_info,
            'test':'bonjour'
    }
        
    if request.method=='POST':
        # Si l utilisateur a tapé un nom dans la bare de recherche:
        if request.form['rech_ens']:
            rech_ens=request.form['rech_ens']
            liste_ens=con.execute(text("select enseigne_intitulé, enseigne_id from enseigne where enseigne_intitulé LIKE :ens and enseigne_actif=1"), {'ens':rech_ens +'%'}).fetchall()
            liste_ens_rech=con.execute(text("select enseigne_intitulé , enseigne_id from enseigne where enseigne_intitulé LIKE :ens and enseigne_actif=1"), {'ens':rech_ens +'%'}).fetchall()                                                                                                  
            if liste_ens_rech:
                data['liste_ens']=liste_ens_rech
            else:
                flash(' aucune enseigne avec ce nom','danger')
            return render_template('pages/modifier_ens.html', **data)   
 
        # si l utilisateur a coché un nom:
        if request.form['ens_select']!='':
            ens_select=request.form['ens_select']
            ens_info=con.execute(text("select enseigne_intitulé, enseigne_id from enseigne where enseigne_intitulé=:ens_select and enseigne_actif=1"), {'ens_select':ens_select}).fetchone()
            data['ens_info']=ens_info
        
    return render_template('pages/modifier_ens.html', **data) 

#**********VALIDER MODIFICATION enseigne********** 
@app.route('/modification-enregistree', methods=['GET','post']) #+++++++++++++++++++++++++++++++++++vérifier la récupération de l id enseinge
def enseigne_modifier():
    ens_intitule=request.form['intitule']
    ens_id=request.form['ens_id']
    test_ens_id=con.execute(text("select enseigne_id from enseigne where enseigne_intitulé=:ens_intitule"), {'ens_intitule':ens_intitule}).fetchone()
    if test_ens_id:
        flash("Cet intitulé d'enseigne existe déjà, Veuillez le changer ",'danger')  
    else :
        con.execute(text("update enseigne set enseigne_intitulé=:ens_intitule where enseigne_id=:ens_id"),{'ens_intitule':ens_intitule, 'ens_id':ens_id})
        flash('les modifications ont été bien prises en compte', 'success')
    return redirect(url_for('modifier_enseigne'))
   
#**********SUPPRIMMER enseigne**********
@app.route('/Supprimer_Enseigne', methods=['GET','post'])
def supp_enseigne():
    ens=request.form['sup_ens']
    ens_id=con.execute(text('select enseigne_id from enseigne where enseigne_intitulé=:ens'), {'ens':ens}).fetchone()
    con.execute(text('update enseigne set enseigne_actif=0 where enseigne_intitulé=:ens'),{'ens':ens})
    con.execute(text('update magasin set magasin_actif=0 where enseigne_id=:ens'),{'ens':ens_id[0]})
    con.execute(text('update info_tarification set tarification_actif=0 where enseigne_id=:ens'),{'ens':ens_id[0]})
    flash('la suppression de l enseigne cochée a bien été prise en charge', 'success')
    
    return redirect(url_for('modifier_enseigne'))    
#***************************************************************************************************************************ESPACE CHAUFFEUR********************************************************************

@app.route('/chauffeur', methods=['GET','post'])
def espace_chauf():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
     
    return render_template('pages/espace_chauf.html')

   
#**************************************************************************************************************************AJOUTER CHAUFFEUR**********************************************************************
#
@app.route('/ajouter_chauf', methods=['GET','post'])
def ajouter_chauf():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    liste_contrat=con.execute(text("select contrat_id, contrat_intitule from contrat")).fetchall()
    liste_groupe=con.execute(text("select groupe_id, intitulé_groupe from groupe")).fetchall()
    data={ 'liste_contrat':liste_contrat,
            'liste_groupe':liste_groupe}
    if request.method=='POST':
        nom=request.form['nom']
        prenom=request.form['prenom']
        groupe=request.form.getlist('liste_groupe')
        contrat=request.form.getlist('liste_contrat')
        date_debut_contrat=request.form['date_D']
        date_fin_contrat=request.form['date_fin']
        cout=request.form['horaire']
        panier1=request.form['panier1']
        panier2=request.form['panier2']
        panier3=request.form['panier3']
        con.execute(text("insert into chauffeur (chauf_nom,chauf_prenom,groupe_id, chauf_cout_horaire,chauff_panier1,chauff_panier2,chauff_panier3) values (:nom,:prenom,:groupe,:cout,:panier1,:panier2,:panier3)"),{'nom':nom,'prenom':prenom,'groupe':groupe,'contrat':contrat,'date_D':date_debut_contrat,'date_fin':date_fin_contrat,'cout':cout,'panier1':panier1,'panier2':panier2,'panier3':panier3})
        chauf_id=con.execute(text("select max(chauf_id ) from chauffeur where chauf_nom=:nom and chauf_prenom=:prenom and groupe_id=:groupe"),{'nom':nom, 'prenom':prenom,'groupe':groupe}).fetchone()
        con.execute(text("insert into chauffeur_contrat (contrat_id,chauf_id, date_debut, date_fin) values (:contrat,:chauf_id,:date_D, :date_fin)"),{"contrat":contrat,'chauf_id':chauf_id[0],'date_D':date_debut_contrat,'date_fin':date_fin_contrat})
        flash("Le chauffeur a été bien ajouté!",'success')
    return render_template('pages/ajouter_chauf.html',**data)

    #***************************************************************************************************************************Ajouter Contrat à un chauffeur**********************************************************
@app.route('/ajout_contrat', methods=['GET','post'])
def ajouter_contrat_chauf():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    
    #liste chauffeurs
    requete_chauf="select chauf_id, chauf_nom, chauf_prenom, concat(chauf_nom,'---' ,chauf_prenom) as NP from chauffeur where chauf_actif=1"
    liste_chauf=con.execute(text(requete_chauf)).fetchall()
    
     #liste statuts
    requete_contrat=" select contrat_id, contrat_intitule from contrat"
    liste_contrat=con.execute(text(requete_contrat)).fetchall()

    data={
            'liste_chauf':liste_chauf,
            'liste_contrat':liste_contrat,
         }
    if request.method== 'POST':
        chauf_id=request.form['liste_chauf']  
        contrat_id=request.form['liste_contrat']
        date_debut=request.form['date_D']
        date_fin=request.form['date_F']
        requete_date_fin=' select chauf_id, date_fin from chauffeur_contrat where chauf_id=:chauf_id and (date_fin > :date_debut) '  
        ver_date_fin=con.execute(text(requete_date_fin), {'chauf_id':chauf_id , 'date_debut':date_debut}).fetchall()
        
        if date_debut>date_fin:
            flash('la date fin doit être supperieure à la date début', 'danger')
        elif ver_date_fin :
            flash('ce chauffeur a déjà un contrat en cours de cette période, si vous voulez lui attribuer un autre, veuillez liu arrêter son contrat à cette période en allant sur editer contrat chauffeur', 'danger') 
        else:
            con.execute(text('insert into chauffeur_contrat (chauf_id, contrat_id, date_debut, date_fin) values (:chauf_id, :contrat_id, :date_debut, :date_fin)'), {'chauf_id':chauf_id, 'contrat_id':contrat_id, 'date_debut': date_debut, 'date_fin': date_fin})    
            flash('ce contrat a été ajouté avec succès à ce chauffeur', 'success') 
        
    return render_template('pages/ajouter_contrat_chauf.html', **data)    


  #resultat_pseudo=request.args.get('resultat_pseudo')
  #********************************************************************************************************************VALIDER MODIFICATION CONTRAT CHAUFFEUR**************************************************************
@app.route('/chaufeur_contrat_modifié', methods=['GET','post']) # post de edit_contrat_chauf
def chauffeur_contrat_modifie():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    chauf_id=request.form['modal_chauf_id'] 
    anc_contrat_id=request.form['modal_anc_contrat_id']
    nv_contrat_id=request.form['modal_liste_contrat']
    anc_date_fin=request.form['modal_anc_date_fin']
    anc_date_deb=request.form['modal_anc_date_deb']
    nv_date_deb=request.form['modal_date_debut']
    nv_date_fin=request.form['modal_date_fin']
    test_contrat=con.execute(text("select chauf_id from chauffeur_contrat where chauf_id=:chauf_id and date_fin> :nv_date_deb and (contrat_id<>:anc_contrat_id and date_debut<>:anc_date_deb and date_fin<>:anc_date_fin)"),{'chauf_id':chauf_id, 'nv_date_deb':nv_date_deb, 'anc_contrat_id':anc_contrat_id, 'anc_date_deb':anc_date_deb,'anc_date_fin':anc_date_fin}).fetchone()
    if nv_date_deb>nv_date_fin:
            flash('la date fin doit être supperieure à la date début', 'danger')
    elif test_contrat:  
         flash('Veuillez vérifier la date début, elle est comprise dans un autre contrat de ce chauffeur', 'danger')   
    else :
        con.execute(text("update chauffeur_contrat set chauf_id=:chauf_id, contrat_id=:nv_contrat_id, date_debut=:nv_date_deb, date_fin=:nv_date_fin where chauf_id=:chauf_id and contrat_id=:anc_contrat_id and date_debut=:anc_date_deb and date_fin= :anc_date_fin"),{'chauf_id':chauf_id, 'nv_contrat_id':nv_contrat_id,'nv_date_deb':nv_date_deb,'nv_date_fin':nv_date_fin, 'anc_contrat_id':anc_contrat_id , 'anc_date_deb':anc_date_deb ,'anc_date_fin': anc_date_fin})
        flash('les modifications ont été bien prises en compte', 'success')
    return redirect(url_for('edit_contrat_chauf'))

    #**************************************************************************************************************VALIDER SUPPRESSION CONTRAT CHAUFFEUR**********************************************************************
@app.route('/chaufeur_contrat_supprime', methods=['GET','post'])
def chauffeur_contrat_supprime():#++++++++++++++++++++++++++++++++++++UPDATE ne marche pas 
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    chauf_id=request.form['chauf_id']
    contrat_id=request.form['contrat_id']
    date_debut=request.form['date_deb']
    date_fin=request.form['date_fin']
    con.execute(text("delete from chauffeur_contrat where chauf_id=:chauf_id and contrat_id=:contrat_id and date_debut=:date_debut and date_fin=:date_fin"),{'chauf_id':chauf_id, 'contrat_id':contrat_id, 'date_debut':date_debut,'date_fin':date_fin})
    flash('Ce Contrat a été bien suppirmé pour ce Chauffeur', 'success')
    return redirect(url_for('edit_contrat_chauf'))
    
#************************************************************************************************************************EDITER CONTRAT CHAUFFEUR********************************************************************************************************************************************
@app.route('/modification_contrat_chauffeur', methods=['GET','post'])
def edit_contrat_chauf():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    rech_chauf=''
    chauf_select=''
    chauf_info=[ '' for i in range(9)]
    liste_chauf= con.execute(text("select chauf_nom, chauf_prenom, contrat_intitule, date_debut, date_fin, chauffeur.chauf_id , contrat.contrat_id  from chauffeur left join  chauffeur_contrat on chauffeur_contrat.chauf_id= chauffeur.chauf_id left join contrat on contrat.contrat_id = chauffeur_contrat.contrat_id where date_fin>date(now()) and chauf_actif=1")).fetchall()
    liste_contrat=con.execute(text("select contrat_id, contrat_intitule from contrat")).fetchall()
    
    data={ 'liste_chauf': liste_chauf,
            'rech_chauf':rech_chauf, 
            'chauf_info':chauf_info,
            'liste_contrat': liste_contrat,
          }
    if request.method=='POST':
        # Si l utilisateur a tapé un nom dans la bare de recherche:
        #chauf_select=request.form.getlist('chauf_select')
        if request.form['rech_chauf']:
            rech_chauf=request.form['rech_chauf']
            liste_chauf_rech=con.execute(text("select chauf_nom, chauf_prenom, contrat_intitule, date_debut, date_fin,chauffeur.chauf_id , contrat.contrat_id    from chauffeur left join  chauffeur_contrat on chauffeur_contrat.chauf_id= chauffeur.chauf_id left join contrat on contrat.contrat_id = chauffeur_contrat.contrat_id where (date_fin>date(now()) or date_fin is null) and chauf_actif=1 and (chauf_nom LIKE :chauf or chauf_prenom LIKE :chauf_pr )"), {'chauf':rech_chauf +'%', 'chauf_pr':rech_chauf +'%'}).fetchall()
            if liste_chauf_rech:
                data['liste_chauf']=liste_chauf_rech
            else:
                flash(' aucun chauffeur avec ce nom','danger')
            return render_template('pages/edit_contrat_chauf.html', **data)   
        # si l utilisateur a coché un nom:
                   
        if request.form['chauf_select']!='':
            chauf_select=request.form['chauf_select']
            chauf_info=con.execute(text("select chauf_nom, chauf_prenom, contrat_intitule, date_debut, date_fin, chauffeur.chauf_id , contrat.contrat_id    from chauffeur left join  chauffeur_contrat on chauffeur_contrat.chauf_id= chauffeur.chauf_id left join contrat on contrat.contrat_id = chauffeur_contrat.contrat_id where chauffeur.chauf_id=:chauf_select and chauf_actif=1 and (date_fin>date(now()) or date_fin is null) "), {'chauf_select':chauf_select}).fetchone()
            data['chauf_info']=chauf_info
            #return render_template('pages/edit_statut_chauf.html', **data)
       
    return render_template('pages/edit_contrat_chauf.html', **data)   
  

#**************************************************************************************************************VALIDER SUPPRESSION CHAUFFEUR**********************************************************************
@app.route('/chaufeur_supprime', methods=['GET','post'])
def chauffeur_supprime():#++++++++++++++++++++++++++++++++++++UPDATE ne marche pas 
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    chauf_id=request.form['chauf_id']
    contra_date_fin=request.form['contra_date_fin']
    test_contrat=con.execute(text("select max(date_fin),date_debut from chauffeur_contrat where chauf_id=:chauf_id "),{'chauf_id':chauf_id}).fetchone()
    if test_contrat[1]> datetime.strptime(contra_date_fin, '%Y-%m-%d').date():
        flash(" Veuillez vérifier la date fin du contrat, elle est inférieure à la date début du contrat en cours", 'danger')    
        return redirect(url_for('edit_contrat_chauf'))
                
    con.execute(text("update chauffeur_statut set date_fin=:contra_date_fin where chauff_id=:chauf_id and date_fin>= :contra_date_fin"),{'chauf_id':chauf_id, 'contra_date_fin':contra_date_fin})    
    con.execute(text("update chauffeur_contrat set date_fin=:contra_date_fin where chauf_id=:chauf_id and date_fin>= :contra_date_fin"),{'chauf_id':chauf_id, 'contra_date_fin':contra_date_fin})
    con.execute(text("update chauffeur set chauf_actif='0' where (chauf_id=:chauf_id)"),{'chauf_id':chauf_id})    
    flash('Ce chauffeur a été bien supprimé ainsi que son contrat en cours a été arrêté ', 'success')
    return redirect(url_for('modifier_chauffeur'))

 #*************************************************************************************************************VALIDER MODIFICATION STATUT CHAUFFEUR**************************************************************
@app.route('/chaufeur_statut_modifié', methods=['GET','post']) # post de edit_statut_chauf
def chauffeur_statut_modifie():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    chauf_id=request.form['modal_chauf_id'] 
    anc_statut_id=request.form['modal_anc_stat_id']
    nv_statut_id=request.form['modal_liste_statut']
    anc_date_fin=request.form['modal_anc_date_fin']
    anc_date_deb=request.form['modal_anc_date_deb']
    nv_date_deb=request.form['modal_date_debut']
    nv_date_fin=request.form['modal_date_fin']
    nv_RC=request.form['modal_RC']
    nv_CP=request.form['modal_CP']
    if nv_date_deb>nv_date_fin:
            flash('la date fin doit être supperieure à la date début', 'danger')
    elif anc_statut_id =="None":
        test_statut_vide=con.execute(text("select chauff_id from chauffeur_statut where chauff_id=:chauf_id and date_fin> :nv_date_deb"),{'chauf_id':chauf_id, 'nv_date_deb':nv_date_deb}).fetchone()
        if test_statut_vide:
            flash('Veuillez vérifier la date début, elle est comprise dans un autre statut pour ce chauffeur', 'danger')   
        else:
            con.execute(text("insert into chauffeur_statut (chauff_id,statut_id,date_debut,date_fin) values (:chauf_id, :nv_statut_id, :date_deb, :date_fin)"),{'chauf_id':chauf_id, 'nv_statut_id':nv_statut_id,'date_deb':nv_date_deb,'date_fin':nv_date_fin} )    
            flash('les modifications ont été bien prises en compte', 'success')
    else:       
        test_statut=con.execute(text("select chauff_id from chauffeur_statut where chauff_id=:chauf_id and date_fin> :nv_date_deb and (statut_id<>:anc_statut_id and date_debut<>:anc_date_deb and date_fin<>:anc_date_fin)"),{'chauf_id':chauf_id, 'nv_date_deb':nv_date_deb, 'anc_statut_id':anc_statut_id, 'anc_date_deb':anc_date_deb,'anc_date_fin':anc_date_fin}).fetchone()
        if test_statut:
            flash('Veuillez vérifier la date début, elle est comprise dans un autre statut pour ce chauffeur', 'danger') 
        else:   
            con.execute(text("update chauffeur_statut set chauff_id=:chauf_id, statut_id=:nv_statut_id, date_debut=:nv_date_deb, date_fin=:nv_date_fin where chauff_id=:chauf_id and statut_id=:anc_statut_id and date_debut=:anc_date_deb and date_fin= :anc_date_fin"),{'chauf_id':chauf_id, 'nv_statut_id':nv_statut_id,'nv_date_deb':nv_date_deb,'nv_date_fin':nv_date_fin, 'anc_statut_id':anc_statut_id , 'anc_date_deb':anc_date_deb ,'anc_date_fin': anc_date_fin})
            CP_id=con.execute(text("select statut_id from statut where statut_intitule='Congé Payé'")).fetchone()
            RC_id=con.execute(text("select statut_id from statut where statut_intitule='Repos Compensé'")).fetchone()
            if int(anc_statut_id)==int(CP_id[0]):
                anc_soldeCP=float(nv_CP)+  jourOuvrable(anc_date_deb,anc_date_fin)
                con.execute(text("update chauffeur set solde_CP=:anc_soldeCP where chauf_id=:chauf_id "),{'anc_soldeCP':anc_soldeCP,'chauf_id':chauf_id})         
            elif int(anc_statut_id)==int(RC_id[0]):
                anc_soldeRC=float(nv_RC)+jourOuvrable(anc_date_deb,anc_date_fin)
                con.execute(text("update chauffeur set solde_RC=:anc_soldeRC where chauf_id=:chauf_id "),{'anc_soldeRC':anc_soldeRC,'chauf_id':chauf_id})         
            if int(nv_statut_id)==int(CP_id[0]):
                nv_CP=con.execute(text("select solde_CP from chauffeur where chauf_id=:chauf_id"),{'chauf_id':chauf_id}).fetchone()
                nv_soldeCP=float(nv_CP[0])-jourOuvrable(nv_date_deb,nv_date_fin)
                con.execute(text("update chauffeur set solde_CP=:nv_soldeCP where chauf_id=:chauf_id "),{'nv_soldeCP':nv_soldeCP,'chauf_id':chauf_id})         
            elif int(nv_statut_id)==int(RC_id[0]):
                nv_RC=con.execute(text("select solde_RC from chauffeur where chauf_id=:chauf_id"),{'chauf_id':chauf_id}).fetchone()
                nv_soldeRC=float(nv_RC[0])-jourOuvrable(nv_date_deb,nv_date_fin)
                con.execute(text("update chauffeur set solde_RC=:nv_soldeRC where chauf_id=:chauf_id "),{'nv_soldeRC':nv_soldeRC,'chauf_id':chauf_id})         
          
            flash('les modifications ont été bien prises en compte', 'success')
    return redirect(url_for('edit_staut_chauf'))
     


#***********************************************************************************EDITER STATUT CHAUFFEUR********************************************************************************************************************************************
@app.route('/modification_statut_chauffeur', methods=['GET','post'])
def edit_staut_chauf():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    rech_chauf=''
    chauf_select=''
    chauf_info=[ '' for i in range(9)]
    liste_chauf= con.execute(text("select chauf_nom, chauf_prenom, statut_intitule, date_debut, date_fin, chauf_id , statut.statut_id, chauffeur.solde_RC, chauffeur.solde_CP  from chauffeur  left join  chauffeur_statut on chauffeur_statut.chauff_id= chauffeur.chauf_id and (date_fin>date(now()) or date_fin is null) left join statut on statut.statut_id = chauffeur_statut.statut_id where chauf_actif=1")).fetchall()
    liste_statut=con.execute(text("select statut_id, statut_intitule from statut")).fetchall()
    data={ 'liste_chauf': liste_chauf,
            'rech_chauf':rech_chauf, 
            'chauf_info':chauf_info,
            'liste_statut': liste_statut,
            'test':'bonjour'
    }
       
    if request.method=='POST':
        # Si l utilisateur a tapé un nom dans la bare de recherche:
        
        if request.form['rech_chauf']:
            rech_chauf=request.form['rech_chauf']
            liste_chauf_rech=con.execute(text("select chauf_nom, chauf_prenom, statut_intitule, date_debut, date_fin, chauf_id , statut.statut_id, solde_RC, solde_CP   from chauffeur left join  chauffeur_statut on chauffeur_statut.chauff_id= chauffeur.chauf_id  and (date_fin>date(now()) or date_fin is null) left join statut on statut.statut_id = chauffeur_statut.statut_id where chauf_actif=1 and (chauf_nom LIKE :chauf or chauf_prenom LIKE :chauf_pr )"), {'chauf':rech_chauf +'%', 'chauf_pr':rech_chauf +'%'}).fetchall()
            if liste_chauf_rech:
                data['liste_chauf']=liste_chauf_rech
            else:
                flash(' aucun chauffeur avec ce nom','danger')
            return render_template('pages/edit_statut_chauf.html', **data)   
        # si l utilisateur a coché un nom:
                   
        if request.form['chauf_select']!='':
            chauf_select=request.form['chauf_select']
            chauf_info=con.execute(text("select chauf_nom, chauf_prenom, statut_intitule, date_debut, date_fin, chauf_id, statut.statut_id, solde_RC, solde_CP   from chauffeur left join  chauffeur_statut on chauffeur_statut.chauff_id= chauffeur.chauf_id and (date_fin>date(now()) or date_fin is null) left join statut on statut.statut_id = chauffeur_statut.statut_id where chauf_id=:chauf_select and chauf_actif=1 "), {'chauf_select':chauf_select}).fetchone()
            data['chauf_info']=chauf_info
            #return render_template('pages/edit_statut_chauf.html', **data)
       
    return render_template('pages/edit_statut_chauf.html', **data)   
#*************************************************************************************************************************************Ajouter statut à un chauffeur**********************************************************
@app.route('/ajout_statut', methods=['GET','post'])
def ajouter_statut_chauf():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    #liste chauffeurs
    requete_chauf="select chauf_id, chauf_nom, chauf_prenom, concat(chauf_nom,'---' ,chauf_prenom) as NP, solde_CP, solde_RC from chauffeur where chauf_actif=1"
    liste_chauf=con.execute(text(requete_chauf)).fetchall()
    
     #liste statuts
    requete_statu=" select STATUT_ID, STATUT_INTITULE from statut"
    liste_statut=con.execute(text(requete_statu)).fetchall()

    data={
            'liste_chauf':liste_chauf,
            'liste_statut':liste_statut,
        }
    if request.method== 'POST':
        chauf_id=request.form['liste_chauf']  
        statut_id=request.form['liste_statut']
        date_debut=request.form['date_D']
        date_fin=request.form['date_F']
        requete_date_fin=' select chauff_id, date_fin, date_debut from chauffeur_statut where chauff_id=:chauf_id and ( (:date_debut between date_debut and date_fin) or  (:date_fin between date_debut and date_fin) ) '  
        ver_date_fin=con.execute(text(requete_date_fin), {'chauf_id':chauf_id , 'date_debut':date_debut, 'date_fin':date_fin}).fetchall()
        
        if date_debut>date_fin:
            flash('la date fin doit être supperieure à la date début', 'danger')
        elif ver_date_fin :
            flash('ce chauffeur a déjà un statut pour cette date', 'danger') 
        else:
            con.execute(text('insert into chauffeur_statut (chauff_id, statut_id, date_debut, date_fin) values (:chauf_id, :statut_id, :date_debut, :date_fin)'), {'chauf_id':chauf_id, 'statut_id':statut_id, 'date_debut': date_debut, 'date_fin': date_fin})    
            CP_id=con.execute(text("select statut_id from statut where statut_intitule='Congé Payé'")).fetchone()
            RC_id=con.execute(text("select statut_id from statut where statut_intitule='Repos Compensé'")).fetchone()
            solde=con.execute(text("select solde_CP,solde_RC from chauffeur where chauf_id=:chauf_id"),{'chauf_id':chauf_id}).fetchone()
            if int(statut_id)==int(CP_id[0]):
                nv_CP=float(solde[0])-jourOuvrable(date_debut,date_fin)
                con.execute(text("update chauffeur set solde_CP=:nv_soldeCP where chauf_id=:chauf_id "),{'nv_soldeCP':nv_CP,'chauf_id':chauf_id})         

            elif int(statut_id)==int(RC_id[0]):
                nv_RC=float(solde[1])-jourOuvrable(date_debut,date_fin)
                con.execute(text("update chauffeur set solde_RC=:nv_soldeRC where chauf_id=:chauf_id "),{'nv_soldeRC':nv_RC,'chauf_id':chauf_id})         
            flash('ce statut a été ajouté avec succès à ce chauffeur', 'success') 
        
    return render_template('pages/ajouter_statut_chauf.jinja', **data)    

#**********************************************************************************************************************Editer un Chauffeur********************************************************************
@app.route('/modification_chauffeur', methods=['GET','post'])
def modifier_chauffeur():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    rech_chauf=''
    chauf_select=''
    chauf_info=[ '' for i in range(9)]
    liste_groupe=con.execute(text("select groupe_id, intitulé_groupe from groupe")).fetchall()
    liste_chauf= con.execute(text("select chauf_nom, chauf_prenom, chauf_cout_horaire, chauff_panier1, chauff_panier2, chauff_panier3, chauf_id, chauffeur.groupe_id,intitulé_groupe, solde_RC,solde_CP from chauffeur  join groupe on groupe.groupe_id=chauffeur.groupe_id and chauf_actif=1")).fetchall()
    data={ 'liste_chauf': liste_chauf,
            'rech_chauf':rech_chauf, 
            'chauf_info':chauf_info,
            'test':'bonjour',
            'liste_groupe':liste_groupe
         }
       
    if request.method=='POST':
        # Si l utilisateur a tapé un nom dans la bare de recherche:
        if request.form['rech_chauf']:
            rech_chauf=request.form['rech_chauf']
            liste_chauf_rech=con.execute(text("select chauf_nom, chauf_prenom, chauf_cout_horaire, chauff_panier1, chauff_panier2, chauff_panier3, chauf_id, chauffeur.groupe_id,intitulé_groupe   from chauffeur  join groupe on groupe.groupe_id=chauffeur.groupe_id  where  (chauf_nom LIKE :chauf or chauf_prenom LIKE :chauf)  and chauf_actif=1 "), {'chauf': rech_chauf +'%'}).fetchall()
            if liste_chauf_rech:
                data['liste_chauf']=liste_chauf_rech
            else:
                flash(' aucun chauffeur avec ce nom','danger')
            return render_template('pages/modifier_chauf.html', **data)   
        # si l utilisateur a coché un nom:
            
            
        if request.form['chauf_select']!='':
            chauf_select=request.form['chauf_select']
            chauf_info=con.execute(text("select chauf_nom, chauf_prenom, chauf_cout_horaire, chauff_panier1, chauff_panier2, chauff_panier3, chauf_id, chauffeur.groupe_id,intitulé_groupe from chauffeur join groupe on groupe.groupe_id=chauffeur.groupe_id where chauf_id=:chauf_select and  chauf_actif=1"), {'chauf_select':chauf_select}).fetchone()
            data['chauf_info']=chauf_info
            #return render_template('pages/modifier_chauf.html', **data)
        
    return render_template('pages/modifier_chauf.html', **data)   
#**********************************************************************************VALIDER MODIFICATION CHAUFFEUR*****************************************************************

@app.route('/chaufeur_modifié', methods=['GET','post'])
def chauffeur_modifie():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    chauf_id=request.form['chauf_id']
    nom=request.form['nom'] 
    prenom=request.form['prenom']
    groupe=request.form.getlist('modal_liste_groupe')
    solde_RC=request.form['RC']
    solde_CP=request.form['CP']
    horaire=request.form['horaire']
    panier1=request.form['panier1']
    panier2=request.form['panier2']
    panier3=request.form['panier3']
    con.execute(text("update chauffeur set chauf_nom=:nom, chauf_prenom=:prenom, groupe_id=:groupe, solde_RC=:solde_RC, solde_CP=:solde_CP, chauf_cout_horaire=:horaire,chauff_panier1=:panier1,chauff_panier2=:panier2, chauff_panier3=:panier3 where chauf_id=:chauf_id"),{'nom':nom,'prenom':prenom,'groupe':groupe[0],'solde_RC':solde_RC,'solde_CP':solde_CP,'horaire':horaire,'panier1':panier1,'panier2':panier2,'panier3':panier3,'chauf_id':chauf_id})
    flash("Les modifications ont bien été prise en compte!",'success')
    return redirect(url_for('modifier_chauffeur'))   

#************************************************************************************TABLEAU RECAP CHAUFFEUR***********************************************
@app.route('/tableau_recap_chauffeur',methods=['GET','post']) 
def tableau_recap_chauffeur():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    L_groupe=con.execute(text("select groupe_id, intitulé_groupe from groupe")).fetchall()
    if request.method=='POST':
        date_D=request.form['date_D']
        date_fin=request.form['date_fin']
        groupe_select=request.form.getlist('L_groupe') 
        intitulé_groupe=con.execute(text("select groupe_id,intitulé_groupe from groupe where groupe_id in :groupe_select"),{'groupe_select':groupe_select}).fetchall()
        L_chauf=[con.execute(text("select chauf_id,chauf_nom,chauf_prenom,solde_RC,solde_CP  from chauffeur join groupe on groupe.groupe_id=chauffeur.groupe_id where chauffeur.groupe_id = :groupe_id"),{'groupe_id':groupe}).fetchall() for groupe in groupe_select]
        L_chauf_complete=con.execute(text("select chauf_id, chauf_nom, chauf_prenom, groupe_id from chauffeur where chauf_actif=1"))
        L_chauf_statut=con.execute(text("select chauf_id, chauffeur_statut.statut_id,statut, date_debut,date_fin from chauffeur join groupe on groupe.groupe_id= chauffeur.groupe_id join chauffeur_statut on chauffeur_statut.chauff_id=chauffeur.chauf_id and date_debut>=:date_debut and date_fin<=:date_fin join statut on statut.statut_id=chauffeur_statut.statut_id"),{'date_debut':date_D,'date_fin':date_fin}).fetchall()
        L_jour=['L','M','M','J','V','S','D']
        jour1=datetime.strptime(date_D,"%Y-%m-%d").weekday()
        nbre_jour=con.execute(text("select datediff(:date_fin,:date_D),month(:date_D),month(:date_fin)"),{'date_D':date_D,'date_fin':date_fin}).fetchone()
        date=datetime.strptime(date_D,"%Y-%m-%d")
        L_jour_select=[]
        mois=[]
        day=[]
        L_date=[]
        solde=[]
        
        for j in range(nbre_jour[0]):
            moisJour=con.execute(text("select month(:date),day(:date),year(:date)"),{'date':date}).fetchone()
            day.append((moisJour[1],date.weekday()))
            if (moisJour[0],moisJour[2]) not in mois:
                mois.append((moisJour[0],moisJour[2]))
            
            L_date.append((date,moisJour[0],date.weekday()))
            date=date+timedelta(days=1)
            if jour1>6:
                jour1=0
            L_jour_select.append((L_jour[jour1],moisJour[0],date))  
            jour1+=1
        jourD=con.execute(text("select month(:date_fin),day(:date_fin)"),{'date_fin':date_fin}).fetchone()
        day.append((jourD[1],datetime.strptime(date_fin,"%Y-%m-%d").weekday()))   
        L_date.append((datetime.strptime(date_fin,"%Y-%m-%d"),jourD[0],datetime.strptime(date_fin,"%Y-%m-%d").weekday()))
        L_jour_select.append((L_jour[datetime.strptime(date_fin,"%Y-%m-%d").weekday()],jourD[0]))
        for ms in mois:
            if ms[0]==1:
                solde.append(con.execute(text("select chauf_id,solde_RC,solde_CP, mois, année from solde where mois=12 and année=:année"),{'année':ms[1]-1}).fetchall())
            else:
                solde.append(con.execute(text("select chauf_id,solde_RC,solde_CP, mois, année from solde where mois=:mois and année=:année"),{'mois':ms[0]-1,'année':ms[1]}).fetchall())
        cp=-1
        #for mois in range(mois):
            
        cptJourMois=[]
        nbreCaseVide=2
        j=0
        for ms in mois:
            j+=1
            cpt=0
            for jr in L_jour_select:
                if jr[1]==ms[0]:
                    cpt+=1
            nbreCaseVide+=cpt        
            cptJourMois.append(cpt)
        nbreCaseVide=nbreCaseVide+(j-1)

        dateDebConvert=datetime.strptime(date_D, "%Y-%m-%d").strftime("%d-%m-%Y")
        dateFinConvert=datetime.strptime(date_fin, "%Y-%m-%d").strftime("%d-%m-%Y")
      
        data={'intitulé_groupe':intitulé_groupe,
          'nbreCaseVide':nbreCaseVide,
          'cptJourMois':cptJourMois,
          'nbre_groupe':len(L_groupe),
          'groupe_select':groupe_select,
          'L_chauf':L_chauf,
          'L_chauf_statut':L_chauf_statut,
          'L_chauf_complete':L_chauf_complete,
          'L_jour_select':L_jour_select,
          'nbre_jour':len(L_jour_select),
          'dateDebConvert':dateDebConvert,
          'dateFinConvert':dateFinConvert,
           'mois':mois,
          'nbre_mois':len(mois),
          'jour':day,
          'L_date':L_date,
          'solde':solde,
          'nbre_solde':len(solde)
          
        }      
        path_wkhtmltopdf = r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe'
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        rendered=render_template('pages/tableau_recap_chauf.html',**data)
        rendered=rendered
        pdf =pdfkit.from_string(rendered, False, configuration=config)
        response=make_response(pdf)
        response.headers['Content-Type']='application/pdf'
        response.headers['Content-Disposition']='attachment; filename=plannig_chauffeur.pdf'
        return response    
    data={'L_groupe':L_groupe} 
    return render_template('pages/formulaire_recap_chauf.html',**data)
#***********************************************************************************************************************Ajouter un utilisateur*********************************************************************

@app.route('/ajout_utilisateur', methods=['GET','post'])
def ajouter_user():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    Fpseudo=''
    Frole,Fmdp,FCmdp,Fnom,Fprenom='','','','',''
    requete_role="select role_id, role_intitule from role"
    role=con.execute(text(requete_role)).fetchall()
    role_n=[row[0] for row in role]
    nbre_role=len(role_n)
    data={
                'role_selec':Frole,
                'role':role,
                'nbre_role' : nbre_role,
                'pseudo':Fpseudo,
                'mdp':Fmdp,
                'Cmpd':FCmdp,
                'nom':Fnom,
                'prenom':Fprenom
         }
    if request.method =='POST':
        Frole=request.form['liste_roles']
        Fpseudo=request.form['pseudo']
        Fnom=request.form['nom']
        Fprenom=request.form['prenom']
        Fmdp=request.form['mdp']
        FCmdp=request.form['Cmdp']
        requet_pseudo=text('select utilisateur_id from utilisateur where utilisateur_pseudo=:pseudo')
        pseudo=con.execute(requet_pseudo,{'pseudo':Fpseudo}).fetchone()
        
        if pseudo:
            flash('ce pseudo existe déjà, veuillez le changer', 'danger')
        elif request.form['mdp'] != request.form['Cmdp']:
            flash('les deux mots de passe ne correspondent pas','danger')
        else:
           # Fmdp=hashlib.sha1(str.encode(Fmdp)).hexdigest()
            Fmdp=generate_password_hash(str(Fmdp))
            #requete_ajout="call create_utilisateur(:nom,:prenom,:mdp,:pseudo, :role)"
           
            """conect = pymysql.connect(host='localhost', user='simplon', password='Simplon2020', db='perrenot', cursorclass= pymysql.cursors.DictCursor)

            try:
                curseur = conect.cursor()
                curseur.execute("call create_utilisateur(?, ?, ?, ?, ?)", ('Janvier','fevier','mars','pseudo', 2))

            except Exception as e:
                print("exception occured: {}".format (e))

            finally:
                conect.close()
            curseur = conect.cursor()"""
            #curseur.execute("call create_utilisateur(?, ?, ?, ?, ?)", ['Janvier','fevier','mars','pseudo', 2])
            requete_ajout="INSERT INTO utilisateur (utilisateur_nom, utilisateur_prenom, utilisateur_MDP, utilisateur_pseudo, role_id) VALUES (:nom, :prenom, :mdp, :pseudo,:role)"

            con.execute(text(requete_ajout),{'nom': Fnom, 'prenom':Fprenom, 'mdp':Fmdp, 'pseudo':Fpseudo,'role':Frole})
            #con.execute(text("call create_utilisateur('Janvier','fevier','mars','pseudo', 2)"))
            flash("l'utilisateur a été bien enregistré", 'success')
            Fpseudo, Fnom, Fprenom, Fmdp, FCmdp, Frole ='', '', '', '', '', ''
            
        data['pseudo']=Fpseudo 
        data['nom']  =Fnom 
        data['prenom']=Fprenom
        data['mdp']=Fmdp
        data['role_selec']=Frole
        return render_template('pages/ajouter_utilisateur.jinja', **data)   
        
    else:
        return render_template('pages/ajouter_utilisateur.jinja', **data)    
#************************************************************************************************************************SUPPRIMER USER********************************************************************
@app.route('/supprimer_user', methods=['GET','post'])
def supprimer_user():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    rech_user=''
    user_select=''
    user_info=[ '' for i in range(9)]
    liste_user= con.execute(text("select utilisateur_id, utilisateur_pseudo, utilisateur_nom, utilisateur_prenom, role_intitule   from utilisateur  join role on role.role_id=utilisateur.role_id")).fetchall()
    data={ 'liste_user': liste_user,
            'rech_user':rech_user, 
            'user_info':user_info
         }
      
    if request.method=='POST':
        # Si l utilisateur a tapé un nom dans la bare de recherche:
        if request.form['rech_user']:
            rech_user=request.form['rech_user']
            liste_user_rech=con.execute(text("select utilisateur_id, utilisateur_pseudo, utilisateur_nom, utilisateur_prenom, utilisateur.role_id, role_intitule from utilisateur join role on role.role_id=utilisateur.role_id where  (utilisateur_pseudo LIKE :user or utilisateur_prenom LIKE :user or utilisateur_nom LIKE :user)   "), {'user': rech_user +'%'}).fetchall()
            if liste_user_rech:
                data['liste_user']=liste_user_rech
            else:
                flash(' le nom/pseudo que vous avez tapé ne correspond à aucun utilistateur','danger')
            return render_template('pages/supprimer_user.html', **data)   
        # si l utilisateur a coché un nom:
                   
        if request.form['user_select']!='':
            user_select=request.form['user_select']
            user_info=con.execute(text("select utilisateur_id, utilisateur_pseudo, utilisateur_nom, utilisateur_prenom from utilisateur  where  utilisateur_id = :user"), {'user':user_select}).fetchone()
            data['user_info']=user_info
            #return render_template('pages/modifier_chauf.html', **data)
        
    return render_template('pages/supprimer_user.html', **data) 
#***********************************************************************************************************************USER SUPPRIMé********************************************************************
@app.route('/user_supprimé', methods=['GET','post'])
def user_supprimé():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    user_supprimé=request.form['user_id']
    con.execute(text('delete from utilisateur where utilisateur_id=:user_id'),{'user_id': user_supprimé})
    flash("l'utilisateur a été bien supprimé",'success')
    return redirect(url_for('supprimer_user'))
    

#*******************************************************************************************Ajouter un MAGASN**************************************************************************
@app.route('/ajout_magasin', methods=['GET','post'])
def ajouter_magasin():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    Fcode, Fadresse, Fheure='', '', ''
    Frolls=0
    Fpal=0
    Fbox=0
    Fenseigne=''
    requete_ens="select enseigne_id, enseigne_intitulé from enseigne where enseigne_actif=1"
    enseigne=con.execute(text(requete_ens)).fetchall()
    ens_n=[row[0] for row in enseigne]
    nbre_ens=len(ens_n)
    data={
                'code':Fcode,
                'adresse':Fadresse,
                'heure' : Fheure,
                'rolls':Frolls,
                'palette':Fpal,
                'boxe':Fbox,
                'nbre_ens':nbre_ens,
                'enseigneS':Fenseigne,
                'enseigne':enseigne
         }
    if request.method =='POST':
        Fcode=request.form['code']
        Fadresse=request.form['adresse']
        Fheure=request.form['heure']
        Frolls=request.form['rolls']
        Fpal=request.form['palette']
        Fbox=request.form['boxe']
        Fenseigne=request.form['liste_ens']
        requet_magasin=text('select magasin_id from magasin where magasin_code=:code and enseigne_id=:enseigne and magasin_actif=1')
        magasin=con.execute(requet_magasin,{'code':Fcode, 'enseigne':Fenseigne}).fetchone()
        magasin_sup=con.execute(text("select magasin_id from magasin where magasin_code=:code and enseigne_id=:enseigne and magasin_actif=0"),{'code':Fcode, 'enseigne':Fenseigne}).fetchone()

        if magasin:
            flash('ce code magasin existe déjà pour cette enseigne, veuillez le changer!', 'danger')
            if request.form['nvl_ens']!="":
                return render_template('pages/mag_nvt_nvl_ens.html', **data)
        elif magasin_sup:
            con.execute(text("update magasin set magasin_actif=1, magasin_adresse=:mag_adr, magasin_heure_livr=:heure_livr, magasin_tarif_rolls=:tarif_rolls, magasin_tarif_palette=:tarif_pal where magasin_id= :mag_id "),{'mag_id':magasin_sup[0], 'mag_adr': Fadresse ,'heure_livr': Fheure,'tarif_rolls': Frolls,'tarif_pal': Fpal })
            flash('ce code magasin supprimé existait déjà pour cette enseigne, il a été récupéré', 'success')   
        else:
              
            requete_ajout="INSERT INTO magasin (magasin_code, magasin_adresse, magasin_heure_livr, magasin_tarif_rolls, enseigne_id, magasin_tarif_palette, magasin_tarif_boxe) VALUES (:code, :adresse, :heure, :rolls,:enseigne, :pal, :boxe)"
            con.execute(text(requete_ajout),{'code': Fcode, 'adresse':Fadresse, 'heure':Fheure, 'rolls':Frolls,'enseigne':Fenseigne,'pal':Fpal, 'boxe':Fbox})
            Fcode=''
            Fadresse=''
            Fheure=''
            Frolls=''
            Fpal=''
            Fbox=''
            flash("le magasin a été bien enregistré", 'success')
            if request.form['nvl_ens']!="": # si on ajoute un magasin après avoir ajouté une nouvelle enseigne
                data['code']=Fcode
                data['adresse']  =Fadresse 
                data['heure']=Fheure
                data['rolls']=Frolls
                data['palette']=Fpal
                data['boxe']=Fbox
                data['ens_intitulé']=request.form['nvl_ens']
                data['nvl_ens_id']=Fenseigne
                data['test_ajout_mag']=1
                return render_template('pages/mag_nvt_nvl_ens.html', **data)
            else:  
                return redirect(url_for('ajouter_magasin'))
        data['code']=Fcode
        data['adresse']  =Fadresse 
        data['heure']=Fheure
        data['rolls']=Frolls
        data['palette']=Fpal
        data['boxe']=Fbox
        data['enseigneS']=Fenseigne
        return render_template('pages/ajouter_magasin.html', **data)   
        
    else:
        
        return render_template('pages/ajouter_magasin.html', **data)  
#*************************************************************************************************MAGASIN_SUPPRIME*********************************************************
@app.route('/suppression_enregistrée', methods=['GET','post']) # post de edit_statut_chauf
def magasin_supprime():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    mag_id=request.form['mag_id'] 
    con.execute(text("update magasin set magasin_actif=0 where magasin_id=:mag_id"),{'mag_id':mag_id})
    flash('Le magasin coché a été bien supprimé', 'success')
          
    return redirect(url_for('editer_magasin'))
#*************************************************************************************************MAGASIN_MODIFE*************************************************************
@app.route('/modification_enregistrée', methods=['GET','post']) # post de edit_statut_chauf
def magasin_modifie():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    anc_ens_id=request.form['enseigne_id'] 
    mag_code=request.form['code']
    adresse=request.form['adresse']
    heure_livraison=request.form['heure_livr']
    tarif_rolls=request.form['tarif_rolls']
    tarif_pal=request.form['tarif_pal']
    anc_code_mag=request.form['anc_code_mag']
    nv_ens_id=request.form.getlist('modal_ensNv')
    mag_facturé=request.form.getlist('modal_mag_facturé')
    test_mag_id=con.execute(text("select magasin_id from magasin where magasin_code=:mag_code and enseigne_id=:ens_id and magasin_code<>:anc_code_mag"),{'mag_code':mag_code, 'ens_id': nv_ens_id, 'anc_code_mag':anc_code_mag }).fetchone()
    if test_mag_id:
        flash('Ce code magsin existe déjà pour cette enesigne, veuillez le modifier', 'danger')
    else :
        con.execute(text("update magasin set magasin_code=:mag_code,magasin_adresse=:adresse,magasin_heure_livr=:heure_livraison,magasin_tarif_rolls=:tarif_rolls,magasin_tarif_palette=:tarif_pal,enseigne_id=:nv_ens_id, magasin_facturé=:mag_factur where enseigne_id=:anc_ens_id and magasin_code=:anc_code_mag"),{'mag_code':mag_code, 'adresse':adresse,'heure_livraison':heure_livraison,'tarif_rolls':tarif_rolls, 'tarif_pal':tarif_pal , 'nv_ens_id':nv_ens_id ,'anc_ens_id': anc_ens_id, 'anc_code_mag':anc_code_mag,'mag_factur':mag_facturé})
        flash('les modifications ont été bien prises en compte', 'success')
        
    return redirect(url_for('editer_magasin'))
     
#***********************************************************************************************Editer un Magasin**************************************************************************
@app.route('/modification_magasin', methods=['GET','post'])
def editer_magasin():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    rech_mag=''
    mag_select=''
    mag_info=[ '' for i in range(9)]
    liste_enseigne=con.execute(text("select enseigne_id, enseigne_intitulé from enseigne ")).fetchall()
    liste_magasin= con.execute(text("select magasin_id, magasin_code, magasin_adresse, magasin_heure_livr, magasin_tarif_rolls, magasin_tarif_palette, enseigne_intitulé, magasin.enseigne_id, magasin_facturé   from magasin join enseigne on enseigne.enseigne_id=magasin.enseigne_id  where magasin_actif=1")).fetchall()
    data={ 'liste_magasin': liste_magasin,
            'rech_mag':rech_mag, 
            'mag_info':mag_info,
            'liste_enseigne':liste_enseigne
            
         }
       
    if request.method=='POST':
        # Si l utilisateur a tapé un nom dans la bare de recherche:
        if request.form['rech_mag']:
            rech_mag=request.form['rech_mag']
            liste_mag_rech=con.execute(text("select magasin_id, magasin_code, magasin_adresse, magasin_heure_livr, magasin_tarif_rolls, magasin_tarif_palette, enseigne_intitulé, magasin.enseigne_id, magasin_facturé from magasin join enseigne on enseigne.enseigne_id=magasin.enseigne_id  where magasin_actif=1 and  (magasin_code LIKE :magC or enseigne.enseigne_intitulé LIKE :magC )  and magasin_actif=1 "), {'magC': rech_mag +'%'}).fetchall()
            if liste_mag_rech:
                data['liste_magasin']=liste_mag_rech
            else:
                flash(' Ce code magasin n exsiste pas','danger')
                data['rech_mag']=rech_mag
            return render_template('pages/edit_magasin.html', **data)   
        # si l utilisateur a coché un nom:
            
            
        if request.form['mag_select']!='':
            mag_select=request.form['mag_select']
            mag_info=con.execute(text("select magasin_id, magasin_code, magasin_adresse, magasin_heure_livr, magasin_tarif_rolls, magasin_tarif_palette, enseigne_intitulé, magasin.enseigne_id, magasin_facturé  from magasin join enseigne on enseigne.enseigne_id=magasin.enseigne_id where magasin.magasin_id=:mag_select and  magasin_actif=1"), {'mag_select':mag_select}).fetchone()
            #liste_mag_rech=con.execute(text("select magasin_id, magasin_code, magasin_adresse, magasin_heure_livr, magasin_tarif_rolls, magasin_tarif_palette, enseigne_intitulé    from magasin join enseigne on enseigne.enseigne_id=magasin.enseigne_id  where magasin_actif=1 and  (magasin_code LIKE :magC )  and magasin_actif=1 "), {'magC': rech_mag +'%'}).fetchall()
           
            data['mag_info']=mag_info
            #return render_template('pages/modifier_chauf.html', **data)
        
    return render_template('pages/edit_magasin.html', **data)  

   
#*******************************************************************************************************************************ENREGISTRER TOURNEES***********************************************************
@app.route('/enregistrement_tournees', methods=['get','post']) #post de valider_tournée.html
def enregistrer_tournee():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    test= 1
    if request.method=='POST':
        nom_chauf=request.form.getlist('nom_chauf')
        nom_chauf_ajout=request.form.getlist('nom_chauf_ajout')
        cam_mat_ajout=request.form.getlist('cam_mat_ajout')
        vlm_rolls=request.form.getlist('vlm_rolls')
        vlm_pal=request.form.getlist('vlm_pal')
        #vlm_box=request.form.getlist('vlm_box')
        mag_code=request.form.getlist('code_mag')
        camion=request.form.getlist('camion')
        date_tour=request.form['date_debut']
        mag_id=request.form.getlist('mag_id')
        nbMag_par_camion=request.form.getlist('Tnbre_mag_cam')
        cpt_mag=-1
        con.execute(text("delete from camion_magasin where date=:date_tour"),{'date_tour':date_tour})
        con.execute(text("delete from chauffeur_camion where date=:date_tour"),{'date_tour':date_tour})
        #Enregistrer les magasins affectés dans les camions SELECTIONNES
        for id, val in enumerate(nbMag_par_camion[:(len(nbMag_par_camion)-len(nom_chauf_ajout))]): 
            if int(val)!=0:
                ligne=1
                #mag_non_sauv=[]
                for i in range(int(val)):
                    cpt_mag+=1
                    ligneT=con.execute(text("select max(ligne) from chauffeur_camion where camion_id=:camion and date=:date"),{'camion':camion[id], 'date':date_tour}).fetchone()
                    #ligneT=con.execute(text("select ligne from chauffeur_camion where chauf_id=1 and camion_id=1 and date='2020-01-01'")).fetchone()
                    if ligneT[0] is not None:
                        ligne=int(ligneT[0])+1
                    con.execute(text(" insert into camion_magasin (camion_id, magasin_id, date, ligne, nbre_rolls, nbre_palette) values(:camion, :mag, :date, :ligne, :rolls, :pal)"), {'camion':camion[id],'mag':mag_id[cpt_mag], 'date':date_tour, 'ligne':ligne, 'rolls':vlm_rolls[cpt_mag], 'pal':vlm_pal[cpt_mag] })
                    con.execute(text("DELETE FROM magasin_journalier WHERE (mag_id = :mag) and (`date` = :date)"),{'mag':mag_id[cpt_mag], 'date':date_tour})
                con.execute(text("insert into chauffeur_camion (chauf_id, camion_id, date,ligne) values (:chauf, :camion, :date, :ligne)"), {'chauf': nom_chauf[id], 'camion':camion[id], 'date':date_tour, 'ligne':ligne})
        #Enregistrer les magasins affectés dans les camions AJOUTES
        if len(cam_mat_ajout) >0:
            for id, val in enumerate(nbMag_par_camion[-len(nom_chauf_ajout):]): 
                if int(val)!=0:
                    ligne=1
                    #mag_non_sauv=[]
                    for i in range(int(val)):
                        cpt_mag+=1
                        ligneT=con.execute(text("select max(ligne) from chauffeur_camion where camion_id=:camion and date=:date"),{'camion':cam_mat_ajout[id], 'date':date_tour}).fetchone()
                        #ligneT=con.execute(text("select ligne from chauffeur_camion where chauf_id=1 and camion_id=1 and date='2020-01-01'")).fetchone()
                        
                        if ligneT[0] is not None:
                            ligne=int(ligneT[0])+1
                                                    
                        con.execute(text(" insert into camion_magasin (camion_id, magasin_id, date, ligne, nbre_rolls, nbre_palette) values(:camion, :mag, :date, :ligne, :rolls, :pal)"), {'camion':cam_mat_ajout[id],'mag':mag_id[cpt_mag], 'date':date_tour, 'ligne':ligne, 'rolls':vlm_rolls[cpt_mag], 'pal':vlm_pal[cpt_mag] })
                        con.execute(text("DELETE FROM magasin_journalier WHERE (mag_id = :mag) and (`date` = :date)"),{'mag':mag_id[cpt_mag], 'date':date_tour})

                    con.execute(text("insert into chauffeur_camion (chauf_id, camion_id, date,ligne) values (:chauf, :camion, :date, :ligne)"), {'chauf': nom_chauf_ajout[id], 'camion':cam_mat_ajout[id], 'date':date_tour, 'ligne':ligne})

        con.execute(text("update magasin_journalier set statut_tournée=0 where  date = :date"),{'date':date_tour})
        #afficher les diagrammes

        requeteLivraison = pd.read_sql_query("SELECT e.enseigne_intitulé AS enseigne, m.magasin_id, magasin_tarif_rolls, magasin_tarif_palette, magasin_tarif_boxe FROM camion_magasin cm join magasin as m on m.magasin_id = cm.magasin_id join enseigne as e on e.enseigne_id = m.enseigne_id where date='%s' " %(date_tour), engine)

        dataLivraison = pd.DataFrame(requeteLivraison)
        ens=dataLivraison["enseigne"].value_counts()
        ens=ens.reset_index()
        ens=ens.rename(columns={'enseigne':'Nbre_mag_livrés', 'index':'enseigne'})
        
        data = [go.Pie(labels=ens.enseigne, values=ens.Nbre_mag_livrés, textposition='inside', textinfo='percent+label')] 
        layoutPieEns=go.Layout(title="1. Répartition des magasins livrés par Enseigne", )
        figPieEns=go.Figure(data=data, layout=layoutPieEns)
        graphJSON1 = json.dumps(figPieEns, cls=plotly.utils.PlotlyJSONEncoder)


        #requeteCasino = pd.read_sql_query("SELECT e.enseigne_intitulé AS enseigne, m.magasin_id, magasin_tarif_rolls, magasin_tarif_palette, magasin_tarif_boxe,nbre_rolls FROM camion_magasin cm join magasin as m on m.magasin_id = cm.magasin_id join enseigne as e on e.enseigne_id = m.enseigne_id where date='%s'  and magasin_tarif_rolls <>-1 and e.enseigne_intitulé='CASINO' "%(date_tour), engine)
        #rolls = pd.DataFrame(requeteCasino)
        #rolls= requeteCasino['magasin_tarif_rolls'].value_count()
        requeteCasinoFinale=pd.read_sql_query("select magasin_tarif_rolls, sum(nbre_rolls) as Nbre_rol from magasin join camion_magasin on camion_magasin.magasin_id=magasin.magasin_id and date='%s'  and magasin_tarif_rolls<>-1 and magasin_tarif_rolls<>0 join enseigne on enseigne.enseigne_id=magasin.enseigne_id and enseigne_intitulé='CASINO' group by magasin_tarif_rolls" %(date_tour), engine)
        #pal=requeteCasino['magasin_tarif_palette'].value_counts()
        #rolls=rolls.reset_index()
        #pal=pal.reset_index()
        #pal=pal.rename(columns={'index':'Tarif_pal', 'magasin_tarif_palette':'Nbre_mag'})
        #rolls=rolls.rename(columns={'index':'Tarif_Rolls', 'magasin_tarif_rolls':'Nbre_mag'})

        #dataAntho = [go.Pie(labels=rolls.Tarif_Rolls, values=rolls.Nbre_mag, textposition='inside',text=['€'], textinfo='percent+label+text') ] 
        data1 = [go.Pie(labels=requeteCasinoFinale.magasin_tarif_rolls, values=requeteCasinoFinale.Nbre_rol, textposition='inside',text=['€'], textinfo='percent+label+text') ] 

        layoutPieRolls=go.Layout(title='2. Répartition Tarif Rolls pour Casino', )
        figPieCam=go.Figure(data=data1, layout=layoutPieRolls)
        graphJSON2 = json.dumps(figPieCam, cls=plotly.utils.PlotlyJSONEncoder)
        
               
    flash('les tournées ont bien été enregistrées,', 'success') 
    dateConvertiTour=datetime.strptime(date_tour, "%Y-%m-%d").strftime("%d-%m-%Y")
    data={'test':test,
          'plot1':graphJSON1,
          'plot2':graphJSON2,
          'date_converti':dateConvertiTour,
          'date_tour':date_tour}
    return render_template('pages/diagram_apres_tournees.html',**data)                   
               
    #*******************************************************************************************************************************MODIFICATION TOURNEES***********************************************************
@app.route('/modification_tournees', methods=['get','post']) #post de valider_tournée.html
def modifier_tournees():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    
    if request.method=='POST':
        date_tour=request.form['date_tour']    
        camionPlus=request.form['camionPlus'] 
        magPlus=request.form['camionPlus']
        date_test=con.execute(text("select distinct date from camion_magasin where date=:date_tour"),{'date_tour':date_tour}).fetchone() 
        if date_test is None:
            flash("Pas de tournées enregistrées à cette date, Veuillez vérifier votre saisie!",'danger')
            return redirect(url_for('identification'))
        else:
            list_camion_mat=con.execute(text("call liste_camion()")).fetchall()
            L_chaufComplete=con.execute(text('call liste_chauffeur(:date_tour)'),{'date_tour':date_tour}).fetchall()
            L_chaufCam=con.execute(text("select chauf_id, camion.camion_id, ligne, camion_mat, camion_cap from chauffeur_camion join camion on camion.camion_id=chauffeur_camion.camion_id where date=:date_tour"),{'date_tour':date_tour}).fetchall()
            L_magasinNonAffect=con.execute(text('select mag_id,magasin.magasin_code,nbre_rolls, nbre_pal, magasin_heure_livr from magasin_journalier join magasin on  magasin.magasin_id = magasin_journalier.mag_id where date=:date_tour '),{'date_tour':date_tour}).fetchall()
            L_camion=con.execute(text("select distinct camion_magasin.camion_id, camion_mat, camion_cap from camion_magasin join camion on camion.camion_id=camion_magasin.camion_id where date=:date_tour"),{'date_tour':date_tour}).fetchall()
            L_magasin=[]   
            for camion in L_chaufCam:
                mag=con.execute(text("select camion_magasin.magasin_id, magasin_code, nbre_rolls, nbre_palette, magasin_heure_livr, ligne from camion_magasin join magasin on magasin.magasin_id=camion_magasin.magasin_id  where date=:date_tour and camion_id=:camion_id and ligne=:ligne order by magasin_heure_livr"),{'date_tour':date_tour,'camion_id':camion[1], 'ligne':camion[2]}).fetchall()
                L_magasin.append(mag)
            data={
                    'L_magasinNonAffect':L_magasinNonAffect,
                    'L_camion':L_camion,
                    'L_magasin':L_magasin,
                    'date_tour':date_tour,
                    'L_chaufComplete':L_chaufComplete,
                    'L_chaufCam':L_chaufCam,
                    'camionPlus':int(camionPlus),
                    'magPlus':int(magPlus),
                    'list_camion_mat':list_camion_mat
                 }
        return render_template('pages/modifier_tournées.html',**data)    

#**************************************************************************************************************************************************SELECTION MAGASINS***********************************************************

@app.route('/selection_magasin', methods=['get','post'])
def selection_magasins():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    if request.method=='POST':
        date_tour=request.form['date_tour']
        date_test=con.execute(text("select date from camion_magasin where date=:date_tour"),{'date_tour':date_tour}).fetchall()
        if len(date_test)>0:
            flash("Des tournées à cette date ont été enregistrées, si vous souhaitez les modifier, Veuillez vous rendre sur Tournée/Modifier Tournées",'danger')
            return redirect(url_for('identification'))    
        requete_nbre_ens='select count(*) from enseigne where enseigne_actif=1'
        nbre_ens=con.execute(text(requete_nbre_ens)).fetchone()[0]
        requete_ens='select enseigne_id,enseigne_intitulé from enseigne where enseigne_actif=1'
        liste_enseigne=con.execute(text(requete_ens)).fetchall()
        
        requete_camion="call liste_camion()"
        camion=con.execute(text(requete_camion)).fetchall()
        
        liste_mag=[con.execute(text("select magasin_code,magasin_id from magasin where enseigne_id=:enseigne and magasin_actif=1"),{'enseigne':liste_enseigne[j][0]}).fetchall() for j in range(len(liste_enseigne))]
        
        # récupérer le nombre d 'eneignes et les enseignes, camion et nbre camion pour les afficher dans la page
        dateTourConvert=datetime.strptime(date_tour, "%Y-%m-%d").strftime("%d-%m-%Y")
        data={
                'nbre_ens': nbre_ens,
                'L_enseigne': liste_enseigne,
                'camion' : camion,
                'liste_mag': liste_mag,
                'date_tour':date_tour,
                'dateTourConvert':dateTourConvert
            }
        
        return render_template('pages/selection_magasin.jinja',**data)
    
 #************************************************************ancienne selection magasins**********************************************
@app.route('/ancien_selection_magasin', methods=['get','post'])
def anc_selection_magasins():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    requete_nbre_ens='select count(*) from enseigne where enseigne_actif=1'
    nbre_ens=con.execute(text(requete_nbre_ens)).fetchone()[0]
    requete_ens='select enseigne_id,enseigne_intitulé from enseigne where enseigne_actif=1'
    liste_enseigne=con.execute(text(requete_ens)).fetchall()
    
    requete_camion="call liste_camion()"
    camion=con.execute(text(requete_camion)).fetchall()
       
    liste_mag=[con.execute(text("select magasin_code,magasin_id from magasin where enseigne_id=:enseigne and magasin_actif=1"),{'enseigne':liste_enseigne[j][0]}).fetchall() for j in range(len(liste_enseigne))]
       
    # récupérer le nombre d 'eneignes et les enseignes, camion et nbre camion pour les afficher dans la page
    test=0
    data={
            'nbre_ens': nbre_ens,
            'L_enseigne': liste_enseigne,
            'camion' : camion,
            'liste_mag': liste_mag,
            'test':test
        }
    if request.method=='POST':
        test=1
        data['test']=test
        liste_magasins=[]
        enseigne_intit=[]
        liste_ens_select=request.form.getlist('liste_ens')
        for ens in liste_ens_select:
            mag=con.execute(text("select magasin_code from magasin where enseigne_id= :ens"),{'ens':ens}).fetchall()
            liste_magasins.append(mag)   
            ens_int= con.execute(text("select enseigne_intitulé from enseigne where enseigne_id =:liste_ens"),{'liste_ens':ens}).fetchone()
            enseigne_intit.append(ens_int)
        data['liste_mag']=liste_magasins
        data['nbre_ens_selec']=len(liste_magasins)
        data['enseigne_intit']=enseigne_intit
        return render_template('pages/non_utilisées/selection_ens.jinja',**data)
          
    return render_template('pages/non_utilisées/selection_ens.jinja',**data)   

 #**********************************************************************************************************************VALIDER les MAGASINS CHOISIS**********************************************************       
@app.route('/effectuer-les-tournees', methods=['get','post'])
def valider_magasins():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    #camion_coche=request.form.getlist('liste_camion')
    list_camion_mat=con.execute(text("call liste_camion()")).fetchall()
    mag_coche=request.form.getlist('mag')
    rolls=request.form.getlist('rolls')
    palette=request.form.getlist('palette')
    nbre_rolls,nbre_pal=[],[]
    cpt=len(rolls)
    for i in range(cpt):
        if not (rolls[i]=='' and palette[i]==''):
            nbre_rolls.append(rolls[i])
            nbre_pal.append(palette[i])
            
    date=request.form['date']    
    camionPlus=request.form['camionPlus']
    magPlus=request.form['magPlus']
    #/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_//_/_/_EXTRAIRE LES MAGASINS A LIVRER DU FICHIER EXCEL/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
    mag_jour_casino = pd.read_excel('D:\\PerrenotStage\\alimentation_tables\\DocumentExploitation.xlsx', sheet_name=0, usecols=[7,9,10,11])
    mag_jour_casino.rename(columns={'Lib Mag':'magasin_adresse', 'H Mag':'magasin_heure_liv','Imm Mag': 'magasin_code', 'Rolls': 'nbre_rolls'}, inplace=True)
    mag_jour_casino=mag_jour_casino.groupby(['magasin_code','magasin_heure_liv','magasin_adresse' ])['nbre_rolls'].sum()
    mag_jour_casino=mag_jour_casino.reset_index()
    magasin_id        =[]
    magasin_Nexistants=[]
    mag_emb=[]
    casino_enseigne_id=pd.read_sql_query("select enseigne_id as ens_id from enseigne where enseigne_intitulé='CASINO' ", engine)['ens_id']
    mag_jour_casino['enseigne_id']=casino_enseigne_id[0]
    requete_mag_id="select magasin_id as id from magasin where magasin_code='%s' and enseigne_id='%s'"  
    for i in range(mag_jour_casino.shape[0]):
        mag_cd  =mag_jour_casino.iloc[i,0]
        ens_id  =mag_jour_casino.iloc[i,4]
        nbre_rol=mag_jour_casino.iloc[i,3]
        heur_liv=mag_jour_casino.iloc[i,1]
        mag_ad  =mag_jour_casino.iloc[i,2]
        if "EMB" in mag_cd:
            mag_emb.append(i)
        else:  # ne pas selectionner les magasins qui commencent par EMB
            mag_id=pd.read_sql_query(requete_mag_id %(mag_cd,ens_id), engine)['id']
            if  mag_id.empty:
                magasin_Nexistants.append((mag_cd,mag_ad,heur_liv))
                con.execute(text("insert into magasin (magasin_code, enseigne_id, magasin_heure_livr, magasin_adresse) values (:mag_code,:casino_enseigne_id, :heur_liv, :mag_ad)"), {'mag_code': mag_cd, 'casino_enseigne_id':int(casino_enseigne_id[0]),'heur_liv':heur_liv,'mag_ad':mag_ad})
            con.execute(text("insert into magasin_journalier (mag_id, nbre_rolls, date, magasin_code) values (:mag_id, :nbre_rolls, :date, :mag_code) on duplicate key update nbre_rolls=:nbre_rolls"), {'mag_id':int(mag_id[0]),'nbre_rolls':float(nbre_rol),'date':date,'mag_code': mag_cd})
            magasin_id.append(mag_id[0]) 
    if mag_emb:
        for i in range(len(mag_emb)):
            mag_jour_casino.drop(i,inplace=True)        
    mag_jour_casino['magasin_id']=magasin_id   
            
    #/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_//_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_//_//__/_/_/_/_/_/_/_/_/FIN/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/   

    # enregistrer les magasin cochés dans la table magasin journalier
    requete_mag_jour_code='select magasin_code from magasin where magasin_id=:magasin_id'     
       
    for j in range(len(nbre_rolls)):
        mag_code=con.execute(text(requete_mag_jour_code),{'magasin_id': mag_coche[j]}).fetchone()
        con.execute(text("insert into magasin_journalier (mag_id, nbre_rolls, nbre_pal, magasin_code, date) values(:mag_id, :nbre_rolls, :nbre_pal,  :magasin_code, :date) on duplicate key update nbre_rolls=:nbre_rolls and nbre_pal=:nbre_pal "), {'mag_id':mag_coche[j], 'nbre_rolls': nbre_rolls[j], 'nbre_pal': nbre_pal[j], 'magasin_code':mag_code[0], 'date':date,'nbre_rolls': nbre_rolls[j], 'nbre_pal': nbre_pal[j]})
        
    excel=request.form['fichier_excel']
    #récupérer le nombre de magains à livrer (sont stockés dans la table magasin_journalier)
    requete_nbre_mag='select count(*) from magasin_journalier where date=:date'
    nbre_mag=con.execute(text(requete_nbre_mag), {'date':date}).fetchone()[0]

    #récupérer les info des magasins à livrer 
    requete_mag_code='select magasin_journalier.magasin_code,nbre_rolls,nbre_pal,nbre_boxe, magasin_heure_livr, magasin_id from magasin_journalier join magasin on magasin.magasin_id =magasin_journalier.mag_id where magasin_journalier.date=:date'
    #requete_mag_code='select magasin_journalier.magasin_code,nbre_rolls,nbre_pal,nbre_boxe, magasin_heure_livr from magasin_journalier join magasin on magasin.magasin_id =magasin_journalier.mag_id'
  
    #mag_code=con.execute(text(requete_mag_code), {'date':date}).fetchall()
    mag_code=con.execute(text(requete_mag_code),{'date': date}).fetchall()

    #récupérer la liste des camion cochés
    camion=request.form.getlist('liste_camion')
   
     
    requete_camion="select camion_mat, camion_cap, camion_id from camion where camion_mat in :camion"
    liste_camion=con.execute(text(requete_camion),{'camion':camion}).fetchall()
    #nbre_camion=len([row[0] for row in liste_camion])
    #récupérer la liste des chauffeurs dispo
    chauffeur=con.execute(text('call liste_chauffeur(:date)'),{'date':date}).fetchall()
    # liste des magasins existants
    L_magains=con.execute(text("select magasin_id, magasin_code, magasin_heure_livr from magasin where magasin_actif=1")).fetchall()
    # données à envoyer a la page valider_tournée
    data={
                'nbre_mag': nbre_mag,
                'mag_code': mag_code,
                'chauffeur': chauffeur,
                'liste_camion':liste_camion,
                'date_tour':date, 
                'nbre_mag_Nexistant':len(magasin_Nexistants),
                'magasin_Nexistants':magasin_Nexistants,
                'list_camion_mat':list_camion_mat,
                'camionPlus':int(camionPlus),
                'magPlus':int(magPlus),
                'L_magains':L_magains
            }
    if   len(magasin_Nexistants)==0:     
        return render_template('pages/valider_tournee.html', **data)
    else:
        #flash('les magasins suivants:'magasin_Nexistants, 'danger') 
        mag_nExist="Erreur, les magasins suivant"+",".join(magasin_Nexistants)+" n'éxistaient pas et ont été ajoutés"
        flash(str(mag_nExist), 'danger')
        #return render_template('pages/valider_tournee.html', **data, return_msg={'msg':u'mag_nExist', 'type':u'danger'})
        return render_template('pages/valider_tournee.html', **data)
    
  #**********************************************************************************************************************************IMPRESSION FACTURATION JOURNALIERE APRES VALIDATION TOURNEES *******************************
@app.route('/facturation_journalière', methods=['get','post']) 
def facturation_journaliere():
    date_tour=request.form['date_tour']
    date_test=con.execute(text("select date from camion_magasin where date=:date_tour"),{'date_tour':date_tour}).fetchall()
    if len(date_test)==0:
        flash("Pas de tournées enregistrées à cette date!",'danger')
        return redirect(url_for('identification'))    
    #requeteLivraison = pd.read_sql_query('SELECT m.magasin_code, magasin_tarif_rolls, nbre_rolls, magasin_tarif_palette, nbre_palette, magasin_tarif_boxe, nbre_box FROM camion_magasin cm join camion on camion.camion_id=cm.camion_id and camion.camion_type<>"VL" join magasin as m on m.magasin_id = cm.magasin_id join enseigne as e on e.enseigne_id = m.enseigne_id where e.enseigne_intitulé ="CASINO" AND date ="%s" ;'%(date_tour), engine)
    requeteLivraison = con.execute(text('SELECT m.magasin_code, magasin_tarif_rolls, nbre_rolls, magasin_tarif_palette, nbre_palette, magasin_tarif_boxe, nbre_box FROM camion_magasin cm join camion on camion.camion_id=cm.camion_id and camion.camion_type<>"VL" join magasin as m on m.magasin_id = cm.magasin_id and magasin_facturé=1 join enseigne as e on e.enseigne_id = m.enseigne_id where e.enseigne_intitulé ="CASINO" AND date =:date_tour'),{'date_tour':date_tour}).fetchall()
    L_tarif=con.execute(text("select distinct magasin_tarif_rolls, magasin_tarif_palette from magasin join enseigne on enseigne.enseigne_id=magasin.enseigne_id and enseigne_intitulé='CASINO'  join camion_magasin on camion_magasin.magasin_id=magasin.magasin_id and date=:date_tour join camion on camion.camion_id=camion_magasin.camion_id and camion_type<>'VL' "),{'date_tour':date_tour}).fetchall()
    #requeteInfoTarif = pd.read_sql_query('SELECT intitule_tarif, tarif FROM info_tarification JOIN enseigne ON info_tarification.enseigne_id = enseigne.enseigne_id WHERE enseigne.enseigne_intitulé = "CASINO";', engine)
    L_trinome=con.execute(text("select magasin_code,magasin_tarif_rolls,nbre_rolls, magasin_tarif_palette, nbre_palette from camion_magasin join camion on camion.camion_id=camion_magasin.camion_id and camion_type='VL' and date=:date_tour join magasin on magasin.magasin_id=camion_magasin.magasin_id and magasin_facturé=1 join enseigne on enseigne.enseigne_id=magasin.enseigne_id and enseigne_intitulé='CASINO'"),{'date_tour':date_tour}).fetchall()
    dateTourConvert=datetime.strptime(date_tour, "%Y-%m-%d").strftime("%d-%m-%Y")
    data = {
            'L_magasin': requeteLivraison,
            'L_tarif':L_tarif,
            'date_tour':dateTourConvert,
            'L_trinome':L_trinome
        }
    #crréation pdf
    path_wkhtmltopdf = r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    rendered=render_template('pages/facturation_journaliere.html',**data)
    rendered=rendered
    pdf =pdfkit.from_string(rendered, False, configuration=config)
    response=make_response(pdf)
    response.headers['Content-Type']='application/pdf'
    response.headers['Content-Disposition']='attachment; filename=facturation_journaliere.pdf'
    return response
      
 #***************************************************************************************************************************DIAGRAMMES********************************************************************************
@app.route('/Diagrammes', methods=['GET','post'])
def diagramme_aprs_tournees():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    date_debut=request.form['date_debut']
    date_fin=request.form['date_fin']
    
    requeteLivraison = pd.read_sql_query('SELECT e.enseigne_intitulé AS enseigne, m.magasin_id, magasin_tarif_rolls, magasin_tarif_palette, magasin_tarif_boxe FROM camion_magasin cm join magasin as m on m.magasin_id = cm.magasin_id join enseigne as e on e.enseigne_id = m.enseigne_id where date between "%s" and "%s"' %(date_debut,date_fin), engine)
    dataLivraison = pd.DataFrame(requeteLivraison)
    ens=dataLivraison["enseigne"].value_counts()
    ens=ens.reset_index()
    ens=ens.rename(columns={'enseigne':'Nbre_mag_livrés', 'index':'enseigne'})
    # afficher diagramme circulaire pour distribution par enseigne  llll
    data = [go.Pie(labels=ens.enseigne, values=ens.Nbre_mag_livrés, textposition='inside', textinfo='percent+label')] 
    layoutPieEns=go.Layout(title="3. Répartition des magasins livrés par Enseigne", )
    figPieEns=go.Figure(data=data, layout=layoutPieEns)
    graphJSON1 = json.dumps(figPieEns, cls=plotly.utils.PlotlyJSONEncoder)

    # afficher diagramme a bar pour les camion utilisé a cette période
    requeteCamion = pd.read_sql_query('select camion_mat, count(camion_mat) As nbre_cam from camion join chauffeur_camion on chauffeur_camion.camion_id=camion.camion_id and date between "%s" and "%s" group by camion_mat' %(date_debut,date_fin), engine)
    traceFRQCamBar=     go.Bar(x=requeteCamion.camion_mat,y=requeteCamion.nbre_cam)
    layoutFRQCamBar=go.Layout(title="5. Fréquence d'utilisation Des Camions", xaxis=dict(title="Immatriculations des camions "), yaxis=dict(title="Nombre d'utilisations "),)
    dataCamFRQBar=[traceFRQCamBar]
    figBarChauf=go.Figure(data=dataCamFRQBar, layout=layoutFRQCamBar)
    graphJSONCam = json.dumps(figBarChauf, cls=plotly.utils.PlotlyJSONEncoder)


    #Afficher diagramme circulaire repartition des tarifs rolls pour toutes les enseignes
    #dataLivraisonRolls = dataLivraison[dataLivraison.magasin_tarif_rolls.notna()]
   # graphique_rolls_ens=px.sunburst(dataLivraisonRolls, path=["enseigne", "magasin_tarif_rolls"], color="enseigne", width=800, title="Répartition des tarifs rolls pour les livraisons entre le 2020-12-01 au 2020-12-15")
    #graphique_rolls_ens = [go.Sunburst(labels=ens.enseigne, values=ens.Nbre_mag_livrés, textposition='inside', textinfo='percent+label', title='Répartition des magasins livrés par enseigne')] 
   
    #graphJSON_ensRolls = json.dumps(graphique_rolls_ens, cls=plotly.utils.PlotlyJSONEncoder)

    #afficher diagramme a bar camion location ou non utilisé à cette période
    requetCamLoc=pd.read_sql_query("select date, count(camion_mat) as nbre_loc from camion join chauffeur_camion on chauffeur_camion.camion_id=camion.camion_id and date between '%s' and '%s' where camion_type ='LOCATION' group by date"%(date_debut,date_fin), engine)
    requetCamNotLoc=pd.read_sql_query("select date, count(camion_mat) as nbre_notLoc from camion join chauffeur_camion on chauffeur_camion.camion_id=camion.camion_id and date between '%s' and '%s' where camion_type <>'LOCATION' group by date"%(date_debut,date_fin), engine)
    requetCamType=pd.read_sql_query("select camion_type as type, count(camion_mat)  nbre_cam from camion join chauffeur_camion on chauffeur_camion.camion_id=camion.camion_id and date between '%s' and '%s' group by camion_type"%(date_debut,date_fin), engine)
      
    trace_loc=go.Bar(x=requetCamLoc.date, y=requetCamLoc.nbre_loc, name='Camion Location', marker=dict(color='#e73f22'))
    trace_notLoc=go.Bar(x=requetCamNotLoc.date, y=requetCamNotLoc.nbre_notLoc, name='Camion PERRENOT', marker=dict(color='#f6cb16'))
    layoutCamLoc=go.Layout(title="6. Utilisation camion de Location et Camion PERRENOT", xaxis=dict(title="Date des Tournées "), yaxis=dict(title="Nombre d'Utilisations "),)
    

    datacamLoc = [trace_loc, trace_notLoc]
    figcamLoc=go.Figure(data=datacamLoc, layout=layoutCamLoc)
    graphJSONcamLoc = json.dumps(figcamLoc, cls=plotly.utils.PlotlyJSONEncoder)

    dataCamType = [go.Pie(labels=requetCamType.type, values=requetCamType.nbre_cam, textposition='inside', textinfo='percent+label', title='')] 
    layoutPieCam=go.Layout(title="7. Répartition Camions de Livraison par Type ", )
    figPieCam=go.Figure(data=dataCamType, layout=layoutPieCam)
    graphJSONCamType = json.dumps(figPieCam, cls=plotly.utils.PlotlyJSONEncoder)

    
    

    #afficher diagrammes par type de contrat Chauffeur
    requeteChaufCDI = pd.read_sql_query("select chauffeur_camion.date,  count(chauffeur_camion.chauf_id) as nbre_chauf from chauffeur_camion join chauffeur on chauffeur.chauf_id = chauffeur_camion.chauf_id and chauffeur_camion.date between '%s' and '%s' join chauffeur_contrat on chauffeur_contrat.chauf_id=chauffeur.chauf_id and chauffeur_contrat.date_fin>date(now()) join contrat on contrat.contrat_id=chauffeur_contrat.contrat_id and contrat_intitule='CDI' group by chauffeur_camion.date" %(date_debut,date_fin), engine)
    requeteChaufCDD = pd.read_sql_query("select chauffeur_camion.date,  count(chauffeur_camion.chauf_id) as nbre_chauf  from chauffeur_camion join chauffeur on chauffeur.chauf_id = chauffeur_camion.chauf_id and chauffeur_camion.date between '%s' and '%s' join chauffeur_contrat on chauffeur_contrat.chauf_id=chauffeur.chauf_id and chauffeur_contrat.date_fin>date(now()) join contrat on contrat.contrat_id=chauffeur_contrat.contrat_id and contrat_intitule='CDD' group by chauffeur_camion.date" %(date_debut,date_fin), engine)
    requeteChaufInterim = pd.read_sql_query("select chauffeur_camion.date,  count(chauffeur_camion.chauf_id) as nbre_chauf from chauffeur_camion join chauffeur on chauffeur.chauf_id = chauffeur_camion.chauf_id and chauffeur_camion.date between '%s' and '%s' join chauffeur_contrat on chauffeur_contrat.chauf_id=chauffeur.chauf_id and chauffeur_contrat.date_fin>date(now()) join contrat on contrat.contrat_id=chauffeur_contrat.contrat_id and contrat_intitule='INTERIMAIRE' group by chauffeur_camion.date" %(date_debut,date_fin), engine)
    requeteChaufContratGlobal = pd.read_sql_query("select contrat_intitule as intitul,  count(chauffeur_camion.chauf_id) as nbre_chauf from chauffeur_camion join chauffeur on chauffeur.chauf_id = chauffeur_camion.chauf_id and chauffeur_camion.date between '%s' and '%s' join chauffeur_contrat on chauffeur_contrat.chauf_id=chauffeur.chauf_id and chauffeur_contrat.date_fin>date(now()) join contrat on contrat.contrat_id=chauffeur_contrat.contrat_id group by contrat_intitule" %(date_debut,date_fin), engine)
    
    trace_chaufCDI=     go.Bar(x=requeteChaufCDI.date, y=requeteChaufCDI.nbre_chauf, name='CDI', marker=dict(color='#450d57'))
    trace_chaufCDD=     go.Bar(x=requeteChaufCDD.date, y=requeteChaufCDD.nbre_chauf, name='CDD', marker=dict(color='#666699'))
    trace_chaufInterim=     go.Bar(x=requeteChaufInterim.date, y=requeteChaufInterim.nbre_chauf, name='INTERIMAIRE', marker=dict(color='#993366'))
    layoutChaufBar=go.Layout(title="8. Nombre de Chauffeurs par Type de Contrat", xaxis=dict(title="Date"), yaxis=dict(title="Nombre Chauffeur"),)
    
    dataChaufContrat=[trace_chaufCDI, trace_chaufCDD, trace_chaufInterim]
    figBarChauf=go.Figure(data=dataChaufContrat, layout=layoutChaufBar)
    graphJSONchaufContrat = json.dumps(figBarChauf, cls=plotly.utils.PlotlyJSONEncoder)

    # diagramme circulaire chauffeur contrat global 
    dataChaufContratGlobal = [go.Pie(labels=requeteChaufContratGlobal.intitul, values=requeteChaufContratGlobal.nbre_chauf, textposition='inside', textinfo='percent+label', )] 
    layoutPieCam=go.Layout(title='9. Répartition des Chauffeurs par Type de Contrat ', )
    figPieCam=go.Figure(data=dataChaufContratGlobal, layout=layoutPieCam)
    graphJSONChaufContratGlobal = json.dumps(figPieCam, cls=plotly.utils.PlotlyJSONEncoder)
    requeteCasino = pd.read_sql_query("select magasin_tarif_rolls, sum(nbre_rolls) as Nbre_rol from magasin join camion_magasin on camion_magasin.magasin_id=magasin.magasin_id and date between '%s' and '%s' and magasin_tarif_rolls<>-1 and magasin_tarif_rolls<>0 join enseigne on enseigne.enseigne_id=magasin.enseigne_id and enseigne_intitulé='CASINO' group by magasin_tarif_rolls" %(date_debut,date_fin), engine)
    data1 = [go.Pie(labels=requeteCasino.magasin_tarif_rolls, values=requeteCasino.Nbre_rol, textposition='inside',text=['€'], textinfo='percent+label+text',) ] 
    layoutPieRolls=go.Layout(title='4. Répartition Tarif Rolls pour Casino', )
    figPieCam=go.Figure(data=data1, layout=layoutPieRolls)
    graphJSON2 = json.dumps(figPieCam, cls=plotly.utils.PlotlyJSONEncoder)

    #diagramme chiffre d'affaire 
    casino_id=pd.read_sql_query("select enseigne_id as ens_id from enseigne where enseigne_intitulé='CASINO'", engine)['ens_id']
    requetCamLoyer=pd.read_sql_query("select date,day(last_day(date)) ,MONTH(date), YEAR(date),DAYOFWEEK(date), sum(camion_loyer) from tarification  join info_tarification on info_tarification.info_tarification_id=tarification.info_tarification_id and type_tarif='trinome' and intitule_tarif='km' and enseigne_id=%s and date between '%s' and '%s'  join camion on camion.camion_id = tarification.camion_id  group by date order by date"%(casino_id[0],date_debut,date_fin), engine)
    L_loyerCam_date=con.execute(text("select date,day(last_day(date)) ,MONTH(date), YEAR(date),DAYOFWEEK(date), sum(camion_loyer) from tarification  join info_tarification on info_tarification.info_tarification_id=tarification.info_tarification_id and type_tarif='trinome' and intitule_tarif='km' and enseigne_id=:casino_id and date between :date_deb and :date_fin  join camion on camion.camion_id = tarification.camion_id  group by date order by date "),{'casino_id':int(casino_id[0]),'date_deb':date_debut,'date_fin':date_fin}).fetchall()
    jour_ouvrable=nbreJourOuvrable(L_loyerCam_date)
    jour_ouvrable=pd.DataFrame(jour_ouvrable)
    for element in range(jour_ouvrable.shape[0]):
        jour_ouvrable.iloc[element,1]=requetCamLoyer.iloc[element,5]/jour_ouvrable.iloc[element,1]
    jour_ouvrable.rename(columns={0:'date', 1:'jour'}, inplace=True)    
    requetTkCasino=pd.read_sql_query("select date,  sum(tarif*valeur ) from tarification  join info_tarification on info_tarification.info_tarification_id=tarification.info_tarification_id and type_tarif='TK' and enseigne_id=%s and date between '%s' and '%s'  join camion on camion.camion_id = tarification.camion_id  group by date order by date"%(casino_id[0],date_debut,date_fin), engine)
    requetTrinomeCasino=pd.read_sql_query("select date,  sum(tarif*valeur ) as cout_trinome from tarification  join info_tarification on info_tarification.info_tarification_id=tarification.info_tarification_id and type_tarif='trinome' and enseigne_id=%s and date between '%s' and '%s'  join camion on camion.camion_id = tarification.camion_id  group by date order by date"%(casino_id[0],date_debut,date_fin), engine)
    requetDistrCasino=pd.read_sql_query("select date, sum(nbre_rolls*magasin_tarif_rolls + nbre_palette*magasin_tarif_palette) as cout_distribution  from camion_magasin  join magasin on magasin.magasin_id=camion_magasin.magasin_id join camion on camion.camion_id=camion_magasin.camion_id and camion_type<>'VL' and camion_type<>'CAISSE_MOBILE' join enseigne on enseigne.enseigne_id = magasin.enseigne_id and enseigne_intitulé='CASINO' where date between '%s' and '%s' group by date order by date"%(date_debut,date_fin), engine)
    cout_paq=pd.read_sql_query("select tarif from info_tarification  where intitule_tarif='passage_a_quai' and enseigne_id=%s"%(casino_id[0]), engine)['tarif']
    cout_tri_emb=pd.read_sql_query("select tarif from info_tarification  where intitule_tarif='tri_emb' and enseigne_id=%s"%(casino_id[0]), engine).tarif
    requetPaQCasino=pd.read_sql_query("select date,  sum(nbre_rolls+nbre_palette)*(%s) as cout_paq from camion_magasin join camion on camion.camion_id=camion_magasin.camion_id and camion_type<>'CAISSE_MOBILE'  join magasin on magasin.magasin_id=camion_magasin.magasin_id  join enseigne on enseigne.enseigne_id = magasin.enseigne_id and enseigne_intitulé='CASINO' where date between '%s' and '%s' group by date order by date"%(cout_paq[0],date_debut,date_fin), engine)
    requetTriEmb=pd.read_sql_query("select date,  sum(nbre_rolls+nbre_palette)*(%s) as cout_tri_emb from camion_magasin join camion on camion.camion_id=camion_magasin.camion_id and camion_type<>'CAISSE_MOBILE' join magasin on magasin.magasin_id=camion_magasin.magasin_id  join enseigne on enseigne.enseigne_id = magasin.enseigne_id and enseigne_intitulé='CASINO' where date between '%s' and '%s'  group by date order by date"%(cout_tri_emb[0],date_debut,date_fin), engine)
    requeteNvtCasino=pd.read_sql_query("select tarification.date, sum(tarif*valeur)from tarification join info_tarification on info_tarification.info_tarification_id=tarification.info_tarification_id and type_tarif='navette' and enseigne_id=%s and date between '%s' and '%s'group by date order by date"%(casino_id[0],date_debut,date_fin),engine)
    requetTrinomeCasino=pd.merge(requetTrinomeCasino,jour_ouvrable.iloc[:,0:2],  how='outer')
    CA_casino=pd.merge(requetDistrCasino,requetTrinomeCasino,  how='outer')
    CA_casino=pd.merge(CA_casino,requeteNvtCasino,  how='outer')
    CA_casino=pd.merge(CA_casino,requetPaQCasino,  how='outer')
    CA_casino=pd.merge(CA_casino,requetTkCasino,  how='outer')
    CA_casino=pd.merge(CA_casino,requetTriEmb,  how='outer')
    CA_casino=CA_casino.fillna(0)
    sumCaCasino=CA_casino.iloc[:,1:].sum(axis = 1)
    #tracer la ligne
    CA_casino_line = pd.DataFrame({'date': CA_casino['date'],'CA_casino': sumCaCasino}, columns = ['date', 'CA_casino'])
    casinoLine=go.Scatter( x=CA_casino_line.date, y=CA_casino_line.CA_casino, mode = 'lines+markers', name='CASINO')
    dataLine=[casinoLine]
   
    L_ens=pd.read_sql_query("select enseigne_id, enseigne_intitulé from enseigne where enseigne_actif=1 and enseigne_intitulé<>'CASINO'",engine)
    
    for cpt in range(L_ens.shape[0]):
        requet_ens=pd.read_sql_query("select date, sum(nbre_rolls*magasin_tarif_rolls + nbre_palette*magasin_tarif_palette) as cout_distribution  from camion_magasin join magasin on magasin.magasin_id=camion_magasin.magasin_id join enseigne on enseigne.enseigne_id = magasin.enseigne_id and enseigne_intitulé='%s' where date between '%s' and '%s' group by date order by date "%(L_ens.iloc[cpt][1],date_debut,date_fin),engine)
        requeteNvt_ens=pd.read_sql_query("select tarification.date as date, sum(tarif*valeur) as cout_navette from tarification join info_tarification on info_tarification.info_tarification_id=tarification.info_tarification_id and type_tarif='navette' and enseigne_id=%s and date between '%s' and '%s'group by date order by date"%(L_ens.iloc[cpt][0],date_debut,date_fin),engine)
        if not requet_ens.empty and not requeteNvt_ens.empty:
            requet_ens=pd.merge(requet_ens,requeteNvt_ens, how='outer')
            requet_ens_sum=requet_ens.iloc[:,1:].sum(axis = 1)
            
            requet_ens_final = pd.DataFrame({'date': requet_ens.date,'CA_ens': requet_ens_sum}, columns = ['date', 'CA_ens'])
            requet_ens_final = requet_ens_final.sort_values(by="date")
            ens_Line=go.Scatter( x=requet_ens_final.date, y=requet_ens_final.CA_ens, mode = 'lines+markers',  name=L_ens.iloc[cpt][1])
            dataLine.append(ens_Line)
            
        """elif not requet_ens.empty and requeteNvt_ens.empty:
            ens_Line=go.Scatter( x=requet_ens['date'], y=requet_ens['cout_distribution'], mode = 'lines+markers', name=L_ens.iloc[cpt][1])
            dataLine.append(ens_Line)
        elif  requet_ens.empty and not requeteNvt_ens.empty:    
            ens_Line=go.Scatter( x=requeteNvt_ens['date'], y=requeteNvt_ens['cout_navette'], mode = 'lines+markers', name=L_ens.iloc[cpt][1])
            dataLine.append(ens_Line)"""

    layoutline=go.Layout(title="2. Chiffre d'Affaire par Enseigne", xaxis=dict(title="Date"), yaxis=dict(title="Chiffre d'Affaire En Euro"),)
    figCALine=go.Figure(data=dataLine, layout=layoutline)
    graphJSONCA_ens = json.dumps(figCALine, cls=plotly.utils.PlotlyJSONEncoder)
   
    for cpt in range(L_ens.shape[0]):
        requet_ens=pd.read_sql_query("select date, sum(nbre_rolls*magasin_tarif_rolls + nbre_palette*magasin_tarif_palette) as cout_distribution%s  from camion_magasin join magasin on magasin.magasin_id=camion_magasin.magasin_id join enseigne on enseigne.enseigne_id = magasin.enseigne_id and enseigne_intitulé='%s' where date between '%s' and '%s' group by date order by 'date'"%(cpt,L_ens.iloc[cpt][1],date_debut,date_fin),engine)
        requeteNvt_ens=pd.read_sql_query("select tarification.date, sum(tarif*valeur) as cout_navette%s from tarification join info_tarification on info_tarification.info_tarification_id=tarification.info_tarification_id and type_tarif='navette' and enseigne_id=%s and date between '%s' and '%s'group by date order by date"%(cpt,L_ens.iloc[cpt][0],date_debut,date_fin),engine)
        if not requet_ens.empty:
            CA_casino=pd.merge(CA_casino,requet_ens, how='outer')
        if not requeteNvt_ens.empty:    
            CA_casino=pd.merge(CA_casino,requeteNvt_ens, how='outer')
            
    sumCaCasino=CA_casino.iloc[:,1:].sum(axis = 1)
    #tracer diagrammme a bar chiffre d affaire
    CA_casino_final = pd.DataFrame({'date': CA_casino['date'],'CA_casino': sumCaCasino}, columns = ['date', 'CA_casino'])
    traceBarCA=go.Bar(x=CA_casino_final.date,y=CA_casino_final.CA_casino, marker=dict(color='#D5D8DC'))
    layoutBarCA=go.Layout(title="1. Chiffre d'affaire global", xaxis=dict(title="Date"), yaxis=dict(title="Chiffre d'Affaire en Euro"),)
    dataBarCA = [traceBarCA]
    figBarCA=go.Figure(data=dataBarCA, layout=layoutBarCA)
    graphJSONCA = json.dumps(figBarCA, cls=plotly.utils.PlotlyJSONEncoder)
    dateDebConvert=datetime.strptime(date_debut, "%Y-%m-%d").strftime("%d-%m-%Y")
    dateFinConvert=datetime.strptime(date_fin, "%Y-%m-%d").strftime("%d-%m-%Y")   
    data={'plot1': graphJSON1,
          'plot2':graphJSON2,
          'plotCam':graphJSONCam,
          'plotCamLoc':graphJSONcamLoc,
          'plotChaufContrat':graphJSONchaufContrat,
          'plotChaufContratGlobal':graphJSONChaufContratGlobal,
          'plotCamType':graphJSONCamType,
          'plotCA':graphJSONCA,
          'plotEnsLine':graphJSONCA_ens,
          'date_debut': dateDebConvert,
          'date_fin':dateFinConvert
          }
    return render_template('pages/diagram_apres_tournees.html',**data)
   
     
 #**********************************************************************************SE DECONNECTER********************************************************************************      

@app.route('/deconnection', methods=['post','get'])
def se_deconnecter(): 
    session.clear()   
    return redirect(url_for('home'))  


#**********************************************************************************CHANGEMENT INFORMATIONS UTILISATEUR ********************************************************************************      

@app.route('/mes_informations', methods=['post','get'])
def chang_info_user():
    if not session.get('connexion'):
        flash("Accès refusé! Veuillez vous connecter pour accéder à cette page!",'danger')
        return redirect(url_for('home'))
    pseudo=session['login']
    info_user=con.execute(text("select utilisateur_nom, utilisateur_prenom, utilisateur_MDP, utilisateur_id from utilisateur where utilisateur_pseudo=:pseudo"),{'pseudo':pseudo }).fetchone()
    nom= info_user[0] 
    prenom =info_user[1]
    user_id=info_user[3]
    data= {
            'nom': nom ,
            'prenom': prenom,
            'pseudo':pseudo
        }
    if request.method== 'POST':
        nvPseudo=request.form['pseudo']
        nvNom=request.form['nom']
        nvPrenom=request.form['prenom']
        
        test_pseudo=con.execute(text("select utilisateur_id from utilisateur where utilisateur_pseudo=:nvPseudo and utilisateur_id<>:ancUser"),{'nvPseudo':nvPseudo, 'ancUser':info_user[3]}).fetchone()
        mot_de_pass=request.form['mdp']
        if request.form['nvMDP']!=request.form['cNvMDP']:
            flash('les deux nouveaux mot de passes ne correspondent pas','danger')
        else:
           # mot_de_pass=hashlib.sha1(str.encode(mot_de_pass)).hexdigest()  
            if check_password_hash(str(info_user[2]),mot_de_pass)==False:    
                flash("Veuillez vérifier la saisie de l'ancien mot de passe",'danger')
            elif test_pseudo:
                flash("Le nouveau pseudo que vous venez de taper existe déjà! Veuillez le changer",'danger')  
            elif request.form['nvMDP']=="":
                con.execute(text("update utilisateur set utilisateur_nom=:nvNom, utilisateur_prenom=:nvPrenom, utilisateur_pseudo=:nvPseudo where utilisateur_id=:user_id"),{'nvNom':nvNom,'nvPrenom':nvPrenom,'nvPseudo':nvPseudo, 'user_id':user_id})
                flash("Les modifications ont bien été prises en charges",'success')
                session['login']=request.form['pseudo']
            else:
                nvMDP=request.form['nvMDP']
                #nvMDP=hashlib.sha1(str.encode(nvMDP)).hexdigest()
                nvMDP=generate_password_hash(str(nvMDP))
                con.execute(text("update utilisateur set utilisateur_nom=:nvNom, utilisateur_prenom=:nvPrenom, utilisateur_pseudo=:nvPseudo, utilisateur_MDP=:nvMDP where utilisateur_id=:user_id"),{'nvNom':nvNom,'nvPrenom':nvPrenom,'nvPseudo':nvPseudo,'nvMDP':nvMDP, 'user_id':user_id})
                session['login']=request.form['pseudo']
                flash("Les modifications ont bien été prises en compte",'success')
        data['nom']=request.form['nom']
        data['prenom']=request.form['prenom']
        data['pseudo']=request.form['pseudo']        
        return render_template('pages/info_compte_user.jinja',**data) 
    return render_template('pages/info_compte_user.jinja',**data)

if __name__=='__main__':
     app.run(debug=True, port=3000)
     
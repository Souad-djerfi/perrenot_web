#*************************************************************************************************Ancienne Selection des magasins à livrer ********************************************   

"""@app.route('/selection-enseigne', methods=['get','post'])
def selection_ens():
    Test=False
    Fenseigne=''
    cpt=0
    magasin_jour = pd.DataFrame(columns=['magasin_code','nbre_rolls','nbre_pal','nbre_box'])
    requete_nbre_ens='select count(*) from enseigne'
    nbre_ens=con.execute(text(requete_nbre_ens)).fetchone()[0]
    requete_ens='select enseigne_id,enseigne_intitulé from enseigne'
    liste_enseigne=con.execute(text(requete_ens)).fetchall()
    
    requete_camion="call liste_camion()"
    camion=con.execute(text(requete_camion)).fetchall()
    liste_camion= [row[0] for row in camion]
    nbre_camion=len(liste_camion)

    # récupérer le nombre d 'eneignes et les enseignes, camion et nbre camion pour les afficher dans la page

    data={
                'nbre_ens': nbre_ens,
                'L_enseigne': liste_enseigne,
                'camion' : camion,
                'nbre_camion':nbre_camion,
                'test':Test,
                'enseigne': Fenseigne,
                'magasin_jour': magasin_jour,
                'cpt':cpt
        }
    if request.method== 'POST':
        Test=True 
        data['test']  = Test   
        Fenseigne=request.form.getlist('liste_ens') #liste enseigne_id cochées
        Fcamion=request.form.getlist('liste_camion')
        data['nbre_ens_selec']=len(Fenseigne)
        Fenseigne_intit=con.execute(text("select enseigne_id, enseigne_intitulé from enseigne where enseigne_id in :enseigne"),{'enseigne':Fenseigne}).fetchall()
        data['enseigne_intit']=Fenseigne_intit
        
        #mag_id=con.execute(text("select magasin_id from magasin where enseigne_id=:enseigne"),{'enseigne':Fenseigne[0][0]}).fetchall()
        liste_mag=[con.execute(text("select magasin_code,magasin_id from magasin where enseigne_id=:enseigne"),{'enseigne':Fenseigne[j][0]}).fetchall() for j in range(len(Fenseigne))]
        L1=[]
        L2=[]
        L3=[]
        L4=[]
        for i in range(len(liste_mag)):
            for mag in liste_mag[i]:
                L1.append(mag[0])
                L2.append(0)
                L3.append(0)
                L4.append(0)
        magasin_jour['magasin_code']=L1
        magasin_jour['nbre_rolls']=L2
        magasin_jour['nbre_pal']=L3
        magasin_jour['nbre_box']=L4
        magasin_jour.reset_index(inplace=True)
        print( magasin_jour)
        
        data['liste_mag']=liste_mag
        data['camionC']=Fcamion
        data['magasin_jour']=magasin_jour
        
        requete_magasin='select magasin_id, magasin_code from magasin where enseigne_id in :enseigne'
        magasin=con.execute(text(requete_magasin),{'enseigne':Fenseigne}).fetchall() # récupérer des magasins des enseignes cochés
        data['magasin']=magasin
        data['nbre_mag']=len(magasin)
        
    return render_template('pages/selection_ens.jinja', **data)

#*******************************************************************************************************Selection magasin****************************************************
@app.route('/selection-magasin', methods=['post'])
def selection_mag():
    #récupérer les camions cochés
    camion=request.form.getlist('liste_camion')
    requete_camion="select camion_mat, camion_cap from camion where camion_mat in :camion"
    camion_code=con.execute(text(requete_camion),{'camion':camion})
    
    #requete_mag='select magasin_code from magasin where enseigne_id in :enseigne_id'
    #magasin=con.execute(text(requete_mag),{'enseigne_id':enseigne_id}).fetchall()
    
    # récupérer le nombre d 'eneignes et les enseignes pour les afficher dans la page
    data={
            'camion': camion_code
        }
       
    #return render_template('pages/valider_tournée.jinja', **data)
    return render_template('pages/contact.jinja', **data)"""

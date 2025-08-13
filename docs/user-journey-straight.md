# User Journey Straight

```mermaid
  graph TD
    /index 
    --> /vers-auswaehlen
        
    /vers-auswaehlen
    	--> /vers-suche/referenz
    	--> /bestaetigung
    
    	/vers-auswaehlen
    	-->/bestaetigung
    
    	/vers-auswaehlen
    	--> /vers-suche/keyword
    	--> /bestaetigung
    
		/bestaetigung
    	--> /checkout/gruppe/daten
    	--> /checkout-zusammenfassung
    
			/bestaetigung
		  --> /checkout/einzelperson/daten
    	--> /checkout-zusammenfassung 
    	
    	/bestaetigung
    	--> /checkout/geschenk/daten
    	--> /checkout-zusammenfassung
    
    /checkout/gruppe/daten --> /vers-auswaehlen
    /checkout/einzelperson/daten --> /vers-auswaehlen
    /checkout/geschenk/daten --> /vers-auswaehlen
    
    /checkout-zusammenfassung
    --> STRIPE
    --> /checkout-erfolg
    --> /register
    --> /registration-success
    --> /login
    --> /dashboard
    
    --> /meine-verse
    --> /dashboard
    /dashboard --> /profil
    /profil --> /dashboard

```


# User Journey Straight

```mermaid
  graph TD
    /index 
    --> /vers-auswaehlen
        
    /vers-auswaehlen
    	--> /vers-suche/referenz
    	--> /spendenart
    
    	/vers-auswaehlen
    	-->/spendenart
    
    	/vers-auswaehlen
    	--> /vers-suche/keyword
    	--> /spendenart
    
		/spendenart
    	--> /checkout/gruppe/daten
    	--> /checkout-zusammenfassung
    
			/spendenart
		  --> /checkout/einzelperson/daten
    	--> /checkout-zusammenfassung 
    	
    	/spendenart
    	--> /checkout/geschenk/daten
    	--> /checkout-zusammenfassung
    
   
    /checkout-zusammenfassung
    	--> /vers-auswaehlen
    
    /checkout-zusammenfassung
   	 --> STRIPE
    	--> /checkout-erfolg
   	 --> /register
   	 
```


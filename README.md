# Football Stats Analyzer — prototipo MVP

## Requisiti
- Python 3.10 o successivo
- Una chiave API-Football (API-Sports)
- Connessione internet

## Installazione
1. Estrai il file ZIP.
2. Apri un terminale nella cartella del progetto.
3. Installa i pacchetti:
   ```bash
   pip install -r requirements.txt
   ```
4. Imposta la chiave API come variabile d'ambiente.

### Windows PowerShell
```powershell
$env:API_FOOTBALL_KEY="INCOLLA_LA_TUA_CHIAVE"
streamlit run app.py
```

### macOS / Linux
```bash
export API_FOOTBALL_KEY="INCOLLA_LA_TUA_CHIAVE"
streamlit run app.py
```

Si aprirà la dashboard nel browser. Per usarla dal telefono e dal PC, la prima versione può essere pubblicata su un servizio di hosting compatibile con Streamlit; non pubblicare mai la chiave API nel codice o in un repository pubblico.

## Cosa include
- Calendario per data
- Filtro dei campionati principali: Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Champions League ed Europa League
- Statistiche di partita: falli, cartellini, tiri, tiri in porta, corner e gol
- Medie recenti per le due squadre selezionate
- Cache temporanea per limitare le richieste

## Limiti dell'MVP
- La disponibilità di statistiche dipende dal campionato e dal piano del provider.
- Il calcolo delle medie può consumare diverse chiamate API per partita; nel piano gratuito analizza poche partite e verifica la quota residua.
- Non include ancora utenti, login, notifiche, database storico proprio, backtesting o modelli probabilistici calibrati.
- Le medie descrittive non sono previsioni garantite.

## Provider dati
Il codice usa l'API REST v3 di API-Football:
https://www.api-football.com/documentation-v3
Prezzi e limiti possono cambiare: verifica il piano direttamente sul sito ufficiale.

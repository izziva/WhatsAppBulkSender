# WhatsApp Automation Bot

Questo progetto è uno script Python per automatizzare l'invio di messaggi WhatsApp a una lista di numeri di telefono. È stato refattorizzato da uno script singolo a un progetto modulare per migliorare la leggibilità, la manutenibilità e la configurabilità.

## Installazione

Si consiglia di utilizzare `uv` per una gestione rapida delle dipendenze e dell'ambiente virtuale.

1.  **Installa `uv`**

    Se non hai `uv`, puoi installarlo con il seguente comando:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
    (Su Windows, usa `pip install uv`).

2.  **Crea e attiva l'ambiente virtuale**

    Crea un ambiente virtuale nella directory del progetto:
    ```bash
    uv venv
    ```
    Attivalo:
    - Su macOS/Linux: `source .venv/bin/activate`
    - Su Windows: `.venv\Scripts\activate`

3.  **Installa le dipendenze**

    Con l'ambiente virtuale attivo, sincronizza l'ambiente con le dipendenze specificate in `pyproject.toml`:
    ```bash
    uv pip sync
    ```

4.  **Driver JDBC (Opzionale)**

    Se intendi caricare i numeri da un database Access (`.mdb`), assicurati di avere i driver UCanAccess. Posiziona i file `.jar` necessari all'interno di una cartella `lib/` nella directory principale del progetto.

Per maggiori informazioni su come gestire le dipendenze con `uv`, consulta la [documentazione ufficiale di uv](https://astral.sh/uv).

## Utilizzo

1.  **Prepara i file di input:**
    -   **Messaggio**: Crea un file `message.txt` con il testo del messaggio che vuoi inviare. Se il file non esiste, lo script ti chiederà di inserire il messaggio al primo avvio.
    -   **Numeri**:
        -   Crea un file `numbers.txt` con i numeri di telefono separati da virgola.
        -   In alternativa, se il file `numbers.txt` è vuoto o non esiste, lo script ti chiederà se vuoi caricarli dal database `archivio.mdb`.

2.  **Esegui lo script**

    Con l'ambiente virtuale attivo, esegui il file `main.py`:
    ```bash
    python main.py
    ```

3.  **Login a WhatsApp Web**

    Al primo avvio, o se la sessione è scaduta, si aprirà una finestra del browser con un QR code. Scansionalo con il tuo telefono per accedere a WhatsApp Web.

import asyncio  
from telethon import TelegramClient, events, functions, types  
from gtts import gTTS
import os  
import time  

# Inserisci i tuoi dati API di Telegram  
api_id = int(os.getenv("23281579"))  
api_hash = os.getevn("16ba69a4299d98d2c7259a8ce33f155c")  

client = TelegramClient('userbot', api_id, api_hash) 

muted_users = set()  
user_data = {}  # Dizionario per memorizzare i dati degli utenti (PayPal e Wallet)

@client.on(events.NewMessage(pattern=r'\.create (gr|ch) (.+)', outgoing=True))
async def create_chat(event):
    """ Crea un gruppo o un canale e restituisce il link privato """
    tipo = event.pattern_match.group(1)
    titolo = event.pattern_match.group(2)

    try:
        if tipo == "gr":
            result = await client(functions.channels.CreateChannelRequest(
                title=titolo,
                about="",
                megagroup=True  # Creazione gruppo
            ))
        else:
            result = await client(functions.channels.CreateChannelRequest(
                title=titolo,
                about="",
                megagroup=False  # Creazione canale
            ))

        chat_id = result.chats[0].id

        # Genera un link di invito valido per gruppi e canali
        invite = await client(functions.messages.ExportChatInviteRequest(chat_id))
        link = invite.link

        tipo_nome = "Gruppo" if tipo == "gr" else "Canale"
        await event.edit(f"✅ {tipo_nome} '{titolo}' creato con successo!\n🔗 [Entra qui]({link})")

    except Exception as e:
        await event.edit(f"⚠️ Errore nella creazione: {str(e)}")

@client.on(events.NewMessage(pattern=r'\.info(?: (.+))?', outgoing=True))  
async def info(event):  
    """ Mostra le informazioni di un utente con immagine profilo, modificando il messaggio originale. """  

    if event.reply_to_msg_id:  
        user = await event.get_reply_message()  
        user = user.sender  
    elif event.pattern_match.group(1):  
        user = await client.get_entity(event.pattern_match.group(1))  
    else:  
        user = await event.get_sender()  

    user_id = user.id  
    first_name = user.first_name if user.first_name else "Nessun Nome"  
    username = f"@{user.username}" if user.username else "Nessun Username"  
    is_premium = "✅" if getattr(user, "premium", False) else "✖️"  
    is_bot = "✅" if user.bot else "✖️"  
    permalink = f"[🔗 Clicca qui](tg://user?id={user_id})"  

    if isinstance(user, types.User) and user.username:  
        usernames = [f"@{user.username}"]  
    else:  
        usernames = []  

    usernamelist = " | ".join(usernames) if usernames else "Nessun Username"  

    # Scarica l'immagine profilo se disponibile  
    profile_pic_path = f"pfp_{user_id}.jpg"  
    photos = await client.get_profile_photos(user)  

    if photos:  
        await client.download_media(photos[0], file=profile_pic_path)  
    else:  
        profile_pic_path = None  # Nessuna foto profilo  

    msg = f"""
🔎 Informazioni utente  

* 💭 ɴᴏᴍᴇ ➯ {first_name}  
* 🆔 ɪᴅ ➯ `{user_id}`  
* 💻 ᴜꜱᴇʀɴᴀᴍᴇ ➯ {usernamelist}  
* 🌟 ᴘʀᴇᴍɪᴜᴍ ➯ {is_premium}  
* 🤖 ʙᴏᴛ ➯ {is_bot}  
* 🔗 ᴘᴇʀᴍᴀʟɪɴᴋ ➯ {permalink}  
"""  

    if profile_pic_path:  
        await client.send_file(event.chat_id, profile_pic_path, caption=msg)  
        os.remove(profile_pic_path)  # Cancella il file locale dopo averlo inviato  
        await event.delete()  # Cancella il comando originale  
    else:  
        await event.edit(msg)  

@client.on(events.NewMessage(pattern=r'\.resolve (\d+)', outgoing=True))  
async def resolve(event):  
    """ Mostra la chiocciola (@) di un utente dato il suo ID, modificando il messaggio originale. """  
    user_id = int(event.pattern_match.group(1))  

    try:  
        user = await client.get_entity(user_id)  
        username = f"@{user.username}" if user.username else "L'utente non ha un username."  
        await event.edit(f"💻 Username: {username}")  
    except Exception as e:  
        await event.edit(f"⚠️ Errore: impossibile trovare l'utente con ID {user_id}.")  

@client.on(events.NewMessage(pattern=r'\.mute', outgoing=True))  
async def mute(event):  
    """ Alterna tra mute e smute in chat privata. """  

    if not event.is_private:  
        await event.edit("⚠️ Questo comando può essere usato solo nelle chat private.")  
        return  

    chat_id = event.chat_id  

    if chat_id in muted_users:  
        muted_users.remove(chat_id)  
        await event.edit("🔊 Mute disattivato! Ora puoi vedere i messaggi del partner.")  
    else:  
        muted_users.add(chat_id)  
        await event.edit("🔇 Mute attivato! Tutti i messaggi del partner verranno eliminati.")  

@client.on(events.NewMessage(incoming=True))  
async def delete_incoming(event):  
    """ Cancella i messaggi in arrivo se il mute è attivo. """  
    if event.chat_id in muted_users and not event.out:  
        await event.delete()  

@client.on(events.NewMessage(pattern=r'\.delme', outgoing=True))  
async def delme(event):  
    """ Elimina tutti i messaggi TUOI in una chat. """  

    if not event.is_private:  
        await event.edit("⚠️ Questo comando può essere usato solo in chat private.")  
        return  

    # Ottieni tutti i messaggi della chat  
    async for message in client.iter_messages(event.chat_id, from_user=event.sender_id):  
        await message.delete()  # Cancella il messaggio  

    await event.edit("🗑️ Tutti i tuoi messaggi sono stati eliminati.")  

@client.on(events.NewMessage(pattern=r'\.spam (\d+) (.+)', outgoing=True))  
async def spam(event):  
    """ Spamma un messaggio per un determinato numero di volte, cancellando il messaggio originale. """  

    try:  
        count = int(event.pattern_match.group(1))  
        message = event.pattern_match.group(2)  

        # Cancella il messaggio originale  
        await event.delete()  

        # Spamma il messaggio  
        for _ in range(count):  
            await event.respond(message)  # Spamma il messaggio  

        await event.edit(f"💬 Messaggio spammato {count} volte.")  
    except ValueError:  
        await event.edit("⚠️ Errore: inserisci un numero valido di spam e un messaggio.")  

@client.on(events.NewMessage(pattern=r'\.ping', outgoing=True))  
async def ping(event):  
    """ Mostra solo i ms di ping senza inviare un altro messaggio. """  
    start_time = time.time()  
    await event.edit("Calcolando il ping...")  # Modifica il messaggio originale  
    end_time = time.time()  
    ping = round((end_time - start_time) * 1000)  # Ping in millisecondi  
    await event.edit(f"Ping: {ping} ms")  # Mostra il tempo di risposta  

@client.on(events.NewMessage(pattern=r'\.creator', outgoing=True))  
async def creator(event):  
    """ Mostra il creatore del bot. """  
    await event.edit("👨‍💻 Creatore: @incartocciato")  

@client.on(events.NewMessage(pattern=r'\.verify', outgoing=True))  
async def verify(event):  
    """ Verifica se l'account è limitato o meno tramite @spambot. """  
    # Manda /start a @spambot  
    spambot = await client.get_entity('@spambot')  
    await client.send_message(spambot, '/start')  

    # Aspetta la risposta del bot  
    response = await client.get_messages(spambot, limit=1, reverse=True)  

    # Verifica la risposta  
    if response:  
        if "limitato" in response[0].text.lower():  
            await event.edit("⚠️ L'account è limitato.")  
        else:  
            await event.edit("✅ L'account non è limitato.")  
    else:  
        await event.edit("⚠️ Impossibile verificare lo stato dell'account.")  

# Funzioni per gestire PayPal e Wallet

@client.on(events.NewMessage(pattern=r'\.setpp (.+)', outgoing=True))
async def set_paypal(event):
    """ Salva il PayPal dell'utente e modifica il messaggio con la conferma. """
    paypal = event.pattern_match.group(1)
    user_data[event.sender_id] = user_data.get(event.sender_id, {})
    user_data[event.sender_id]['paypal'] = paypal  # Salva il PayPal
    await event.edit(f" ✅PayPal impostato correttamente")

@client.on(events.NewMessage(pattern=r'\.setwallet (.+)', outgoing=True))
async def set_wallet(event):
    """ Salva il Wallet dell'utente e modifica il messaggio con la conferma. """
    wallet = event.pattern_match.group(1)
    user_data[event.sender_id] = user_data.get(event.sender_id, {})
    user_data[event.sender_id]['wallet'] = wallet  # Salva il Wallet
    await event.edit(f" ✅Wallet impostato correttamente")

@client.on(events.NewMessage(pattern=r'\.pp', outgoing=True))
async def show_paypal(event):
    """ Mostra il PayPal settato dall'utente. """
    paypal = user_data.get(event.sender_id, {}).get('paypal', '❌Nessun PayPal impostato.')
    await event.edit(f"{paypal}")

@client.on(events.NewMessage(pattern=r'\.btc', outgoing=True))
async def show_wallet(event):
    """ Mostra il Wallet settato dall'utente. """
    wallet = user_data.get(event.sender_id, {}).get('wallet', '❌Nessun Wallet impostato.')
    await event.edit(f"{wallet}")

async def get_bot_id(username):
    try:
        bot_entity = await client.get_entity(username)
        return bot_entity.id
    except Exception as e:
        print(f"Errore nel recupero dell'ID per il bot {username}: {e}")
        return None

@client.on(events.NewMessage(pattern=r'\.exch (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)', outgoing=True))
async def exch(event):
    """ Calcola la percentuale di una cifra e modifica il messaggio con il risultato. """
    try:
        percentuale = float(event.pattern_match.group(1))
        cifra = float(event.pattern_match.group(2))
        risultato = (percentuale / 100) * cifra
        await event.edit(f"💱 {percentuale}% di {cifra} è {risultato:.2f}")
    except Exception as e:
        await event.edit(f"⚠️ Errore durante il calcolo: {str(e)}")

@client.on(events.NewMessage(pattern=r'\.stickermsg', outgoing=True))
async def stickermsg(event):
    """ Inoltra un messaggio a @QuotLyBot per generare uno sticker e lo invia nella chat originale. """
    if not event.reply_to_msg_id:
        await event.edit("⚠️ Rispondi a un messaggio per trasformarlo in sticker!")
        return

    reply_msg = await event.get_reply_message()

    quotlybot_username = "QuotLyBot"  # Usa il nome utente corretto del bot
    quotlybot_id = await get_bot_id(quotlybot_username)

    if quotlybot_id is None:
        await event.edit(f"⚠️ Errore: impossibile trovare il bot {quotlybot_username}.")
        return

    try:
        # Inoltra il messaggio al bot
        await client.forward_messages(quotlybot_id, reply_msg)
        await event.edit("🎨 Creazione dello sticker in corso...")

        # Attendi la risposta del bot
        for _ in range(15):  # Aumentato il numero di tentativi
            await asyncio.sleep(3)  # Aumentato il tempo di attesa per ogni ciclo
            async for msg in client.iter_messages(quotlybot_id, limit=5):
                if msg.sticker:
                    await client.send_file(event.chat_id, msg.sticker)
                    await event.delete()
                    return

        await event.edit("⚠️ Errore: impossibile ottenere lo sticker.")
    except Exception as e:
        await event.edit(f"⚠️ Errore: {str(e)}")
# Nuovo comando: .typespace [TESTO] - Crea animazione al testo nello stesso messaggio
@client.on(events.NewMessage(pattern=r'\.typespace (.+)', outgoing=True))
async def typespace(event):
    """ Crea un'animazione di scrittura del testo nello stesso messaggio. """
    testo = event.pattern_match.group(1)

    # Inizializza con un messaggio vuoto tra backtick
    messaggio = "ㅤ"
    await event.edit(messaggio)  # Modifica il messaggio iniziale

    # Crea l'animazione modificando il messaggio
    for char in testo:
        messaggio += char  # Aggiungi il carattere al messaggio
        await event.edit(f"`{messaggio}`")  # Modifica il messaggio con il testo aggiornato, sempre tra backtick
        await asyncio.sleep(1)  # Ritardo di 1 secondo tra ogni carattere

    # Una volta completato, invia il testo finale, racchiuso nei backtick
    await event.edit(f"`{testo}`")  # Modifica l'ultimo messaggio con il testo completo tra backtick
    # Comando .audio - Invia un vocale con il testo fornito
@client.on(events.NewMessage(pattern=r'\.audio (.+)', outgoing=True))
async def audio_message(event):
    """ Crea un file audio con il testo fornito e lo invia. """
    text = event.pattern_match.group(1)  # Prende il testo che segue il comando

    # Genera il file audio con gTTS (voce femminile)
    tts = gTTS(text=text, lang='it', slow=False)  # Lang 'it' per italiano, slow=False per velocità normale
    audio_file = 'audio.mp3'
    tts.save(audio_file)  # Salva il file audio

    # Invia il file audio come un nuovo messaggio, senza fare un reply
    await event.respond(file=audio_file)

    # Cancella il messaggio originale che ha inviato il comando .audio
    await event.delete()

    # Rimuove il file audio dopo l'invio
    os.remove(audio_file)

# Comando .bersaglio - Animazione della sparatoria
@client.on(events.NewMessage(pattern=r'\.bersaglio', outgoing=True))
async def bersaglio_animation(event):
    """ Esegue un'animazione di una sparatoria tra poliziotti. """

    frames = [
        "👮🏿‍♂️\n🎯                                🔫👮🏼‍♂️\n👮🏻‍♂️",
        "👮🏿‍♂️\n🎯                                💥🔫👮🏼‍♂️\n👮🏻‍♂️",
        "🪦\n🎯                                🔫👮🏼‍♂️\n👮🏻‍♂️",
        "🪦\n🎯                                🔫👮🏼‍♂️\n👮🏻‍♂️👍🏻",
        "🪦\n🎯                                🔫👮🏼‍♂️\n👮🏻‍♂️💬 nice job!"
    ]

    for frame in frames:
        await event.edit(frame)
        await asyncio.sleep(1.6)  # Pausa tra i frame per rendere l'animazione fluida

# Comando .sega - Animazione ciclica del testo
@client.on(events.NewMessage(pattern=r'\.sega', outgoing=True))
async def sega_animation(event):
    """ Esegue un'animazione ciclica del testo. """

    frames = [
        "8=✊=D",
        "8✊==D",
        "8=✊=D",
        "8✊==D",
        "8=✊=D💦"
    ]

    sleep_time = 0.5  # Tempo di attesa tra i frame
    for _ in range(2):  # Ripete l'animazione 2 volte
        for frame in frames:
            await event.edit(frame)
            await asyncio.sleep(sleep_time)

    await event.edit("💀 Finito...")  # Testo finale dopo l'animazione

# Comando .hack - Simula un attacco hacker su un account
@client.on(events.NewMessage(pattern=r'\.hack', outgoing=True))
async def hack_animation(event):
    """ Simula un attacco hacker su un account e mostra l'animazione. """

    # Recupera il messaggio precedente e il nome dell'utente
    if event.reply_to_msg_id:
        replied_message = await event.get_reply_message()
        user_name = replied_message.sender.username if replied_message.sender.username else replied_message.sender.first_name
    else:
        await event.edit("🚫 Devi rispondere a un messaggio per usare il comando!")
        return

    frames = [
        "Stiamo bypassando e facendo brech nel tuo account...👨🏼‍💻",
        "Estraendo la chiave 2FA🔑",
        f"Siamo nel tuo account! @{user_name} sei fottuto👹"
    ]

    # Eseguiamo l'animazione dei frame
    for frame in frames:
        await event.edit(frame)
        await asyncio.sleep(3)  # Pausa tra i frame

print("⚡ UserBot attivo!")  
client.start()  
client.run_until_disconnected()

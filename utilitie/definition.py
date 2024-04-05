import json
import pandas as pd
import os
import time
from datetime import datetime, timedelta

def initialisation(exchange, dossier_data, dossier_exchange, dossier_interval, params, nom_exchange):

    # Création des dossiers s'ils n'existent pas
    for directory in [dossier_data, dossier_exchange, dossier_interval]:
        os.makedirs(directory, exist_ok=True)

    # ajouter la position_amount à chaque paire
    for pair in params:
        params[pair]['position_amount'] = 0

    # Charge les marchés disponibles sur l'échange Bitget
    markets = exchange.load_markets()

    # Boucle sur une copie des clés pour éviter les problèmes de modification pendant l'itération
    for pair in list(params.keys()):
        # Vérifie si la paire est disponible sur l'échange
        if pair not in markets:
            # Si la paire n'est pas disponible, la supprime de params
            del params[pair]
            print(f"The {pair} is not available on the {nom_exchange} exchange and has been removed from params.")

    for envelope in params.values():
        envelope['long_envelopes'] = [sublist + [1] for sublist in envelope['long_envelopes']]
        envelope['short_envelopes'] = [sublist + [1] for sublist in envelope['short_envelopes']]

    # À la fin de votre code, écrivez les paramètres dans un fichier JSON
    with open('utilitie/params.json', 'w') as f:
        json.dump(params, f)


def get_ohlcv(exchange, start_date_milliseconds, limit, time, dossier_interval):

    
    # Ouvrir le fichier JSON et charger les paramètres
    with open('utilitie/params.json', 'r') as f:
        params = json.load(f)

    for pair in params:
        name_pair = f"{pair.replace('/', '_')}.csv"
        fichier_name = f"{dossier_interval}/{name_pair}"
        since = start_date_milliseconds
        ohlcv_data = []
        while True:
            fetched_ohlcv = exchange.fetch_ohlcv(pair, time, since=since, limit=limit)
            ohlcv_data.extend(fetched_ohlcv)
            if len(fetched_ohlcv) < limit:
                print(f"OHLCV data have been recovered for {pair}")
                break
                
            else:
                since = fetched_ohlcv[-1][0]

        # Conversion des données récupérées en DataFrame et enregistrement dans un fichier CSV
        if ohlcv_data:
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df.iloc[:-1]  # Supprime la dernière ligne du DataFrame
            df.to_csv(fichier_name)

            # Calcul de la moyenne mobile
            df['ma'] = df['close'].rolling(window=params[pair]["moyenne_mobile"]).mean()

            # Stockage de la dernière valeur de la moyenne mobile dans params
            params[pair]["value_last_moyenne_mobile"] = df['ma'].iloc[-1]

    # Récupération de l'heure actuelle
    current_hour = datetime.now()
    current_hour_truncated = current_hour.replace(minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")

    # Enregistrement de l'heure actuelle tronquée dans un fichier JSON
    data = {"last_hour": current_hour_truncated}
    with open('utilitie/timestamp_last_hour.json', 'w') as file:
        json.dump(data, file)
            
    # À la fin de votre code, écrivez les paramètres dans un fichier JSON
    with open('utilitie/params.json', 'w') as f:
        json.dump(params, f)


def calcul_params(exchange, multiplicator):

    balance = exchange.fetch_balance()
    usdt_balance = balance['USDT']['total']
    print(f"USDT balance: {usdt_balance}")

    # Ouvrir le fichier JSON et charger les paramètres
    with open('utilitie/params.json', 'r') as f:
        params = json.load(f)

    total_size = sum(params[pair]['size'] for pair in params)

    for pair, values in params.items():
        params[pair]['size'] /= total_size

        if values.get('ratio') == 0:
            del values['long_envelopes']
        if values.get('ratio') == 1:
            del values['short_envelopes']

        if 'long_envelopes' in values:
        # Additionne les troisièmes chiffres de long_envelopes
            total = sum(envelope[1] for envelope in values['long_envelopes'])

            values['total_long_envelopes'] = total
            size_long = values['size'] * values['ratio']
            values['size_long'] = size_long


        if 'short_envelopes' in values:
        # Additionne les troisièmes chiffres de short_envelopes
            total = sum(envelope[1] for envelope in values['short_envelopes'])

            values['total_short_envelopes'] = total
            size_short = values['size'] * ( 1 - values['ratio'])
            values['size_short'] = size_short




    for pair, values in params.items():        
    # Vérifie si long_envelopes existe pour cette paire
        if 'long_envelopes' in values:
        # Parcourt chaque liste dans long_envelopes
            for envelope in values['long_envelopes']:
            # Modifie les valeurs dans la liste
            # Remplacez ceci par votre propre logique de modification
                envelope[0] = values['value_last_moyenne_mobile'] + values['value_last_moyenne_mobile'] * envelope[0]
                envelope[1] = ((usdt_balance * (values["size_long"] * (envelope[1]/values['total_long_envelopes'])))/envelope[0]) * multiplicator

        if 'short_envelopes' in values:
        # Parcourt chaque liste dans long_envelopes
            for envelope in values['short_envelopes']:
            # Modifie les valeurs dans la liste
            # Remplacez ceci par votre propre logique de modification
                envelope[0] = values['value_last_moyenne_mobile'] - values['value_last_moyenne_mobile'] * envelope[0]
                envelope[1] = ((usdt_balance * (values["size_short"] * (envelope[1]/values['total_short_envelopes'])))/envelope[0]) * multiplicator



    long_envelopes_values = [value for sublist in params.values() for value in sublist.get('long_envelopes', [])]
    short_envelopes_values = [value for sublist in params.values() for value in sublist.get('short_envelopes', [])]

    # À la fin de votre code, écrivez les paramètres dans un fichier JSON
    with open('utilitie/order.json', 'w') as f:
        json.dump(params, f)



def open_order(exchange, margin_mode):

    # Ouvrir le fichier JSON et charger les paramètres
    with open('utilitie/order.json', 'r') as f:
        params = json.load(f)

    exchange.options['marginMode'] = margin_mode  # 'isolated' ou 'cross'

    # Créer une liste pour stocker les informations sur les ordres
    order_history = []
    # Placer les ordres pour chaque paire
    
    for pair, values in params.items():
        symbol = f"{pair}:USDT"
        type = "limit"
        params = {}
        
        if 'long_envelopes' in values:
            for envelope in values['long_envelopes']:
                price = envelope[0]
                amount = envelope[1]
                side = "sell" # buy ou sell
                
                if envelope[2] == 1:
                    try:
                        order_info = exchange.create_order(symbol=symbol, type=type, side=side, amount=amount, price=price, params=params)
                        order_history.append({'id': order_info['id'], 'envelopes': [side,values['long_envelopes'].index(envelope)], 'pair': pair})
                        print(f"Order created for {symbol}")
                    except Exception as e:
                        print(f"Error creating order for {symbol}: {str(e)}")
        
        if 'short_envelopes' in values:
            for envelope in values['short_envelopes']:
                price = envelope[0]
                amount = envelope[1]
                side = "buy" # buy ou sell
                
                if envelope[2] == 1:
                    try:
                        order_info = exchange.create_order(symbol=symbol, type=type, side=side, amount=amount, price=price, params=params)
                        order_history.append({'id': order_info['id'], 'envelopes': [side, values['short_envelopes'].index(envelope)], 'pair': pair})
                        print(f"Order created for {symbol}")
                    except Exception as e:
                        print(f"Error creating order for {symbol}: {str(e)}")

    with open('utilitie/order_history.json', 'w') as f:
        json.dump(order_history, f)



def order_executer(exchange):

    # Charger order_history depuis le fichier JSON
    try:
        with open('utilitie/order_history.json', 'r') as f:
            order_history = json.load(f)
    except FileNotFoundError:
        # Gérer le cas où le fichier n'existe pas encore
       order_history = []

    # Ouvrir le fichier JSON et charger les paramètres
    with open('utilitie/params.json', 'r') as f:
        params = json.load(f)

    following_orders = exchange.fetch_closed_orders(since=None)

    # Trie les ordres par timestamp
    following_orders.sort(key=lambda order: order['timestamp'])

    # Parcourt chaque ordre dans following_orders
    for order in following_orders:
    # Parcourt chaque élément dans order_history
        for history in order_history:
        # Vérifie si l'ordre est un ordre d'ouverture
            if order['info']['tradeSide'] == 'open':
                if order['id'] == history['id']:
                    if order['id'] == history['id']:
                    # Récupère la liste contenue dans envelopes et le nom de la paire
                        pair_name = history['pair']
                        position = history['envelopes']
                        position_ls = position[0]
                        position_envelopes = position[1]

                    # Vérifie si la paire existe dans params
                        if pair_name in params:
                        # Vérifie si la position est long ou short
                            if position_ls == "sell":
                            # Vérifie si long_envelopes existe pour cette paire
                                if 'long_envelopes' in params[pair_name]:
                                    # Remplacez ceci par votre propre logique de modification
                                    params[pair_name]['long_envelopes'][position_envelopes][2] = 0


                            elif position_ls == "buy":
                            # Vérifie si short_envelopes existe pour cette paire
                                if 'short_envelopes' in params[pair_name]:
                                    # Remplacez ceci par votre propre logique de modification
                                    params[pair_name]['short_envelopes'][position_envelopes][2] = 0

    # Vérifie si l'ordre est un ordre de fermeture
        if order['info']['tradeSide'] == 'close':
            symbol = order['symbol']
            pair_name = symbol.replace('/USDT:USDT', '/USDT')
        # Vérifie si la paire existe dans params
            if pair_name in params:
            # Modifie la troisième valeur dans toutes les sous-listes de long_envelopes
                for envelope in params[pair_name].get('long_envelopes', []):
                    if len(envelope) >= 3:
                        envelope[2] = 1
            # Modifie la troisième valeur dans toutes les sous-listes de short_envelopes
                for envelope in params[pair_name].get('short_envelopes', []):
                    if len(envelope) >= 3:
                        envelope[2] = 1

    # À la fin de votre code, écrivez les paramètres dans un fichier JSON
    with open('utilitie/params.json', 'w') as f:
        json.dump(params, f)



    

def close_order(exchange, type):

    # Ouvrir le fichier JSON et charger les paramètres
    with open('utilitie/params.json', 'r') as f:
        params = json.load(f)
    open_positions = exchange.fetch_positions()

    for pair in params:
        name_pair = pair
        for position in open_positions:
            if position['symbol'] == name_pair + ':USDT':

                symbol_position = position['symbol']
                symbol = symbol_position.replace(':USDT', '')
                side = 'sell' if position['side'] == 'long' else 'buy'
                price = params[symbol]['value_last_moyenne_mobile']

                if params[pair]['position_amount'] == 0:

                    amount = position['contracts']

                    try:
                        order = exchange.create_order(symbol=symbol_position, price=price, type=type, side=side, amount=amount, params={"reduceOnly": True}) 
                    except Exception as e:
                        print(f"Failed to place closing order for position {symbol}. Error: {e}")

                    params[pair]["position_amount"] = position['contracts']

                if params[pair]['position_amount'] < position['contracts']:
        
                    amount = position['contracts'] - params[pair]['position_amount']

                    try:
                        order = exchange.create_order(symbol=symbol_position, price=price, type=type, side=side, amount=amount, params={"reduceOnly": True}) 
                    except Exception as e:
                        print(f"Failed to place closing order for position {symbol}. Error: {e}")

                    params[pair]["position_amount"] = position['contracts']


            elif pair not in open_positions:
                params[pair]["position_amount"] = 0

        # À la fin de votre code, écrivez les paramètres dans un fichier JSON
        with open('utilitie/params.json', 'w') as f:
            json.dump(params, f)


def cancel_order(exchange, params):

    # Ouvrir le fichier JSON et charger les paramètres
    with open('utilitie/params.json', 'r') as f:
        params = json.load(f)

    # Récupérer tous les ordres ouverts
    open_orders = exchange.fetch_open_orders()

    # Annuler les ordres par groupe de 100 jusqu'à ce que tous les ordres ouverts soient annulés
    while open_orders:
        # Sélectionner les 100 premiers ordres ouverts
        orders_to_cancel = open_orders[:50]

        # Annuler les ordres sélectionnés
        for open_order in orders_to_cancel:
            try:
                exchange.cancel_order(open_order['id'], open_order['symbol'])
                print(f"Ordre {open_order['id']} annulé avec succès.")
            except Exception as e:
                print(f"Erreur lors de l'annulation de l'ordre {open_order['id']}: {str(e)}")

        # Attendre un court instant pour respecter la limite de requêtes de l'API
        time.sleep(1)  # Attendez 1 seconde entre chaque groupe d'annulations

        # Mettre à jour la liste des ordres ouverts après annulation des ordres précédents
        open_orders = exchange.fetch_open_orders()
        
        for pair in params:
            params[pair]["position_amount"] = 0
        params[pair]["position_amount"] = 0

        # À la fin de votre code, écrivez les paramètres dans un fichier JSON
        with open('utilitie/params.json', 'w') as f:
            json.dump(params, f)

# Fonction pour charger la dernière heure à partir du fichier JSON
def load_last_hour():
    try:
        with open('utilitie/timestamp_last_hour.json', 'r') as file:
            data = json.load(file)
            return data.get("last_hour")
    except FileNotFoundError:
        return None

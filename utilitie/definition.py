import json
import pandas as pd
import os
from datetime import datetime, timedelta

def initialisation(exchange, dossier_data, dossier_exchange, dossier_interval, params):


    # ajouter la position_amount à chaque paire
    for pair in params:
        params[pair]['position_amount'] = 0

    # Charge les marchés disponibles sur l'échange Bitget
    markets = exchange.load_markets()

    # Boucle sur une copie des clés pour éviter les problèmes de modification pendant l'itération
    for pair in list(params.keys()):
        print(pair)  # Utiliser list() pour obtenir une copie des clés
        # Vérifie si la paire est disponible sur l'échange
        if pair not in markets:
            # Si la paire n'est pas disponible, la supprime de params
            del params[pair]
            print(f"The {pair} is not available on the exchange and has been removed from params.")
    print(params)
    # À la fin de votre code, écrivez les paramètres dans un fichier JSON
    with open('utilitie/params.json', 'w') as f:
        json.dump(params, f)


def calcul_params(usdt_balance):

    # Ouvrir le fichier JSON et charger les paramètres
    with open('utilitie/params.json', 'r') as f:
        params = json.load(f)

    total_size = sum(params[pair]['size'] for pair in params)
    for envelope in params.values():
        envelope['long_envelopes'] = [sublist + [1] for sublist in envelope['long_envelopes']]
        envelope['short_envelopes'] = [sublist + [1] for sublist in envelope['short_envelopes']]

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
                envelope[1] = (usdt_balance * (values["size_long"] * (envelope[1]/values['total_long_envelopes'])))/envelope[0]

        if 'short_envelopes' in values:
        # Parcourt chaque liste dans long_envelopes
            for envelope in values['short_envelopes']:
            # Modifie les valeurs dans la liste
            # Remplacez ceci par votre propre logique de modification
                envelope[0] = values['value_last_moyenne_mobile'] - values['value_last_moyenne_mobile'] * envelope[0]
                envelope[1] = (usdt_balance * (values["size_short"] * (envelope[1]/values['total_short_envelopes'])))/envelope[0]



    long_envelopes_values = [value for sublist in params.values() for value in sublist.get('long_envelopes', [])]
    short_envelopes_values = [value for sublist in params.values() for value in sublist.get('short_envelopes', [])]

    # À la fin de votre code, écrivez les paramètres dans un fichier JSON
    with open('utilitie/params.json', 'w') as f:
        json.dump(params, f)


def get_ohlcv(exchange, start_date_milliseconds, limit, time, ):

    
    # Ouvrir le fichier JSON et charger les paramètres
    with open('utilitie/params.json', 'r') as f:
        params = json.load(f)

    for pair in params:

        since = start_date_milliseconds
        ohlcv_data = []
        while True:
            fetched_ohlcv = exchange.fetch_ohlcv(pair, time, since=since, limit=limit)
            ohlcv_data.extend(fetched_ohlcv)
            if len(fetched_ohlcv) < limit:
                break
            else:
                since = fetched_ohlcv[-1][0]

        # Conversion des données récupérées en DataFrame et enregistrement dans un fichier CSV
        if ohlcv_data:
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df.iloc[:-1]  # Supprime la dernière ligne du DataFrame

            # Calcul de la moyenne mobile
            df['ma'] = df['close'].rolling(window=params[pair]["moyenne_mobile"]).mean()

            # Stockage de la dernière valeur de la moyenne mobile dans params
            params[pair]["value_last_moyenne_mobile"] = df['ma'].iloc[-1]

    # À la fin de votre code, écrivez les paramètres dans un fichier JSON
    with open('utilitie/params.json', 'w') as f:
        json.dump(params, f)





def order_executer(exchange, order_history):

    
    # Ouvrir le fichier JSON et charger les paramètres
    with open('utilitie/params.json', 'r') as f:
        params = json.load(f)
   
    timestamp_last_order = ""

    # Chemin du fichier où nous allons stocker timestamp_last_order
    timestamp_file = 'utilitie/timestamp_last_order.json'
    
    # Si le fichier existe, lire la valeur de timestamp_last_order à partir de ce fichier
    if os.path.exists(timestamp_file):
        with open(timestamp_file, 'r') as file:
            timestamp_last_order = json.load(file)
    # Utilisation de fetch_closed_orders avec le paramètre since pour récupérer les ordres suivants à partir du timestamps spécifié +1
        following_orders = exchange.fetch_closed_orders(since=int(timestamp_last_order) + 1)
    else:
    # Si le fichier n'existe pas, récupérer tous les ordres
        following_orders = exchange.fetch_closed_orders(since=None)
        timestamp_last_order = str(following_orders[-1]['timestamp']) if following_orders else timestamp_last_order

    # Écrire la valeur de timestamp_last_order dans le fichier pour l'utiliser lors de la prochaine exécution
    with open(timestamp_file, 'w') as file:
        json.dump(timestamp_last_order, file)

    # Trie les ordres par timestamp
    following_orders.sort(key=lambda order: order['timestamp'])

    # Parcourt chaque ordre dans following_orders
    for order in following_orders:
    # Parcourt chaque élément dans order_history
        for history in order_history:
        # Vérifie si l'ordre est un ordre d'ouverture
            if order['info']['tradeSide'] == 'open':
                if order['id'] == history['id']:
                    print('Order is open')  # Remplacez ceci par votre propre logique
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
            print('test')
            symbol = order['symbol']
            print(symbol)
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


def open_order(exchange, margin_mode):

    # Ouvrir le fichier JSON et charger les paramètres
    with open('utilitie/params.json', 'r') as f:
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
                        print(order)
                    except Exception as e:
                        print(f"Failed to place closing order for position {symbol}. Error: {e}")

                    params[pair]["position_amount"] = position['contracts']

                if params[pair]['position_amount'] < position['contracts']:
        
                    amount = position['contracts'] - params[pair]['position_amount']

                    try:
                        order = exchange.create_order(symbol=symbol_position, price=price, type=type, side=side, amount=amount, params={"reduceOnly": True}) 
                        print(order)
                    except Exception as e:
                        print(f"Failed to place closing order for position {symbol}. Error: {e}")

                    params[pair]["position_amount"] = position['contracts']


            elif pair not in open_positions:
                params[pair]["position_amount"] = 0

        # À la fin de votre code, écrivez les paramètres dans un fichier JSON
        with open('utilitie/params.json', 'w') as f:
            json.dump(params, f)

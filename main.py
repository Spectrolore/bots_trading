import csv
import os
import json
import ccxt
from datetime import datetime, timedelta
import time
import pandas as pd
from secret import ACCOUNTS
from utilitie.definition import initialisation, calcul_params, get_ohlcv, order_executer, open_order, close_order, cancel_order, load_last_hour



exchange_auth_object = ACCOUNTS["bitget_envelope"]
exchange = ccxt.bitget(exchange_auth_object)
nom_exchange = 'bitget'
dossier_data = 'data'
margin_mode = 'cross' # cross ou isolated
interval = '1h'
#start_date = '2024-03-01'
start_date = (datetime.now() - timedelta(hours=10)).strftime("%Y-%m-%d %H:%M:%S")
limit = 200
usdt_balance = 800
multiplicator = 2
levrage = 5
stop_loss = 0.05

params = {

    "BTC/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1]],
    },

    "ETH/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1]],
    },

    "ADA/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.09, 1], [0.12, 1], [0.15, 1]],
        "short_envelopes": [[0.07, 1], [0.09, 1], [0.12, 1], [0.15, 1]],
    },

    "AVAX/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.09, 1], [0.12, 1], [0.15, 1]],
        "short_envelopes": [[0.07, 1], [0.09, 1], [0.12, 1], [0.15, 1]],
    },

    "EGLD/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "KSM/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "OCEAN/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "REN/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "ACH/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "APE/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "CRV/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "DOGE/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "ENJ/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "FET/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "ICP/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "IMX/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "LDO/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "MAGIC/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "REEF/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "SAND/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "TRX/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

    "XTZ/USDT": {
        "size": 1,
        "moyenne_mobile": 5,
        "ratio": 0.5, # 0.5 = 50% long 50% short 1 = que long, 0 = que short 
        "long_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
        "short_envelopes": [[0.07, 1], [0.1, 1], [0.15, 1], [0.2, 1]],
    },

}

# Création d'un dossier pour stocker les données
dossier_exchange = f"{dossier_data}/{nom_exchange}"
dossier_interval = f"{dossier_exchange}/{interval}"

# Conversion de la date de début en millisecondes
start_date_obj = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
start_date_timestamp = datetime.timestamp(start_date_obj)
start_date_milliseconds = int(start_date_timestamp * 1000)


# Initialisation
initialisation(exchange, dossier_data, dossier_exchange, dossier_interval, params, nom_exchange)


# Récupération des données OHLCV + moyenne mobile
get_ohlcv(exchange, start_date_milliseconds, limit, interval, dossier_interval)

# calcul tous les parametres utiles pour les ordres
calcul_params(exchange, multiplicator)

# Annuler les ordres en attente
cancel_order(exchange, params)

# modifier params en fonction des nouveau ordres executer 
order_executer(exchange)

# placer ordre open 
open_order(exchange, margin_mode)

# Récupération de l'heure actuelle avec les minutes et les secondes mises à zéro
current_hour = datetime.now().replace(minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")

# Chargement de la dernière heure depuis le fichier JSON
last_hour = load_last_hour()



while True:
    # Récupération de l'heure actuelle avec les minutes et les secondes mises à zéro
    current_hour = datetime.now().replace(minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")

    # Chargement de la dernière heure depuis le fichier JSON
    last_hour = load_last_hour()

    # modifier params en fonction des nouveau ordres executer 
    order_executer(exchange)

    # Placer l'ordre de clôture
    close_order(exchange, type="limit")


    # Comparaison de la dernière heure avec l'heure actuelle
    if last_hour is not None and last_hour != current_hour:


        # Récupération des données OHLCV + moyenne mobile
        get_ohlcv(exchange, start_date_milliseconds, limit, interval, dossier_interval)

        # calcul tous les parametres utiles pour les ordres
        calcul_params(exchange, multiplicator)

        # Annuler les ordres en attente
        cancel_order(exchange, params)

        # modifier params en fonction des nouveau ordres executer 
        order_executer(exchange)

        # placer ordre open 
        open_order(exchange, margin_mode)

    # Faire une pause de 5 secondes
    time.sleep(5)

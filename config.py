#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import logging
import os
import configparser as parser
from pathlib import Path



config_file = parser.ConfigParser()
p = Path(os.path.dirname(__file__)).parent
config_file.read(os.path.join(p, 'prueba.conf'))
log = config_file.get('RUTA', 'log')
logging.basicConfig(filename=log + str(os.path.basename(p)) + str(os.path.basename(Path(os.path.dirname(__file__)))) +str(datetime.date.today())+'.log', filemode='a',
                    level=os.environ.get("LOGLEVEL", "INFO"),
                    format='%(asctime)s - '+str(os.getenv('USERNAME')) + ' - %(name)s - %(levelname)s - %(message)s')
logging.info('Started')
logging.info(__file__)
logging.info("log Level: " + str(os.environ.get("LOGLEVEL", "INFO")))

btasa = config_file.getboolean('REPLICA', 'TASA')
logging.info("Replica de Tasa: " + str(btasa))
file = config_file.get('RUTA', 'ICONO')
logging.info("Ruta de Icono: " + str(file))
bicono = config_file.getboolean('CONFIG', 'ICONO')
logging.info("Cargar Icono: " + str(bicono))



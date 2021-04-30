#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import logging
import os
import configparser as parser
from pathlib import Path



config_file = parser.ConfigParser()
p = str(Path(os.path.dirname(__file__)))
#print str(os.path.join((p), 'prueba.conf'))
config_file.read(os.path.join(p, 'prueba.conf'))
log = config_file.get('RUTA', 'log')
logging.basicConfig(filename=log +str(os.getenv('USERNAME'))+ str(datetime.date.today())+'.log', filemode='a',
                    level=os.environ.get("LOGLEVEL", "INFO"),
                    format='%(asctime)s - '+str(os.getenv('USERNAME')) + ' - %(name)s - %(levelname)s - %(message)s')
logging.info('Started')
logging.info(__file__)
logging.info("log Level: " + str(os.environ.get("LOGLEVEL", "INFO")))


file = config_file.get('RUTA', 'ICONO')
logging.info("Ruta de Icono: " + str(file))
bicono = config_file.getboolean('CONFIG', 'ICONO')
logging.info("Cargar Icono: " + str(bicono))
dias = config_file.get('CONFIG', 'DIAS_QUERY')
logging.info("Días atras en la consulta: " + str(dias))
reportez = config_file.get('RUTA', 'REPORTEZ')
logging.info("Ruta de Reportes Z: " + str(reportez))

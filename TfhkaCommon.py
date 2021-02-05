# -*- coding: iso-8859-1 -*-

import serial
import operator
import sys
import time
import glob
import os
import datetime

class port:
  portName = "COM3" #Changed by p
  baudRate =9600
  dataBits =serial.EIGHTBITS
  stopBits =serial.STOPBITS_ONE
  parity =serial.PARITY_EVEN
  readBufferSize =256
  writeBufferSize =256
  readTimeOut=1.5
  writeTimeOut=5

class tf_ve_ifpython:
  bandera=False
  mdepura=False
  status =''
  envio  =''
  error  =''
  ##
  Port=port()
  
#Funcion ABRIR
  def OpenFpctrl(self, p):
    if not self.bandera:
      try:
        self.ser=serial.Serial(port=p, baudrate=self.Port.baudRate, bytesize=self.Port.dataBits, parity=self.Port.parity, stopbits=self.Port.stopBits, timeout=self.Port.readTimeOut, writeTimeout=self.Port.writeTimeOut, xonxoff=0, rtscts=0)##Find out what are xonxoff, and rtscts for
        #print "baudrate", self.Port.baudRate
        self.bandera=True
        return True
      except (serial.portNotOpenError, serial.SerialTimeoutException):
        self.bandera=False
        self.envio = "Impresora no conectada o error accediendo al puerto" + str(p)
        return False

#Funcion CERRAR
  def CloseFpctrl(self):
    if self.bandera:
      self.ser.close()
      self.bandera=False
      return self.bandera

#Funcion MANIPULA
  def _HandleCTSRTS(self):
    try:
      self.ser.setRTS(True)
      lpri=1
      while not self.ser.getCTS():
        time.sleep(lpri/10)
        lpri=lpri+1
        if lpri>20:
          self.ser.setRTS(False)
          return False
      return True
    except serial.SerialException:
      return False

  def SendCmd(self,cmd):
    try:
      self.ser.flushInput()
      self.ser.flushOutput()
      if self._HandleCTSRTS():
        msj=self._AssembleQueryToSend(cmd)
        self._write(msj)
        rt=self._read(1)
        if rt==chr(0x06):
          self.envio = "Status: 00  Error: 00"
          rt=True
        else:
          self.envio = "Status: 00  Error: 89"
          rt=False
      else:
        self._GetStatusError(0, 128);
        self.envio = "Error... CTS in False"
        rt=False
      self.ser.setRTS(False)
    except serial.SerialException:
      rt=False
    return rt

  def SendCmdFile(self, f):
    for linea in f:
       if (linea!=""):
          #print linea
          self.SendCmd(linea)

  def _QueryCmd(self,cmd):
      try:
         self.ser.flushInput()
         self.ser.flushOutput()
         if self._HandleCTSRTS():
            msj=self._AssembleQueryToSend(cmd)
            self._write(msj)
            rt=True
         else:
            self._GetStatusError(0, 128);
            self.envio = "Error... CTS in False"
            rt=False
            self.ser.setRTS(False)
      except serial.SerialException:
         rt=False
      return rt

  def _FetchRow(self):
    while True:
      time.sleep(1)
      bytes = self.ser.inWaiting()
      if bytes>1:
        msj=self._read(bytes)
        linea=msj[1:-1]
        lrc=chr(self._Lrc(linea))
        if lrc==msj[-1]:
          self.ser.flushInput()
          self.ser.flushOutput()
          return msj
        else:
          break
      else:
        break
    return None

  def ReadFpStatus(self):
    if self._HandleCTSRTS():
      msj=chr(0x05)
      self._write(msj)
      time.sleep(0.05)
      r=self._read(5)
      if len(r)==5:
        if ord(r[1])^ord(r[2])^0x03 == ord(r[4]):
          return self._GetStatusError(ord(r[1]), ord(r[2]))
        else:
          return self._GetStatusError(0, 144)
      else:
        return self._GetStatusError(0, 114)
    else:
      return self._GetStatusError(0, 128);

  def _write(self,msj):
    if self.mdepura:
      print '<<< '+self._Debug(msj)
    self.ser.write(msj)

  def _read(self,bytes):
    msj = self.ser.read(bytes)
    if self.mdepura:
      print '>>> '+self._Debug(msj)
    return msj

  def _AssembleQueryToSend(self,linea):
    lrc = self._Lrc(linea+chr(0x03))
    previo=chr(0x02)+linea+chr(0x03)+chr(lrc)
    return previo

  def _Lrc(self,linea):
    return reduce(operator.xor, map(ord, linea))

  def _Debug(self,linea):
    if linea!=None:
      if len(linea)==0:
        return 'null'
      if len(linea)>3:
        lrc=linea[-1]
        linea=linea[0:-1]
        adic=' LRC('+str(ord(lrc))+')'
      else:
        adic=''
      linea=linea.replace('STX',chr(0x02),1)
      linea=linea.replace('ENQ',chr(0x05),1)
      linea=linea.replace('ETX',chr(0x03),1)
      linea=linea.replace('EOT',chr(0x04),1)
      linea=linea.replace('ACK',chr(0x06),1)
      linea=linea.replace('NAK',chr(0x15),1)
      linea=linea.replace('ETB',chr(0x17),1)

    return linea+adic

  def _States(self, cmd):
    #print cmd
    self._QueryCmd(cmd)
    while True:
      trama=self._FetchRow()
      #print "La trama es", trama, "hasta aca"
      if trama==None:
        break
      return trama
  
  def _UploadDataReport(self, cmd):
    try:
      self.ser.flushInput()
      self.ser.flushOutput()
      if self._HandleCTSRTS():
        msj=1
        msj=self._AssembleQueryToSend(cmd)
        self._write(msj)
        rt=self._read(1)
        while rt==chr(0x05):
          rt=self._read(1)
          while rt!=None:
            time.sleep(0.05)
            msj=self._Debug('ACK')
            self._write(msj)
            time.sleep(0.05)
            msj=self._FetchRow()
            return msj
          else:
            self._GetStatusError(0, 128);
            self.envio = "Error... CTS in False"
            rt=None
            self.ser.setRTS(False)
    except serial.SerialException:
      rt=None
      return rt

  def _UpdateFiscalMemoryReading(self, cmd):
    try:
      msj=""
      arreglodemsj=[]
      counter=0
      self.ser.flushInput()
      self.ser.flushOutput()
      if self._HandleCTSRTS():
         m=""
         msj=self._AssembleQueryToSend(cmd)
         self._write(msj)
         rt=self._read(1)
         while True:
            while msj!= chr(0x05):
               time.sleep(0.5)
               msj=self._Debug('ACK')
               self._write(msj)
               time.sleep(0.5)
               msj=self._FetchRow()
               if(msj==None):
                 counter+=1
               else:
                 arreglodemsj.append(msj)
               if counter>2:
                 counter=0
                 break
            return arreglodemsj            
      else:
         self._GetStatusError(0, 128);
         self.envio = "Error... CTS in False"
         m=None
         self.ser.setRTS(False)
    except serial.SerialException:
       m=None
    return m

  def _ReadFiscalMemoryByDate(self, cmd):
    msj=""
    arreglodemsj=[]
    counter=0
    try:
      self.ser.flushInput()
      self.ser.flushOutput()
      if self._HandleCTSRTS():
         msj=self._AssembleQueryToSend(cmd)
         self._write(msj)
         time.sleep(5)
         msj=self._read(1)
         while msj!= chr(0x05):
           time.sleep(5)
           msj=self._Debug('ACK')
           self._write(msj)
           time.sleep(5)
           msj=self._FetchRow()
           if(msj==None):
             counter+=1
           else:
             arreglodemsj.append(msj)
           if counter>2:
             counter=0
             break
         return arreglodemsj
      else:
         self._GetStatusError(0, 128);
         self.envio = "Error... CTS in False"
         msj= arreglodemsj #None
         self.ser.setRTS(False)
    except serial.SerialException:
       msj= arreglodemsj
    return arreglodemsj
  
  def _GetStatusError(self,st,er):
    st_aux = st;
    st = st & ~0x04

    if   (st & 0x6A) == 0x6A: #En modo fiscal, carga completa de la memoria fiscal y emisión de documentos no fiscales
      self.status='En modo fiscal, carga completa de la memoria fiscal y emisión de documentos no fiscales'
      status = "12"
    elif (st & 0x69) == 0x69: #En modo fiscal, carga completa de la memoria fiscal y emisión de documentos  fiscales
      self.status='En modo fiscal, carga completa de la memoria fiscal y emisión de documentos  fiscales'
      status = "11"
    elif (st & 0x68) == 0x68: #En modo fiscal, carga completa de la memoria fiscal y en espera
      self.status='En modo fiscal, carga completa de la memoria fiscal y en espera'
      status = "10"
    elif (st & 0x72) == 0x72: #En modo fiscal, cercana carga completa de la memoria fiscal y en emisión de documentos no fiscales
      self.status='En modo fiscal, cercana carga completa de la memoria fiscal y en emisión de documentos no fiscales'
      status = "9 "
    elif (st & 0x71) == 0x71: #En modo fiscal, cercana carga completa de la memoria fiscal y en emisión de documentos no fiscales
      self.status='En modo fiscal, cercana carga completa de la memoria fiscal y en emisión de documentos no fiscales'
      status = "8 "
    elif (st & 0x70) == 0x70: #En modo fiscal, cercana carga completa de la memoria fiscal y en espera
      self.status='En modo fiscal, cercana carga completa de la memoria fiscal y en espera'
      status = "7 "
    elif (st & 0x62) == 0x62: #En modo fiscal y en emisión de documentos no fiscales
      self.status='En modo fiscal y en emisión de documentos no fiscales'
      status = "6 "
    elif (st & 0x61) == 0x61: #En modo fiscal y en emisión de documentos fiscales
      self.status='En modo fiscal y en emisión de documentos fiscales'
      status = "5 "
    elif (st & 0x60) == 0x60: #En modo fiscal y en espera
      self.status='En modo fiscal y en espera'
      status = "4 "
    elif (st & 0x42) == 0x42: #En modo prueba y en emisión de documentos no fiscales
      self.status='En modo prueba y en emisión de documentos no fiscales'
      status = "3 "
    elif (st & 0x41) == 0x41: #En modo prueba y en emisión de documentos fiscales
      self.status='En modo prueba y en emisión de documentos fiscales'
      status = "2 "
    elif (st & 0x40) == 0x40: #En modo prueba y en espera
      self.status='En modo prueba y en espera'
      status = "1 "
    elif (st & 0x00) == 0x00: #Status Desconocido
      self.status='Status Desconocido'
      status = "0 "

    if   (er & 0x6C) == 0x6C: #Memoria Fiscal llena
      self.error = 'Memoria Fiscal llena'
      error = "108"
    elif (er & 0x64) == 0x64: #Error en memoria fiscal
      self.error = 'Error en memoria fiscal'
      error = "100"
    elif (er & 0x60) == 0x60: #Error Fiscal
      self.error = 'Error Fiscal'
      error = "96 "
    elif (er & 0x5C) == 0x5C: #Comando Invalido
      self.error = 'Comando Invalido'
      error = "92 "
    elif (er & 0x58) == 0x58: # No hay asignadas  directivas
      self.error = 'No hay asignadas  directivas'
      error = "88 "
    elif (er & 0x54) == 0x54: #Tasa Invalida
      self.error = 'Tasa Invalida'
      error = "84 "
    elif (er & 0x50) == 0x50: #Comando Invalido/Valor Invalido
      self.error = 'Comando Invalido/Valor Invalido'
      error = "80 "
    elif (er & 0x43) == 0x43: #Fin en la entrega de papel y error mecánico
      self.error = 'Fin en la entrega de papel y error mecánico'
      error = "3  "
    elif (er & 0x42) == 0x42: #Error de indole mecanico en la entrega de papel
      self.error = 'Error de indole mecanico en la entrega de papel'
      error = "2  "
    elif (er & 0x41) == 0x41: #Fin en la entrega de papel
      self.error = 'Fin en la entrega de papel'
      error = "1  "
    elif (er & 0x40) == 0x40: #Sin error
      self.error = 'Sin error'
      error = "0  "

    if (st_aux & 0x04) == 0x04: #Buffer Completo
      self.error = ''
      error = "112 "
    elif er == 128:     # Error en la comunicacion
      self.error = 'CTS en falso'
      error = "128 ";
    elif er == 137:     # No hay respuesta
      self.error = 'No hay respuesta'
      error = "137 ";
    elif er == 144:     # Error LRC
      self.error = 'Error LRC'
      error = "144 ";
    elif er == 114:
      self.error = 'Impresora no responde o ocupada'
      error = "114 ";
    return status+"   " +error+"   " +self.error  


from PyQt4.QtCore import *
import PyQt4.QtCore as QC
from PyQt4.QtGui import *
from PyQt4 import uic
import queryexecutor as connect
from operator import xor
from datetime import datetime
from datetime import (timedelta, datetime as pyDateTime, date as pyDate, time as pyTime)

import sys
import Tfhka
import serial
import os



class Principal(QMainWindow):


	def __init__(self):
		QMainWindow.__init__(self)
		uic.loadUi("DemoPython.ui", self)
		self.printer = Tfhka.Tfhka()
		self.btnabrir.clicked.connect(self.abrir_puerto)
		self.btncerrar.clicked.connect(self.cerrar_puerto)
		#self.btnprogramacion.clicked.connect(self.programacion)
		#self.btnenviar.clicked.connect(self.enviar_cmd)
		#self.btnarchivo.clicked.connect(self.CERRARfactura)
		self.btnestadoerror.clicked.connect(self.estado_error)
		self.btnimprimirZ.clicked.connect(self.imprimir_ReporteZ)
		self.btnimprimirX.clicked.connect(self.imprimir_ReporteX)
		self.btnestado.clicked.connect(self.obtener_estado)
		self.btnleerZ.clicked.connect(self.obtener_reporteZ)
		self.btnleerX.clicked.connect(self.obtener_reporteX)
		self.btnZnumero_imp.clicked.connect(self.ImpZpornumero)
		self.btnZfecha_imp.clicked.connect(self.ImpZporfecha)
		#self.btnFactura.clicked.connect(self.factura)
		#self.btnFacturaPer.clicked.connect(self.facturaper)
		#self.btnFacturaAnu.clicked.connect(self.facturaanu)
		#self.btnDocNoFiscal.clicked.connect(self.documentoNF)
		#self.btnNotaCredito.clicked.connect(self.notaCredito)
		#self.btnNotaDebito.clicked.connect(self.notaDebito)
		#self.btnreipmFact_numero.clicked.connect(self.ReimprimirFacturas)
		self.btnZnumero_obt.clicked.connect(self.ObtZpornumero)
		self.btnZfecha_obt.clicked.connect(self.ObtZporfecha)
		self.btnListado.clicked.connect(self.leer_pedidos)
		self.btnImprimir.clicked.connect(self.validar_Error)

	def abrir_puerto(self):
		self.txt_informacion.setText("")
		puerto = self.cmbports.currentText()
		try:
			resp = self.printer.OpenFpctrl(str(puerto))
			if resp:
				self.txt_informacion.setText("Impresora Conectada Correctamente en: " + puerto)
			else:
				self.txt_informacion.setText("Impresora no Conectada o Error Accediendo al Puerto")
		except serial.SerialException:
			self.txt_informacion.setText("Impresora no Conectada o Error Accediendo al Puerto")

	def cerrar_puerto(self):
		self.txt_informacion.setText("")
		resp = self.printer.CloseFpctrl()
		if not resp:
			self.txt_informacion.setText("Impresora Desconectada")
		else:
			self.txt_informacion.setText("Error")

	def programacion(self):
		self.txt_informacion.setText(str(self.printer.SendCmd("D")))

	def enviar_cmd(self):
		cmd = self.txt_cmd.text()
		self.txt_informacion.setText(str( self.printer.SendCmd(str(cmd))))

	def enviar_archivo(self):
		nombre_fichero = QFileDialog.getOpenFileName(self, "Abrir fichero", "/Desktop")
		if nombre_fichero:
			fichero_actual = nombre_fichero
			filename = str(QFileInfo(nombre_fichero).fileName())
			dirname = str(QFileInfo(nombre_fichero).path())
			path = open(os.path.join(dirname, filename), 'r')
			self.printer.SendCmdFile(path)
			self.txt_informacion.setText("archivo enviado")

	def estado_error(self):
		self.txt_informacion.setText("")
		self.estado = self.printer.ReadFpStatus()
		salida = "Estado: " + self.estado[0]
		salida += "\n"+ estado.get(self.estado[0], "Desconocido")
		salida += "\nError: " + self.estado[5]
		salida += "\n" + error.get(self.estado[5], "Desconocido")
		self.txt_informacion.setText(salida)

	def leer_pedidos(self):
		queryprov = "SELECT o.documento  ,trim(o.codcliente) , trim(o.contacto),trim( cast(o.totalfinal as DECIMAL(20,0))) " +\
					"FROM psk_pf.orden o  join psk_pf.orden_linea ol on " +\
					"o.tipodoc = ol.tipodoc	and o.documento = ol.documento left join psk_pf.factura f on f.tipodoc = 'FAC' " + \
					"AND  o.documento = f.orden AND o.codcliente = f.codcliente  " +\
					" WHERE   o.tipodoc ='PED' and f.documento is null " +\
					"	group by	o.documento ,	trim(o.codcliente) ,	trim(o.contacto),	o.totalfinal " +\
					"order by o.documento "
		codprov = connect.run_query(query=queryprov)
		self.tablaRegistro.setRowCount(len(codprov)/4)
		col = 0
		for x in range(0, len(codprov), 4):
			documento = QTableWidgetItem(codprov[x])
			documento.setFlags(xor(documento.flags(),  QC.Qt.ItemIsEditable))
			self.tablaRegistro.setItem(col, 0, documento)

			cliente = QTableWidgetItem(codprov[x+1])
			cliente.setFlags(xor(cliente.flags(), QC.Qt.ItemIsEditable))
			self.tablaRegistro.setItem(col, 1, cliente)

			nombre = QTableWidgetItem(codprov[x + 2])
			nombre.setFlags(xor(nombre.flags(), QC.Qt.ItemIsEditable))
			self.tablaRegistro.setItem(col, 2, nombre)

			monto = QTableWidgetItem(codprov[x+3])
			monto.setFlags(xor(monto.flags(), QC.Qt.ItemIsEditable))
			self.tablaRegistro.setItem(col, 3, monto)
			col += 1


	def validar_Error(self):
		try:
			self.estado = self.printer.ReadFpStatus()
			errorvAR = self.estado[5]
			estatusvAR = self.estado[0]
			if errorvAR!="0":
				salida = "Error: " + errorvAR
				salida += "\n" + error.get(errorvAR, "Desconocido")
				QMessageBox.about(self, "ERROR",  salida)
			elif not(estatusvAR == "1" or estatusvAR == "4" or estatusvAR == "7"):
				salida = "Estatus: " + estatusvAR
				salida += "\n" + estado.get(estatusvAR, "Desconocido")
				QMessageBox.about(self, "ERROR", salida)
		except:
			QMessageBox.about(self, "ERROR", "Impresora No Responde")
		else:
			self.imprimir()


	def imprimir(self):
		self.txt_informacion.setText("")
		indexes = self.tablaRegistro.selectionModel().selectedRows()
		print("seleccionado " + str(len(indexes)))
		if len(indexes) > 0:
			index = sorted(indexes)[0]
			lista=list()
			lista.append('Documento: %s ' % self.tablaRegistro.item(index.row(), 0).text())
			documento = unicode(self.tablaRegistro.item(index.row(), 0).text())
			lista.append('Cliente: %s ' % self.tablaRegistro.item(index.row(), 1).text())
			cliente = unicode(self.tablaRegistro.item(index.row(), 1).text())
			lista.append('Row %d is selected' % index.row())

			datos_cabecera = self.leer_cabecera(documento, cliente, lista)
			self.imprimir_cabecera(datos_cabecera, documento, cliente, lista)
			datos_lineas = self.leer_lineas(documento, cliente, lista)
			self.imprimir_lineas(datos_lineas, documento, cliente, lista)
			while True:
				estado_s1 = self.printer.GetS1PrinterData()
				print("numero de documento: "+str(estado_s1._lastInvoiceNumber))
				if estado_s1._lastInvoiceNumber!=0:
					break
			newdocumento = str(estado_s1._lastInvoiceNumber).rjust(8, '0')
			query_update = "update psk_pf.factura_linea set   " + \
					   " tipodoc = 'FAC' , documento = '" + newdocumento + \
					   "' where tipodoc = 'TRX' and documento = '" + documento + "' AND trim(proveedor) = '" + cliente + "' "
			connect.run_query(query=query_update)
			formatofechatabla = "%Y-%m-%d"
			formatofechaimpresora = "%d-%m-%Y"
			fecha = datetime.strptime(estado_s1._currentPrinterDate,formatofechaimpresora)
			fecha = fecha.strftime(formatofechatabla)
			hora = str(estado_s1._currentPrinterTime)
			if hora[0:2]>"12":
				hora = str(int(hora[0:2])-12)+hora[2:5]
				ampm=2
			else:
				hora = hora[0:5]
				ampm = 1

			query_update = "update psk_pf.factura set   " + \
				" tipodoc = 'FAC' , documento = '" + newdocumento + \
				"' , serialprintf = '" + str(estado_s1._registeredMachineNumber) + \
				"' , fechacrea = '" + str(fecha) + \
				"' , emision = '" + str(fecha) + \
				"' , recepcion = '" + str(fecha) + \
				"' , ultimopag = '" + str(fecha) + \
				"' , horadocum = '" + str(hora) + \
				"' , ampm = " + str(ampm) + \
				" where tipodoc = 'TRX' and documento = '" + documento + "' AND trim(codcliente) = '" + cliente + "' "
			connect.run_query(query=query_update)
			selected = self.tablaRegistro.currentRow()
			self.tablaRegistro.removeRow(selected)

			QMessageBox.about(self, "OK", "Finalizado")
		else:
			print("nada seleccionado")
			QMessageBox.about(self, "Ups", "no hay pedidos seleccionados")


	def leer_cabecera(self, documento, cliente, salida):
		query_cabecera = "SELECT TRIM(rif), TRIM(nombrecli), " + \
						 " coalesce( TRIM(direccion),'Sin Especificar'), "+ \
						 " coalesce( TRIM(telefonos),'Sin Especificar') , "+ \
						 "  coalesce( TRIM(nombre), 'Oficina Principal') " + \
					"FROM psk_pf.orden  g  Left join almacene a on a.codigo =g.almacen WHERE   " + \
					"tipodoc ='PED' and trim(documento) = '" + unicode(documento) + "' and trim(codcliente) = '" + unicode(cliente) + "' "
		datoscliente = connect.run_query(query=query_cabecera)
		print(datoscliente)
		return datoscliente


	def imprimir_cabecera(self, datoscliente,documento, cliente, salida):
		for x in range(0, len(datoscliente), 5):
			self.printer.SendCmd(str("iR*" + datoscliente[x].encode('latin1')))
			salida.append("Rif: " + datoscliente[x].encode('latin1'))
			self.printer.SendCmd(str("iS*" + datoscliente[x+1].encode('latin1')))
			salida.append("Razon Social: " + datoscliente[x+1].encode('latin1'))
			dir ="Direccion: " + datoscliente[x+2].encode('utf-8')
			salida.append(dir)
			linea = 0
			maxlen = 40
			while True:
				aux = "i0"+str(linea)+dir[0:maxlen]
				self.printer.SendCmd(str(aux))
				linea += 1
				if len(dir) > maxlen:
					dir = dir[maxlen:]
				else:
					break
			self.printer.SendCmd(str("i0"+str(linea)+"Telefono: " + datoscliente[x+3].encode('latin1')))
			salida.append("Telefono: " + datoscliente[x+3].encode('latin1'))
			linea += 1
			self.printer.SendCmd(str("i0"+str(linea)+"CAJERO:" +datoscliente[x+4].encode('latin1')))
			salida.append("CAJERO:" +datoscliente[x+4].encode('latin1'))


	def leer_lineas(self, documento, cliente, salida):
		query_lineas = "SELECT a.impuesto1,g.preciounit ,cantidad, trim(g.nombre) ,TRIM(G.CODIGO) " + \
					"FROM psk_pf.orden_linea  g join articulo a on a.codigo =g.codigo  WHERE   " + \
					"tipodoc ='PED' and trim(documento) = '" + (documento) + "' and trim(proveedor) = '" + (cliente) + "' "
		articulos_pedidos = connect.run_query(query=query_lineas)
		print(articulos_pedidos)
		return articulos_pedidos

	def imprimir_lineas(self, datos_articulos,documento, cliente, salida):

		porcentage_impuesto = {0: ' ', 16: '!', 8: '"', 31: '#'}
		base_acu = 0
		impuesto_acu = 0
		base_imponible = 0
		exento = 0
		for x in range(0, len(datos_articulos), 5):
			codigo_impuesto = porcentage_impuesto.get(int(datos_articulos[x]), ' ')

			precio = datos_articulos[x+1]
			precio = round(precio, 2)
			precio_entero = str(int(precio))
			precio_decimal = str(int((precio % 1)*100))
			precio_entero = precio_entero.rjust(14, '0')
			precio_decimal = precio_decimal.rjust(2, '0')

			cantidad = datos_articulos[x+2]
			cantidad=round(cantidad, 3)
			cantidad_entero = str(int(cantidad))
			cantidad_decimal = str(int((cantidad % 1)*1000))
			cantidad_entero = cantidad_entero.rjust(14, '0')
			cantidad_decimal = cantidad_decimal.rjust(3, '0')

			nombre = datos_articulos[x+3].encode('latin1')

			aux = codigo_impuesto + precio_entero + precio_decimal + cantidad_entero + cantidad_decimal + nombre
			salida.append(aux)

			if (self.printer.SendCmd(str(aux))):
				while True:
					estado_s2 = self.printer.GetS2PrinterData()
					base_linea = estado_s2._subTotalBases -base_acu
					impuesto_linea = estado_s2._subTotalTax -impuesto_acu
					if base_linea > 0:
						break
					else:
						print("base cero")
				base_imponible_articulo = 0
				if codigo_impuesto == " ":
					exento += base_linea
				else:
					base_imponible += base_linea
					base_imponible_articulo = base_linea
				base_articulo = base_linea/cantidad
				impuesto = impuesto_linea/cantidad


				base_acu = estado_s2._subTotalBases
				impuesto_acu = estado_s2._subTotalTax
				query_update = "update psk_pf.factura_linea set   preciooriginal = preciounit ," + \
							   "preciounit = "+ str(base_articulo) + " , preciofin = "+str(base_articulo) +" , " + \
							   " montoneto = " + str(base_linea) + " , " + \
							   "impuesto1 = " + str(impuesto) + " , baseimpo1 = " + str(base_imponible_articulo) + " , " + \
							   "montototal = " + str( base_linea + impuesto) + " , tipodoc ='TRX' " + \
							   " where tipodoc = 'PED' and documento = '" + documento + "' AND trim(proveedor) = '" + cliente +\
								"' and codigo = '" +datos_articulos[x+4].encode('latin1')+"'"
				connect.run_query(query=query_update)
		query_update = "update psk_pf.factura set   " + \
					   "totbruto = " + str(base_acu) + " , totneto = " + str(base_acu) + " ," + \
					   "totimpuest = " + str(impuesto_acu) + " , impuesto1 = " + str(impuesto_acu) + " , impuesto2 = " + str(impuesto_acu) + " ," + \
					   "totalfinal = " + str(base_acu+impuesto_acu) + ", totpagos = " + str(base_acu + impuesto_acu) + " " + \
					   ", sinimpuest = " + str(exento) + " " + \
					   ", baseimpo1 = " + str(base_imponible) + " , tipodoc ='TRX' " + \
					   " where tipodoc = 'PED' and documento = '" + documento + "' AND trim(codcliente) = '" + cliente + "' "

		connect.run_query(query=query_update)
		self.printer.SendCmd(str("3"))
		self.printer.SendCmd(str("101"))

	def imprimir_ReporteZ(self):
		self.transferir_reporteZ()
		self.printer.PrintZReport()

	def imprimir_ReporteX(self):
		self.printer.PrintXReport()

	def obtener_estado(self):
		estado = str(self.cmbestado.currentText())

		if estado == "S1":
			estado_s1 = self.printer.GetS1PrinterData()
			salida= "---Estado S1---\n" 
			salida+= "\nNumero Cajero: "+ str(estado_s1._cashierNumber) 
			salida+= "\nSubtotal Ventas: " + str(estado_s1._totalDailySales) 
			salida+= "\nNumero Ultima Factura: " + str(estado_s1._lastInvoiceNumber)
			salida+= "\nCantidad Facturas Hoy: " + str(estado_s1._quantityOfInvoicesToday)  
			salida+= "\nNumero Ultima Nota de Debito: " + str(estado_s1._lastDebtNoteNumber) 
			salida+= "\nCantidad Notas de Debito Hoy: " + str(estado_s1._quantityDebtNoteToday) 
			salida+= "\nNumero Ultima Nota de Credito: " + str(estado_s1._lastNCNumber) 
			salida+= "\nCantidad Notas de Credito Hoy: " + str(estado_s1._quantityOfNCToday) 
			salida+= "\nNumero Ultimo Documento No Fiscal: " + str(estado_s1._numberNonFiscalDocuments) 
			salida+= "\nCantidad de Documentos No Fiscales: " + str(estado_s1._quantityNonFiscalDocuments) 
			salida+= "\nCantidad de Reportes de Auditoria: " + str(estado_s1._auditReportsCounter) 
			salida+= "\nCantidad de Reportes Fiscales: " + str(estado_s1._fiscalReportsCounter)
			salida+= "\nCantidad de Reportes Z: " + str(estado_s1._dailyClosureCounter)
			salida+= "\nNumero de RIF: " + str(estado_s1._rif)
			salida+= "\nNumero de Registro: " + str(estado_s1._registeredMachineNumber)
			salida+= "\nHora de la Impresora: " + str(estado_s1._currentPrinterTime)
			salida+= "\nFecha de la Impresora: " + str(estado_s1._currentPrinterDate)
			self.txt_informacion.setText(salida)

		if estado == "S2":
			estado_s2 = self.printer.GetS2PrinterData()
			salida= "---Estado S2---\n" 
			salida+= "\nSubtotal de BI: "+ str(estado_s2._subTotalBases)  
			salida+= "\nSubtotal de Impuesto: " + str(estado_s2._subTotalTax) 
			salida+= "\nData Dummy: " + str(estado_s2._dataDummy)
			salida+= "\nCantidad de articulos: " + str(estado_s2._quantityArticles)  
			salida+= "\nMonto por Pagar: " + str(estado_s2._amountPayable) 
			salida+= "\nNumero de Pagos Realizados: " + str(estado_s2._numberPaymentsMade) 
			salida+= "\nTipo de Documento: " + str(estado_s2._typeDocument) 
			self.txt_informacion.setText(salida)

		if estado == "S3":
			estado_s3 = self.printer.GetS3PrinterData()
			salida= "---Estado S3---\n"
			salida+= "\nTipo Tasa 1 (1 = Incluido, 2= Excluido): "+ str(estado_s3._typeTax1) 
			salida+= "\nValor Tasa 1: "+ str(estado_s3._tax1) + " %"
			salida+= "\nTipo Tasa 2 (1 = Incluido, 2= Excluido): " + str(estado_s3._typeTax2) 
			salida+= "\nValor Tasa2: " + str(estado_s3._tax2) + " %"
			salida+= "\nTipo Tasa 3 (1 = Incluido, 2= Excluido): " + str(estado_s3._typeTax3)  
			salida+= "\nValor Tasa 3: " + str(estado_s3._tax3) + " %"
			salida+= "\n\nLista de Flags: " + str(estado_s3._systemFlags)
			self.txt_informacion.setText(salida)

		if estado == "S4":
			estado_s4 = self.printer.GetS4PrinterData()
			salida= "---Estado S4---\n"
			salida+= "\nMontos en Medios de Pago: " + str(estado_s4._allMeansOfPayment)
			self.txt_informacion.setText(salida)

		if estado == "S5":
			estado_s5 = self.printer.GetS5PrinterData()
			salida= "---Estado S5---\n"
			salida+= "\nNumero de RIF: "+ str(estado_s5._rif) 
			salida+= "\nNumero de Registro: " + str(estado_s5._registeredMachineNumber) 
			salida+= "\nNumero de Memoria de Auditoria : " + str(estado_s5._auditMemoryNumber)
			salida+= "\nCapacidad Total de Memoria Auditoria: " + str(estado_s5._auditMemoryTotalCapacity) + " MB" 
			salida+= "\nEspacio Disponible: " + str(estado_s5._auditMemoryFreeCapacity) + " MB" 
			salida+= "\nCantidad Documentos Registrados: " + str(estado_s5._numberRegisteredDocuments)
			self.txt_informacion.setText(salida)

		if estado == "S6":
			estado_s6 = self.printer.GetS6PrinterData()
			salida= "---Estado S6---\n"
			salida+= "\nModo Facturacion: "+ str(estado_s6._bit_Facturacion) 
			salida+= "\nModo Slip: " + str(estado_s6._bit_Slip) 
			salida+= "\nModo Validacion: " + str(estado_s6._bit_Validacion) 
			self.txt_informacion.setText(salida)

	def obtener_reporteZ(self):
		reporte = self.printer.GetZReport()
		salida= "Numero Ultimo Reporte Z: "+ str(reporte._numberOfLastZReport) 
		salida+= "\nFecha Ultimo Reporte Z: "+ str(reporte._zReportDate) 
		salida+= "\nHora Ultimo Reporte Z: "+ str(reporte._zReportTime) 
		salida+= "\nNumero Ultima Factura: "+ str(reporte._numberOfLastInvoice) 
		salida+= "\nFecha Ultima Factura: "+ str(reporte._lastInvoiceDate) 
		salida+= "\nHora Ultima Factura: "+ str(reporte._lastInvoiceTime)
		salida+= "\nNumero Ultima Nota de Debito: "+ str(reporte._numberOfLastDebitNote)
		salida+= "\nNumero Ultima Nota de Credito: "+ str(reporte._numberOfLastCreditNote)
		salida+= "\nNumero Ultimo Doc No Fiscal: "+ str(reporte._numberOfLastNonFiscal)
		salida+= "\nVentas Exento: "+ str(reporte._freeSalesTax)
		salida+= "\nBase Imponible Ventas IVA G: "+ str(reporte._generalRate1Sale)
		salida+= "\nImpuesto IVA G: "+ str(reporte._generalRate1Tax)
		salida+= "\nBase Imponible Ventas IVA R: "+ str(reporte._reducedRate2Sale)
		salida+= "\nImpuesto IVA R: "+ str(reporte._reducedRate2Tax)
		salida+= "\nBase Imponible Ventas IVA A: "+ str(reporte._additionalRate3Sal)
		salida+= "\nImpuesto IVA A: "+ str(reporte._additionalRate3Tax)
		salida+= "\nNota de Debito Exento: "+ str(reporte._freeTaxDebit)
		salida+= "\nBI IVA G en Nota de Debito: "+ str(reporte._generalRateDebit)
		salida+= "\nImpuesto IVA G en Nota de Debito: "+ str(reporte._generalRateTaxDebit)
		salida+= "\nBI IVA R en Nota de Debito: "+ str(reporte._reducedRateDebit)
		salida+= "\nImpuesto IVA R en Nota de Debito: "+ str(reporte._reducedRateTaxDebit)
		salida+= "\nBI IVA A en Nota de Debito: "+ str(reporte._additionalRateDebit)
		salida+= "\nImpuesto IVA A en Nota de Debito: "+ str(reporte._additionalRateTaxDebit)
		salida+= "\nNota de Credito Exento: "+ str(reporte._freeTaxDevolution)
		salida+= "\nBI IVA G en Nota de Credito: "+ str(reporte._generalRateDevolution)
		salida+= "\nImpuesto IVA G en Nota de Credito: "+ str(reporte._generalRateTaxDevolution)
		salida+= "\nBI IVA R en Nota de Credito: "+ str(reporte._reducedRateDevolution)
		salida+= "\nImpuesto IVA R en Nota de Credito: "+ str(reporte._reducedRateTaxDevolution)
		salida+= "\nBI IVA A en Nota de Credito: "+ str(reporte._additionalRateDevolution)
		salida+= "\nImpuesto IVA A en Nota de Credito: "+ str(reporte._additionalRateTaxDevolution)
		self.txt_informacion.setText(salida)

	def transferir_reporteZ(self):
		reporte = self.printer.GetXReport()
		salida= "Numero Proximo Reporte Z: "+ str(reporte._numberOfLastZReport) 
		salida+= "\nFecha Ultimo Reporte Z: "+ str(reporte._zReportDate) 
		salida+= "\nHora Ultimo Reporte Z: "+ str(reporte._zReportTime) 
		salida+= "\nNumero Ultima Factura: "+ str(reporte._numberOfLastInvoice) 
		salida+= "\nFecha Ultima Factura: "+ str(reporte._lastInvoiceDate) 
		salida+= "\nHora Ultima Factura: "+ str(reporte._lastInvoiceTime)
		salida+= "\nNumero Ultima Nota de Debito: "+ str(reporte._numberOfLastDebitNote)
		salida+= "\nNumero Ultima Nota de Credito: "+ str(reporte._numberOfLastCreditNote)
		salida+= "\nNumero Ultimo Doc No Fiscal: "+ str(reporte._numberOfLastNonFiscal)
		salida+= "\nVentas Exento: "+ str(reporte._freeSalesTax)
		salida+= "\nBase Imponible Ventas IVA G: "+ str(reporte._generalRate1Sale)
		salida+= "\nImpuesto IVA G: "+ str(reporte._generalRate1Tax)
		salida+= "\nBase Imponible Ventas IVA R: "+ str(reporte._reducedRate2Sale)
		salida+= "\nImpuesto IVA R: "+ str(reporte._reducedRate2Tax)
		salida+= "\nBase Imponible Ventas IVA A: "+ str(reporte._additionalRate3Sal)
		salida+= "\nImpuesto IVA A: "+ str(reporte._additionalRate3Tax)
		salida+= "\nNota de Debito Exento: "+ str(reporte._freeTaxDebit)
		salida+= "\nBI IVA G en Nota de Debito: "+ str(reporte._generalRateDebit)
		salida+= "\nImpuesto IVA G en Nota de Debito: "+ str(reporte._generalRateTaxDebit)
		salida+= "\nBI IVA R en Nota de Debito: "+ str(reporte._reducedRateDebit)
		salida+= "\nImpuesto IVA R en Nota de Debito: "+ str(reporte._reducedRateTaxDebit)
		salida+= "\nBI IVA A en Nota de Debito: "+ str(reporte._additionalRateDebit)
		salida+= "\nImpuesto IVA A en Nota de Debito: "+ str(reporte._additionalRateTaxDebit)
		salida+= "\nNota de Credito Exento: "+ str(reporte._freeTaxDevolution)
		salida+= "\nBI IVA G en Nota de Credito: "+ str(reporte._generalRateDevolution)
		salida+= "\nImpuesto IVA G en Nota de Credito: "+ str(reporte._generalRateTaxDevolution)
		salida+= "\nBI IVA R en Nota de Credito: "+ str(reporte._reducedRateDevolution)
		salida+= "\nImpuesto IVA R en Nota de Credito: "+ str(reporte._reducedRateTaxDevolution)
		salida+= "\nBI IVA A en Nota de Credito: "+ str(reporte._additionalRateDevolution)
		salida+= "\nImpuesto IVA A en Nota de Credito: "+ str(reporte._additionalRateTaxDevolution)
		estado_s1 = self.printer.GetS1PrinterData()
		salida += "\nNumero Cajero: " + str(estado_s1._cashierNumber)
		salida += "\nSubtotal Ventas: " + str(estado_s1._totalDailySales)
		salida += "\nNumero Ultima Factura: " + str(estado_s1._lastInvoiceNumber)
		salida += "\nCantidad Facturas Hoy: " + str(estado_s1._quantityOfInvoicesToday)
		salida += "\nNumero Ultima Nota de Debito: " + str(estado_s1._lastDebtNoteNumber)
		salida += "\nCantidad Notas de Debito Hoy: " + str(estado_s1._quantityDebtNoteToday)
		salida += "\nNumero Ultima Nota de Credito: " + str(estado_s1._lastNCNumber)
		salida += "\nCantidad Notas de Credito Hoy: " + str(estado_s1._quantityOfNCToday)
		salida += "\nNumero Ultimo Documento No Fiscal: " + str(estado_s1._numberNonFiscalDocuments)
		salida += "\nCantidad de Documentos No Fiscales: " + str(estado_s1._quantityNonFiscalDocuments)
		salida += "\nCantidad de Reportes de Auditoria: " + str(estado_s1._auditReportsCounter)
		salida += "\nCantidad de Reportes Fiscales: " + str(estado_s1._fiscalReportsCounter)
		salida += "\nCantidad de Reportes Z: " + str(estado_s1._dailyClosureCounter)
		salida += "\nNumero de RIF: " + str(estado_s1._rif)
		salida += "\nNumero de Registro: " + str(estado_s1._registeredMachineNumber)
		salida += "\nHora de la Impresora: " + str(estado_s1._currentPrinterTime)
		salida += "\nFecha de la Impresora: " + str(estado_s1._currentPrinterDate)
		estado_s5 = self.printer.GetS5PrinterData()
		salida+= "\nNumero de RIF: "+ str(estado_s5._rif)
		salida+= "\nNumero de Registro: " + str(estado_s5._registeredMachineNumber)
		salida+= "\nNumero de Memoria de Auditoria : " + str(estado_s5._auditMemoryNumber)
		salida+= "\nCapacidad Total de Memoria Auditoria: " + str(estado_s5._auditMemoryTotalCapacity) + " MB"
		salida+= "\nEspacio Disponible: " + str(estado_s5._auditMemoryFreeCapacity) + " MB"
		salida+= "\nCantidad Documentos Registrados: " + str(estado_s5._numberRegisteredDocuments)
		estado_s6 = self.printer.GetS6PrinterData()
		salida+= "\nModo Facturacion: "+ str(estado_s6._bit_Facturacion)
		salida+= "\nModo Slip: " + str(estado_s6._bit_Slip)
		salida+= "\nModo Validacion: " + str(estado_s6._bit_Validacion)
		f = open('Z:\ReporteZ\\reporteZ'+str(reporte._numberOfLastZReport)+'.txt', 'wb')
		f.write(salida)
		f.close()
		return salida

	def obtener_reporteX(self):
		reporte = self.printer.GetXReport()
		salida= "Numero Proximo Reporte Z: "+ str(reporte._numberOfLastZReport)
		salida+= "\nFecha Ultimo Reporte Z: "+ str(reporte._zReportDate)
		salida+= "\nHora Ultimo Reporte Z: "+ str(reporte._zReportTime)
		salida+= "\nNumero Ultima Factura: "+ str(reporte._numberOfLastInvoice)
		salida+= "\nFecha Ultima Factura: "+ str(reporte._lastInvoiceDate)
		salida+= "\nHora Ultima Factura: "+ str(reporte._lastInvoiceTime)
		salida+= "\nNumero Ultima Nota de Debito: "+ str(reporte._numberOfLastDebitNote)
		salida+= "\nNumero Ultima Nota de Credito: "+ str(reporte._numberOfLastCreditNote)
		salida+= "\nNumero Ultimo Doc No Fiscal: "+ str(reporte._numberOfLastNonFiscal)
		salida+= "\nVentas Exento: "+ str(reporte._freeSalesTax)
		salida+= "\nBase Imponible Ventas IVA G: "+ str(reporte._generalRate1Sale)
		salida+= "\nImpuesto IVA G: "+ str(reporte._generalRate1Tax)
		salida+= "\nBase Imponible Ventas IVA R: "+ str(reporte._reducedRate2Sale)
		salida+= "\nImpuesto IVA R: "+ str(reporte._reducedRate2Tax)
		salida+= "\nBase Imponible Ventas IVA A: "+ str(reporte._additionalRate3Sal)
		salida+= "\nImpuesto IVA A: "+ str(reporte._additionalRate3Tax)
		salida+= "\nNota de Debito Exento: "+ str(reporte._freeTaxDebit)
		salida+= "\nBI IVA G en Nota de Debito: "+ str(reporte._generalRateDebit)
		salida+= "\nImpuesto IVA G en Nota de Debito: "+ str(reporte._generalRateTaxDebit)
		salida+= "\nBI IVA R en Nota de Debito: "+ str(reporte._reducedRateDebit)
		salida+= "\nImpuesto IVA R en Nota de Debito: "+ str(reporte._reducedRateTaxDebit)
		salida+= "\nBI IVA A en Nota de Debito: "+ str(reporte._additionalRateDebit)
		salida+= "\nImpuesto IVA A en Nota de Debito: "+ str(reporte._additionalRateTaxDebit)
		salida+= "\nNota de Credito Exento: "+ str(reporte._freeTaxDevolution)
		salida+= "\nBI IVA G en Nota de Credito: "+ str(reporte._generalRateDevolution)
		salida+= "\nImpuesto IVA G en Nota de Credito: "+ str(reporte._generalRateTaxDevolution)
		salida+= "\nBI IVA R en Nota de Credito: "+ str(reporte._reducedRateDevolution)
		salida+= "\nImpuesto IVA R en Nota de Credito: "+ str(reporte._reducedRateTaxDevolution)
		salida+= "\nBI IVA A en Nota de Credito: "+ str(reporte._additionalRateDevolution)
		salida+= "\nImpuesto IVA A en Nota de Credito: "+ str(reporte._additionalRateTaxDevolution)
		self.txt_informacion.setText(salida)

	def ImpZpornumero(self):
		n_ini = self.imp_num_ini.value()
		n_fin = self.imp_num_fin.value()
		self.printer.PrintZReport("A",n_ini,n_fin)

	def ImpZporfecha(self):
		n_ini = self.imp_date_ini.date().toPyDate()
		n_fin = self.imp_date_fin.date().toPyDate()
		self.printer.PrintZReport("A",n_ini,n_fin)

	def factura(self):
		#Factura sin Personalizar*
		self.printer.SendCmd(str("@COMMENT/COMENTARIO"))
		self.printer.SendCmd(str("@cantidad 14enteros 3decimales"))
		self.printer.SendCmd(str("@precio 14enteros 2decimales"))
		self.printer.SendCmd(str(" 000000001111115000000000000001000Tax Rate 1/Producto Tasa General"))
		self.printer.SendCmd(str("!000000001111115000000000000001000Tax Rate 1/Producto Tasa General"))
		self.printer.SendCmd(str('"' + "000000001111115000000000000001000Tax Rate 2/ Producto Tasa Reducida"))
		self.printer.SendCmd(str("#000000001111115000000000000001000Tax Rate 3/ Producto Tasa Adicional"))
		self.printer.SendCmd(str("3"))
		self.printer.SendCmd(str("101"))


	def CERRARfactura(self):
		self.printer.SendCmd(str("3"))
		self.printer.SendCmd(str("101"))


	def facturaper(self):
		#Factura Personalizada
		self.printer.SendCmd(str("iR*21.122.012"))
		self.printer.SendCmd(str("iS*Pedro Perez"))
		self.printer.SendCmd(str("i00Direccion: Ppal Siempre Viva"))
		self.printer.SendCmd(str("i01Telefono: +58(212)555-55-55"))
		self.printer.SendCmd(str("i02CAJERO: 00001"))
		self.printer.SendCmd(str("@COMMENT/COMENTARIO"))
		self.printer.SendCmd(str(" 000000030000001000Tax Free/Producto Exento"))
		self.printer.SendCmd(str("!000000050000001000Tax Rate 1/Producto Tasa General"))
		self.printer.SendCmd(str('"' + "000000070000001000Tax Rate 2/ Producto Tasa Reducida"))
		self.printer.SendCmd(str("#000000090000001000Tax Rate 3/ Producto Tasa Adicional"))
		self.printer.SendCmd(str("3"))
		self.printer.SendCmd(str("101"))

	def facturaanu(self):
		#Factura Anulada
		self.printer.SendCmd(str("iR*21.122.012"))
		self.printer.SendCmd(str("iS*Pedro Perez"))
		self.printer.SendCmd(str("i00Direccion: Ppal Siempre Viva"))
		self.printer.SendCmd(str("i01Telefono: +58(212)555-55-55"))
		self.printer.SendCmd(str("i02CAJERO: 00001"))
		self.printer.SendCmd(str("@COMMENT/COMENTARIO"))
		self.printer.SendCmd(str(" 000000030000001000Tax Free/Producto Exento"))
		self.printer.SendCmd(str("!000000050000001000Tax Rate 1/Producto Tasa General"))
		self.printer.SendCmd(str('"' + "000000070000001000Tax Rate 2/ Producto Tasa Reducida"))
		self.printer.SendCmd(str("#000000090000001000Tax Rate 3/ Producto Tasa Adicional"))
		self.printer.SendCmd(str("7"))

	def documentoNF(self):
		#Documento No Fiscal
		self.printer.SendCmd(str("80$Documento de Prueba"))
		self.printer.SendCmd(str("80¡Esto es un documento de texto"))
		self.printer.SendCmd(str("80!Es un documento no fiscal"))
		self.printer.SendCmd(str("80*Es bastante util y versatil"))
		self.printer.SendCmd(str("810Fin del Documento no Fiscal"))

	def notaCredito(self):
		#Nota de Credito
		self.printer.SendCmd(str("iR*21.122.012"))
		self.printer.SendCmd(str("iS*Pedro Perez"))
		self.printer.SendCmd(str("iF*00000000001"))
		self.printer.SendCmd(str("iD*22/08/2016"))
		self.printer.SendCmd(str("iI*Z1F1234567"))
		self.printer.SendCmd(str("i00Direccion: Ppal Siempre Viva"))
		self.printer.SendCmd(str("i01Telefono: +58(212)555-55-55"))
		self.printer.SendCmd(str("i02CAJERO: 00001"))
		self.printer.SendCmd(str("ACOMENTARIO NOTA DE CREDITO"))
		self.printer.SendCmd(str("d0000000030000001000Tax Free/Producto Exento"))
		self.printer.SendCmd(str("d1000000050000001000Tax Rate 1/Producto Tasa General"))
		self.printer.SendCmd(str("d2000000070000001000Tax Rate 2/ Producto Tasa Reducida"))
		self.printer.SendCmd(str("d3000000090000001000Tax Rate 3/ Producto Tasa Adicional"))
		self.printer.SendCmd(str("3"))
		self.printer.SendCmd(str("101"))

	def notaDebito(self):
		self.printer.SendCmd(str("iR*21.122.012"))
		self.printer.SendCmd(str("iS*Pedro Perez"))
		self.printer.SendCmd(str("iF*00000000001"))
		self.printer.SendCmd(str("iD*22/08/2016"))
		self.printer.SendCmd(str("iI*Z1F1234567"))
		self.printer.SendCmd(str("i00Direccion: Ppal Siempre Viva"))
		self.printer.SendCmd(str("i01Telefono: +58(212)555-55-55"))
		self.printer.SendCmd(str("i02CAJERO: 00001"))
		self.printer.SendCmd(str("BCOMENTARIO NOTA DE DEBITO"))
		self.printer.SendCmd(str("`0" + "000000003000000100Tax Free/Producto Exento"))
		self.printer.SendCmd(str("`1" + "100000005000000100Tax Rate 1/Producto Tasa General"))
		self.printer.SendCmd(str("`2" + "200000007000000100Tax Rate 2/ Producto Tasa Reducida"))
		self.printer.SendCmd(str("`3" + "300000009000000100Tax Rate 3/ Producto Tasa Adicional"))
		self.printer.SendCmd(str("3"))
		self.printer.SendCmd(str("101"))

	def ReimprimirFacturas(self):
		n_ini = self.reimp_ini.value()
		n_fin = self.reimp_fin.value()

		starString = str(n_ini)
		while (len(starString) < 7):
			starString = "0" + starString
		endString = str(n_fin)
		while (len(endString) < 7):
			endString = "0" + endString
		self.printer.SendCmd("RF" + starString + endString)

	def ObtZpornumero(self):
		n_ini = self.obt_num_ini.value()
		n_fin = self.obt_num_fin.value()
		reportes = self.printer.GetZReport("A",n_ini,n_fin)
		CR = len(reportes)
		Enc = "Lista de Reportes\n"+"\n"
		salida = ""
		for NR in range(CR):
			salida+= "Numero de Reporte Z: "+ str(reportes[NR]._numberOfLastZReport) 
			salida+= "\nFecha Ultimo Reporte Z: "+ str(reportes[NR]._zReportDate) 
			salida+= "\nHora Ultimo Reporte Z: "+ str(reportes[NR]._zReportTime) 
			salida+= "\nNumero Ultima Factura: "+ str(reportes[NR]._numberOfLastInvoice) 
			salida+= "\nFecha Ultima Factura: "+ str(reportes[NR]._lastInvoiceDate) 
			salida+= "\nHora Ultima Factura: "+ str(reportes[NR]._lastInvoiceTime)
			salida+= "\nNumero Ultima Nota de Credito: "+ str(reportes[NR]._numberOfLastCreditNote)
			salida+= "\nNumero Ultima Nota de Debito: "+ str(reportes[NR]._numberOfLastDebitNote)			
			salida+= "\nNumero Ultimo Doc No Fiscal: "+ str(reportes[NR]._numberOfLastNonFiscal)
			salida+= "\nVentas Exento: "+ str(reportes[NR]._freeSalesTax)
			salida+= "\nBase Imponible Ventas IVA G: "+ str(reportes[NR]._generalRate1Sale)
			salida+= "\nImpuesto IVA G: "+ str(reportes[NR]._generalRate1Tax)
			salida+= "\nBase Imponible Ventas IVA R: "+ str(reportes[NR]._reducedRate2Sale)
			salida+= "\nImpuesto IVA R: "+ str(reportes[NR]._reducedRate2Tax)
			salida+= "\nBase Imponible Ventas IVA A: "+ str(reportes[NR]._additionalRate3Sal)
			salida+= "\nImpuesto IVA A: "+ str(reportes[NR]._additionalRate3Tax)
			salida+= "\nNota de Debito Exento: "+ str(reportes[NR]._freeTaxDebit)
			salida+= "\nBI IVA G en Nota de Debito: "+ str(reportes[NR]._generalRateDebit)
			salida+= "\nImpuesto IVA G en Nota de Debito: "+ str(reportes[NR]._generalRateTaxDebit)
			salida+= "\nBI IVA R en Nota de Debito: "+ str(reportes[NR]._reducedRateDebit)
			salida+= "\nImpuesto IVA R en Nota de Debito: "+ str(reportes[NR]._reducedRateTaxDebit)
			salida+= "\nBI IVA A en Nota de Debito: "+ str(reportes[NR]._additionalRateDebit)
			salida+= "\nImpuesto IVA A en Nota de Debito: "+ str(reportes[NR]._additionalRateTaxDebit)
			salida+= "\nNota de Credito Exento: "+ str(reportes[NR]._freeTaxDevolution)
			salida+= "\nBI IVA G en Nota de Credito: "+ str(reportes[NR]._generalRateDevolution)
			salida+= "\nImpuesto IVA G en Nota de Credito: "+ str(reportes[NR]._generalRateTaxDevolution)
			salida+= "\nBI IVA R en Nota de Credito: "+ str(reportes[NR]._reducedRateDevolution)
			salida+= "\nImpuesto IVA R en Nota de Credito: "+ str(reportes[NR]._reducedRateTaxDevolution)
			salida+= "\nBI IVA A en Nota de Credito: "+ str(reportes[NR]._additionalRateDevolution)
			salida+= "\nImpuesto IVA A en Nota de Credito: "+ str(reportes[NR]._additionalRateTaxDevolution)+"\n"+"\n"
			print(salida)			
		self.txt_informacion.setText(Enc+salida)

	def ObtZporfecha(self):
		n_ini = self.obt_date_ini.date().toPyDate()
		n_fin = self.obt_date_fin.date().toPyDate()
		reportes = self.printer.GetZReport("A",n_ini,n_fin)
		CR = len(reportes)
		Enc = "Lista de Reportes\n"+"\n"
		salida = ""
		for NR in range(CR):
			salida+= "Numero de Reporte Z: "+ str(reportes[NR]._numberOfLastZReport) 
			salida+= "\nFecha Ultimo Reporte Z: "+ str(reportes[NR]._zReportDate) 
			salida+= "\nHora Ultimo Reporte Z: "+ str(reportes[NR]._zReportTime) 
			salida+= "\nNumero Ultima Factura: "+ str(reportes[NR]._numberOfLastInvoice) 
			salida+= "\nFecha Ultima Factura: "+ str(reportes[NR]._lastInvoiceDate) 
			salida+= "\nHora Ultima Factura: "+ str(reportes[NR]._lastInvoiceTime)
			salida+= "\nNumero Ultima Nota de Credito: "+ str(reportes[NR]._numberOfLastCreditNote)
			salida+= "\nNumero Ultima Nota de Debito: "+ str(reportes[NR]._numberOfLastDebitNote)			
			salida+= "\nNumero Ultimo Doc No Fiscal: "+ str(reportes[NR]._numberOfLastNonFiscal)
			salida+= "\nVentas Exento: "+ str(reportes[NR]._freeSalesTax)
			salida+= "\nBase Imponible Ventas IVA G: "+ str(reportes[NR]._generalRate1Sale)
			salida+= "\nImpuesto IVA G: "+ str(reportes[NR]._generalRate1Tax)
			salida+= "\nBase Imponible Ventas IVA R: "+ str(reportes[NR]._reducedRate2Sale)
			salida+= "\nImpuesto IVA R: "+ str(reportes[NR]._reducedRate2Tax)
			salida+= "\nBase Imponible Ventas IVA A: "+ str(reportes[NR]._additionalRate3Sal)
			salida+= "\nImpuesto IVA A: "+ str(reportes[NR]._additionalRate3Tax)
			salida+= "\nNota de Debito Exento: "+ str(reportes[NR]._freeTaxDebit)
			salida+= "\nBI IVA G en Nota de Debito: "+ str(reportes[NR]._generalRateDebit)
			salida+= "\nImpuesto IVA G en Nota de Debito: "+ str(reportes[NR]._generalRateTaxDebit)
			salida+= "\nBI IVA R en Nota de Debito: "+ str(reportes[NR]._reducedRateDebit)
			salida+= "\nImpuesto IVA R en Nota de Debito: "+ str(reportes[NR]._reducedRateTaxDebit)
			salida+= "\nBI IVA A en Nota de Debito: "+ str(reportes[NR]._additionalRateDebit)
			salida+= "\nImpuesto IVA A en Nota de Debito: "+ str(reportes[NR]._additionalRateTaxDebit)
			salida+= "\nNota de Credito Exento: "+ str(reportes[NR]._freeTaxDevolution)
			salida+= "\nBI IVA G en Nota de Credito: "+ str(reportes[NR]._generalRateDevolution)
			salida+= "\nImpuesto IVA G en Nota de Credito: "+ str(reportes[NR]._generalRateTaxDevolution)
			salida+= "\nBI IVA R en Nota de Credito: "+ str(reportes[NR]._reducedRateDevolution)
			salida+= "\nImpuesto IVA R en Nota de Credito: "+ str(reportes[NR]._reducedRateTaxDevolution)
			salida+= "\nBI IVA A en Nota de Credito: "+ str(reportes[NR]._additionalRateDevolution)
			salida+= "\nImpuesto IVA A en Nota de Credito: "+ str(reportes[NR]._additionalRateTaxDevolution)+"\n"+"\n"
			print(salida)
		self.txt_informacion.setText(Enc+salida)

error = {
		"0": "No hay error.",
		"1": "Fin en la entrega de papel.",
		"2": "Error de índole mecánico en la entrega de papel.",
		"3": "Fin en la entrega de papel y error mecánico.",
		"80": "Comando inválido o valor inválido.",
		"84": "Tasa inválida.",
		"88": "No hay asignadas directivas.",
		"92": "Comando invalido.",
		"96": "Error fiscal.",
		"100": "Error de la memoria fiscal.",
		"108": "Memoria fiscal llena.",
		"112": "Buffer completo. (debe enviar el comando de reinicio)",
		"128": "Error en la comunicación.",
		"137": "No hay respuesta.",
		"144": "Error LRC.",
		"145": "Error interno api.",
		"153": "Error en la apertura del archivo."}

estado = {
		"0": "Estado desconocido.",
		"1": "En modo prueba y en espera.",
		"2": "En modo prueba y emisión de documentos fiscales.",
		"3": "En modo prueba y emisión de documentos no fiscales.",
		"4": "En modo fiscal y en espera.",
		"5": "En modo fiscal y emisión de documentos fiscales.",
		"6": "En modo fiscal y emisión de documentos no fiscales.",
		"7": "En modo fiscal, cercana carga completa de la memoria fiscal y en espera.",
		"8": "En modo fiscal, cercana carga completa de la memoria fiscal y en emisión de documentos fiscales.",
		"9": "En modo fiscal, cercana carga completa de la memoria fiscal y en emisión de documentos no fiscales.",
		"10": "En modo fiscal, carga completa de la memoria fiscal y en espera.",
		"11": "En modo fiscal, carga completa de la memoria fiscal y en emisión de documentos fiscales.",
		"12": "En modo fiscal, carga completa de la memoria fiscal y en emisión de documentos no fiscales."
	}


if __name__ == "__main__":
	app = QApplication(sys.argv)
	principal = Principal()
	principal.show()
	app.exec_()
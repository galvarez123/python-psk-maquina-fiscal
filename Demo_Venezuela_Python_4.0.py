# coding=utf-8
import PyQt4.QtCore as QC
from PyQt4.QtGui import *
from PyQt4 import uic
import queryexecutor as connect
from operator import xor
from datetime import datetime
import config
from serial.tools.list_ports import comports
import sys
import Tfhka
import serial
import os


class Principal(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        uic.loadUi("DemoPython.ui", self)
        puerto = sorted(x[0] for x in comports())
        self.cmbports.addItems(puerto)
        self.btnImprimirDet.hide()
        self.todos.hide()
        self.groupBox_9.hide()
        self.printer = Tfhka.Tfhka()
        self.btnabrir.clicked.connect(self.abrir_puerto)
        self.btncerrar.clicked.connect(self.cerrar_puerto)
        self.btnestadoerror.clicked.connect(self.estado_error)
        self.btnimprimirZ.clicked.connect(self.reporteZ_imprimir)
        self.btnimprimirX.clicked.connect(self.reporteX_imprimir)
        self.btnestado.clicked.connect(self.obtener_estado)
        self.btnleerZ.clicked.connect(self.reporteZ_obtener)
        self.btnleerX.clicked.connect(self.reporteX_obtener)
        self.btnListadoPed.clicked.connect(lambda: self.leer('PED'))
        self.btnLeerFac.clicked.connect(lambda: self.leer('FAC'))
        self.btnImprimir.clicked.connect(lambda: self.ProcesarDocumento(tuple(())))
        self.btnImprimirDet.clicked.connect(self.validar_Articulos)
        self.tablaRegistro.itemSelectionChanged.connect(self.mostrar_detalle)
        self.btnAnular.clicked.connect(self.anular)
        self.btnBorrar.clicked.connect(self.borrar)
        self.todos.clicked.connect(self.doCheck)

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
        #resp = self.printer
        if hasattr(self.printer, 'ser'):
            delattr(self.printer, 'ser')
        if not resp:
            self.txt_informacion.setText("Impresora Desconectada")
        else:
            self.txt_informacion.setText("Error")

    def programacion(self):
        self.txt_informacion.setText(str(self.printer.SendCmd("D")))

    def anular(self):
        if not hasattr(self.printer, 'ser'):
            QMessageBox.about(self, "ERROR", "Debe Abrir la Conexion")
            return
        estado_s2 = self.printer.GetS2PrinterData()
        typedoc = estado_s2.TypeDocument()
        tipodoc = self.getTipoDoc()
        estado_s1, newdocumento = self.getNextDocument()
        if self.printer.SendCmd("7"):

            query_update = "update psk_pf.factura_linea set   " + \
                           " tipodoc = '" + tipodoc + "' , documento = '" + newdocumento + \
                           "' where tipodoc = 'TRX' "
            connect.run_query(query=query_update)
            formatofechatabla = "%Y-%m-%d"
            formatofechaimpresora = "%d-%m-%Y"
            fecha = datetime.strptime(estado_s1.CurrentPrinterDate(), formatofechaimpresora)
            fecha = fecha.strftime(formatofechatabla)
            hora = str(estado_s1.CurrentPrinterTime())
            if hora[0:2] > "12":
                hora = str(int(hora[0:2]) - 12) + hora[2:5]
                ampm = 2
            else:
                hora = hora[0:5]
                ampm = 1

            query_update = "update psk_pf.factura set   " + \
                           " tipodoc = '"+tipodoc+"' , documento = '" + newdocumento + \
                           "' , serialprintf = '" + str(estado_s1._registeredMachineNumber) + \
                           "' , fechacrea = '" + str(fecha) + \
                           "' , emision = '" + str(fecha) + \
                           "' , recepcion = '" + str(fecha) + \
                           "' , ultimopag = '" + str(fecha) + \
                           "' , horadocum = '" + str(hora) + \
                           "' , ampm = " + str(ampm) + \
                           " , estatusdoc = 3 " + \
                           " , fechanul = '" + str(fecha) + \
                           "', uanulador = '" + str(os.getenv('USERNAME')) + \
                           "', orden = '00000000' " + \
                           ", sinimpuest = 0 " + \
                           ", totalfinal = 0 " + \
                           ", totbruto = 0 " + \
                           ", totdescuen = 0 " + \
                           ", totcosto = 0 " + \
                           ", totneto = 0 " + \
                           " where tipodoc = 'TRX' "
            connect.run_query(query=query_update)
            self.txt_informacion.setText(tipodoc + " " + newdocumento + " anulada")
        else:
            self.txt_informacion.setText("No hay documento")

    def getNextDocument(self):
        estado_s2 = self.printer.GetS2PrinterData()
        typedoc = estado_s2.TypeDocument()
        print "typedoc: " + str(typedoc)
        count=0
        while True:
            estado_s1 = self.printer.GetS1PrinterData()
            lastFactura = estado_s1.LastInvoiceNumber()
            if typedoc == 0:
                return estado_s1, 0
            print "lastFactura: " + str(lastFactura)
            lastND = estado_s1.LastDebtNoteNumber()
            print "lastND: " + str(lastND)
            lastNC = estado_s1.LastNCNumber()
            print "lastNC: " + str(lastNC)
            funcion_documentos = {1: lastFactura, 2: lastNC, 3: lastND}
            numeroDocumento = funcion_documentos.get(int(typedoc),  0)
            print "numeroDocumento: " + str(numeroDocumento)
            count = count + 1
            print "count: " + str(count)
            if count > 5:
                self.txt_informacion.setText("Error Reporte a Sistemas")
                self.printer.SendCmd("7")
                QMessageBox.about(self, "OK", "Error Reporte a Sistemas")
                return estado_s1, 0
            if numeroDocumento != 0:
                break
        newdocumento = str(numeroDocumento+1).rjust(8, '0')
        return estado_s1, newdocumento

    def borrar(self):
        indexes = self.tablaRegistro.selectionModel().selectedRows()
        if not hasattr(self.printer, 'ser'):
            QMessageBox.about(self, "ERROR", "Debe Abrir la Conexion")
            return
        estado_s1 = self.printer.GetS1PrinterData()
        if len(indexes) > 0:
            index = sorted(indexes)[0]
            lista = list()
            lista.append('Documento: %s ' % self.tablaRegistro.item(index.row(), 0).text())
            documento = self.tablaRegistro.item(index.row(), 0).text()
            documento = str(documento.toUtf8()).decode("utf-8")
            lista.append('Cliente: %s ' % self.tablaRegistro.item(index.row(), 1).text())
            cliente = self.tablaRegistro.item(index.row(), 1).text()
            cliente = str(cliente.toUtf8()).decode("utf-8")
            lista.append('Row %d is selected' % index.row())
            tipodoc = self.tablaRegistro.item(index.row(), 4).text()
            tipodoc = str(tipodoc.toUtf8()).decode("utf-8")
            print("seleccionado cliente: " + str(cliente) + " documento: " + str(documento) + " tipodoc: " + str(
                tipodoc))
            formatofechatabla = "%Y-%m-%d"
            formatofechaimpresora = "%d-%m-%Y"
            fecha = datetime.strptime(estado_s1.CurrentPrinterDate(), formatofechaimpresora)
            fecha = fecha.strftime(formatofechatabla)
            hora = str(estado_s1.CurrentPrinterTime())
            if hora[0:2] > "12":
                hora = str(int(hora[0:2]) - 12) + hora[2:5]
                ampm = 2
            else:
                hora = hora[0:5]
                ampm = 1
            query_update = "update psk_pf.factura set   " + \
                           "  serialprintf = '" + str(estado_s1._registeredMachineNumber) + \
                           "' , fechacrea = '" + str(fecha) + \
                           "' , emision = '" + str(fecha) + \
                           "' , recepcion = '" + str(fecha) + \
                           "' , ultimopag = '" + str(fecha) + \
                           "' , horadocum = '" + str(hora) + \
                           "' , ampm = " + str(ampm) + \
                           " , estatusdoc = 3 " + \
                           " , fechanul = '" + str(fecha) + \
                           "', uanulador = '" + str(os.getenv('USERNAME')) + \
                           "' where tipodoc = 'PED' AND documento = '" + documento + "'"
            if tipodoc == 'PED':
                connect.run_query(query=query_update)
                self.txt_informacion.setText(tipodoc + " " + documento + " ANULADO")
                selected = self.tablaRegistro.currentRow()
                self.tablaRegistro.removeRow(selected)
            else:
                QMessageBox.about(self, "Error", "No se Puede Borrar")
        else:
            self.txt_informacion.setText("No hay documento Seleccionado")



    def estado_error(self):
        self.txt_informacion.setText("")
        if hasattr(self.printer, 'ser'):
            self.estado = self.printer.ReadFpStatus()
            salida = "Estado: " + self.estado[0]
            salida += "\n" + estado.get(self.estado[0], "Desconocido")
            salida += "\nError: " + self.estado[5]
            salida += "\n" + error.get(self.estado[5], "Desconocido")
            self.txt_informacion.setText(salida)
        else:
            QMessageBox.about(self, "ERROR", "Debe Abrir la Conexion")


    def mostrar_detalle(self):
        salida_cabecera  = list()
        salida_lineas = list()
        row = self.tablaRegistro.currentRow()
        documento = self.tablaRegistro.item(row, 0).text()
        cedula = self.tablaRegistro.item(row, 1).text()
        tipodoc = self.tablaRegistro.item(row, 4).text()
        print "documento: " + documento +" cedula: " + cedula + " tipodoc: " + tipodoc

        self.leer_cabecera(documento, cedula, tipodoc, salida_cabecera)
        lineas=self.leer_lineas(documento, cedula, tipodoc, salida_lineas)
        texto = ""
        total =0
        for ele in salida_cabecera:
            texto += str(ele).decode("utf-8", errors="ignore")
        for ele in salida_lineas:
            texto += str(ele).decode("utf-8", errors="ignore")

        self.txt_preview.setText(texto)

        self.tablaArticulo.setRowCount(len(lineas) / 5)
        col = 0
        for x in range(0, len(lineas), 5):

            chkBoxItem = QCheckBox()
            #chkBoxItem = QTableWidgetItem()
            #chkBoxItem.setCheckState(QC.Qt.Unchecked)
            if self.todos.isChecked():
                chkBoxItem.setCheckState(QC.Qt.Checked)
            #chkBoxItem.setFlags(QC.Qt.ItemIsUserCheckable | QC.Qt.ItemIsEnabled)
            #chkBoxItem.setFlags(chkBoxItem.flags() | QC.Qt.AlignHCenter)
            #self.tablaArticulo.setItem(col, 0, chkBoxItem)
            self.tablaArticulo.setCellWidget(col, 0, chkBoxItem)

            codigo = QTableWidgetItem(lineas[x + 4])
            codigo.setFlags(xor(codigo.flags(), QC.Qt.ItemIsEditable))
            self.tablaArticulo.setItem(col, 1, codigo)

            cantidad = QSpinBox()
            cantidad.setRange(0, lineas[x + 2])
            cantidad.setValue( lineas[x + 2])
            i = self.tablaArticulo.model().index(col, 2)
            #self.tablaArticulo.setIndexWidget(i, cantidad)
            self.tablaArticulo.setCellWidget(col,2,cantidad)


            max = QTableWidgetItem(str("{:}".format(lineas[x + 2])))
            max.setFlags(xor(max.flags(), QC.Qt.ItemIsEditable))
            self.tablaArticulo.setItem(col, 3, max)

            precio = QTableWidgetItem(str("{:}".format(lineas[x + 1])))
            precio.setFlags(xor(precio.flags(), QC.Qt.ItemIsEditable))
            self.tablaArticulo.setItem(col, 4, precio)

            nombre = QTableWidgetItem(lineas[x + 3])
            nombre.setFlags(xor(nombre.flags(), QC.Qt.ItemIsEditable))
            self.tablaArticulo.setItem(col, 5, nombre)

            gravable = QTableWidgetItem(str("{:}".format(lineas[x])))
            gravable.setFlags(xor(nombre.flags(), QC.Qt.ItemIsEditable))
            self.tablaArticulo.setItem(col, 6, gravable)
            col += 1
        self.tablaArticulo.resizeColumnToContents(0)
        self.tablaArticulo.resizeColumnToContents(1)
        self.tablaArticulo.resizeColumnToContents(2)
        self.tablaArticulo.resizeColumnToContents(3)
        self.tablaArticulo.resizeColumnToContents(4)
        self.tablaArticulo.resizeColumnToContents(5)


    def hayErrorEnImpresora(self):
        try:
            if not hasattr(self.printer, 'ser'):
                QMessageBox.about(self, "ERROR", "Debe Abrir la Conexion")
                return True
            self.estado = self.printer.ReadFpStatus()
            errorvAR = self.estado[5]
            estatusvAR = self.estado[0]
            if errorvAR != "0":
                salida = "Error: " + errorvAR
                salida += "\n" + error.get(errorvAR, "Desconocido")
                QMessageBox.about(self, "ERROR", salida)
                return True
            elif not (estatusvAR == "1" or estatusvAR == "4" or estatusvAR == "7"):
                salida = "Estatus: " + estatusvAR
                salida += "\n" + estado.get(estatusvAR, "Desconocido")
                QMessageBox.about(self, "ERROR", salida)
                return True
        except:
            QMessageBox.about(self, "ERROR", "Impresora No Responde")
            return True
        else:
            print "Programa de Facturacion"
            return False


    def validar_Articulos(self):
        articulos = tuple(())
        for n in range(0, int(self.tablaArticulo.rowCount()), 1):
            if self.tablaArticulo.cellWidget(n, 0).isChecked() and float(self.tablaArticulo.cellWidget(n, 2).value())>0 :
                s = tuple((float(self.tablaArticulo.item(n, 6).text()),
                float(self.tablaArticulo.item(n, 4).text()),
                float(self.tablaArticulo.cellWidget(n, 2).value()),
                unicode(self.tablaArticulo.item(n, 5).text()),
                unicode(self.tablaArticulo.item(n, 1).text())
                ))
                articulos = articulos + s
        if len(articulos) == 0:
            QMessageBox.about(self, "Error", "No hay articulos Selecccionados")
        else:
            print "imprimir N/C"
            self.ProcesarDocumento(articulos)


    def ProcesarDocumento(self, ArticulosNC):
        try:
            self.txt_informacion.setText("")
            indexes = self.tablaRegistro.selectionModel().selectedRows()
            if self.hayErrorEnImpresora():
                print "error impresora"
            elif len(indexes) > 0:
                index = sorted(indexes)[0]
                lista = list()
                lista.append('Documento: %s ' % self.tablaRegistro.item(index.row(), 0).text())
                documento = self.tablaRegistro.item(index.row(), 0).text()
                documento = str(documento.toUtf8()).decode("utf-8")
                lista.append('Cliente: %s ' % self.tablaRegistro.item(index.row(), 1).text())
                cliente = self.tablaRegistro.item(index.row(), 1).text()
                cliente = str(cliente.toUtf8()).decode("utf-8")
                lista.append('Row %d is selected' % index.row())
                tipodoc = self.tablaRegistro.item(index.row(), 4).text()
                tipodoc = str(tipodoc.toUtf8()).decode("utf-8")
                print("seleccionado cliente: " + str(cliente) + " documento: " + str(documento) +" tipodoc: " + str(tipodoc)  )
                config.logging.info("seleccionado cliente: " + str(cliente) + " documento: " + str(documento) +" tipodoc: " + str(tipodoc)  )
                datos_cabecera = self.leer_cabecera(documento, cliente,tipodoc, lista)
                self.imprimir_cabecera(datos_cabecera, documento, cliente, lista, tipodoc)
                if tipodoc == 'FAC':
                    datos_lineas = ArticulosNC
                else:
                    datos_lineas = self.leer_lineas(documento, cliente, tipodoc, lista)

                self.imprimir_lineas(datos_lineas, documento, cliente, tipodoc, lista)

                tipodoc = self.getTipoDoc()
                self.totalizar_factura(cliente, documento, tipodoc)
                self.printer.SendCmd(str("3"))
                self.printer.SendCmd(str("101"))

                QMessageBox.about(self, "OK", "Finalizado")
            else:
                print("nada seleccionado")
                QMessageBox.about(self, "Ups", "No hay pedido seleccionado")
        except Exception, e:
            config.logging.info("Error al Emitir Documento "+str(e))
            self.txt_informacion.setText("Error al Emitir Documento")
            print "Error al Emitir Documento"
            print str(e)

    def getTipoDoc(self):
        tipo_documentos = {0: 'ERR', 1: 'FAC', 2: 'N/C', 3: 'N/D'}
        estado_s2 = self.printer.GetS2PrinterData()
        typedoc = estado_s2.TypeDocument()
        tipodoc = tipo_documentos.get(int(typedoc), 'ERR')
        return tipodoc

    def totalizar_factura(self, cliente, documento, tipodoc):
        try:
            estado_s1,newdocumento = self.getNextDocument()
            query_update = "update psk_pf.factura_linea set   " + \
                           " tipodoc = '"+tipodoc+"' , documento = '" + newdocumento + \
                           "' where tipodoc = 'TRX' and documento = '" + documento + "' AND trim(proveedor) = '" + cliente + "' "
            connect.run_query(query=query_update)
            formatofechatabla = "%Y-%m-%d"
            formatofechaimpresora = "%d-%m-%Y"
            fecha = datetime.strptime(estado_s1._currentPrinterDate, formatofechaimpresora)
            fecha = fecha.strftime(formatofechatabla)
            hora = str(estado_s1._currentPrinterTime)
            if hora[0:2] > "12":
                hora = str(int(hora[0:2]) - 12) + hora[2:5]
                ampm = 2
            else:
                hora = hora[0:5]
                ampm = 1
            query_update = "update psk_pf.factura set   " + \
                           " tipodoc = '"+tipodoc+"' , documento = '" + newdocumento + \
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
        except Exception, e:
            config.logging.info("Error al totalizar Documento "+str(e))
            self.txt_informacion.setText("Error al totalizar Documento")
            print "Error al totalizar Documento"
            print str(e)

    def leer_cabecera(self, documento, cliente, tipo, salida):
        query_cabecera = "SELECT TRIM(rif), TRIM(nombrecli), " + \
                         " coalesce( TRIM(direccion),'Sin Especificar'), " + \
                         " coalesce( TRIM(telefonos),'Sin Especificar') , " + \
                         "  coalesce( TRIM(nombre), 'Oficina Principal'), " + \
                         "  documento , emision , serialprintf " + \
                         "FROM psk_pf.factura  g  Left join adminpurofm.almacene a on a.codigo =g.almacen WHERE   " + \
                         "tipodoc ='" + tipo + "' and trim(documento) = '" + documento + "' and trim(codcliente) = '" + cliente + "' "
        datoscliente = connect.run_query(query=str(query_cabecera).decode("utf-8"))
        if tipo == 'FAC':
            salida.append("Fac: " + datoscliente[5].encode('latin1'))
            salida.append("\nFecha: " + str(datoscliente[6]).encode('latin1'))
            salida.append("\nSERIAL MAQ: " + datoscliente[7].encode('latin1'))
            config.logging.info("Fac: " + datoscliente[5].encode('latin1') + "\nFecha: " + str(datoscliente[6]).encode(
                'latin1') + "\nSERIAL MAQ: " + datoscliente[7].encode('latin1'))
        salida.append("\nRif: " + datoscliente[0].encode('latin1'))
        salida.append("\nRazon Social: " + datoscliente[1].encode('latin1'))
        salida.append("\nDireccion: " + datoscliente[2].encode('utf-8'))
        salida.append("\nTelefono: " + datoscliente[3].encode('latin1'))
        salida.append("\nCAJERO:" + datoscliente[4].encode('latin1'))
        if tipo == 'PED':
            salida.append("\nPedido:" + str(documento))
        config.logging.info("\nRif: " + datoscliente[0].encode('latin1')+"\nRazon Social: " + datoscliente[1].encode('latin1')+"\nDireccion: " + datoscliente[2].encode('utf-8')+"\nTelefono: " + datoscliente[3].encode('latin1')+"\nCAJERO:" + datoscliente[4].encode('latin1')+ "\nPedido:" + str(documento ))
        return datoscliente

    def imprimir_cabecera(self, datoscliente, documento, cliente, salida, tipodoc):
        try:
            for x in range(0, len(datoscliente), 8):
                if tipodoc == 'FAC':
                    self.printer.SendCmd(str("iF*" + str(datoscliente[x + 5]).encode('latin1')))
                    self.printer.SendCmd(str("iD*" + str(datoscliente[x + 6]).encode('latin1')))
                    self.printer.SendCmd(str("iI*" + str(datoscliente[x + 7]).encode('latin1')))
                self.printer.SendCmd(str("iR*" + datoscliente[x].encode('latin1')))
                self.printer.SendCmd(str("iS*" + datoscliente[x + 1].encode('latin1')))


                dir = "DIRECCION: " + datoscliente[x + 2].encode('utf-8')
                #salida.append(dir)
                linea = 0
                maxlen = 40
                while True:
                    aux = "i0" + str(linea) + dir[0:maxlen]
                    self.printer.SendCmd(str(aux))
                    linea += 1
                    if len(dir) > maxlen:
                        dir = dir[maxlen:]
                    else:
                        break
                self.printer.SendCmd(str("i0" + str(linea) + "TELEFONO: " + datoscliente[x + 3].encode('latin1')))
                linea += 1
                self.printer.SendCmd(str("i0" + str(linea) + "CAJERO: " + datoscliente[x + 4].encode('latin1')))
                linea += 1
                if tipodoc == 'PED':
                    self.printer.SendCmd(str("i0" + str(linea) + "PEDIDO: " + str(documento)))
        except Exception, e:
            config.logging.info("Error al totalizar Documento "+str(e))
            self.txt_informacion.setText("Error al totalizar Documento")
            print "Error al totalizar factura"
            print str(e)

    def leer_lineas(self, documento, cliente,  tipo,  salida):
        total =0
        query_lineas = "SELECT a.impuesto1,g.preciooriginal ,cantidad, trim(g.nombre) ,TRIM(G.CODIGO) " + \
                       "FROM psk_pf.factura_linea  g join adminpurofm.articulo a on a.codigo =g.codigo  WHERE   " + \
                       "tipodoc ='"+tipo+"' and trim(documento) = '" + documento + "' and trim(proveedor) = '" + cliente + "' "
        articulos_pedidos = connect.run_query(query=str(query_lineas).decode("utf-8" , errors="ignore"))
        for x in range(0, len(articulos_pedidos), 5):
            z= "\n{0} {1} cant: {2} precio: {3}".format(
                articulos_pedidos[x+4].encode("utf-8", errors="ignore")
                , articulos_pedidos[x+3].encode("utf-8", errors="ignore")
                , articulos_pedidos[x + 2], articulos_pedidos[x + 1])
            salida.append(z)
            total += (articulos_pedidos[x+2]) * articulos_pedidos[x+1]
        salida.append("\n")
        salida.append("\nTotal Orden: "+"{:,}".format(total))
        return articulos_pedidos

    def imprimir_lineas(self, datos_articulos, documento, cliente,  tipodoc, salida):
        flags_impuesto_factura = {0: ' ', 16: '!', 8: '"', 31: '#'}
        flags_impuesto_nc = {0: 'd0', 16: 'd1', 8: 'd2', 31: 'd3'}
        if tipodoc == 'PED':
            porcentage_impuesto=flags_impuesto_factura
            print "flags factura"
        else:
            porcentage_impuesto = flags_impuesto_nc
            print "flags NC"
        base_acu = 0
        impuesto_acu = 0
        base_imponible = 0
        exento = 0
        cantidadArticuloProcesado = 0
        for x in range(0, len(datos_articulos), 5):
            codigo_impuesto = porcentage_impuesto.get(int(datos_articulos[x]), ' ')

            precio = datos_articulos[x + 1]
            precio = round(precio, 2)
            precio_entero = str(int(precio))
            precio_decimal = str(int((precio % 1) * 100))
            precio_entero = precio_entero.rjust(14, '0')
            precio_decimal = precio_decimal.rjust(2, '0')

            cantidad = datos_articulos[x + 2]
            cantidad = round(cantidad, 3)
            cantidad_entero = str(int(cantidad))
            cantidad_decimal = str(int((cantidad % 1) * 1000))
            cantidad_entero = cantidad_entero.rjust(14, '0')
            cantidad_decimal = cantidad_decimal.rjust(3, '0')

            nombre = datos_articulos[x + 3].encode('latin1')

            aux = codigo_impuesto + precio_entero + precio_decimal + cantidad_entero + cantidad_decimal + nombre
            #salida.append(aux)

            if (self.printer.SendCmd(str(aux))):
                config.logging.info("aceptado " + str(aux))
                while True:
                    estado_s2 = self.printer.GetS2PrinterData()
                    base_linea = estado_s2._subTotalBases - base_acu
                    impuesto_linea = estado_s2._subTotalTax - impuesto_acu
                    if base_linea > 0:
                        break
                    else:
                        print("base cero")
                base_imponible_articulo = 0
                if datos_articulos[x] == 0:
                    exento += base_linea
                else:
                    base_imponible += base_linea
                    base_imponible_articulo = base_linea

                base_articulo = base_linea / cantidad
                impuesto = impuesto_linea / cantidad

                base_acu = estado_s2._subTotalBases
                impuesto_acu = estado_s2._subTotalTax


                query_update = "insert into psk_pf.factura_linea select  id_empresa, agencia, 'TRX', documento, grupo, subgrupo, origen, codigo, codhijo, round( pid* rand())  , nombre, costounit, " + str(base_articulo) + ", diferencia, dsctounit, coddescuento, dsctoprc, dsctoendm, dsctomtolinea, dsctoendp, " + str(base_articulo) + ", prcrecargo, recargounit, preciounit, cantidad, cntdevuelt, unidevuelt, cntentrega, tallas, colores, " + str(base_linea) + ", " + str(base_linea + impuesto) + ", almacen, proveedor, fechadoc, " + str(impuesto) + " , impuesto2, impuesto3, impuesto4, impuesto5, impuesto6, " + str(datos_articulos[x]) + ", impu_mto, comision, comisprc, vendedor, emisor, usaserial, tipoprecio, unidad, agrupado, cntagrupada, seimporto, desdeimpor, notas, oferta, compuesto, usaexist, marca, aux1, estacion, estacionfac, clasifica, cuentacont, placa, placaod, udinamica, cantref, unidadref, " + str(
                    base_imponible_articulo) + ", baseimpo2, baseimpo3, lote, imp_nacional, imp_producc, se_imprimio, ofertaconvenio, cod_servidor, prc_comi_servidor, mto_comi_servidor, checkin, habi_nro, idvalidacion, idoferta, agenciant, tipodocant, documant, uemisorant, estacioant, fechadocant, fechayhora, frog, documentolocal, linbloq, enviado_kmonitor, se_guardo, baseimpo4, baseimpo5, baseimpo6 from psk_pf.factura_linea "+\
                                                   " where tipodoc = '"+tipodoc+"' and documento = '" + documento + "' AND trim(proveedor) = '" + cliente + \
                               "' and codigo = '" + datos_articulos[x + 4].encode('latin1') + "'"
                connect.run_query(query=query_update)
            else:
                config.logging.info("rechazado  " + str(aux))

        query_update = " insert into psk_pf.factura select id_empresa ,agencia ,'TRX' ,subtipodoc ,moneda ,documento ,codcliente ,nombrecli ,contacto ,comprador ,rif ,nit ,direccion ,telefonos ,tipoprecio ,orden ,emision ,recepcion ,vence ,ult_interes ,fechacrea ,totcosto ,totcomi ," + str(base_acu) + " ," + str(base_acu) + " ," + str( base_acu + impuesto_acu) + " , " + str(base_acu + impuesto_acu) + " ," + str(impuesto_acu) + " ,totdescuen ," + str(impuesto_acu) + " , " + str(impuesto_acu) + " ,impuesto3 ,impuesto4 ,impuesto5 ,impuesto6 ,recargos ,dsctoend1 ,dsctoend2 ,dsctolinea ,notas ,estatusdoc ,ultimopag ,diascred ,vendedor ,factorcamb ,multi_div ,factorreferencial ,fechanul ,uanulador ,uemisor ,estacion ," + str(exento) + " ,almacen ,sector ,formafis ,al_libro ,codigoret ,retencion ,aux1 ,aux2 ,aplicadoa , '"+str(tipodoc)+str(documento) +"' ,refmanual ,doc_class_id ,operac ,motanul ,seimporto ,dbcr ,horadocum ,ampm ,tranferido ,procedecre ,entregado ,vuelto ,integrado ,escredito ,seq_nodo ,tipo_nc ,porbackord ,chequedev ,ordentrab ,compcont ,planillacob ,nodoremoto ,turno ,codvend_a ,codvend_b ,codvend_c ,codvend_d , " + str(base_imponible) + " ,baseimpo2 ,baseimpo3 ,iddocumento ,imp_nacional ,imp_producc ,retencioniva ,fechayhora ,tipopersona ,idvalidacion ,nosujeto ,serialprintf ,documentofiscal ,numeroz ,ubica ,usa_despacho ,despachador ,despacho_nro ,checkin ,nureserva ,grandocnum ,agenciant ,tipodocant ,documant ,uemisorant ,estacioant ,emisionant ,fchyhrant ,frog ,apa_nc ,documentolocal ,comanda_movil ,comanda_kmonitor ,para_llevar ,notimbrar ,antipo ,antdoc ,xrequest ,xresponse ,parcialidad ,cedcompra ,subcodigo ,cprefijoserie ,contingencia ,precta_movil ,tipodocfiscal ,cprefijodeserie ,cserie ,serieincluyeimpuesto ,serieauto ,opemail ,refmanual2 ,baseimpo4 ,baseimpo5 ,baseimpo6 from psk_pf.factura "+\
                       " where tipodoc = '" + tipodoc + "' and documento = '" + documento + "' AND trim(codcliente) = '" + cliente + "' "

        cantidadArticuloProcesado = connect.run_query(query=query_update)
        return cantidadArticuloProcesado

    def reporteZ_imprimir(self):
        if not hasattr(self.printer, 'ser'):
            QMessageBox.about(self, "ERROR", "Debe Abrir la Conexion")
            return
        self.reporteZ_transferir()
        self.printer.PrintZReport()

    def reporteX_imprimir(self):
        if not hasattr(self.printer, 'ser'):
            QMessageBox.about(self, "ERROR", "Debe Abrir la Conexion")
            return
        self.printer.PrintXReport()

    def obtener_estado(self):
        estado = str(self.cmbestado.currentText())
        if not hasattr(self.printer, 'ser'):
            QMessageBox.about(self, "ERROR", "Debe Abrir la Conexion")
            return
        if estado == "S1":
            estado_s1 = self.printer.GetS1PrinterData()
            salida = "---Estado S1---\n"
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
            self.txt_informacion.setText(salida)

        if estado == "S2":
            estado_s2 = self.printer.GetS2PrinterData()
            salida = "---Estado S2---\n"
            salida += "\nSubtotal de BI: " + str(estado_s2._subTotalBases)
            salida += "\nSubtotal de Impuesto: " + str(estado_s2._subTotalTax)
            salida += "\nData Dummy: " + str(estado_s2._dataDummy)
            salida += "\nCantidad de articulos: " + str(estado_s2._quantityArticles)
            salida += "\nMonto por Pagar: " + str(estado_s2._amountPayable)
            salida += "\nNumero de Pagos Realizados: " + str(estado_s2._numberPaymentsMade)
            salida += "\nTipo de Documento: " + str(estado_s2._typeDocument)
            self.txt_informacion.setText(salida)

        if estado == "S3":
            estado_s3 = self.printer.GetS3PrinterData()
            salida = "---Estado S3---\n"
            salida += "\nTipo Tasa 1 (1 = Incluido, 2= Excluido): " + str(estado_s3._typeTax1)
            salida += "\nValor Tasa 1: " + str(estado_s3._tax1) + " %"
            salida += "\nTipo Tasa 2 (1 = Incluido, 2= Excluido): " + str(estado_s3._typeTax2)
            salida += "\nValor Tasa2: " + str(estado_s3._tax2) + " %"
            salida += "\nTipo Tasa 3 (1 = Incluido, 2= Excluido): " + str(estado_s3._typeTax3)
            salida += "\nValor Tasa 3: " + str(estado_s3._tax3) + " %"
            salida += "\n\nLista de Flags: " + str(estado_s3._systemFlags)
            self.txt_informacion.setText(salida)

        if estado == "S4":
            estado_s4 = self.printer.GetS4PrinterData()
            salida = "---Estado S4---\n"
            salida += "\nMontos en Medios de Pago: " + str(estado_s4._allMeansOfPayment)
            self.txt_informacion.setText(salida)

        if estado == "S5":
            estado_s5 = self.printer.GetS5PrinterData()
            salida = "---Estado S5---\n"
            salida += "\nNumero de RIF: " + str(estado_s5._rif)
            salida += "\nNumero de Registro: " + str(estado_s5._registeredMachineNumber)
            salida += "\nNumero de Memoria de Auditoria : " + str(estado_s5._auditMemoryNumber)
            salida += "\nCapacidad Total de Memoria Auditoria: " + str(estado_s5._auditMemoryTotalCapacity) + " MB"
            salida += "\nEspacio Disponible: " + str(estado_s5._auditMemoryFreeCapacity) + " MB"
            salida += "\nCantidad Documentos Registrados: " + str(estado_s5._numberRegisteredDocuments)
            self.txt_informacion.setText(salida)

        if estado == "S6":
            estado_s6 = self.printer.GetS6PrinterData()
            salida = "---Estado S6---\n"
            salida += "\nModo Facturacion: " + str(estado_s6._bit_Facturacion)
            salida += "\nModo Slip: " + str(estado_s6._bit_Slip)
            salida += "\nModo Validacion: " + str(estado_s6._bit_Validacion)
            self.txt_informacion.setText(salida)

    def reporteZ_obtener(self):
        if not hasattr(self.printer, 'ser'):
            QMessageBox.about(self, "ERROR", "Debe Abrir la Conexion")
            return
        reporte = self.printer.GetZReport()
        salida = "Numero Ultimo Reporte Z: " + str(reporte._numberOfLastZReport)
        salida += "\nFecha Ultimo Reporte Z: " + str(reporte._zReportDate)
        salida += "\nHora Ultimo Reporte Z: " + str(reporte._zReportTime)
        salida += "\nNumero Ultima Factura: " + str(reporte._numberOfLastInvoice)
        salida += "\nFecha Ultima Factura: " + str(reporte._lastInvoiceDate)
        salida += "\nHora Ultima Factura: " + str(reporte._lastInvoiceTime)
        salida += "\nNumero Ultima Nota de Debito: " + str(reporte._numberOfLastDebitNote)
        salida += "\nNumero Ultima Nota de Credito: " + str(reporte._numberOfLastCreditNote)
        salida += "\nNumero Ultimo Doc No Fiscal: " + str(reporte._numberOfLastNonFiscal)
        salida += "\nVentas Exento: " + str(reporte._freeSalesTax)
        salida += "\nBase Imponible Ventas IVA G: " + str(reporte._generalRate1Sale)
        salida += "\nImpuesto IVA G: " + str(reporte._generalRate1Tax)
        salida += "\nBase Imponible Ventas IVA R: " + str(reporte._reducedRate2Sale)
        salida += "\nImpuesto IVA R: " + str(reporte._reducedRate2Tax)
        salida += "\nBase Imponible Ventas IVA A: " + str(reporte._additionalRate3Sal)
        salida += "\nImpuesto IVA A: " + str(reporte._additionalRate3Tax)
        salida += "\nNota de Debito Exento: " + str(reporte._freeTaxDebit)
        salida += "\nBI IVA G en Nota de Debito: " + str(reporte._generalRateDebit)
        salida += "\nImpuesto IVA G en Nota de Debito: " + str(reporte._generalRateTaxDebit)
        salida += "\nBI IVA R en Nota de Debito: " + str(reporte._reducedRateDebit)
        salida += "\nImpuesto IVA R en Nota de Debito: " + str(reporte._reducedRateTaxDebit)
        salida += "\nBI IVA A en Nota de Debito: " + str(reporte._additionalRateDebit)
        salida += "\nImpuesto IVA A en Nota de Debito: " + str(reporte._additionalRateTaxDebit)
        salida += "\nNota de Credito Exento: " + str(reporte._freeTaxDevolution)
        salida += "\nBI IVA G en Nota de Credito: " + str(reporte._generalRateDevolution)
        salida += "\nImpuesto IVA G en Nota de Credito: " + str(reporte._generalRateTaxDevolution)
        salida += "\nBI IVA R en Nota de Credito: " + str(reporte._reducedRateDevolution)
        salida += "\nImpuesto IVA R en Nota de Credito: " + str(reporte._reducedRateTaxDevolution)
        salida += "\nBI IVA A en Nota de Credito: " + str(reporte._additionalRateDevolution)
        salida += "\nImpuesto IVA A en Nota de Credito: " + str(reporte._additionalRateTaxDevolution)
        self.txt_informacion.setText(salida)

    def reporteZ_transferir(self):
        reporte = self.printer.GetXReport()
        salida = "Numero Proximo Reporte Z: " + str(reporte._numberOfLastZReport)
        salida += "\nFecha Ultimo Reporte Z: " + str(reporte._zReportDate)
        salida += "\nHora Ultimo Reporte Z: " + str(reporte._zReportTime)
        salida += "\nNumero Ultima Factura: " + str(reporte._numberOfLastInvoice)
        salida += "\nFecha Ultima Factura: " + str(reporte._lastInvoiceDate)
        salida += "\nHora Ultima Factura: " + str(reporte._lastInvoiceTime)
        salida += "\nNumero Ultima Nota de Debito: " + str(reporte._numberOfLastDebitNote)
        salida += "\nNumero Ultima Nota de Credito: " + str(reporte._numberOfLastCreditNote)
        salida += "\nNumero Ultimo Doc No Fiscal: " + str(reporte._numberOfLastNonFiscal)
        salida += "\nVentas Exento: " + str(reporte._freeSalesTax)
        salida += "\nBase Imponible Ventas IVA G: " + str(reporte._generalRate1Sale)
        salida += "\nImpuesto IVA G: " + str(reporte._generalRate1Tax)
        salida += "\nBase Imponible Ventas IVA R: " + str(reporte._reducedRate2Sale)
        salida += "\nImpuesto IVA R: " + str(reporte._reducedRate2Tax)
        salida += "\nBase Imponible Ventas IVA A: " + str(reporte._additionalRate3Sal)
        salida += "\nImpuesto IVA A: " + str(reporte._additionalRate3Tax)
        salida += "\nNota de Debito Exento: " + str(reporte._freeTaxDebit)
        salida += "\nBI IVA G en Nota de Debito: " + str(reporte._generalRateDebit)
        salida += "\nImpuesto IVA G en Nota de Debito: " + str(reporte._generalRateTaxDebit)
        salida += "\nBI IVA R en Nota de Debito: " + str(reporte._reducedRateDebit)
        salida += "\nImpuesto IVA R en Nota de Debito: " + str(reporte._reducedRateTaxDebit)
        salida += "\nBI IVA A en Nota de Debito: " + str(reporte._additionalRateDebit)
        salida += "\nImpuesto IVA A en Nota de Debito: " + str(reporte._additionalRateTaxDebit)
        salida += "\nNota de Credito Exento: " + str(reporte._freeTaxDevolution)
        salida += "\nBI IVA G en Nota de Credito: " + str(reporte._generalRateDevolution)
        salida += "\nImpuesto IVA G en Nota de Credito: " + str(reporte._generalRateTaxDevolution)
        salida += "\nBI IVA R en Nota de Credito: " + str(reporte._reducedRateDevolution)
        salida += "\nImpuesto IVA R en Nota de Credito: " + str(reporte._reducedRateTaxDevolution)
        salida += "\nBI IVA A en Nota de Credito: " + str(reporte._additionalRateDevolution)
        salida += "\nImpuesto IVA A en Nota de Credito: " + str(reporte._additionalRateTaxDevolution)
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
        salida += "\nNumero de RIF: " + str(estado_s5._rif)
        salida += "\nNumero de Registro: " + str(estado_s5._registeredMachineNumber)
        salida += "\nNumero de Memoria de Auditoria : " + str(estado_s5._auditMemoryNumber)
        salida += "\nCapacidad Total de Memoria Auditoria: " + str(estado_s5._auditMemoryTotalCapacity) + " MB"
        salida += "\nEspacio Disponible: " + str(estado_s5._auditMemoryFreeCapacity) + " MB"
        salida += "\nCantidad Documentos Registrados: " + str(estado_s5._numberRegisteredDocuments)
        estado_s6 = self.printer.GetS6PrinterData()
        salida += "\nModo Facturacion: " + str(estado_s6._bit_Facturacion)
        salida += "\nModo Slip: " + str(estado_s6._bit_Slip)
        salida += "\nModo Validacion: " + str(estado_s6._bit_Validacion)
        maquina = estado_s1.RegisteredMachineNumber()
        if maquina =="??????????":
            maquina="entrenamiento"

        f = open(str(config.reportez)+'ReporteZ'+ str(reporte._numberOfLastZReport)+" "+ str(maquina)  + '.txt', 'wb')
        f.write(salida)
        f.close()
        return salida

    def reporteX_obtener(self):
        if not hasattr(self.printer, 'ser'):
            QMessageBox.about(self, "ERROR", "Debe Abrir la Conexion")
            return
        reporte = self.printer.GetXReport()
        salida = "Numero Proximo Reporte Z: " + str(reporte._numberOfLastZReport)
        salida += "\nFecha Ultimo Reporte Z: " + str(reporte._zReportDate)
        salida += "\nHora Ultimo Reporte Z: " + str(reporte._zReportTime)
        salida += "\nNumero Ultima Factura: " + str(reporte._numberOfLastInvoice)
        salida += "\nFecha Ultima Factura: " + str(reporte._lastInvoiceDate)
        salida += "\nHora Ultima Factura: " + str(reporte._lastInvoiceTime)
        salida += "\nNumero Ultima Nota de Debito: " + str(reporte._numberOfLastDebitNote)
        salida += "\nNumero Ultima Nota de Credito: " + str(reporte._numberOfLastCreditNote)
        salida += "\nNumero Ultimo Doc No Fiscal: " + str(reporte._numberOfLastNonFiscal)
        salida += "\nVentas Exento: " + str(reporte._freeSalesTax)
        salida += "\nBase Imponible Ventas IVA G: " + str(reporte._generalRate1Sale)
        salida += "\nImpuesto IVA G: " + str(reporte._generalRate1Tax)
        salida += "\nBase Imponible Ventas IVA R: " + str(reporte._reducedRate2Sale)
        salida += "\nImpuesto IVA R: " + str(reporte._reducedRate2Tax)
        salida += "\nBase Imponible Ventas IVA A: " + str(reporte._additionalRate3Sal)
        salida += "\nImpuesto IVA A: " + str(reporte._additionalRate3Tax)
        salida += "\nNota de Debito Exento: " + str(reporte._freeTaxDebit)
        salida += "\nBI IVA G en Nota de Debito: " + str(reporte._generalRateDebit)
        salida += "\nImpuesto IVA G en Nota de Debito: " + str(reporte._generalRateTaxDebit)
        salida += "\nBI IVA R en Nota de Debito: " + str(reporte._reducedRateDebit)
        salida += "\nImpuesto IVA R en Nota de Debito: " + str(reporte._reducedRateTaxDebit)
        salida += "\nBI IVA A en Nota de Debito: " + str(reporte._additionalRateDebit)
        salida += "\nImpuesto IVA A en Nota de Debito: " + str(reporte._additionalRateTaxDebit)
        salida += "\nNota de Credito Exento: " + str(reporte._freeTaxDevolution)
        salida += "\nBI IVA G en Nota de Credito: " + str(reporte._generalRateDevolution)
        salida += "\nImpuesto IVA G en Nota de Credito: " + str(reporte._generalRateTaxDevolution)
        salida += "\nBI IVA R en Nota de Credito: " + str(reporte._reducedRateDevolution)
        salida += "\nImpuesto IVA R en Nota de Credito: " + str(reporte._reducedRateTaxDevolution)
        salida += "\nBI IVA A en Nota de Credito: " + str(reporte._additionalRateDevolution)
        salida += "\nImpuesto IVA A en Nota de Credito: " + str(reporte._additionalRateTaxDevolution)
        self.txt_informacion.setText(salida)

    def ImpZpornumero(self):
        n_ini = self.imp_num_ini.value()
        n_fin = self.imp_num_fin.value()
        self.printer.PrintZReport("A", n_ini, n_fin)

    def ImpZporfecha(self):
        n_ini = self.imp_date_ini.date().toPyDate()
        n_fin = self.imp_date_fin.date().toPyDate()
        self.printer.PrintZReport("A", n_ini, n_fin)



    def doCheck(self):
        if self.todos.isChecked():
            for n in range(0, int(self.tablaArticulo.rowCount())):
                self.tablaArticulo.cellWidget(n, 0).setCheckState(QC.Qt.Checked)
        else:
            for n in range(0, int(self.tablaArticulo.rowCount())):
                self.tablaArticulo.cellWidget(n, 0).setCheckState(QC.Qt.Unchecked)



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
        reportes = self.printer.GetZReport("A", n_ini, n_fin)
        CR = len(reportes)
        Enc = "Lista de Reportes\n" + "\n"
        salida = ""
        for NR in range(CR):
            salida += "Numero de Reporte Z: " + str(reportes[NR]._numberOfLastZReport)
            salida += "\nFecha Ultimo Reporte Z: " + str(reportes[NR]._zReportDate)
            salida += "\nHora Ultimo Reporte Z: " + str(reportes[NR]._zReportTime)
            salida += "\nNumero Ultima Factura: " + str(reportes[NR]._numberOfLastInvoice)
            salida += "\nFecha Ultima Factura: " + str(reportes[NR]._lastInvoiceDate)
            salida += "\nHora Ultima Factura: " + str(reportes[NR]._lastInvoiceTime)
            salida += "\nNumero Ultima Nota de Credito: " + str(reportes[NR]._numberOfLastCreditNote)
            salida += "\nNumero Ultima Nota de Debito: " + str(reportes[NR]._numberOfLastDebitNote)
            salida += "\nNumero Ultimo Doc No Fiscal: " + str(reportes[NR]._numberOfLastNonFiscal)
            salida += "\nVentas Exento: " + str(reportes[NR]._freeSalesTax)
            salida += "\nBase Imponible Ventas IVA G: " + str(reportes[NR]._generalRate1Sale)
            salida += "\nImpuesto IVA G: " + str(reportes[NR]._generalRate1Tax)
            salida += "\nBase Imponible Ventas IVA R: " + str(reportes[NR]._reducedRate2Sale)
            salida += "\nImpuesto IVA R: " + str(reportes[NR]._reducedRate2Tax)
            salida += "\nBase Imponible Ventas IVA A: " + str(reportes[NR]._additionalRate3Sal)
            salida += "\nImpuesto IVA A: " + str(reportes[NR]._additionalRate3Tax)
            salida += "\nNota de Debito Exento: " + str(reportes[NR]._freeTaxDebit)
            salida += "\nBI IVA G en Nota de Debito: " + str(reportes[NR]._generalRateDebit)
            salida += "\nImpuesto IVA G en Nota de Debito: " + str(reportes[NR]._generalRateTaxDebit)
            salida += "\nBI IVA R en Nota de Debito: " + str(reportes[NR]._reducedRateDebit)
            salida += "\nImpuesto IVA R en Nota de Debito: " + str(reportes[NR]._reducedRateTaxDebit)
            salida += "\nBI IVA A en Nota de Debito: " + str(reportes[NR]._additionalRateDebit)
            salida += "\nImpuesto IVA A en Nota de Debito: " + str(reportes[NR]._additionalRateTaxDebit)
            salida += "\nNota de Credito Exento: " + str(reportes[NR]._freeTaxDevolution)
            salida += "\nBI IVA G en Nota de Credito: " + str(reportes[NR]._generalRateDevolution)
            salida += "\nImpuesto IVA G en Nota de Credito: " + str(reportes[NR]._generalRateTaxDevolution)
            salida += "\nBI IVA R en Nota de Credito: " + str(reportes[NR]._reducedRateDevolution)
            salida += "\nImpuesto IVA R en Nota de Credito: " + str(reportes[NR]._reducedRateTaxDevolution)
            salida += "\nBI IVA A en Nota de Credito: " + str(reportes[NR]._additionalRateDevolution)
            salida += "\nImpuesto IVA A en Nota de Credito: " + str(
                reportes[NR]._additionalRateTaxDevolution) + "\n" + "\n"
            print(salida)
        self.txt_informacion.setText(Enc + salida)

    def ObtZporfecha(self):
        n_ini = self.obt_date_ini.date().toPyDate()
        n_fin = self.obt_date_fin.date().toPyDate()
        reportes = self.printer.GetZReport("A", n_ini, n_fin)
        CR = len(reportes)
        Enc = "Lista de Reportes\n" + "\n"
        salida = ""
        for NR in range(CR):
            salida += "Numero de Reporte Z: " + str(reportes[NR]._numberOfLastZReport)
            salida += "\nFecha Ultimo Reporte Z: " + str(reportes[NR]._zReportDate)
            salida += "\nHora Ultimo Reporte Z: " + str(reportes[NR]._zReportTime)
            salida += "\nNumero Ultima Factura: " + str(reportes[NR]._numberOfLastInvoice)
            salida += "\nFecha Ultima Factura: " + str(reportes[NR]._lastInvoiceDate)
            salida += "\nHora Ultima Factura: " + str(reportes[NR]._lastInvoiceTime)
            salida += "\nNumero Ultima Nota de Credito: " + str(reportes[NR]._numberOfLastCreditNote)
            salida += "\nNumero Ultima Nota de Debito: " + str(reportes[NR]._numberOfLastDebitNote)
            salida += "\nNumero Ultimo Doc No Fiscal: " + str(reportes[NR]._numberOfLastNonFiscal)
            salida += "\nVentas Exento: " + str(reportes[NR]._freeSalesTax)
            salida += "\nBase Imponible Ventas IVA G: " + str(reportes[NR]._generalRate1Sale)
            salida += "\nImpuesto IVA G: " + str(reportes[NR]._generalRate1Tax)
            salida += "\nBase Imponible Ventas IVA R: " + str(reportes[NR]._reducedRate2Sale)
            salida += "\nImpuesto IVA R: " + str(reportes[NR]._reducedRate2Tax)
            salida += "\nBase Imponible Ventas IVA A: " + str(reportes[NR]._additionalRate3Sal)
            salida += "\nImpuesto IVA A: " + str(reportes[NR]._additionalRate3Tax)
            salida += "\nNota de Debito Exento: " + str(reportes[NR]._freeTaxDebit)
            salida += "\nBI IVA G en Nota de Debito: " + str(reportes[NR]._generalRateDebit)
            salida += "\nImpuesto IVA G en Nota de Debito: " + str(reportes[NR]._generalRateTaxDebit)
            salida += "\nBI IVA R en Nota de Debito: " + str(reportes[NR]._reducedRateDebit)
            salida += "\nImpuesto IVA R en Nota de Debito: " + str(reportes[NR]._reducedRateTaxDebit)
            salida += "\nBI IVA A en Nota de Debito: " + str(reportes[NR]._additionalRateDebit)
            salida += "\nImpuesto IVA A en Nota de Debito: " + str(reportes[NR]._additionalRateTaxDebit)
            salida += "\nNota de Credito Exento: " + str(reportes[NR]._freeTaxDevolution)
            salida += "\nBI IVA G en Nota de Credito: " + str(reportes[NR]._generalRateDevolution)
            salida += "\nImpuesto IVA G en Nota de Credito: " + str(reportes[NR]._generalRateTaxDevolution)
            salida += "\nBI IVA R en Nota de Credito: " + str(reportes[NR]._reducedRateDevolution)
            salida += "\nImpuesto IVA R en Nota de Credito: " + str(reportes[NR]._reducedRateTaxDevolution)
            salida += "\nBI IVA A en Nota de Credito: " + str(reportes[NR]._additionalRateDevolution)
            salida += "\nImpuesto IVA A en Nota de Credito: " + str(
                reportes[NR]._additionalRateTaxDevolution) + "\n" + "\n"
            print(salida)
        self.txt_informacion.setText(Enc + salida)




    def leer(self, tipo):
        query = {
            "PED": "SELECT o.documento  ,trim(o.codcliente) , trim(o.contacto), cast(o.totalfinal as DECIMAL(20,2)), o.tipodoc " +
                   "FROM psk_pf.factura o  join psk_pf.factura_linea ol on " +
                   "o.tipodoc = ol.tipodoc	and o.documento = ol.documento left join psk_pf.factura f on f.tipodoc = 'FAC' " +
                   "AND  o.documento = f.orden AND o.codcliente = f.codcliente  " +
                   " WHERE   o.tipodoc ='PED' and f.documento is null and o.estatusdoc !=3 " +
                   "	group by	o.documento ,	trim(o.codcliente) ,	trim(o.contacto),	o.totalfinal " +
                   "order by o.documento "

            ,
            "FAC": "select	F.documento ,	trim(F.codcliente) ,	trim(F.contacto), cast(f.totalfinal as DECIMAL(20, 2)) , f.tipodoc " +
                   " from	psk_pf.factura f join psk_pf.factura_linea fl on	f.tipodoc = fl.tipodoc	and f.documento = fl.documento " +
                   " where	F.tipodoc = 'FAC' and f.estatusdoc !=3 and f.emision > ADDDATE( CURDATE() , INTERVAL - " + config.dias +")"+
                   " group by	f.documento ,	trim(f.codcliente) ,	trim(f.contacto),	f.totalfinal " +
                   " order by	f.documento "
        }
        queryprov = query.get(tipo, "SELECT 1 + 1 FROM DUAL")
        codprov = connect.run_query(query=str(queryprov).decode("utf-8" , errors="ignore"))
        self.tablaRegistro.setRowCount(len(codprov) / 5)
        self.tablaArticulo.setRowCount(0)
        col = 0
        for x in range(0, len(codprov), 5):
            documento = QTableWidgetItem(codprov[x])
            documento.setFlags(xor(documento.flags(), QC.Qt.ItemIsEditable))
            self.tablaRegistro.setItem(col, 0, documento)

            cliente = QTableWidgetItem(codprov[x + 1])
            cliente.setFlags(xor(cliente.flags(), QC.Qt.ItemIsEditable))
            self.tablaRegistro.setItem(col, 1, cliente)

            nombre = QTableWidgetItem(codprov[x + 2])
            nombre.setFlags(xor(nombre.flags(), QC.Qt.ItemIsEditable))
            self.tablaRegistro.setItem(col, 2, nombre)

            monto = QTableWidgetItem("{:,}".format(codprov[x + 3]))
            monto.setFlags(xor(monto.flags(), QC.Qt.ItemIsEditable))
            self.tablaRegistro.setItem(col, 3, monto)

            tipo = QTableWidgetItem(codprov[x + 4])
            tipo.setFlags(xor(monto.flags(), QC.Qt.ItemIsEditable))
            self.tablaRegistro.setItem(col, 4, tipo)
            col += 1
        self.tablaRegistro.resizeColumnToContents(0)
        self.tablaRegistro.resizeColumnToContents(1)


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

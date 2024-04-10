# ================================================================
# Responsive GUI to control the TMS device

# @author Daniel Estrada
# @colabotor: Valentina Franco
# @date 04-2024
# @version 1.0.0
# ================================================================


import os
import sys
import serial
import json
import warnings
import resources
from PyQt5 import QtCore, QtWidgets
from PyQt5.uic import loadUi
from dialogwidgets import *
from mplwidgets import linear_plots_styles
from pandasmodel import PandasModel
from serial.tools import list_ports
from numpy import zeros, arange
from pandas import DataFrame, ExcelWriter
from pathlib import Path
from openpyxl.styles import Font
from datetime import datetime


warnings.simplefilter(action='ignore', category=FutureWarning)


ui_filename = Path(resource_path("ui_files/interface.ui"))

class MS_interface(QtWidgets.QMainWindow):
    _linear_plot_refs = None
    _map_plot_ref = None
    _cbar = None

    def __init__(self):
        super(MS_interface, self).__init__()
        loadUi(ui_filename, self)

        # upload parameters
        self.upload_default_params()

        # ------------------------ ----- setting up UI elements -------------------------------------
        #remove frame from MainWindow
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.resize_window(0)

        # add a sizeGrip control
        size_grip=QtWidgets.QSizeGrip(self.centralwidget)
        self.size_grip_layout.addWidget(size_grip,  0, QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)
        # setting up the movement of the window with the mouse
        self.window_header_frame.mouseMoveEvent = self.move_window

        # start in home page 
        self.set_body_page(0)

        # hide some panels when GUI starts
        self.show_hide_menu(0, "main")
        self.show_hide_menu(0, "advance-connection")
        self.COM_disconnect_frame.hide()

        self.stop_button.hide()
        self.streaming_controls_frame.setEnabled(False)

        # showing user credentials in the tooltip
        self.user_button.setToolTip(
            "name: " + self.user_name + 
            "\nRole: " + self.user_role + 
            "\ne-mail: " + self.user_email + "\n"
        )

        # showing data paramters in the tooltip
        self.streaming_params_button.setToolTip(
            "Sampling rate: " + str(self.sampling_rate) + 
            "\nPlotting rate: " + str(self.plotting_rate) + 
            "\nAnalysis time: " + str(self.analysis_time) +
            "\nBuffer size: " + str(self.buffer_size)
        )

        # setting up COM interfaces 
        self.serial_port = serial.Serial(timeout=3)
        self.serial_params = dict()
        self.baud_list = {
            "1200": 1200, "2400": 2400, "4800": 4800, "9600": 9600, "19200": 19200,
            "38400": 38400, "57600": 57600, "115200": 115200
        }
        self.data_bits_list = {
            "5": serial.FIVEBITS, "6": serial.SIXBITS, "7": serial.SEVENBITS, "8": serial.EIGHTBITS
        }
        self.parity_list = {
            "None": serial.PARITY_NONE, "Even": serial.PARITY_EVEN, "Odd": serial.PARITY_ODD
        }
        self.stop_bits_list = {
            "1": serial.STOPBITS_ONE, "1.5": serial.STOPBITS_ONE_POINT_FIVE, "2": serial.STOPBITS_TWO
        }
        self.flowcontrol_list = ["None", "XON/XOFF", "RTS/CTS", "DTR/DSR"]

        self.refreshCOMPorts()
        self.baud_combobox.addItems([*self.baud_list])
        self.databits_combobox.addItems([*self.data_bits_list])
        self.parity_combobox.addItems([*self.parity_list])
        self.stopbits_combobox.addItems([*self.stop_bits_list])
        self.flowcontrol_combobox.addItems([*self.flowcontrol_list])

        # setting up data view interface
        self.reset_table_data()

        # seeting up grpah view interface
        self.reset_plot_data()
        # ------------------------------ setting up singals-slots ----------------------------------
        # window buttons
        self.minimize_window_button.clicked.connect(lambda: self.showMinimized())
        self.restore_max_window_button.clicked.connect(lambda: self.resize_window(1))
        self.restore_min_window_button.clicked.connect(lambda: self.resize_window(0))
        self.close_window_button.clicked.connect(lambda: self.close())

        # show-hide buttons
        self.show_left_menu_button.clicked.connect(lambda: self.show_hide_menu(1, "main"))
        self.hide_left_menu_button.clicked.connect(lambda: self.show_hide_menu(0, "main"))
        self.show_connection_settings_menu_button.clicked.connect(
            lambda: self.show_hide_menu(1, "connection")
        )
        self.hide_connection_settings_menu_button.clicked.connect(
            lambda: self.show_hide_menu(0, "connection")
        )
        self.show_advance_connection_settings_button.clicked.connect(
            lambda: self.show_hide_menu(1, "advance-connection")
        )
        self.hide_advance_connection_settings_button.clicked.connect(
            lambda: self.show_hide_menu(0, "advance-connection")
        )

        # menu buttons
        self.home_button.clicked.connect(lambda: self.set_body_page(0))
        self.connection_button.clicked.connect(lambda: self.set_body_page(1))
        self.graph_view_button.clicked.connect(lambda: self.set_body_page(2))
        self.table_view_button.clicked.connect(lambda: self.set_body_page(3))
        self.user_button.clicked.connect(self.update_user_info)
        self.settings_button.clicked.connect(self.open_settings)
        self.streaming_params_button.clicked.connect(self.update_streaming_params)
        self.info_button.clicked.connect(self.show_info)

        # connection combobox
        self.COM_combobox.currentIndexChanged.connect(
            lambda: self.serial_combobox_selection("port")
        )
        self.baud_combobox.currentIndexChanged.connect(
            lambda: self.serial_combobox_selection("baudrate")
        )
        self.databits_combobox.currentIndexChanged.connect(
            lambda: self.serial_combobox_selection("databits")
        )
        self.parity_combobox.currentIndexChanged.connect(
            lambda: self.serial_combobox_selection("parity")
        )
        self.stopbits_combobox.currentIndexChanged.connect(
            lambda: self.serial_combobox_selection("stopbits")
        )
        self.flowcontrol_combobox.currentIndexChanged.connect(
            lambda: self.serial_combobox_selection("flowcontrol")
        )

        self.COM_combobox.setCurrentIndex(self.COM_index)
        self.baud_combobox.setCurrentIndex(self.baud_index)
        self.databits_combobox.setCurrentIndex(self.databits_index)

        # connection buttons
        self.COM_connect_button.clicked.connect(lambda: self.connect_disconnect_COM(1))
        self.COM_disconnect_button.clicked.connect(lambda: self.connect_disconnect_COM(0))
        self.start_button.clicked.connect(self.start_streaming)
        self.stop_button.clicked.connect(self.stop_streaming)

        # setting up a timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timer_isr)

        # data buttons
        self.reset_button.clicked.connect(self.reset)
        self.save_button.clicked.connect(self.save)

    # --------------------------------------- class methods ----------------------------------------
    # config methods
    def upload_default_params(self):
        with open(resource_path('params.json')) as f:
            self.default_params = json.load(f)

        self.user_name = self.default_params.get("user_name", "None")
        self.user_email = self.default_params.get("user_email", "None")
        self.user_role =self.default_params.get("user_role", "None")

        self.COM_index = self.default_params.get("COM_index", 2)
        self.baud_index = self.default_params.get("baud_index", 7)
        self.databits_index = self.default_params.get("databits_index", 3)

        self.sampling_rate = self.default_params.get("sampling_rate", 250)
        self.plotting_rate = self.default_params.get("plotting_rate", 200)
        self.analysis_time = self.default_params.get("analysis_time", 10000)
        self.buffer_size = self.default_params.get("buffer_size", 40)
        self.inital_data_size = self.default_params.get("initial_data_size", 10)
        self.params_to_apply = {
            "sampling_rate": self.sampling_rate,
            "plotting_rate": self.plotting_rate,
            "analysis_time": self.analysis_time,
            "buffer_size": self.buffer_size, 
        }

        self.files_prefix = self.default_params.get("files_prefix", "result")
        self.output_path = Path(resource_path(self.default_params.get("out_path", "./results")))

    # serial methods
    def refreshCOMPorts(self):
        ports = ["---", "refresh"]
        for i in list_ports.comports():
            ports.append(i.device)

        self.COM_combobox.clear()
        self.COM_combobox.addItems(ports)


    def serial_combobox_selection(self, combobox):
        if combobox == "port":
            selectItem = self.COM_combobox.currentText()
            if selectItem == "refresh":
                self.refreshCOMPorts()
            elif selectItem == "---":
                pass
            else:
                self.serial_params["port"] = selectItem

        elif combobox == "baudrate":
            self.serial_params["baudrate"] = self.baud_list[self.baud_combobox.currentText()]

        elif combobox == "databits":
            self.serial_params["bytesize"] = self.data_bits_list[
                self.databits_combobox.currentText()
            ]

        elif combobox == "parity":
            self.serial_params["parity"] = self.parity_list[self.parity_combobox.currentText()]

        elif combobox == "stopbits":
            self.serial_params["stopbits"] = self.stop_bits_list[
                self.stopbits_combobox.currentText()
            ]

        elif combobox == "flowcontrol":
            selectItem = self.flowcontrol_combobox.currentText()

            if selectItem == "XON/XOFF":
                self.serial_params["xonxoff"] = True
            elif selectItem == "RTS/CTS":
                self.serial_params["rtscts"] = True
            elif selectItem == "DTR/DSR":
                self.serial_params["dsrdtr"] = True
            else:
                pass


    def connect_disconnect_COM(self, state):
        if state:
            try:
                self.serial_port.__init__(timeout=5, **self.serial_params)

                self.serial_port.close()
                self.serial_port.open()
                self.COM_disconnect_frame.show()    
                self.COM_connect_frame.hide()
                self.serial_monitor_textedit.appendPlainText(self.serial_params["port"] + " Connected...")
                self.serial_monitor_textedit.appendPlainText("applying streaming parameters...")
                self.streaming_controls_frame.setEnabled(True)
                self.apply_streaming_params()

            except Exception as e:
                self.serial_monitor_textedit.appendPlainText(str(e))
                self.serial_port.close()

        else:
            try:
                self.stop_streaming()
                self.serial_port.close()
                self.COM_disconnect_frame.hide()
                self.COM_connect_frame.show()
                self.serial_monitor_textedit.appendPlainText(self.serial_params["port"] + " Disconnected...")
                self.streaming_controls_frame.setEnabled(False)

            except Exception as e:
                self.serial_monitor_textedit.appendPlainText("Error trying to close " + self.serial_params["port"])


    def arduino_request(self, command):
        self.serial_monitor_textedit.appendPlainText("request: " + command)
        self.serial_port.write(str.encode(command))


    def arduino_response(self):
        res = self.serial_port.readline().decode("utf-8")

        try:
            res = res.split("\r")[0]
            self.serial_monitor_textedit.appendPlainText("response: " + res)

        except Exception as e:
            self.serial_monitor_textedit.appendPlainText("Fail readed " + str(e))
            return None

        return res


    # responsives and widget
    def show_hide_menu(self, show, menu):
        if menu == "main":
            widget = self.content_left_menu
            show_button = self.show_left_menu_button
            hide_button = self.hide_left_menu_button
            animate = b"maximumWidth"
            values = (150, 35)

        elif menu == "connection":
            widget = self.connection_page_menu_settings
            show_button = self.show_connection_settings_menu_button
            hide_button = self.hide_connection_settings_menu_button
            animate = b"maximumWidth"
            values = (150, 0)

        elif menu == "advance-connection":
            if show:
                self.advanced_connection_settings_frame.show()
                self.show_advance_connection_settings_button.hide()
                self.hide_advance_connection_settings_button.show()
            else:
                self.advanced_connection_settings_frame.hide()
                self.hide_advance_connection_settings_button.hide()
                self.show_advance_connection_settings_button.show()
            return 0

        animation = QtCore.QPropertyAnimation(widget, animate)

        if show:
            show_button.hide()
            hide_button.show()
            animation.setStartValue(values[0])
            animation.setEndValue(values[1])
        else:
            show_button.show()
            hide_button.hide()
            animation.setStartValue(values[1])
            animation.setEndValue(values[0])

        animation.setDuration(1000)
        animation.setEasingCurve(QtCore.QEasingCurve.Linear)
        animation.start()


    def resize_window(self, size):
        if size:
            self.restore_max_window_button.hide()
            self.restore_min_window_button.show()
            self.showMaximized()
        else:
            self.restore_max_window_button.show()
            self.restore_min_window_button.hide()
            self.showNormal()


    def move_window(self, event):
        if not self.isMaximized():
            if event.buttons() == QtCore.Qt.LeftButton:
                dir_vect = event.globalPos() - self.pos()
                self.move(self.pos()+ dir_vect)
                event.accept()

        if event.globalPos().y() <= 2:
            self.resize_window(1)
        else:
            self.resize_window(0)


    def set_body_page(self, page):
        if page == 0:
            self.content_stacked.setCurrentWidget(self.home_page)
        if page == 1:
            self.content_stacked.setCurrentWidget(self.connection_page)
        else:
            self.show_hide_menu(0, "connection")
        if page == 2:
            self.content_stacked.setCurrentWidget(self.graph_view_page)
        if page == 3:
            self.content_stacked.setCurrentWidget(self.table_view_page)

        if page != 0:
            self.connection_control_buttons_frame.show()
            self.connection_controls_frame.show()
        else:
            self.connection_control_buttons_frame.hide()
            self.connection_controls_frame.hide()


    def show_info(self):
        info_window = InfoDialog(self)
        info_window.exec_()


    def update_user_info(self):
        user_dialog = UserDialog(
            self,
            name=self.user_name,
            role=self.user_role, 
            email=self.user_email
        )
        user_dialog.setModal(True)

        if user_dialog.exec_() == QtWidgets.QDialog.Accepted :
            self.user_name, self.user_email, self.user_role = user_dialog.get_user_values()

        self.user_button.setToolTip(
            "name: " + self.user_name + 
            "\nRole: " + self.user_role + 
            "\ne-mail: " + self.user_email + "\n"
        )


    def update_streaming_params(self):
        streaming_dialog = StreamingDialog(
            self,
            sampling_rate=self.sampling_rate,
            plotting_rate=self.plotting_rate, 
            analysis_time=self.analysis_time,
            buffer_size=self.buffer_size,
        )
        streaming_dialog.setModal(True)

        if streaming_dialog.exec_() == QtWidgets.QDialog.Accepted :
            params = streaming_dialog.get_streaming_params()
            self.params_to_apply = params
            self.apply_streaming_params()


    def open_settings(self):
        settings_dialog = SettingsDialog(self, **self.default_params)
        settings_dialog.setModal(True)

        if settings_dialog.exec_() == QtWidgets.QDialog.Accepted :
            self.default_params = settings_dialog.get_params()
            self.update_default_params()
            
            self.connect_disconnect_COM(0)
            ui = MS_interface()
            ui.show()
            self.close()


    def update_default_params(self):
        with open(resource_path('params.json'), 'w') as f:
            json.dump(self.default_params, f, indent=4)


    # data and visualization
    def start_streaming(self):
        self.start_button.hide()
        self.stop_button.show()
        self.data_buttons_frame.setEnabled(False)
        self.arduino_request('START')

        if self.arduino_response() == "STAOK":
            self.timer.start(self.plotting_rate)
        else:
            self.serial_monitor_textedit.appendPlainText("Not started ")


    def stop_streaming(self):
        self.start_button.show()
        self.stop_button.hide()
        self.data_buttons_frame.setEnabled(True)
        self.arduino_request('STOP')

        if self.arduino_response() == "STOOK":
            self.timer.stop()
        else:
            self.serial_monitor_textedit.appendPlainText("Not stopped ")


    def timer_isr(self):
        if self.update_data():
            self.render_data()


    def update_data(self):
        self.arduino_request('GET')
        res = self.arduino_response()
        if res == "BE":
            self.stop_streaming()
            msgBox = QMessageBox()
            msgBox.setText("DONE!")
            msgBox.setWindowTitle("")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_()
            return 2

        elif res == "BF":
            self.stop_streaming()
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText("STREAMING STOPPED: BUffer limit reached, try to change streaming parameters.")
            msgBox.setWindowTitle("")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_()
            self.stop_streaming()
            return 0

        elif res:
            try:
                res = json.loads(res)
                res["time"] = self.data["time"].iloc[-1] + self.sampling_rate
                self.data = self.data.append(
                    res,
                    ignore_index=True,
                )
                return 1

            except ValueError:
                res = {
                    "time": self.data["time"].iloc[-1] + self.sampling_rate,
                    "T1": -1,
                    "T2": -1,
                    "T3": -1,
                    "T4": -1,
                    "T5": -1,
                    "T6": -1,
                }
                self.data = self.data.append(
                    res,
                    ignore_index=True,
                )
                self.serial_monitor_textedit.appendPlainText("failed data!, filled with -1 ")
                return -1

            except Exception as e:
                self.serial_monitor_textedit.appendPlainText(str(e))
                return 0
        else:
            return 0


    def render_data(self):
        self.update_table_data()
        self.update_plots_data()


    def reset_table_data(self):
        times = arange(
            0 - self.inital_data_size * self.sampling_rate,
            0 + self.sampling_rate, self.sampling_rate)
        # initialize data with zeros
        data = dict(zip(["T1", "T2", "T3", "T4", "T5", "T6"], zeros((6, len(times)))))
        data["time"] = times

        self.data = DataFrame(
            data,
            columns=["time", "T1", "T2", "T3", "T4", "T5", "T6"]
        )
        self.update_table_data()


    def update_table_data(self):
        self.data_table_viewer.setModel(PandasModel(self.data))


    def reset_plot_data(self):
        self._linear_plot_refs = dict()
        for key in self.data.columns[1:]:
            self._linear_plot_refs[key] = self.linear_plot.canvas.axes.plot(
                self.data["time"],
                self.data[key],
                label=key,
                **linear_plots_styles[key],
            )[0]
        self.linear_plot.canvas.axes.set_title("\nTemperatures - Time Series\n")
        self.linear_plot.canvas.axes.set_xlabel("t [ms]")
        self.linear_plot.canvas.axes.set_ylabel("T [°C]")
        self.linear_plot.canvas.axes.legend(bbox_to_anchor=(0,0,1,1), borderpad=.5, ncols=3)

        self._map_plot_ref = self.map_plot.canvas.axes.imshow(
            self.data[self.data.columns[1:]].T,
            aspect="auto",
            cmap='inferno',
            origin="lower",
            vmin=0,
            vmax=self.data[self.data.columns[1:]].max().max(),
        )

        if self._cbar is None:
            self._cbar = self.map_plot.canvas.figure.colorbar(
                    self._map_plot_ref,
                    ax=self.map_plot.canvas.axes,
                    pad=0.01,
                    fraction=0.048,
                )

        self.map_plot.canvas.axes.set_yticks(range(0, 6), self.data.columns[1:])
        self.map_plot.canvas.axes.set_title("\nMap of temperatures - Time Series\n")
        self.map_plot.canvas.axes.set_xlabel("t [ms]")
        self.map_plot.canvas.axes.set_ylabel("Thermocouples")

        self.rescale_lims(cbar=False)


    def update_plots_data(self):
        for key in self.data.columns[1:]:
            self._linear_plot_refs[key].set_xdata(self.data["time"])
            self._linear_plot_refs[key].set_ydata(self.data[key])

        self._map_plot_ref.set_data(self.data[self.data.columns[1:]].T)

        self.rescale_lims()
        self.linear_plot.canvas.draw()
        self.map_plot.canvas.draw()


    def rescale_lims(self, cbar=True):
        self.linear_plot.canvas.axes.dataLim.y1 = self.data[self.data.columns[1:]].max().max() + 30
        self.linear_plot.canvas.axes.dataLim.y0 = self.data[self.data.columns[1:]].min().min() - 5
        self.linear_plot.canvas.axes.dataLim.x0 = self.data["time"].iloc[0]
        self.linear_plot.canvas.axes.dataLim.x1 = self.data["time"].iloc[-1]

        self.linear_plot.canvas.axes.autoscale_view()

        self._map_plot_ref.set_extent(
            [
                self.data["time"].iloc[0],
                self.data["time"].iloc[-1], 
                0,
                6,
            ]
        )

        if cbar:
            self._cbar.mappable.set_clim(vmin=0,vmax=self.data[self.data.columns[1:]].max().max())


    def reset(self):
        self.serial_monitor_textedit.clear()
        if self.timer.isActive():
            self.stop_streaming()
        if self.serial_port.is_open:
            self.arduino_request("CLEAR")
            _=self.arduino_response()
        self.reset_table_data()
        self.update_plots_data()


    def save(self):
        try:
            self.output_path = Path(
                resource_path(
                    QFileDialog.getExistingDirectory(self, "Output path", str(self.output_path))
                )
            )
            time_stamp = datetime.now()
            path_timestamp = time_stamp.strftime("_%Y-%m-%d_%H%M%S")
            base_file_name = self.files_prefix + "_{}" + path_timestamp + ".{}"

            # saving data
            data_file_name = self.output_path / base_file_name.format("data", "xlsx")
            self.write_data_file(data_file_name, time_stamp)

            #saving plots
            self.linear_plot.canvas.axes.figure.savefig(
                self.output_path / base_file_name.format("linear-plot", "png"),
                dpi=500
            )
            self.map_plot.canvas.axes.figure.savefig(
                self.output_path / base_file_name.format("map-plot", "png"),
                dpi=500
            )
            saved=True

        except Exception as e:
            error = e
            saved=False
        
        if saved:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Graphs and data sucessfully saved in: \n" + str(self.output_path))
            msgBox.setWindowTitle("")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_()
        else:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText("It was not possible to save the results: \n" + str(error))
            msgBox.setWindowTitle("")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_()


    def write_data_file(self, filename, timestamp):
        with ExcelWriter(filename, mode='w', engine='openpyxl') as writer:
            self.data.to_excel(writer, index=False, startrow=7)
            worksheet = writer.sheets['Sheet1']
            header = [
                ["Temperature Measurement System - results"],
                ["User name:", self.user_name],
                ["User role:", self.user_role],
                ["User email:", self.user_email],
                ["Date:", timestamp.ctime()]
            ]
            for i, row in enumerate(header):
                for j, value in enumerate(row):
                    cell = worksheet.cell(row=i+1, column=j+1, value=value)
                    if i == 0:
                        cell.font = Font(bold=True, size=14)


    def apply_streaming_params(self):
        if not self.serial_port.is_open:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText("Not applied: changes will take place when connect serial communication\n")
            msgBox.setWindowTitle("")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec_()

        else:
            self.plotting_rate = self.params_to_apply.get("plotting_rate", self.plotting_rate)
            changed = [0, 1, 0, 0]

            # setting up arduino parameters
            self.arduino_request("SETS " + str(self.params_to_apply.get("sampling_rate", self.sampling_rate)))
            res = self.arduino_response()
            while res != "SSOK" and res != "SSNOK":
                self.arduino_request("SETS " + str(self.params_to_apply.get("sampling_rate", self.sampling_rate)))
                res = self.arduino_response()
            if res == "SSOK":
                self.sampling_rate = self.params_to_apply.get("sampling_rate")
                changed[0] = 1

            self.arduino_request("SETA " + str(self.params_to_apply.get("analysis_time", self.analysis_time)))
            res = self.arduino_response()
            while res != "SAOK" and res != "SANOK":
                self.arduino_request("SETA " + str(self.params_to_apply.get("analysis_time", self.analysis_time)))
                res = self.arduino_response()
            if res == "SAOK":
                self.analysis_time = self.params_to_apply.get("analysis_time", self.analysis_time)
                changed[2] = 1

            self.arduino_request("BSIZE " + str(self.params_to_apply.get("buffer_size", self.buffer_size)))
            res = self.arduino_response()
            while res != "BSOK" and res != "BSNOK":
                self.arduino_request("BSIZE " + str(self.params_to_apply.get("buffer_size", self.buffer_size)))
                res = self.arduino_response()
            if res == "BSOK":
                self.buffer_size = self.params_to_apply.get("buffer_size")
                changed[3] = 1
            
            self.streaming_params_button.setToolTip(
                "Sampling rate: " + str(self.sampling_rate) + 
                "\nPlotting rate: " + str(self.plotting_rate) + 
                "\nAnalysis time: " + str(self.analysis_time) +
                "\nBuffer size: " + str(self.buffer_size)
            )

            if not all(changed):
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Warning)
                not_changed_values = ""
                for i, param in enumerate(self.params_to_apply.keys()):
                    if not changed[i]:
                        not_changed_values += param + "\n"
                msgBox.setText("It was not possible to change the following parameters: \n" + not_changed_values)
                msgBox.setWindowTitle("")
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.exec_()

if __name__ == "__main__":
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    ui = MS_interface()
    ui.show()
    sys.exit(app.exec_())
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.uic import loadUi
from pathlib import Path

user_ui_filename = Path("../ui_files/user_dialog.ui")
info_ui_filename = Path("../ui_files/info_dialog.ui")
settings_ui_filename = Path("../ui_files/settings_dialog.ui")
streaming_ui_filename = Path("../ui_files/streaming_dialog.ui")

class DialogWidget(QtWidgets.QDialog):
    def __init__(self, parent, ui_file):
        super(DialogWidget, self).__init__(parent)
        loadUi(ui_file, self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setWindowOpacity(1)
        self.window_header.mouseMoveEvent = self.move_window

    def move_window(self, event):
        self.clickPosition = self.pos()
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.clickPosition)
            self.clickPosition = event.globalPos()
            event.accept()


class UserDialog(DialogWidget):
    def __init__(self, parent, **kargs):
        super(UserDialog, self).__init__(parent, user_ui_filename)
        self.name = kargs.get("name", '')
        self.role = kargs.get("role", '')
        self.email = kargs.get("email", '')

        self.name_lineEdit.setText(self.name)
        self.role_lineEdit.setText(self.role)
        self.email_lineEdit.setText(self.email)

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText("Change")
        self.close_button.clicked.connect(self.reject)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.accept)
        

    def get_user_values(self):
        name = "None" if not self.name_lineEdit.text() else self.name_lineEdit.text()
        email = "None" if not self.email_lineEdit.text() else self.email_lineEdit.text()
        role = "None" if not self.role_lineEdit.text() else self.role_lineEdit.text()

        return name, email, role


class StreamingDialog(DialogWidget):
    def __init__(self, parent, **kargs):
        super(StreamingDialog, self).__init__(parent, streaming_ui_filename)
        self.sampling_rate = kargs.get("sampling_rate", 250)
        self.plotting_rate = kargs.get("plotting_rate", 200)
        self.analysis_time = kargs.get("analysis_time", 10000)
        self.buffer_size = kargs.get("buffer_size", 40)

        self.sampling_rate_spinbox.setValue(self.sampling_rate)
        self.plotting_rate_spinbox.setValue(self.plotting_rate)
        self.analysis_time_spinbox.setValue(self.analysis_time)
        self.buffer_size_spinbox.setValue(self.buffer_size)

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText("Change")
        self.close_button.clicked.connect(self.reject)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.accept)
        

    def get_streaming_params(self):
        sampling_rate = self.sampling_rate_spinbox.value()
        plotting_rate = self.plotting_rate_spinbox.value()
        analysis_time = self.analysis_time_spinbox.value()
        buffer_size = self.buffer_size_spinbox.value()

        return {"sampling_rate": sampling_rate, "plotting_rate": plotting_rate, "analysis_time": analysis_time, "buffer_size": buffer_size}


class SettingsDialog(DialogWidget):
    def __init__(self, parent=None, **kargs):
        super(SettingsDialog, self).__init__(parent, settings_ui_filename)
        self.default_params = kargs
        self.params = {
            0: {"name": "COM_index", "widget": self.COM_index_spinbox},
            1: {"name": "baud_index", "widget": self.baud_index_spinbox},
            2: {"name": "databits_index", "widget": self.databits_index_spinbox},
            3: {"name": "sampling_rate", "widget": self.sampling_rate_spinbox},
            4: {"name": "plotting_rate", "widget": self.plotting_rate_spinbox},
            5: {"name": "analysis_time", "widget": self.analysis_time_spinbox},
            6: {"name": "buffer_size", "widget": self.buffer_size_spinbox_2},
            7: {"name": "user_name", "widget": self.name_lineEdit},
            8: {"name": "user_role", "widget": self.role_lineEdit},
            9: {"name": "user_email", "widget": self.email_lineEdit},
            10: {"name": "initial_data_size", "widget": self.initial_data_size_spinbox},
            11: {"name": "files_prefix", "widget": self.file_name_prefix_lineEdit},
            12: {"name": "out_path", "widget": self.output_path_button},
        }

        self.upload_params()

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText("Apply")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText("Cancel")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.accept)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.close_button.clicked.connect(self.reject)
        
        for idx, widget_info in self.params.items():
            if isinstance(widget_info["widget"],QtWidgets.QSpinBox):
                widget_info["widget"].valueChanged.connect(lambda value, index=idx: self.update_param(index))

            elif isinstance(widget_info["widget"],QtWidgets.QLineEdit):
                widget_info["widget"].textEdited.connect(lambda value, index=idx: self.update_param(index))

            elif isinstance(widget_info["widget"], QtWidgets.QToolButton):
                widget_info["widget"].clicked.connect(lambda checked, index=idx: self.update_param(index))


    def get_params(self):
        return self.default_params

    def upload_params(self):
        for _, widget_info in self.params.items():
            if isinstance(widget_info["widget"], QtWidgets.QSpinBox):
                widget_info["widget"].setValue(self.default_params[widget_info["name"]])

            elif isinstance(widget_info["widget"],QtWidgets.QLineEdit):
                widget_info["widget"].setText(self.default_params[widget_info["name"]])

            elif isinstance(widget_info["widget"], QtWidgets.QToolButton):
                self.output_path_lineEdit.setText(self.default_params[widget_info["name"]])

    def update_param(self, index):
        if isinstance(self.sender(), QtWidgets.QSpinBox):
            new_value = self.sender().value()

        elif isinstance(self.sender(), QtWidgets.QLineEdit):
            new_value = self.sender().text()

        elif isinstance(self.sender(), QtWidgets.QToolButton):
            new_value = QFileDialog.getExistingDirectory(
                self, "Output path",
                self.default_params.get("out_path", "./results")
            )
            self.output_path_lineEdit.setText(new_value)

        self.default_params[self.params.get(index)["name"]] = new_value


class InfoDialog(DialogWidget):
    def __init__(self, parent):
        super(InfoDialog, self).__init__(parent, info_ui_filename)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText("Ok")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.accept)
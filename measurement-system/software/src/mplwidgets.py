
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from PyQt5.QtCore import Qt


figure_configs = {
	'figure.dpi': 200,                         # Dots per inch (resolution)
	'axes.labelsize': 6,                       # Axes label size
	'axes.titlesize': 8,                      # Axes title size
	'axes.titleweight': 'bold',                # Axes title weight
	'axes.titlepad': 5,                       # Spacing between title and axes
	'legend.fontsize': 6,                     # Legend font size
	'xtick.labelsize': 4,                     # X-axis tick label size
	'ytick.labelsize': 4,                     # Y-axis tick label size
	'axes.titlelocation': 'center',              # Location of axes title
	'figure.autolayout': True,                 # Automatic figure layout adjustment
	'figure.constrained_layout.use': True,     # Use constrained layout for figure
	'figure.constrained_layout.h_pad': 0.1,    # Horizontal spacing between subplots
	'figure.constrained_layout.w_pad': 0.1     # Vertical spacing between subplots
}

plt.rcParams.update(figure_configs)    


line_width = 0.5
marker_size = 2
linear_plots_styles = {
	"T1": {
		"color": "#1f77b4",  # Blue
		"linewidth": line_width,
		"markersize": marker_size,
		"linestyle": "--",  # Dashed line
		"marker": "o"  # Circle
	},
	"T2": {
		"color": "#ff7f0e",  # Orange
		"linewidth": line_width,
		"markersize": marker_size,
		"linestyle": "--",  # Dashed line
		"marker": "s"  # Square
	},
	"T3": {
		"color": "#2ca02c",  # Green
		"linewidth": line_width,
		"markersize": marker_size,
		"linestyle": "--",  # Dashed line
		"marker": "^"  # Triangle up
	},
	"T4": {
		"color": "#d62728",  # Red
		"linewidth": line_width,
		"markersize": marker_size,
		"linestyle": "--",  # Dashed line
		"marker": "+"  # Cross 1
	},
	"T5": {
		"color": "#9467bd",  # Violet
		"linewidth": line_width,
		"markersize": marker_size,
		"linestyle": "--",  # Dashed line
		"marker": "x"  # Cross 2
	},
	"T6": {
		"color": "#8c564b",  # Brown
		"linewidth": line_width,
		"markersize": marker_size,
		"linestyle": "--",  # Dashed line
		"marker": "P"  # Pentagon
	}
}


# custom toolbar with lorem ipsum text
class ToolbarWidget(NavigationToolbar):
	def __init__(self, canvas_, parent_=None):
		self.toolitems = (
		('Home', 'Reset original view', 'home', 'home'),
		#('Back', 'Back to  previous view', 'back', 'back'),
		#('Forward', 'Forward to next view', 'forward', 'forward'),
		('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
		('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
		('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
		#('Save', 'Save the figure', 'filesave', 'save_figure'),
		)
		NavigationToolbar.__init__(self, canvas_, parent_)


class PlotWidget(QWidget):
	"""docstring for MplWidget"""
	def __init__(self, parent = None):
		super(PlotWidget, self).__init__()
		
		self.vertical_layout = QVBoxLayout()
		self.canvas = FigureCanvas(plt.Figure(dpi=100, facecolor="#fff"))
		self.toolbar = ToolbarWidget(self.canvas, parent)

		self.vertical_layout.addWidget(self.canvas, stretch=3)
		self.vertical_layout.addWidget(self.toolbar, stretch=0)

		self.vertical_layout.setAlignment(self.toolbar, Qt.AlignBaseline)
		self.vertical_layout.setSpacing(0)
		self.vertical_layout.setContentsMargins(0, 0, 0, 0)

		self.canvas.axes = self.canvas.figure.add_subplot(111, facecolor="#000")
		self.canvas.axes.grid(True, color="gray", linewidth=0.5)
		self.setLayout(self.vertical_layout)

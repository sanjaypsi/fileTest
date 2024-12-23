import os
import logging
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as cmds
from functools import partial
from shiboken2 import wrapInstance, isValid
from PySide2.QtWidgets import QWidget, QMainWindow, QScrollArea, QLabel, QVBoxLayout, QMessageBox
from PySide2.QtCore import QFile
from PySide2 import QtUiTools

import importlib

# External modules
import LoadCollapsed_widget
import Collapsible
import MainCallbackManager

importlib.reload(Collapsible)
importlib.reload(LoadCollapsed_widget)
importlib.reload(MainCallbackManager)

# Paths and Styles
SCRIPT_LOC 			= os.path.dirname(__file__)
collapseWidgetUI 	= os.path.join(SCRIPT_LOC, 'ui', 'HeadUI01.ui')
collapseNeckUI 		= os.path.join(SCRIPT_LOC, 'ui', 'Neck.ui')
collapseNoseUI 		= os.path.join(SCRIPT_LOC, 'ui', 'Nose.ui')
collapseEarUI 		= os.path.join(SCRIPT_LOC, 'ui', 'Ear.ui')
collapseShoulderrUI = os.path.join(SCRIPT_LOC, 'ui', 'Shoulder.ui')
collapseArmUI 		= os.path.join(SCRIPT_LOC, 'ui', 'Arm.ui')
collapseHandUI 		= os.path.join(SCRIPT_LOC, 'ui', 'Hand.ui')
collapseTorsoUI 	= os.path.join(SCRIPT_LOC, 'ui', 'Torso.ui')
collapseLegUI 		= os.path.join(SCRIPT_LOC, 'ui', 'Leg.ui')
collapseFootUI 		= os.path.join(SCRIPT_LOC, 'ui', 'Foot.ui')

SLIDER_STYLESHEET = """
				QSlider::groove:horizontal {
					border: 1px solid #999;
					height: 6px;
					background: #ccc;
					margin: 0px;
					border-radius: 3px;
				}
				QSlider::handle:horizontal {
					background: #5c5c5c;
					border: 1px solid #444;
					width: 14px;
					margin: -5px 0;
					border-radius: 7px;
				}
				QSlider::handle:horizontal:hover {
					background: #787878;
					border: 1px solid #555;
				}
				QSlider::sub-page:horizontal {
					background: #409eff;
					border: 1px solid #5a9;
					height: 6px;
					border-radius: 3px;
				}
				QSlider::add-page:horizontal {
					background: #ccc;
					border: 1px solid #999;
					height: 6px;
					border-radius: 3px;
				}
				"""

def get_maya_window():
	"""Get Maya's main window as a PySide2 object."""
	main_window_ptr = omui.MQtUtil.mainWindow()
	if not main_window_ptr:
		raise RuntimeError("Failed to obtain Maya's main window.")
	return wrapInstance(int(main_window_ptr), QWidget)  # Replace 'long' with 'int'

def load_ui(ui_file, parent=None):
	"""Load the .ui file and return the corresponding widget."""
	loader = QtUiTools.QUiLoader()
	ui_file = QFile(ui_file)
	if not ui_file.exists():
		raise FileNotFoundError("UI file {} not found.".format(ui_file.fileName()))
	ui_file.open(QFile.ReadOnly)
	ui_widget = loader.load(ui_file, parent)
	ui_file.close()
	if not ui_widget:
		raise RuntimeError("Failed to load UI file {}.".format(ui_file.fileName()))
	return ui_widget

class MyWindow(QMainWindow):
	"""Main UI Window."""
	def __init__(self, parent=None):
		super(MyWindow, self).__init__(parent)
		
		self.main_ui = os.path.join(SCRIPT_LOC, "ui", "main02.ui")
		if not os.path.exists(self.main_ui):
			raise FileNotFoundError(f"UI file not found: {self.main_ui}")
		
		# Load UI
		self.ui = load_ui(self.main_ui, parent=self)
		self.setWindowTitle("Maya Attribute Controller")
		self.resize(600, 700)

		self.headUI 		= None
		self.NeckUI			= None
		self.NoseUI			= None
		self.EarUI 			= None
		self.ShoulderUI		= None

		self.tabs 			= None
		# self.NoseUI		= None
		self.globalContrl 	= "con_world_L"
		self.controlname 	= ['con_headScaleUp']
		
		self.slider_label_map 		= {
									'sliderSacler01'		: 'lineEditSacler01', 
									'sliderSacler02'		: 'lineEditSacler02',
									'HeadSliderSize'		: 'HeadLineEditSize',
									"HeadSliderScaleX"		: "HeadLineEditScaleX",
									"HeadSliderScaleY"		: "HeadLineEditScaleY",
									"HeadSliderScaleZ"		: "HeadLineEditScaleZ",
									"HeadSliderUpDn"		: "HeadLineEditUpDn",
									"HeadSliderFntBack"		: "HeadLineEditFntBack",
									"HeadSliderRotate"		: "HeadLineEditRotate",
									'NeckUP_Size_SD'		: 'NeckUP_Size_LD',
									"NeckUP_ScaleY_SD"		: "NeckUP_ScaleY_LD",
									"NeckUP_ScaleZ_SD"		: "NeckUP_ScaleZ_LD",
									"NeckDN_Size_SD"		: "NeckDN_Size_LD",
									"NeckDN_ScaleY_SD"		: "NeckDN_ScaleY_LD",
									"NeckDN_ScaleZ_SD"		: "NeckDN_ScaleZ_LD",
									"NeckRootUP_Dn_SD"		: "NeckRootUP_Dn_LD",
									"NeckRootFront_Back_SD"	: "NeckRootFront_Back_LD",
								}
		
		self.slider_attr_map 		= {
									'sliderSacler01': 'all_scale',
									'sliderSacler02': 'all_translate',
								}
		
		self.sliderLabel_map 		= {

									'HeadSliderSize'	: ('HeadLineEditSize',		'HeadRestSize'),
									"HeadSliderScaleX"	: ("HeadLineEditScaleX",	'HeadRestSizeX'),
									"HeadSliderScaleY"	: ("HeadLineEditScaleY",	'HeadRestSizeY'),
									"HeadSliderScaleZ"	: ("HeadLineEditScaleZ",	'HeadRestSizeZ'),
									"HeadSliderUpDn"	: ("HeadLineEditUpDn",		'HeadRestUpDn'),
									"HeadSliderFntBack"	: ("HeadLineEditFntBack",	'HeadRestFntBack'),
									"HeadSliderRotate"	: ("HeadLineEditRotate",	'HeadRestRotate'),
									
									'NeckUP_Size_SD'	: ('NeckUP_Size_LD',		'NeckUP_Size_BT'),
									"NeckUP_ScaleY_SD"	: ("NeckUP_ScaleY_LD",		'NeckUP_ScaleY_BT'),
									"NeckUP_ScaleZ_SD"	: ("NeckUP_ScaleZ_LD",		'NeckUP_ScaleZ_BT'),
									"NeckDN_Size_SD"	: ("NeckDN_Size_LD",		'NeckDN_Size_BT'),
									"NeckDN_ScaleY_SD"	: ("NeckDN_ScaleY_LD",		'NeckDN_ScaleY_BT'),
									"NeckDN_ScaleZ_SD"	: ("NeckDN_ScaleZ_LD",		'NeckDN_ScaleZ_BT'),
									"NeckRootUP_Dn_SD"	: ("NeckRootUP_Dn_LD",		'NeckRootUP_Dn_BT'),
									"NeckRootFront_Back_SD"	: ("NeckRootFront_Back_LD",	'NeckRootFront_Back_BT'),
								}
		
		self.sliderAttr_map			= {
									'headUI': [
										('self.headUI',	'HeadSliderSize', 	'con_headScaleUp', 'size'),
										('self.headUI',	'HeadSliderScaleX', 'con_headScaleUp', 'scaleX'),
										('self.headUI',	'HeadSliderScaleY', 'con_headScaleUp', 'scaleY'),
										('self.headUI',	'HeadSliderScaleZ', 'con_headScaleUp', 'scaleZ'),
										('self.headUI',	'HeadSliderUpDn', 	'con_headPosition', 'translateY'),
										('self.headUI',	'HeadSliderFntBack','con_headPosition','translateZ'),
										('self.headUI',	'HeadSliderRotate', 'con_headRotate', 	'rotateY'),
									],

									'NeckUI': [
										('self.NeckUI',	'NeckUP_Size_SD', 		'con_headScaleDn', 'size'),
										('self.NeckUI',	'NeckUP_ScaleY_SD', 	'con_headScaleDn', 'scaleY'),
										('self.NeckUI',	'NeckUP_ScaleZ_SD', 	'con_headScaleDn', 'scaleZ'),
										('self.NeckUI',	'NeckDN_Size_SD', 		'con_neck', 		'size'),
										('self.NeckUI',	'NeckDN_ScaleY_SD', 	'con_neck', 		'scaleY'),
										('self.NeckUI',	'NeckDN_ScaleZ_SD', 	'con_neck', 		'scaleZ'),
										('self.NeckUI',	'NeckRootUP_Dn_SD', 	'con_neckPosition', 'translateY'),
										('self.NeckUI',	'NeckRootFront_Back_SD','con_neckPosition', 'translateZ'),
									],

								}
		
		self.restAttr				= {
									'headUI': [
										('HeadRestSize',	'HeadSliderSize', 	'con_headScaleUp', 'size', '1'),
										('HeadRestSizeX',	'HeadSliderScaleX', 'con_headScaleUp', 'scaleX','1'),
										('HeadRestSizeY',	'HeadSliderScaleY', 'con_headScaleUp', 'scaleY','1'),
										('HeadRestSizeZ',	'HeadSliderScaleZ', 'con_headScaleUp', 'scaleZ','1'),
										('HeadRestUpDn',	'HeadSliderUpDn', 	'con_headPosition', 'translateY','0'),
										('HeadRestFntBack',	'HeadSliderFntBack','con_headPosition','translateZ','0'),
										('HeadRestRotate',	'HeadSliderRotate', 'con_headRotate', 	'rotateY','0'),
									],
									'neckUI': [
										('NeckUP_Size_BT',		'NeckUP_Size_SD', 		'con_headScaleDn', 'size', '1'),
										('NeckUP_ScaleY_BT',	'NeckUP_ScaleY_SD', 	'con_headScaleDn', 'scaleY', '1'),
										('NeckUP_ScaleZ_BT',	'NeckUP_ScaleZ_SD', 	'con_headScaleDn', 'scaleZ', '1'),
										('NeckDN_Size_BT',		'NeckDN_Size_SD', 		'con_neck', 		'size', '1'),
										('NeckDN_ScaleY_BT',	'NeckDN_ScaleY_SD', 	'con_neck', 		'scaleY', '1'),
										('NeckDN_ScaleZ_BT',	'NeckDN_ScaleZ_SD', 	'con_neck', 		'scaleZ', '1'),
										('NeckRootUP_Dn_BT',	'NeckRootUP_Dn_SD', 	'con_neckPosition', 'translateY', '0'),
										('NeckRootFront_Back_BT','NeckRootFront_Back_SD','con_neckPosition', 'translateZ', '0'),
									],
									# 'NoseUI': [
									# 	('self.NoseUI',	'NoseTranslateY_SD', 'con_nosePosition', 'translateY'),
									# 	('self.NoseUI',	'NoseTranslateZ_SD', 'con_nosePosition', 'translateZ'),
									# 	('self.NoseUI',	'NoseRotateX_SD', 	'con_noseRotate',  	'rotateX'),
									# 	('self.NoseUI',	'NoseScaleX_SD', 	'con_nose', 	'scaleX'),
									# 	('self.NoseUI',	'NoseScaleY_SD', 	'con_nose', 	'scaleY'),
									# 	('self.NoseUI',	'NoseScaleZ_SD', 	'con_nose', 	'scaleZ'),
									# ],

								}
		
		self.attribute_slider_pairs = {
			'con_headScaleDn': [
				('size', 'NeckUP_Size_SD', 'NeckUP_Size_LD'),
				('scaleY', 'NeckUP_ScaleY_SD', 'NeckUP_ScaleY_LD'),
				('scaleZ', 'NeckUP_ScaleZ_SD', 'NeckUP_ScaleZ_LD'),
			],
			'con_neck': [
				('size', 'NeckDN_Size_SD', 'NeckDN_Size_LD'),
				('scaleY', 'NeckDN_ScaleY_SD', 'NeckDN_ScaleY_LD'),
				('scaleZ', 'NeckDN_ScaleZ_SD', 'NeckDN_ScaleZ_LD'),
			],
			'con_neckPosition': [
				('translateY', 'NeckRootUP_Dn_SD', 'NeckRootUP_Dn_LD'),
				('translateZ', 'NeckRootFront_Back_SD', 'NeckRootFront_Back_LD'),
			],
		}
		
		# Scrollable Area
		self.scroll_area = QScrollArea(self)
		self.scroll_area.setWidget(self.ui)
		self.scroll_area.setWidgetResizable(True)
		self.setCentralWidget(self.scroll_area)

		# Configure UI
		self.create_menu_bar()
		self.setup_sliders()
		self.connect_sliders()
		self.initialize_ui_values()
		self.globalCntrl_connection()

		self.add_ui_widget()
		self.connection()
		self.dynamic_sliders_styleSheet()
		self.dynamic_connect_sliders()
		self.dynaicInitialize_ui_values()
		self.dynamicRest_value()
		self.dynamic_callback_connection()
		self.on_slider_click()

	# =======================================================================================================
	# Create Custom MenuBar
	# =======================================================================================================
	def create_menu_bar(self):
		"""Create a menu bar for the application."""
		menu_bar = self.menuBar()

		# File menu
		file_menu = menu_bar.addMenu("File")
		file_menu.addAction("Open")
		file_menu.addAction("Save")
		file_menu.addSeparator()
		exit_action = file_menu.addAction("Exit")
		exit_action.triggered.connect(self.close)

		# Edit menu
		edit_menu = menu_bar.addMenu("Edit")
		edit_menu.addAction("Undo")
		edit_menu.addAction("Redo")
		edit_menu.addSeparator()
		edit_menu.addAction("Preferences")

		# Help menu
		help_menu = menu_bar.addMenu("Help")
		about_action = help_menu.addAction("About")
		about_action.triggered.connect(self.show_about_dialog)

	def show_about_dialog(self):
		"""Display an About dialog."""
		QMessageBox.about(self, "About", "Master File Manager ver2.0\nCreated using PySide2 for Maya.")
	# =======================================================================================================
	#  Global Control Setup:-
	# =======================================================================================================
	def globalCntrl_connection(self):
		"""Initialize the Callback Manager"""
		self.callback_manager = MainCallbackManager.CallbackManager(self.globalContrl,
																	self.slider_label_map, 
																	self.ui)

	def setup_sliders(self):
		"""Apply stylesheets to sliders."""
		for slider_name in self.slider_label_map.keys():
			slider = getattr(self.ui, slider_name, None)
			if slider:
				slider.setStyleSheet(SLIDER_STYLESHEET)
				slider.setMinimum(0)
				slider.setMaximum(100)

	def connect_sliders(self):
		"""Connect sliders and QLineEdits to update Maya attributes."""
		for slider_name, attribute in self.slider_attr_map .items():
			slider 			= getattr(self.ui, slider_name, None)
			line_edit_name 	= self.slider_label_map.get(slider_name)
			line_edit 		= getattr(self.ui, line_edit_name, None)

			# Connect slider to update Maya attribute and QLineEdit
			if slider:
				slider.sliderPressed.connect(self.on_slider_click)
				slider.sliderReleased.connect(self.on_slider_release)
				slider.valueChanged.connect(partial(self.update_attribute_from_slider, attribute, slider_name))

			# Connect QLineEdit to update Maya attribute and QSlider
			if line_edit and slider:
				line_edit.editingFinished.connect(partial(self.update_slider_from_line_edit, line_edit, slider, attribute))

	def update_attribute_from_slider(self, attribute, slider_name, slider_value):
		"""Update Maya attribute and QLineEdit when slider is moved."""
		float_value = slider_value / 10.0
		if cmds.objExists(self.globalContrl):
			cmds.setAttr(f"{self.globalContrl}.{attribute}", float_value)
		# Update QLineEdit
		line_edit_name = self.slider_label_map.get(slider_name)
		line_edit = getattr(self.ui, line_edit_name, None)
		if line_edit:
			line_edit.setText(f"{float_value:.1f}")

	def update_slider_from_line_edit(self, line_edit, slider, attribute):
		"""Update slider and Maya attribute when QLineEdit value is changed."""
		try:
			float_value = float(line_edit.text())
			slider_value = int(float_value * 10)

			# Update the QSlider
			slider.blockSignals(True)
			slider.setValue(slider_value)
			slider.blockSignals(False)

			# Update Maya attribute
			if cmds.objExists(self.globalContrl):
				cmds.setAttr(f"{self.globalContrl}.{attribute}", float_value)

		except ValueError:
			print("Invalid input in QLineEdit. Please enter a numeric value.")

	def initialize_ui_values(self):
		"""Initialize slider and QLineEdit values with Maya attribute values."""

		for slider_name, attribute in self.slider_attr_map .items():
			if cmds.objExists(self.globalContrl):
				current_value = cmds.getAttr(f"{self.globalContrl}.{attribute}")
				slider = getattr(self.ui, slider_name, None)
				line_edit_name = self.slider_label_map.get(slider_name)
				line_edit = getattr(self.ui, line_edit_name, None)

				if slider:
					slider.setValue(int(current_value * 10))
				if line_edit:
					line_edit.setText(f"{current_value:.1f}")

	# =======================================================================================================
	# Add Collapse Tab in Main UI : - collapseLegUI
	# =======================================================================================================
	def add_ui_widget(self):
		"""Add collapsible functionality to the layout."""
		self.headUI 	= LoadCollapsed_widget._loadWidget(widgetCollapse=collapseWidgetUI)._loadUI()
		self.NeckUI 	= LoadCollapsed_widget._loadWidget(widgetCollapse=collapseNeckUI)._loadUI()
		self.NoseUI 	= LoadCollapsed_widget._loadWidget(widgetCollapse=collapseNoseUI)._loadUI()
		self.EarUI 		= LoadCollapsed_widget._loadWidget(widgetCollapse=collapseEarUI)._loadUI()
		self.ShoulderUI = LoadCollapsed_widget._loadWidget(widgetCollapse=collapseShoulderrUI)._loadUI()
		self.ArmUI 		= LoadCollapsed_widget._loadWidget(widgetCollapse=collapseArmUI)._loadUI()
		self.HandUI 	= LoadCollapsed_widget._loadWidget(widgetCollapse=collapseHandUI)._loadUI()
		self.TorsoUI 	= LoadCollapsed_widget._loadWidget(widgetCollapse=collapseTorsoUI)._loadUI()
		self.LegUI 		= LoadCollapsed_widget._loadWidget(widgetCollapse=collapseLegUI)._loadUI()
		self.FootUI 	= LoadCollapsed_widget._loadWidget(widgetCollapse=collapseFootUI)._loadUI()

		main_layout = getattr(self.ui, "CollapseLayout", None)
		if not main_layout:
			logging.warning("Main layout not found. Creating a new QVBoxLayout.")
			main_layout = QVBoxLayout(self.ui)
			self.ui.setLayout(main_layout)

		# Add collapsible tabs
		self.tabs = []

		def create_tab(title, content):
			tab = Collapsible.CollapsibleTab(title)
			tab.content_layout.addWidget(content)
			main_layout.addWidget(tab)
			self.tabs.append(tab)

		create_tab("HEAD-TAB", self.headUI)
		create_tab("NECK-TAB", self.NeckUI)
		create_tab("NOSE-TAB", self.NoseUI)
		create_tab("Ear-TAB", self.EarUI)
		create_tab("Shoulder-TAB", self.ShoulderUI)
		create_tab("Arm-TAB", self.ArmUI)
		create_tab("Hand-TAB", self.HandUI)
		create_tab("Torso-TAB", self.TorsoUI)
		create_tab("Leg-TAB", self.LegUI)
		create_tab("Foot-TAB", self.FootUI)

		main_layout.addStretch()

	def connection(self):
		"""Connect button actions to specific tab operations."""
		# Connect the button to expand the "HEAD-TAB"
		self.ui.pushButton_2.clicked.connect(self.expand_head_tab)

	def expand_head_tab(self):
		"""Collapse all tabs and expand only the HEAD-TAB."""
		for tab in self.tabs:
			if tab.toggle_button.text() == "HEAD-TAB":
				tab.expand()  # Expand the "HEAD-TAB"
			else:
				tab.collapse()  # Collapse all other tabs
				
	def dynamic_sliders_styleSheet(self):
		"""Apply stylesheets and configure sliders and splitters"""
		# Iterate over UI elements and their attribute mappings
		for ui_element, slider_mappings in self.sliderAttr_map.items():
			for ui, slider_name, control, attribute in slider_mappings:
				# Map ui_element to corresponding UI object
				ui_object = None
				if ui_element in 'headUI':
					ui_object = self.headUI
				
				elif ui_element in 'NeckUI':
					ui_object = self.NeckUI

				elif ui_element in 'NoseUI':
					ui_object = self.NoseUI
				
				# Apply the stylesheet if the slider exists
				if ui_object:
					slider = getattr(ui_object, slider_name, None)
					if slider:
						slider.setStyleSheet(SLIDER_STYLESHEET)
					else:
						print(f"Warning: Slider '{slider_name}' not found in {ui_element}.")

	def dynamic_connect_sliders(self):
		"""Connect sliders and QLineEdits to update Maya attributes."""
		for ui_element, slider_mappings in self.sliderAttr_map.items():
			# Determine the target UI object
			Gui = None
			if ui_element == 'headUI':
				Gui = self.headUI
			elif ui_element == 'NeckUI':
				Gui = self.NeckUI

			# Skip if no valid UI object is found
			if not Gui:
				continue

			# Iterate through slider mappings
			for ui, slider_name, controlname, attribute in slider_mappings:
				slider = getattr(Gui, slider_name, None)
				line_edit_name = self.sliderLabel_map.get(slider_name, [None])
				line_edit = getattr(Gui, line_edit_name[0], None)

				# Connect slider to update Maya attribute and QLineEdit
				if slider:
					slider.valueChanged.connect(partial(
						self.dynamicUpdate_attribute_from_slider,
						controlname, attribute, slider_name, Gui
					))

				# Connect QLineEdit to update Maya attribute and QSlider
				if line_edit and slider:
					line_edit.editingFinished.connect(partial(
						self.dynamicUpdate_slider_from_line_edit,
						line_edit, slider, attribute, controlname
					))

	def dynamicUpdate_attribute_from_slider(self, control, 
										 attribute, slider_name, 
										 Gui, slider_value):
		"""Update Maya attribute and QLineEdit when slider is moved."""
		float_value = slider_value / 10.0

		# Update Maya attribute
		if cmds.objExists(control):
			cmds.setAttr(f"{control}.{attribute}", float_value)

		# Update QLineEdit
		line_edit_name = self.sliderLabel_map.get(slider_name, [None])
		line_edit = getattr(Gui, line_edit_name[0], None)
		if line_edit:
			line_edit.setText(f"{float_value:.1f}")

	def dynamicUpdate_slider_from_line_edit(self, line_edit, 
										slider, attribute,
										controlname):
		"""Update slider and Maya attribute when QLineEdit value is changed."""
		try:
			float_value = float(line_edit.text())
			slider_value = int(float_value * 10)

			# Update the QSlider
			slider.blockSignals(True)
			slider.setValue(slider_value)
			slider.blockSignals(False)

			# Update Maya attribute
			if cmds.objExists(controlname):
				cmds.setAttr(f"{controlname}.{attribute}", float_value)
		except ValueError:
			print("Invalid input in QLineEdit. Please enter a numeric value.")

	def dynaicInitialize_ui_values(self):
		"""Initialize slider and QLineEdit values with Maya attribute values."""
		"""Connect sliders and QLineEdits to update Maya attributes."""	
		for ui_element, slider_mappings in self.sliderAttr_map.items():
			for ui, slider_name, controlname, attribute in slider_mappings:
				if ui_element in 'headUI':
					if cmds.objExists(controlname):
						current_value 	= cmds.getAttr(f"{controlname}.{attribute}")
						slider 			= getattr(self.headUI, slider_name, None)
						line_edit_name 	= self.sliderLabel_map.get(slider_name)
						line_edit 		= getattr(self.headUI, line_edit_name[0], None)

						if slider:
							slider.setValue(int(current_value * 10))
						if line_edit:
							line_edit.setText(f"{current_value:.1f}")

				if ui_element in 'NeckUI':
					if cmds.objExists(controlname):
						current_value 	= cmds.getAttr(f"{controlname}.{attribute}")
						slider 			= getattr(self.NeckUI, slider_name, None)
						line_edit_name 	= self.sliderLabel_map.get(slider_name)
						line_edit 		= getattr(self.NeckUI, line_edit_name[0], None)

						if slider:
							slider.setValue(int(current_value * 10))
						if line_edit:
							line_edit.setText(f"{current_value:.1f}")

	def dynamicRest_value(self):
		# Iterate over UI elements and their attribute mappings
		for ui_element, slider_mappings in self.restAttr.items():
			for restbtn, slider_name, control, attribute, value in slider_mappings:
				# Identify UI to operate on
				if ui_element in 'headUI':
					ui 	= self.headUI
				
				elif ui_element in 'neckUI':
					ui = self.NeckUI
				
				else:
					continue

				reset_button 	= getattr(ui, restbtn, None)
				slider 			= getattr(ui, slider_name, None)
				line_edit_name 	= self.sliderLabel_map.get(slider_name, None)
				line_edit 		= getattr(ui, line_edit_name[0], None) if line_edit_name else None

				if reset_button:
					# Connect reset button to update Maya attribute
					reset_button.clicked.connect(
						lambda ctrl=control, attr=attribute, val=value: cmds.setAttr(f"{ctrl}.{attr}", float(val))
					)
					# Connect reset button to reset slider and line edit
					reset_button.clicked.connect(
						partial(self.reset_attribute, line_edit, slider_name, float(value), ui)
					)

	def reset_attribute(self, line_edit, slider_name, value, ui):
		slider 			= getattr(ui, slider_name, None)
		line_edit_name 	= self.sliderLabel_map.get(slider_name, None)
		line_edit 		= getattr(ui, line_edit_name[0], None) if line_edit_name else None

		if line_edit:
			line_edit.setText(f"{value:.1f}")

		if slider:
			slider.setValue(int(value * 10))  # Assuming scaling by 10 is correct

	def dynamic_callback_connection(self):
		"""Initialize the Callback Manager"""
		for ui_element, slider_mappings in self.restAttr.items():
			for restbtn, slider_name, control, attribute, value in slider_mappings:
				# Map ui_element to corresponding UI object
				ui_object = None
				if ui_element in 'headUI':
					ui_object = self.headUI
				
				elif ui_element in 'NeckUI':
					ui_object = self.NeckUI
				
				self.callback_manager = MainCallbackManager.CallbackManager(control, self.slider_label_map, ui_object)

				# -------------------------------------------------------------------------------------------------------------
		"""Initialize the Callback Manager"""
		# Dictionary of node names with their attribute mappings
		self.dynamiccallback_manager = MainCallbackManager.DynamicCallbackManager(self.NeckUI)				
		# Loop through dictionary to add mappings dynamically
		for node_name, attributes in self.attribute_slider_pairs.items():
			for attribute_name, slider_name, line_edit_name in attributes:
				self.dynamiccallback_manager.add_attribute_slider_pair(node_name, attribute_name, slider_name, line_edit_name)

	# =======================================================================================================
	def on_slider_click(self):
		"""Handle slider click events."""
		slider = self.sender()
		if slider:
			slider_name = slider.objectName()
			print(f"Clicked on Slider: {slider_name}")
			# slider.setStyleSheet("background-color: lightblue;")  # Highlight slider

	def on_slider_release(self):
		"""Reset slider appearance after release."""
		slider = self.sender()
		if slider:
			slider.setStyleSheet(SLIDER_STYLESHEET)  # Reset slider to default style

	def closeEvent(self, event):
		"""Clean up when the window is closed."""
		self.callback_manager.remove_callback()
		self.dynamiccallback_manager.remove_callbacks()
		# callback_manager.remove_callback()
		event.accept()

# ============================================================================================================
def show_window():
	"""Show the window."""
	global my_window
	try:
		my_window.close()
		my_window.deleteLater()
	except:
		pass
	my_window = MyWindow(parent=get_maya_window())
	my_window.show()
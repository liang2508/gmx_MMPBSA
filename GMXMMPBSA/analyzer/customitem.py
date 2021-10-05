# ##############################################################################
#                           GPLv3 LICENSE INFO                                 #
#                                                                              #
#  Copyright (C) 2020  Mario S. Valdes-Tresanco and Mario E. Valdes-Tresanco   #
#                                                                              #
#   Project: https://github.com/Valdes-Tresanco-MS/gmx_MMPBSA                  #
#                                                                              #
#   This program is free software; you can redistribute it and/or modify it    #
#  under the terms of the GNU General Public License version 3 as published    #
#  by the Free Software Foundation.                                            #
#                                                                              #
#  This program is distributed in the hope that it will be useful, but         #
#  WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY  #
#  or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License    #
#  for more details.                                                           #
# ##############################################################################
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pandas as pd
from .utils import com2str, energy2pdb_pml


class SpacerItem(QToolButton):
    def __init__(self, parent=None):
        super(SpacerItem, self).__init__(parent)
        self.setDisabled(True)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("QToolButton { /* mimic the look of the QToolButton with MenuButtonPopup */ "
                           "padding-right: 15px; /* make way for the popup button */}")


class CorrelationItem(QTreeWidgetItem):
    def __init__(self, parent, stringlist, model=None, enthalpy=None, dgie=None, dgnmode=None, dgqh=None, col_box=None):
        super(CorrelationItem, self).__init__(parent, stringlist)

        self.model = model
        self.enthalpy = enthalpy
        self.dgie = dgie
        self.dgnmode = dgnmode
        self.dgqh = dgqh
        self.chart_title = f'Correlation Using {stringlist[0].upper()} model'
        self.chart_subtitle = ['Exp. Energy vs Enthalpy (ΔH)', 'Exp. Energy vs Pred. Energy (ΔH+IE)',
                               'Exp. Energy vs Pred. Energy (ΔH+NMODE)', 'Exp. Energy vs Pred. Energy (ΔH+QH)']
        self.item_name = stringlist[0]
        if col_box:
            for col in col_box:
                self.setCheckState(col, Qt.Unchecked)

        self.dh_sw = None
        self.dgie_sw = None
        self.dgnmode_sw = None
        self.dgqh_sw = None


class CustomItem(QTreeWidgetItem):
    def __init__(self, parent, stringlist, data=None, app=None, level=0, chart_title='Binding Free Energy',
                 chart_subtitle='', system_index=1, iec2_data=None, item_type='energy',
                 buttons=(), options_btn=False, remove_empty_terms=False):
        super(CustomItem, self).__init__(parent, stringlist)

        self.remove_empty_terms = remove_empty_terms
        self.data = data
        self.system_index = system_index
        self.app = app
        self.level = level
        self.chart_title = chart_title
        self.chart_subtitle = chart_subtitle
        self.item_name = stringlist[0]
        self.buttons = buttons
        self.options_btn = options_btn
        self.iec2_data = iec2_data
        self.item_type = item_type
        self.properties = {}

        self.lp_subw = None
        self.bp_subw = None
        self.hmp_subw = None
        self.pymol_process = None
        self.pymol_data_change = False
        self.bfactor_pml = None
        self.output_file_subw = None
        self.decomp_output_file_subw = None
        self.line_table_subw = None
        self.bar_table_subw = None
        self.heatmap_table_subw = None
        self.ie_plot_data = None

        # changes
        self.frange = []
        self.line_change = False
        self.bar_change = False
        self.heatmap_change = False


        self.changed = False

        self.tb = QToolBar()
        self.tb.setStyleSheet("QToolBar {padding: 0, 20, 0, 20;}")

        self.tb.setIconSize(QSize(16, 16))
        self.tb.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.item_charts = []

        self.btn_group = QButtonGroup()
        self.btn_group.setExclusive(False)
        self.btn_group.buttonToggled.connect(self.fn_btn_group)

        self.mark_all = QCheckBox()
        self.mark_all.setToolTip('Mark all actions at the same time')
        self.mark_all.setTristate(True)
        self.mark_all.setCheckable(True)
        self.mark_all.stateChanged.connect(self.fn_mark_all)

        self.charts_action = {
            1: self._define_line_chart_btn,
            2: self._define_bar_chart_btn,
            3: self._define_heatmap_chart_btn,
            4: self._define_vis_btn,
        }

    def changes(self, line, bar, heatmap):
        self.line_change = line
        self.bar_change = bar
        self.heatmap_change = heatmap

    def _define_line_chart_btn(self):
        line_menu = QMenu()
        line_menu.setTitle('Line charts menu')
        self.line_table_action = line_menu.addAction('Show in table')
        self.line_table_action.setCheckable(True)
        self.line_table_action.toggled.connect(self._show_line_table)

        self.line_chart_action = QToolButton()
        self.line_chart_action.setIcon(QIcon(
            '/home/mario/PycharmProjects/gmx_MMPBSA/GMXMMPBSA/analyzer/style/line-chart.svg'))
        self.line_chart_action.setText('Line Chart')
        self.line_chart_action.setCheckable(True)
        self.line_chart_action.setPopupMode(QToolButton.MenuButtonPopup)
        self.line_chart_action.setContentsMargins(0, 0, 0, 0)
        self.line_chart_action.setMenu(line_menu)
        self.btn_group.addButton(self.line_chart_action, 1)

        self.tb.addWidget(self.line_chart_action)

    def _show_line_table(self, state):
        from GMXMMPBSA.analyzer.plots import Tables
        self.app.treeWidget.clearSelection()
        if state:
            self.setSelected(True)
            self.line_table_subw = Tables(self.line_plot_data, self.line_table_action)
            self.app.mdi.addSubWindow(self.line_table_subw)
            self.line_table_subw.show()
        elif self.line_table_subw:
            self.app.mdi.activatePreviousSubWindow()
            self.line_table_subw.close()

    def _define_bar_chart_btn(self):
        bar_menu = QMenu()
        bar_menu.setTitle('Bar charts menu')
        self.bar_table_action = bar_menu.addAction('Show in table')
        self.bar_table_action.setCheckable(True)
        self.bar_table_action.toggled.connect(self._show_bar_table)

        self.bar_chart_action = QToolButton()
        self.bar_chart_action.setIcon(
            QIcon('/home/mario/PycharmProjects/gmx_MMPBSA/GMXMMPBSA/analyzer/style/bar-chart.png'))
        self.bar_chart_action.setText('Bar Chart')
        self.bar_chart_action.setCheckable(True)
        self.bar_chart_action.setPopupMode(QToolButton.MenuButtonPopup)
        self.bar_chart_action.setContentsMargins(0, 0, 0, 0)
        self.bar_chart_action.setMenu(bar_menu)
        self.btn_group.addButton(self.bar_chart_action, 2)

        self.tb.addWidget(self.bar_chart_action)

    def _show_bar_table(self, state):
        from GMXMMPBSA.analyzer.plots import Tables
        self.app.treeWidget.clearSelection()
        if state:
            self.setSelected(True)
            if not self.bar_table_subw:
                self.bar_table_subw = Tables(self.bar_plot_data, self.bar_table_action)
                self.app.mdi.addSubWindow(self.bar_table_subw)
            self.bar_table_subw.show()
        elif self.bar_table_subw:
            self.app.mdi.activatePreviousSubWindow()
            self.bar_table_subw.close()

    def _define_heatmap_chart_btn(self):
        heatmap_menu = QMenu()
        heatmap_menu.setTitle('heatmap charts menu')
        self.heatmap_table_action = heatmap_menu.addAction('Show in table')
        self.heatmap_table_action.setCheckable(True)
        self.heatmap_table_action.toggled.connect(self._show_heatmap_table)

        self.heatmap_chart_action = QToolButton()
        self.heatmap_chart_action.setIcon(
            QIcon('/home/mario/PycharmProjects/gmx_MMPBSA/GMXMMPBSA/analyzer/style/heatmap_icon.svg'))
        self.heatmap_chart_action.setText('Heatmap Chart')
        self.heatmap_chart_action.setCheckable(True)
        self.heatmap_chart_action.setPopupMode(QToolButton.MenuButtonPopup)
        self.heatmap_chart_action.setContentsMargins(0, 0, 0, 0)
        self.heatmap_chart_action.setMenu(heatmap_menu)
        self.btn_group.addButton(self.heatmap_chart_action, 3)

        self.tb.addWidget(self.heatmap_chart_action)

    def _show_heatmap_table(self, state):
        from GMXMMPBSA.analyzer.plots import Tables
        self.app.treeWidget.clearSelection()
        if state:
            self.setSelected(True)
            if not self.heatmap_table_subw:
                self.heatmap_table_subw = Tables(self.heatmap_plot_data, self.heatmap_table_action)
                self.app.mdi.addSubWindow(self.heatmap_table_subw)
            self.heatmap_table_subw.show()
        elif self.heatmap_table_subw:
            self.app.mdi.activatePreviousSubWindow()
            self.heatmap_table_subw.close()

    def _define_vis_btn(self):
        heatmap_menu = QMenu()
        heatmap_menu.setTitle('Visualization menu')
        # self.heatmap_table_action = heatmap_menu.addAction('Show in text')
        # self.heatmap_table_action.setCheckable(True)
        # self.heatmap_table_action.toggled.connect(self._show_heatmap_table)

        self.vis_action = QToolButton()
        self.vis_action.setIcon(QIcon('/home/mario/PycharmProjects/gmx_MMPBSA/GMXMMPBSA/analyzer/style/molecule.svg'))
        self.vis_action.setText('Visualization')
        self.vis_action.setCheckable(True)
        self.vis_action.setPopupMode(QToolButton.MenuButtonPopup)
        self.vis_action.setContentsMargins(0, 0, 0, 0)
        # self.vis_action.setMenu(heatmap_menu)
        self.btn_group.addButton(self.vis_action, 4)

        self.tb.addWidget(self.vis_action)

    def _define_option_button(self):
        options_menu = QMenu()
        options_menu.setTitle('System Options')
        self.output_action = options_menu.addAction('Show Output file')
        self.output_action.setCheckable(True)
        self.output_action.toggled.connect(self._show_output_file)
        if self.app.systems[self.system_index]['namespace'].INFO['decomp_output_file']:
            self.decomp_output_action = options_menu.addAction('Show Decomp Output file')
            self.decomp_output_action.setCheckable(True)
            self.decomp_output_action.toggled.connect(self._show_decomp_output_file)

        self.options_button = QToolButton()
        self.options_button.setIcon(QIcon('/home/mario/PycharmProjects/PyQtRibbon/error_checker.png'))
        self.options_button.setText('Options')
        self.options_button.setPopupMode(QToolButton.InstantPopup)
        self.options_button.setContentsMargins(0, 0, 0, 0)
        self.options_button.setMenu(options_menu)

    def _show_output_file(self, state):
        from GMXMMPBSA.analyzer.plots import OutputFiles
        self.app.treeWidget.clearSelection()
        if state:
            self.setSelected(True)
            if not self.output_file_subw:
                self.output_file_subw = OutputFiles(
                    self.app.systems[self.system_index]['namespace'].INFO['output_file'],
                    self.output_action)
                self.app.mdi.addSubWindow(self.output_file_subw)
            self.output_file_subw.show()
        elif self.output_file_subw:
            self.app.mdi.activatePreviousSubWindow()
            self.output_file_subw.close()

    def _show_decomp_output_file(self, state):
        from GMXMMPBSA.analyzer.plots import OutputFiles
        self.app.treeWidget.clearSelection()
        if state:
            self.setSelected(True)
            if not self.decomp_output_file_subw:
                self.decomp_output_file_subw = OutputFiles(
                    self.app.systems[self.system_index]['namespace'].INFO['decomp_output_file'],
                    self.decomp_output_action)
                self.app.mdi.addSubWindow(self.decomp_output_file_subw)
            self.decomp_output_file_subw.show()
        elif self.decomp_output_file_subw:
            self.app.mdi.activatePreviousSubWindow()
            self.decomp_output_file_subw.close()

    def fn_mark_all(self, state):
        if state == Qt.PartiallyChecked:
            pass
        elif state == Qt.Checked:
            for x in self.btn_group.buttons():
                x.setChecked(True)
        else:
            for x in self.btn_group.buttons():
                x.setChecked(False)

    def fn_btn_group(self, btn, checked):
        all_checked = all(x.isChecked() for x in self.btn_group.buttons())
        all_unchecked = not any(x.isChecked() for x in self.btn_group.buttons())
        if all_checked:
            self.mark_all.setCheckState(Qt.Checked)
        elif all_unchecked:
            self.mark_all.setCheckState(Qt.Unchecked)
        else:
            self.mark_all.setCheckState(Qt.PartiallyChecked)
        if self.btn_group.id(btn) == 1:
            self.plotting_line(checked)
        elif self.btn_group.id(btn) == 2:
            self.plotting_bar(checked)
        elif self.btn_group.id(btn) == 3:
            self.plotting_heatmap(checked)
        elif self.btn_group.id(btn) == 4:
            self.visualizing(checked)

    def plotting_line(self, state):
        from GMXMMPBSA.analyzer.plots import LineChart
        self.app.treeWidget.clearSelection()

        options = {'general_options': self.app.systems[self.system_index]['chart_options']['general_options'],
                   'line_options': self.app.systems[self.system_index]['chart_options']['line_options'],
                   'chart_title': self.chart_title, 'chart_subtitle': self.chart_subtitle}

        if state:
            self.setSelected(True)
            if not self.lp_subw or self.frange != self.lp_subw.frange or self.line_change:
                self.lp_subw = LineChart(self.line_plot_data, self.line_chart_action, data2=self.ie_plot_data,
                                         options=options)
                # darkgrid, whitegrid, dark, white, ticks
                self.lp_subw.frange = self.frange  # set the frange
                self.line_change = False  # make False again
                self.app.mdi.addSubWindow(self.lp_subw)
            self.lp_subw.show()
        elif self.lp_subw:
            self.app.mdi.activatePreviousSubWindow()
            self.lp_subw.close()

    def plotting_bar(self, state):
        from GMXMMPBSA.analyzer.plots import BarChart
        self.app.treeWidget.clearSelection()
        options = {'general_options': self.app.systems[self.system_index]['chart_options']['general_options'],
                   'bar_options': self.app.systems[self.system_index]['chart_options']['bar_options'],
                   'chart_title': self.chart_title, 'chart_subtitle': self.chart_subtitle}
        if 'groups' in self.properties:
            options['groups'] = self.properties['groups']
        if 'scalable' in self.properties:
            options['scalable'] = self.properties['scalable']

        if state:
            self.setSelected(True)
            if not self.bp_subw or self.frange != self.bp_subw.frange or self.bar_change:
                self.bp_subw = BarChart(self.bar_plot_data, self.bar_chart_action, options=options)
                self.bp_subw.frange = self.frange
                self.bar_change = False # make False again
                self.app.mdi.addSubWindow(self.bp_subw)
            self.bp_subw.show()
        elif self.bp_subw:
            self.app.mdi.activatePreviousSubWindow()
            self.bp_subw.close()

    def plotting_heatmap(self, state):
        from GMXMMPBSA.analyzer.plots import HeatmapChart
        self.app.treeWidget.clearSelection()
        options = {'general_options': self.app.systems[self.system_index]['chart_options']['general_options'],
                   'heatmap_options': self.app.systems[self.system_index]['chart_options']['heatmap_options'],
                   'chart_title': self.chart_title, 'chart_subtitle': self.chart_subtitle}
        if state:
            self.setSelected(True)
            if not self.hmp_subw or self.frange != self.hmp_subw.frange or self.heatmap_change:
                self.pymol_data_change = True  # To don't get to save per-residue data in the pdb
                self.hmp_subw = HeatmapChart(self.heatmap_plot_data, self.heatmap_chart_action, options=options)
                self.hmp_subw.frange = self.frange
                self.heatmap_change = False # make False again
                self.app.mdi.addSubWindow(self.hmp_subw)
            self.hmp_subw.show()
        elif self.hmp_subw:
            self.app.mdi.activatePreviousSubWindow()
            self.hmp_subw.close()

    def visualizing(self, checked):
        self.app.treeWidget.clearSelection()
        import os
        if checked:
            self.setSelected(True)
            pymol_path = [os.path.join(path, 'pymol') for path in os.environ["PATH"].split(os.pathsep)
                          if os.path.exists(os.path.join(path, 'pymol')) and
                          os.access(os.path.join(path, 'pymol'), os.X_OK)]
            if not pymol_path:
                QMessageBox.critical(self, 'PyMOL not found!', 'PyMOL not found!. Make sure PyMOL is in the '
                                                               'PATH.', QMessageBox.Ok)
                self.vis_action.setChecked(False)
                return
            else:
                pymol = pymol_path[0]

            if not self.pymol_process:
                self.pymol_process = QProcess()
            elif self.pymol_process.state() == QProcess.Running:
                QMessageBox.critical(self.app, 'This PyMOL instance already running!',
                                     'This PyMOL instance already running! Please, close it to open a new PyMOL '
                                     'instance', QMessageBox.Ok)
                return

            if self.pymol_data_change or not self.bfactor_pml:
                self.bfactor_pml = self._e2pdb()

            self.pymol_process.start(pymol, [self.bfactor_pml.as_posix()])
            self.pymol_process.finished.connect(lambda: self.vis_action.setChecked(False))
            self.pymol_data_change = False
        elif self.pymol_process.state() == QProcess.Running:
            self.pymol_process.kill()
            self.pymol_process.waitForFinished(3000)

    def _e2pdb(self):
        com_pdb = self.app.systems[self.system_index]['namespace'].INFO['COM_PDB']
        bfactor_pml = self.app.systems[self.system_index]['path'].parent.joinpath('bfactor.pml')
        output_path = self.app.systems[self.system_index]['path'].parent.parent.joinpath(
            f"{self.app.systems[self.system_index]['name']}_energy2bfactor.pdb")
        qpd = QProgressDialog('Generate modified pdb and open it in PyMOL', 'Abort', 0, 2, self.app)
        qpd.setWindowModality(Qt.WindowModal)
        qpd.setMinimumDuration(1500)

        for i in range(2):
            qpd.setValue(i)
            if qpd.wasCanceled():
                break
            if i == 0:
                com_pdb_str = com2str(com_pdb)
                res_dict = self.bar_plot_data.aggregate(["mean"]).iloc[0].to_dict()
                for res in com_pdb_str.residues:
                    res_notation = f'{res.chain}:{res.name}:{res.number}'
                    if res.insertion_code:
                        res_notation += res.insertion_code

                    res_energy = res_dict[res_notation] if res_notation in res_dict else 0.00
                    for at in res.atoms:
                        at.bfactor = res_energy
                com_pdb_str.save(output_path.as_posix(), 'pdb', True, renumber=False)
                energy2pdb_pml(res_dict, bfactor_pml, output_path)
        qpd.setValue(2)

        return bfactor_pml

    def setup_buttons(self):
        if not self.buttons:
            return
        for b in self.charts_action:
            if b not in self.buttons:
                self.tb.addWidget(SpacerItem())
            else:
                self.charts_action[b]()
        if len(self.buttons) > 1 and -1 not in self.buttons:
            self.tb.addWidget(self.mark_all)
        if -1 in self.buttons:
            self._define_option_button()
            self.tb.addWidget(self.options_button)

        return self.tb

    def setup_data(self, frange, iec2frames=0):
        if self.data is None:
            return
        if self.frange == frange:
            return
        self.frange = frange
        if self.level == 0:
            self.line_plot_data = self.data.loc[frange[0]:frange[1]:frange[2]]
            if self.item_type == 'ie':
                tempserie = self.line_plot_data[-iec2frames:]
                self.ie_plot_data = pd.concat([tempserie, pd.Series([self.iec2_data['sigma']] * iec2frames,
                                                                    index=tempserie.index, name='sigma')], axis=1)
        elif self.level == 1:
            self.bar_plot_data = self.data.loc[frange[0]:frange[1]:frange[2]]
            # IMPORTANT: can be used in nmode
        elif self.level == 2:
            tempdf = self.data.loc[frange[0]:frange[1]:frange[2], self.data.columns.get_level_values(1) == 'tot']
            self.bar_plot_data = tempdf.droplevel(level=1, axis=1)
            self.line_plot_data = self.bar_plot_data.sum(axis=1)
            self.heatmap_plot_data = self.bar_plot_data.transpose(copy=True)
            del tempdf
        elif self.level == 3:
            # Select only the "tot" column, remove the level, change first level of comlumn to rows and remove the mean
            # index
            tempdf = self.data.loc[frange[0]:frange[1]:frange[2], self.data.columns.get_level_values(2) == 'tot']
            self.heatmap_plot_data = tempdf.aggregate(["mean"]).droplevel(level=2, axis=1).stack().droplevel(level=0)
            self.bar_plot_data = tempdf.sum(axis=1, level=0)
            self.line_plot_data = self.bar_plot_data.sum(axis=1)
            del tempdf


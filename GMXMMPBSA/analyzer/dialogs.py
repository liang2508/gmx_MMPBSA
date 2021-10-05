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

from PyQt5.QtWidgets import (QDialog, QSpinBox, QLabel, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QCheckBox,
                             QGroupBox, QButtonGroup, QGridLayout, QTreeWidget, QTreeWidgetItem, QRadioButton,
                             QTreeWidgetItemIterator, QHeaderView, QProgressBar, QStatusBar, QMessageBox, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from queue import Queue, Empty
from GMXMMPBSA import API
from pathlib import Path
from GMXMMPBSA.analyzer.utils import worker, ncpu
from GMXMMPBSA.analyzer.chartsettings import ChartSettings



class InitDialog(QDialog):
    def __init__(self,parent=None):
        super(InitDialog, self).__init__(parent)
        self.parent = parent
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle('Initialization gmx_MMPBSA_ana')
        self.curr_progress = 0
        self.data = []
        self.chart_settings = ChartSettings()

        self.processing_label = QLabel()

        self.show_decomp_btn = QCheckBox('Show decomposition data')
        self.show_decomp_btn.setToolTip('Defines whether the decomposition graphs will be available during the '
                                        'session. Useful when defining a system for correlation analysis.')
        self.show_decomp_btn.setChecked(True)
        self.remove_empty_charts_btn = QCheckBox('Remove empty charts')
        self.remove_empty_charts_btn.setToolTip('Does not show charts in which all trajectory is zero')
        self.remove_empty_charts_btn.setChecked(True)
        self.remove_empty_charts_btn.clicked.connect(self.show_warn)

        self.remove_empty_terms_btn = QCheckBox('Remove empty terms')
        self.remove_empty_terms_btn.setToolTip('Does not show null terms in graphics')
        self.remove_empty_terms_btn.setChecked(True)
        self.remove_empty_terms_btn.clicked.connect(self.show_warn)

        self.check_l = QHBoxLayout()
        self.check_l.addWidget(self.show_decomp_btn)
        self.check_l.addWidget(self.remove_empty_charts_btn)
        self.check_l.addWidget(self.remove_empty_terms_btn)
        self.warn_label_empty = QLabel('Note: Remove empty charts and terms options will hide the charts and empty '
                                       'terms respectively. This does not change your results at all, it only changes '
                                       'the representation of the data.')
        self.warn_label_empty.setStyleSheet("border:3px solid green")
        self.warn_label_empty.setWordWrap(True)

        self.corr_sys_btn = QCheckBox('Calculate correlation between systems')
        self.corr_sys_btn.setToolTip('Make correlation between systems. Only works if you define more than 3 systems')
        self.corr_sys_btn.setChecked(False)

        # mutants correlation
        self.corr_mut_btn = QCheckBox('Calculate correlation between mutants')
        self.corr_mut_btn.setToolTip('Make correlation between mutants systems. Only works if you define more than 3 '
                                 'mutants')
        self.corr_mut_btn.setChecked(False)

        self.corr_group = QGroupBox('Correlation')
        self.corr_group_layout = QGridLayout(self.corr_group)
        self.corr_group_layout.addWidget(self.corr_sys_btn, 0, 0)
        self.corr_group_layout.addWidget(self.corr_mut_btn, 0, 1)

        self.delta_btn = QCheckBox('delta')
        self.delta_btn.setChecked(True)
        self.delta_btn.setEnabled(False)
        self.com_btn = QCheckBox('complex')
        self.com_btn.clicked.connect(self.show_warn)
        self.rec_btn = QCheckBox('receptor')
        self.rec_btn.clicked.connect(self.show_warn)
        self.lig_btn = QCheckBox('ligand')
        self.lig_btn.clicked.connect(self.show_warn)
        self.warn_label_big = QLabel('Warning: This can generate a huge amount of graphics which can crash the '
                                     'application!. So far, we have not registered this issue, but be cautious')
        self.warn_label_big.setStyleSheet("border:3px solid orange")
        self.warn_label_big.setWordWrap(True)
        self.warn_label_big.hide()

        self.comp_group = QGroupBox('Computation of Components Charts')
        self.comp_group_layout = QGridLayout(self.comp_group)
        self.comp_group_layout.addWidget(self.delta_btn, 0, 0)
        self.comp_group_layout.addWidget(self.com_btn, 0, 1)
        self.comp_group_layout.addWidget(self.rec_btn, 0, 2)
        self.comp_group_layout.addWidget(self.lig_btn, 0, 3)
        self.comp_group_layout.addWidget(self.warn_label_big, 1, 0, 1, 4)

        self.sys_group = QGroupBox('Systems options')
        self.sys_group_layout = QVBoxLayout(self.sys_group)
        self.sys_group_layout.addLayout(self.check_l)
        self.sys_group_layout.addWidget(self.warn_label_empty)
        self.sys_group_layout.addWidget(self.corr_group)
        self.sys_group_layout.addWidget(self.comp_group)

        self.header_item = QTreeWidgetItem(['Folder name', 'Select', 'Name', 'Exp.Ki (nM)', 'Chart Settings', 'Path'])
        self.header_item.setToolTip(0, 'Container')
        self.header_item.setToolTip(1, 'Name')
        self.header_item.setTextAlignment(0, Qt.AlignCenter)
        self.header_item.setTextAlignment(1, Qt.AlignCenter)
        self.header_item.setTextAlignment(2, Qt.AlignCenter)
        self.header_item.setTextAlignment(3, Qt.AlignCenter)
        self.header_item.setTextAlignment(4, Qt.AlignCenter)
        self.result_tree = QTreeWidget(self)
        self.result_tree.setHeaderItem(self.header_item)
        self.result_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.result_tree.itemChanged.connect(self.update_item_info)
        self.pb = QProgressBar()
        # self.pb.setRange(0, 0)
        # self.save_btn.clicked.connect(self.save)

        self.jobs_label = QLabel('Jobs:')
        self.jobs_label.setToolTip('Defines how many cores of your processor will be used simultaneously to process '
                                   'the selected systems')
        self.jobs_spin = QSpinBox(self)
        self.jobs_spin.setToolTip('Defines how many cores of your processor will be used simultaneously to process '
                                  'the selected systems')
        self.jobs_spin.setRange(1, ncpu-1)
        self.jobs_spin.setValue(ncpu-1)

        self.accept_btn = QPushButton('Accept')
        self.accept_btn.clicked.connect(self.get_data)

        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.parent.close)

        self.btn_layout = QHBoxLayout()
        self.btn_layout.addWidget(self.pb, 10)
        self.btn_layout.addStretch(1)
        self.btn_layout.addWidget(self.jobs_label, 1)
        self.btn_layout.addWidget(self.jobs_spin, 1)
        self.btn_layout.addStretch(1)
        self.btn_layout.addWidget(self.cancel_btn, 2, alignment=Qt.AlignRight)
        self.btn_layout.addWidget(self.accept_btn, 2, alignment=Qt.AlignRight)

        self.statusbar = QStatusBar(self)

        self.content_layout = QVBoxLayout(self)
        self.content_layout.addWidget(self.processing_label)
        self.content_layout.addWidget(self.sys_group)
        self.content_layout.addWidget(self.result_tree)
        self.content_layout.addWidget(self.statusbar)
        self.content_layout.addLayout(self.btn_layout)

        self.worker = worker()
        self.worker.job_finished.connect(self.jobfinished)
        self.worker.finished.connect(self.alljobs_finished)


    def show_warn(self):
        if self.com_btn.isChecked() or self.rec_btn.isChecked() or self.lig_btn.isChecked():
            self.warn_label_big.show()
        else:
            self.warn_label_big.hide()

        if self.remove_empty_terms_btn.isChecked() or self.remove_empty_charts_btn.isChecked():
            self.warn_label_empty.show()
        else:
            self.warn_label_empty.hide()

    def update_item_info(self, item: QTreeWidgetItem, col):
        if item.text(0) == 'All':
            return
        # path = item.info[1]
        # basename = item.text(2)
        # exp_ki = float(item.text(3))
        # custom_sett = float(item.checkState(4))
        # item.info = [basename, path, exp_ki, custom_sett]

    def get_files_info(self, info_files):
        self.nfiles = len(info_files)
        self.f_item = QTreeWidgetItem(['All'])
        self.f_item.setCheckState(1, Qt.Checked)
        self.f_item.info = None
        self.f_item.setFlags(self.f_item.flags() | Qt.ItemIsAutoTristate)
        self.result_tree.addTopLevelItem(self.f_item)

        self.processing_label.setText(f'Processing {self.nfiles} systems...')

        files_list = info_files
        names = []
        for c, fname in enumerate(files_list, start=1):
            basename = None
            exp_ki = None
            mut_only = False
            mutant = None
            with open(fname) as fi:
                for line in fi:
                    if line.startswith("INPUT['sys_name']"):
                        basename = str(line.split()[2]).strip('"\'')
                        if basename in names:
                            while basename in names:
                                basename = f"{basename}-{names.count(basename) + 1}"
                            names.append(basename)
                    if line.startswith("INPUT['exp_ki']"):
                        exp_ki = float(line.split()[2])
                    if line.startswith("INPUT['mutant_only']"):
                        mut_only = int(line.split()[2])
                    if line.startswith("mut_str"):
                        mutant = line.split()[2].replace("'", "")
            # check for custom settings
            custom_settings = fname.parent.joinpath('settings.json').exists()
            # custom_settings = True
            cb = QComboBox()
            cb.addItem('Default')
            if custom_settings:
                cb.addItem('Custom')
                cb.setCurrentIndex(1)

            if not basename:
                basename = f'System-{c}'
            if not exp_ki:
                exp_ki = 0.0

            item = QTreeWidgetItem([f'{fname.parent.name}', '', f'{basename}', '', '', f'{fname.parent.absolute()}'])
            item.setFlags(item.flags() | Qt.ItemIsAutoTristate)

            self._set_item_properties(item, custom_settings=True)
            self.f_item.addChild(item)

            if not mut_only:
                witem = QTreeWidgetItem(['', '', 'wild type', f'{exp_ki}', '', ''])
                # witem.info = [basename, Path(fname)]
                self._set_item_properties(witem)
                item.addChild(witem)

            if mutant:
                print(mutant)
                mitem = QTreeWidgetItem(['', '', f'{mutant}', f'{exp_ki}', '', ''])
                # mitem.info = [basename, Path(fname)]
                self._set_item_properties(mitem)
                item.addChild(mitem)

            item.info = [basename, Path(fname), custom_settings]

            item.setExpanded(True)
            self.result_tree.setItemWidget(item, 4, cb)
        self.f_item.setExpanded(True)

    def _set_item_properties(self, item: QTreeWidgetItem, custom_settings=False):
        # if custom_settings:
        #     item.setText(4, 'Custom')
        #     item.setCheckState(4, Qt.Checked)
        #     print('fffffffffffffffffFFFF')
        item.setCheckState(1, Qt.Checked)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        item.setTextAlignment(2, Qt.AlignCenter)
        item.setTextAlignment(3, Qt.AlignRight)
        item.setTextAlignment(4, Qt.AlignCenter)

    def get_data(self):

        self.pb.setValue(0)
        queue = Queue()
        self.result_queue = Queue()
        self.systems_list = []
        self.options = {'corr_sys': self.corr_sys_btn.isChecked(),
                        'corr_mut': self.corr_mut_btn.isChecked(),
                        'decomposition': self.show_decomp_btn.isChecked(),
                        'components': [x.text() for x in [self.com_btn, self.rec_btn, self.lig_btn] if x.isChecked()],
                        'remove_empty_charts': self.remove_empty_charts_btn.isChecked(),
                        'remove_empty_terms':self.remove_empty_terms_btn.isChecked(),
                        # 'default_chart_options': self.default_settings_btn.isChecked()
                        }
        counter = 0
        for c in range(self.f_item.childCount()):
            child = self.f_item.child(c)
            if not child.checkState(1):
                continue
            t = {}
            if child.childCount():
                for c1 in range(child.childCount()):
                    if child.child(c1).checkState(1) == Qt.Checked:
                        if child.child(c1).text(2) == 'wild type':
                            t['wt'] = float(child.child(c1).text(3))
                        else:
                            t['mut'] = float(child.child(c1).text(3))
            if self.result_tree.itemWidget(child, 4).currentText() == 'Default':
                settings = self.chart_settings.read_config()
            else:
                settings = self.chart_settings.read_config(child.info[1].parent)
            readable_sett = self.chart_settings.get_settings(settings)
            child.info += [t, readable_sett, settings]
            queue.put(child.info)
            counter += 1
        if not counter:
            QMessageBox.critical(self, 'Error processing systems', 'You must select at least one system.',
                                 QMessageBox.Ok)
            return
        self.pb.setRange(0, counter)
        self.worker.define_dat(API.load_gmxmmpbsa_info, queue, self.result_queue, self.jobs_spin.value())
        self.worker.start()

    def jobfinished(self):
        self.curr_progress += 1
        self.pb.setValue(self.curr_progress)

    def alljobs_finished(self):
        self.worker.deleteLater()
        self.parent.process_data(self.result_queue, self.options)


class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super(ExportDialog, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle('Save Energy to b-factor')
        self.current_frame_s = QSpinBox()
        self.current_frame_l = QLabel('Frame:')

        self.output_label = QLabel('Output:')
        self.output_text = QLineEdit('complex_e2bfactor')
        self.output_text.setPlaceholderText('complex_e2bfactor')
        self.save_btn = QPushButton('Save')
        self.save_btn.clicked.connect(self.save)
        self.close_btn = QPushButton('Close')
        self.close_btn.clicked.connect(self.close)

        self.out_layout = QHBoxLayout()
        self.out_layout.addWidget(self.output_label)
        self.out_layout.addWidget(self.output_text)

        self.frame_layout = QHBoxLayout()
        self.frame_layout.addWidget(self.current_frame_l)
        self.frame_layout.addWidget(self.current_frame_s)
        # self.frame_layout.addWidget(self.interval_l, alignment=Qt.AlignRight)
        # self.frame_layout.addWidget(self.interval_s)

        self.btn_layout = QHBoxLayout()
        self.btn_layout.addStretch(1)
        self.btn_layout.addWidget(self.save_btn, alignment=Qt.AlignRight)
        self.btn_layout.addWidget(self.close_btn, alignment=Qt.AlignRight)

        self.layout = QVBoxLayout(self)
        self.layout.addLayout(self.out_layout)
        # self.layout.addWidget(self.location_btn)
        self.layout.addLayout(self.frame_layout)
        self.layout.addLayout(self.btn_layout)

        self.getdata()

    @pyqtSlot()
    def save(self):
        self.ntraj.Outtraj('_temp_.pdb', frames=str(self.current_frame_s.value()),
                           filetype='pdb')
        self.ntraj.Run('cpptraj.out')
        pdb = PDB()
        pdb.parse('_temp_.pdb')
        with open(str(self.output_text.text()) + '.pdb', 'w') as pdbout:
            for atm in pdb.allAtoms:
                if atm['id'] == 'TER':
                    pdbout.write(pdb.getOutLine(atm, ter=True))
                else:
                    if atm['resnum'] in self.parent.decomp and atm['resname'] in std_aa:
                        atm['b_factor'] = self.parent.decomp[atm['resnum']]
                    else:
                        atm['b_factor'] = 0.0
                    pdbout.write(pdb.getOutLine(atm, ter=False))
        # os.remove('_temp_.pdb')
        self.parent.statusbar.showMessage('Saving {} file... Done'.format(self.output_text.text() + '.pdb'))
        self.close()


class ExportDialogCSV(QDialog):
    def __init__(self, parent=None):
        super(ExportDialogCSV, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle('Export Energy to CSV')

        self.output_label = QLabel('Output:')
        self.output_text = QLineEdit('TOTAL_ENERGY')
        self.output_text.setPlaceholderText('TOTAL_ENERGY')
        self.save_btn = QPushButton('Save')
        self.save_btn.clicked.connect(self.save)
        self.close_btn = QPushButton('Close')
        self.close_btn.clicked.connect(self.close)

        self.out_layout = QHBoxLayout()
        self.out_layout.addWidget(self.output_label)
        self.out_layout.addWidget(self.output_text)

        self.btn_layout = QHBoxLayout()
        self.btn_layout.addStretch(1)
        self.btn_layout.addWidget(self.save_btn, alignment=Qt.AlignRight)
        self.btn_layout.addWidget(self.close_btn, alignment=Qt.AlignRight)

        self.layout = QVBoxLayout(self)
        self.layout.addLayout(self.out_layout)
        self.layout.addLayout(self.btn_layout)

    @pyqtSlot()
    def save(self):
        with open(str(self.output_text.text()) + '.csv', 'w') as out_file:
            if self.parent.gb_data:
                out_file.write('GB data\n')
                out_file.write(','.join(['FRAME'] + [x[0].upper() for x in self.parent.gb_data]) + '\n')
                self.parent.writeData(out_file, self.parent.gb_data)
            if self.parent.mut_gb_data:
                out_file.write('Mutant GB data\n')
                out_file.write(','.join(['FRAME'] + [x[0].upper() for x in self.parent.mut_gb_data]) + '\n')
                self.parent.writeData(out_file, self.parent.mut_gb_data)
            if self.parent.pb_data:
                out_file.write('PB data\n')
                out_file.write(','.join(['FRAME'] + [x[0].upper() for x in self.parent.pb_data]) + '\n')
                self.parent.writeData(out_file, self.parent.pb_data)
            if self.parent.mut_pb_data:
                out_file.write('Mutant PB data\n')
                out_file.write(','.join(['FRAME'] + [x[0].upper() for x in self.parent.mut_pb_data]) + '\n')
                self.parent.writeData(out_file, self.parent.mut_pb_data)
        self.parent.statusbar.showMessage('Exporting PB/GB energy to csv file... Done.')
        self.close()
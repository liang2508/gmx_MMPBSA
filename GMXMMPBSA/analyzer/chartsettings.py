import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from matplotlib._cm import datad
from pathlib import Path
import json


class ChartSettings:
    params = {
        'type': 'group', 'enabled': True, 'expanded': True, 'name': 'params', 'value': None, 'default': None,
        'children': {
            'General': {
                'type': 'group', 'enabled': True, 'expanded': True, 'name': 'General', 'value': None, 'default':
                    None,
                'children': {
                    'theme': {
                        'type': 'list', 'enabled': True, 'expanded': True, 'name': 'theme', 'value': 'darkgrid',
                        'values': ['darkgrid', 'whitegrid', 'dark', 'white', 'ticks'],
                        'limits': ['darkgrid', 'whitegrid', 'dark', 'white', 'ticks'], 'default': 'darkgrid',
                        'tip': 'Esto es un tip'},
                    'toolbar': {'type': 'bool', 'enabled': True, 'expanded': True, 'name': 'toolbar',
                                'value': False, 'default': False},
                    'save-figure': {
                        'type': 'list', 'enabled': True, 'expanded': True, 'name': 'save-figure', 'value': 'svg',
                        'values': ['eps', 'jpg', 'jpeg', 'pdf', 'pgf', 'png', 'ps', 'raw', 'rgba', 'svg', 'svgz', 'tif',
                                   'tiff'],
                        'default': 'svg', 'tip': 'Esto es un tip'},
                    'dpi': {
                        'type': 'group', 'enabled': True, 'expanded': True, 'name': 'dpi', 'value': None, 'default':
                            None,
                        'children': {
                            'plot': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'plot',
                                     'value': 100, 'step': 10, 'accelerated': True, 'limits': (50, 300),
                                     'default': 100},
                            'save-color': {'type': 'int', 'enabled': True, 'expanded': True,
                                           'name': 'save-color', 'value': 300, 'step': 10,
                                           'accelerated': True, 'limits': (50, 1200), 'default': 300},
                            # 'save-grayscale': {'type': 'int', 'enabled': True, 'expanded': True,
                            #                        'name': 'save-dpi-grayscale', 'value': 600, 'step': 10,
                            #                        'accelerated': True, 'limits': (50, 1200), 'default': 600}
                        }},
                    'fontsize': {
                        'type': 'group', 'enabled': True, 'expanded': True, 'name': 'fontsize', 'value': None,
                        'default': None,
                        'children': {
                            'x-ticks': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'x-ticks',
                                        'value': 10, 'default': 10},
                            'y-ticks': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'y-ticks',
                                        'value': 10, 'default': 10},
                            'x-label': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'x-label',
                                        'value': 12, 'default': 12},
                            'y-label': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'y-label',
                                        'value': 12, 'default': 12},
                            'title': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'title',
                                      'value': 14, 'default': 14},
                            'suptitle': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'suptitle',
                                         'value': 12, 'default': 12},
                            'legend': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'legend',
                                       'value': 9, 'default': 9},
                            'colorbar-ticks': {'type': 'int', 'enabled': True, 'expanded': True,
                                               'name': 'colorbar-ticks', 'value': 9, 'default': 9},
                            'colorbar-label': {'type': 'int', 'enabled': True, 'expanded': True,
                                               'name': 'colorbar-label', 'value': 11, 'default': 11},
                            'annotation': {'type': 'int', 'enabled': True, 'expanded': True,
                                           'name': 'annotation', 'value': 8, 'default': 8}
                        }}}},
            'Line Plot': {
                'type': 'group', 'enabled': True, 'expanded': True, 'name': 'Line Plot', 'value': None, 'default':
                    None,
                'children': {
                    'line-width': {'type': 'float', 'enabled': True, 'expanded': True, 'name': 'line-width',
                                   'value': 0.7, 'step': 0.1, 'limits': (0.1, 1.5), 'accelerated': True,
                                   'default': 0.7},
                    'line-color': {'type': 'color', 'enabled': True, 'expanded': True, 'name': 'line-color',
                                   'value': [0, 0, 0, 255], 'default': [0, 0, 0, 255]},
                    'axes': {
                        'type': 'group', 'enabled': True, 'expanded': True, 'name': 'axes', 'value': None,
                        'default': None,
                        'children': {
                            'num-xticks': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'num-xticks',
                                           'value': 10, 'default': 10},
                            'num-yticks': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'num-yticks',
                                           'value': 10, 'default': 10},
                            'x-rotation': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'x-rotation',
                                           'value': 0, 'step': 1, 'limits': (-90, 90), 'accelerated': True,
                                           'default': 0},
                            'y-rotation': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'y-rotation',
                                           'value': 0, 'step': 1, 'limits': (-90, 90), 'accelerated': True,
                                           'default': 0}
                        }},
                    'rolling': {
                        'type': 'group', 'enabled': True, 'expanded': True, 'name': 'Rolling', 'value': None,
                        'default': None,
                        'children': {
                            'color': {'type': 'color', 'enabled': True, 'expanded': True, 'name': 'color',
                                      'value': [255, 0, 0, 255], 'default': [255, 0, 0, 255]},
                            'width': {'type': 'float', 'enabled': True, 'expanded': True, 'name': 'width',
                                      'value': 0.8, 'step': 0.1, 'default': 0.8},
                            'window': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'window',
                                       'value': 50, 'step': 1, 'default': 50}}},
                    'Interaction Entropy': {
                        'type': 'group', 'enabled': True, 'expanded': True, 'name': 'Interaction Entropy',
                        'value': None, 'default': None,
                        'children': {
                            'ie-color': {'type': 'color', 'enabled': True, 'expanded': True, 'name': 'ie-color',
                                         'value': [0, 0, 255, 255], 'default': [0, 0, 255, 255]},
                            'sigma-color': {
                                'type': 'group', 'enabled': True, 'expanded': True, 'name': 'sigma-color',
                                'value': None, 'default': None,
                                'children': {
                                    'reliable': {'type': 'color', 'enabled': True, 'expanded': True, 'name': 'reliable',
                                                 'value': [0, 255, 0, 255], 'default': [0, 255, 0, 255]},
                                    'non-reliable': {'type': 'color', 'enabled': True, 'expanded': True,
                                                     'name': 'non-reliable', 'value': [255, 0, 0, 255],
                                                     'default': [255, 0, 0, 255]}}},
                            'bar-plot': {
                                'type': 'group', 'enabled': True, 'expanded': True, 'name': 'bar-plot', 'value': None,
                                'default': None,
                                'children': {
                                    'bar-label-fontsize': {'type': 'int', 'enabled': True, 'expanded': True,
                                                           'name': 'bar-label-fontsize', 'value': 8, 'default': 8},
                                    'bar-label-padding': {'type': 'int', 'enabled': True, 'expanded': True,
                                                          'name': 'bar-label-padding', 'value': 4, 'default': 4},
                                    'axes-fontsize': {'type': 'int', 'enabled': True, 'expanded': True,
                                                      'name': 'axes-fontsize', 'value': 8, 'default': 8},
                                    'width': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'width',
                                              'value': 30, 'siPrefix': True, 'suffix': '%', 'default': 30},
                                    'height': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'height',
                                               'value': 35, 'siPrefix': True, 'suffix': '%', 'default': 35}}},
                            'bbox_to_anchor': {
                                'type': 'group', 'enabled': True, 'expanded': True, 'name': 'bbox_to_anchor',
                                'value': None, 'default': None,
                                'children': {
                                    'x-pos': {'type': 'float', 'enabled': True, 'expanded': True, 'name': 'x-pos',
                                              'value': 0.4, 'step': 0.01, 'limits': (0, 1), 'default': 0.4},
                                    'y-pos': {'type': 'float', 'enabled': True, 'expanded': True, 'name': 'y-pos',
                                              'value': 0.15, 'step': 0.01, 'limits': (0, 1), 'default': 0.15}}}}},
                    'figure': {
                        'type': 'group', 'enabled': True, 'expanded': True, 'name': 'figure', 'value': None,
                        'default': None,
                        'children': {
                            'width': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'width', 'value': 8,
                                      'default': 8},
                            'height': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'height',
                                       'value': 4, 'default': 4}}}}},
            'Bar Plot': {
                'type': 'group', 'enabled': True, 'expanded': True, 'name': 'Bar Plot', 'value': None, 'default': None,
                'children': {
                    'orientation': {'type': 'list', 'enabled': True, 'expanded': True, 'name': 'orientation',
                                    'value': 'v', 'values': ('v', 'h'), 'default': 'v'},
                    'use-palette': {'type': 'bool', 'enabled': True, 'expanded': True, 'name': 'use-palette',
                                    'value': True, 'default': True},
                    'palette': {'type': 'list', 'enabled': True, 'expanded': True, 'name': 'palette',
                                'value': 'husl', 'values': ['husl', 'hls', 'deep', 'muted', 'bright', 'pastel', 'dark',
                                                            'colorblind', '---0',
                                                            'Pastel1', 'Pastel2', 'Paired', 'Accent', 'Dark2', 'Set1',
                                                            'Set2', 'Set3', 'tab10', 'tab20', 'tab20b', 'tab20c'],
                                'default': 'husl'},
                    'color': {'type': 'color', 'enabled': True, 'expanded': True, 'name': 'color',
                              'value': [44, 105, 176, 255], 'default': [44, 105, 176, 255]},
                    'subplot-components': {'type': 'bool', 'enabled': True, 'expanded': True,
                                           'name': 'subplot-components', 'value': True, 'default': True},
                    'scale-big-values': {'type': 'bool', 'enabled': True, 'expanded': True,
                                         'name': 'scale-big-values', 'value': True, 'default': True},
                    'error-line': {'type': 'group', 'enabled': True, 'expanded': True, 'name': 'error-line',
                                   'value': None, 'default': None, 'children': {
                            'width': {'type': 'float', 'enabled': True, 'expanded': True, 'name': 'width', 'value': 0.7,
                                      'step': 0.1, 'limits': (0.1, 1.5), 'accelerated': True, 'default': 0.7},
                            'color': {'type': 'color', 'enabled': True, 'expanded': True, 'name': 'color',
                                      'value': [0, 0, 0, 255], 'default': [0, 0, 0, 255]}}},
                    'bar-label': {
                        'type': 'group', 'enabled': True, 'expanded': True, 'name': 'bar-label', 'value': None,
                        'default': None,
                        'children': {
                            'show': {'type': 'bool', 'enabled': True, 'expanded': True, 'name': 'show', 'value': False,
                                     'default': False},
                            'fontsize': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'fontsize',
                                         'value': 8, 'limits': (2, 20), 'default': 8},
                            'padding': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'padding',
                                        'value': 5, 'limits': (0, 50), 'default': 5}
                        }},
                    'axes': {
                        'type': 'group', 'enabled': True, 'expanded': True, 'name': 'axes', 'value': None,
                        'default': None,
                        'children': {
                            'num-yticks': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'num-yticks',
                                           'value': 10, 'default': 10},
                            'x-rotation': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'x-rotation',
                                           'value': 45, 'step': 1, 'limits': (-90, 90),
                                           'accelerated': True, 'default': 45},
                            'y-rotation': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'y-rotation',
                                           'value': 0, 'step': 1, 'limits': (-90, 90),
                                           'accelerated': True, 'default': 0},
                        }},
                    'figure': {
                        'type': 'group', 'enabled': True, 'expanded': True, 'name': 'figure', 'value': None,
                        'default': None,
                        'children': {
                            'width': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'width',
                                      'value': 5, 'default': 5},
                            'height': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'height',
                                       'value': 4, 'default': 4}}}}},
            'Heatmap Plot': {
                'type': 'group', 'enabled': True, 'expanded': True, 'name': 'Heatmap Plot', 'value': None,
                'default': None,
                'children': {
                    'highlight-components': {'type': 'bool', 'enabled': True, 'expanded': True,
                                             'name': 'highlight-components', 'value': True, 'default': True},
                    'legend': {'type': 'bool', 'enabled': True, 'expanded': True, 'name': 'legend', 'value': True,
                               'default': True},
                    'remove-molid': {'type': 'bool', 'enabled': True, 'expanded': True, 'name': 'remove-molid',
                                     'value': True, 'default': True},
                    'receptor-color': {'type': 'color', 'enabled': True, 'expanded': True, 'name': 'receptor-color',
                                       'value': [0, 0, 255, 255], 'default': [0, 0, 255, 255]},
                    'ligand-color': {'type': 'color', 'enabled': True, 'expanded': True, 'name': 'ligand-color',
                                     'value': [0, 255, 0, 255], 'default': [0, 255, 0, 255]},

                    'y-rotation': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'y-rotation',
                                   'value': 0, 'step': 1, 'limits': (-90, 90), 'accelerated': True, 'default': 0},
                    'Per-wise': {
                        'type': 'group', 'enabled': True, 'expanded': True, 'name': 'Per-wise', 'value': None,
                        'default': None,
                        'children': {
                            'palette': {'type': 'list', 'enabled': True, 'expanded': True, 'name': 'palette',
                                        'value': 'seismic', 'values': ['seismic', '---1',
                                                                       'Balance_7', 'Balance_5', 'Curl_7', 'Curl_5',
                                                                       'Delta_7', 'Delta_5', '---2',
                                                                       'ArmyRose_7', 'ArmyRose_5', 'Geyser_7',
                                                                       'Geyser_5', 'Temps_7', 'Temps_5', 'TealRose_7',
                                                                       'TealRose_5', 'Tropic_7', 'Tropic_5', '---3',
                                                                       'BrBG_7', 'BrBG_5', 'PRGn_7', 'PRGn_5', 'PiYG_7',
                                                                       'PiYG_5', 'PuOr_7', 'PuOr_5', 'RdBu_7', 'RdBu_5',
                                                                       'RdGy_7', 'RdGy_5', '---4', '---5',
                                                                       'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm'
                                                                       ], 'default': 'seismic'},
                            'annotation': {'type': 'bool', 'enabled': True, 'expanded': True, 'name': 'annotation',
                                           'value': False, 'default': False},
                            'x-rotation': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'x-rotation',
                                           'value': 90, 'step': 1, 'limits': (-90, 90), 'accelerated': True,
                                           'default': 90}}},
                    'Per-residue': {
                        'type': 'group', 'enabled': True, 'expanded': True, 'name': 'Per-residue', 'value': None,
                        'default': None,
                        'children': {
                            'palette': {'type': 'list', 'enabled': True, 'expanded': True, 'name': 'palette',
                                        'value': 'seismic', 'values': ['seismic', '---1',
                                                                       'Balance_7', 'Balance_5', 'Curl_7', 'Curl_5',
                                                                       'Delta_7', 'Delta_5', '---2',
                                                                       'ArmyRose_7', 'ArmyRose_5', 'Geyser_7',
                                                                       'Geyser_5', 'Temps_7', 'Temps_5', 'TealRose_7',
                                                                       'TealRose_5', 'Tropic_7', 'Tropic_5', '---3',
                                                                       'BrBG_7', 'BrBG_5', 'PRGn_7', 'PRGn_5', 'PiYG_7',
                                                                       'PiYG_5', 'PuOr_7', 'PuOr_5', 'RdBu_7', 'RdBu_5',
                                                                       'RdGy_7', 'RdGy_5', '---4', '---5',
                                                                       'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm'
                                                                       ], 'default': 'seismic'},
                            'num-xticks': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'num-xticks',
                                           'value': 10, 'default': 10},
                            'x-rotation': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'x-rotation',
                                           'value': 0, 'step': 1, 'limits': (-90, 90), 'accelerated': True,
                                           'default': 0}}},
                    'figure': {
                        'type': 'group', 'enabled': True, 'expanded': True, 'name': 'figure', 'value': None,
                        'default': None,
                        'children': {
                            'width-per-residue': {'type': 'int', 'enabled': True, 'expanded': True,
                                                  'name': 'width-per-residue', 'value': 10, 'default': 10},
                            'width-per-wise': {'type': 'int', 'enabled': True, 'expanded': True,
                                               'name': 'width-per-wise', 'value': 8, 'default': 8},
                            'height': {'type': 'int', 'enabled': True, 'expanded': True, 'name': 'height',
                                       'value': 7, 'default': 7}}}}},
            'Visualization': {
                'type': 'group', 'enabled': True, 'expanded': True, 'name': 'Visualization', 'value': None,
                'default': None,
                'children': {
                    'palette': {'type': 'list', 'enabled': True, 'expanded': True, 'name': 'palette',
                                'value': 'auto', 'values': ['auto', '---0', 'seismic', '---1',
                                                            'Balance_7', 'Balance_5', 'Curl_7', 'Curl_5',
                                                            'Delta_7', 'Delta_5', '---2',
                                                            'ArmyRose_7', 'ArmyRose_5', 'Geyser_7',
                                                            'Geyser_5', 'Temps_7', 'Temps_5', 'TealRose_7',
                                                            'TealRose_5', 'Tropic_7', 'Tropic_5', '---3',
                                                            'BrBG_7', 'BrBG_5', 'PRGn_7', 'PRGn_5', 'PiYG_7',
                                                            'PiYG_5', 'PuOr_7', 'PuOr_5', 'RdBu_7', 'RdBu_5',
                                                            'RdGy_7', 'RdGy_5'
                                                            ], 'default': 'auto'},
                }}
        }}

    def __init__(self):
        self.config_folder = Path('~').expanduser().absolute().joinpath('.config', 'gmx_MMPBSA')
        self.config_folder.mkdir(exist_ok=True)
        self.filename = self.config_folder.joinpath('settings.json')

    def write_global_config(self, overwrite=False):
        """

        @param overwrite: Only used to restore the original settings
        """
        if self.filename.exists() and overwrite or not self.filename.exists():
            with open(self.filename, "w") as write_file:
                json.dump(self.params, write_file, indent=4)

    def write_system_config(self, syspath: Path, settings):
        """

        @param syspath: Current system path
        @param settings: settings dict with custom properties
        @return:
        """
        filename = syspath.joinpath('settings.json')
        with open(filename, "w") as write_file:
            json.dump(settings, write_file, indent=4)

    def read_config(self, custom: Path = None):
        """

        @param custom: Custom settings for a system
        @return: settings dict
        """
        if custom:
            with open(custom.joinpath('settings.json')) as read_file:
                config = json.load(read_file)
        elif self.filename.exists():
            with open(self.filename) as read_file:
                config = json.load(read_file)
        else:
            self.write_global_config()
            config = self.params
        return config

    def get_settings(self, settings):
        print(settings)
        settings = settings['children']

        general_options = self._get_2lvl_data(settings['General']['children'])
        line_options = self._get_3lvl_data(settings['Line Plot']['children'])
        bar_options = self._get_2lvl_data(settings['Bar Plot']['children'])
        heatmap_options = self._get_3lvl_data(settings['Heatmap Plot']['children'])

        return {'general_options': general_options, 'line_options': line_options, 'bar_options': bar_options,
                'heatmap_options': heatmap_options}

    @staticmethod
    def _get_3lvl_data(data):
        options = {}
        for k in data:
            if 'children' in data[k]:
                options[k] = {}
                sub_data = data[k]['children']
                for k1 in sub_data:
                    if 'children' in sub_data[k1]:
                        options[k][k1] = {}
                        for k2 in sub_data[k1]['children']:
                            options[k][k1][k2] = sub_data[k1]['children'][k2]['value']
                    else:
                        options[k][k1] = sub_data[k1]['value']
            else:
                options[k] = data[k]['value']
        return options

    @staticmethod
    def _get_2lvl_data(data):
        return {
            k: {
                k1: data[k]['children'][k1]['value']
                for k1 in data[k]['children']
            }
            if 'children' in data[k]
            else data[k]['value']
            for k in data
        }


class Palette(LinearSegmentedColormap):
    def __init__(self, name, clist, type):
        super(Palette, self).__init__(name, clist)
        self.name = name
        self.colors = [list(map(lambda x: x / 255, color)) for color in clist]
        self.type = type
        self.colormap = self.from_list(self.name, self.colors)


color_store = {
    'cartoon': {
        'sequential': {
        },
        'diverging': dict(
            ArmyRose_5=[
                [121, 130, 52],
                [208, 211, 162],
                [253, 251, 228],
                [240, 198, 195],
                [212, 103, 128]],
            ArmyRose_7=[
                [121, 130, 52],
                [163, 173, 98],
                [208, 211, 162],
                [253, 251, 228],
                [240, 198, 195],
                [223, 145, 163],
                [212, 103, 128]],
            Geyser_5=[
                [0, 128, 128],
                [180, 200, 168],
                [246, 237, 189],
                [237, 187, 138],
                [202, 86, 44]],
            Geyser_7=[
                [0, 128, 128],
                [112, 164, 148],
                [180, 200, 168],
                [246, 237, 189],
                [237, 187, 138],
                [222, 138, 90],
                [202, 86, 44]],
            Temps_5=[
                [0, 147, 146],
                [156, 203, 134],
                [233, 226, 156],
                [238, 180, 121],
                [207, 89, 126]],
            Temps_7=[
                [0, 147, 146],
                [57, 177, 133],
                [156, 203, 134],
                [233, 226, 156],
                [238, 180, 121],
                [232, 132, 113],
                [207, 89, 126]],
            TealRose_5=[
                [0, 147, 146],
                [177, 199, 179],
                [241, 234, 200],
                [229, 185, 173],
                [208, 88, 126]],
            TealRose_7=[
                [0, 147, 146],
                [114, 170, 161],
                [177, 199, 179],
                [241, 234, 200],
                [229, 185, 173],
                [217, 137, 148],
                [208, 88, 126]],
            Tropic_5=[
                [0, 155, 158],
                [167, 211, 212],
                [241, 241, 241],
                [228, 193, 217],
                [199, 93, 171]],
            Tropic_7=[
                [0, 155, 158],
                [66, 183, 185],
                [167, 211, 212],
                [241, 241, 241],
                [228, 193, 217],
                [214, 145, 193],
                [199, 93, 171]],
        ),
        'Qualitative': {
        }},
    'cmocean': {
        'diverging': dict(
            Balance_5=[
                [24, 28, 67],
                [56, 136, 186],
                [241, 236, 235],
                [192, 90, 60],
                [60, 9, 18]],
            Balance_7=[
                [24, 28, 67],
                [12, 94, 190],
                [117, 170, 190],
                [241, 236, 235],
                [208, 139, 115],
                [167, 36, 36],
                [60, 9, 18]],
            Curl_5=[
                [21, 29, 68],
                [44, 148, 127],
                [254, 246, 245],
                [196, 90, 97],
                [52, 13, 53]],
            Curl_7=[
                [21, 29, 68],
                [21, 109, 115],
                [125, 179, 144],
                [254, 246, 245],
                [219, 140, 119],
                [157, 48, 96],
                [52, 13, 53]],
            Delta_5=[
                [17, 32, 64],
                [51, 145, 169],
                [255, 253, 205],
                [97, 146, 11],
                [23, 35, 19]],
            Delta_7=[
                [17, 32, 64],
                [28, 103, 160],
                [108, 181, 179],
                [255, 253, 205],
                [170, 172, 32],
                [24, 115, 40],
                [23, 35, 19]])
    },
    'colorbrewer': {
        'diverging': dict(
            BrBG_5=[[166, 97, 26],
                    [223, 194, 125],
                    [245, 245, 245],
                    [128, 205, 193],
                    [1, 133, 113]],
            BrBG_7=[[140, 81, 10],
                    [216, 179, 101],
                    [246, 232, 195],
                    [245, 245, 245],
                    [199, 234, 229],
                    [90, 180, 172],
                    [1, 102, 94]],
            PRGn_5=[[123, 50, 148],
                    [194, 165, 207],
                    [247, 247, 247],
                    [166, 219, 160],
                    [0, 136, 55]],
            PRGn_7=[[118, 42, 131],
                    [175, 141, 195],
                    [231, 212, 232],
                    [247, 247, 247],
                    [217, 240, 211],
                    [127, 191, 123],
                    [27, 120, 55]],
            PiYG_5=[[208, 28, 139],
                    [241, 182, 218],
                    [247, 247, 247],
                    [184, 225, 134],
                    [77, 172, 38]],
            PiYG_7=[[197, 27, 125],
                    [233, 163, 201],
                    [253, 224, 239],
                    [247, 247, 247],
                    [230, 245, 208],
                    [161, 215, 106],
                    [77, 146, 33]],
            PuOr_5=[[230, 97, 1],
                    [253, 184, 99],
                    [247, 247, 247],
                    [178, 171, 210],
                    [94, 60, 153]],
            PuOr_7=[[179, 88, 6],
                    [241, 163, 64],
                    [254, 224, 182],
                    [247, 247, 247],
                    [216, 218, 235],
                    [153, 142, 195],
                    [84, 39, 136]],
            RdBu_5=[[202, 0, 32],
                    [244, 165, 130],
                    [247, 247, 247],
                    [146, 197, 222],
                    [5, 113, 176]],
            RdBu_7=[[178, 24, 43],
                    [239, 138, 98],
                    [253, 219, 199],
                    [247, 247, 247],
                    [209, 229, 240],
                    [103, 169, 207],
                    [33, 102, 172]],
            RdGy_5=[[202, 0, 32],
                    [244, 165, 130],
                    [255, 255, 255],
                    [186, 186, 186],
                    [64, 64, 64]],
            RdGy_7=[[178, 24, 43],
                    [239, 138, 98],
                    [253, 219, 199],
                    [255, 255, 255],
                    [224, 224, 224],
                    [153, 153, 153],
                    [77, 77, 77]])
    }
}

seismic_colors = [list(map(lambda x: x * 255, c)) for c in datad['seismic']]


class Palettes:
    # -- BEGIN -- Diverging palettes
    # Cartoon
    ArmyRose_5 = Palette('Armyrose_5', color_store['cartoon']['diverging']['ArmyRose_5'], 'diverging')
    ArmyRose_7 = Palette('Armyrose_7', color_store['cartoon']['diverging']['ArmyRose_7'], 'diverging')
    Geyser_5 = Palette('Geyser_5', color_store['cartoon']['diverging']['Geyser_5'], 'diverging')
    Geyser_7 = Palette('Geyser_7', color_store['cartoon']['diverging']['Geyser_7'], 'diverging')
    Temps_5 = Palette('Temps_5', color_store['cartoon']['diverging']['Temps_5'], 'diverging')
    Temps_7 = Palette('Temps_7', color_store['cartoon']['diverging']['Temps_7'], 'diverging')
    TealRose_5 = Palette('TealRose_5', color_store['cartoon']['diverging']['TealRose_5'], 'diverging')
    TealRose_7 = Palette('TealRose_7', color_store['cartoon']['diverging']['TealRose_7'], 'diverging')
    Tropic_5 = Palette('Tropic_5', color_store['cartoon']['diverging']['Tropic_5'], 'diverging')
    Tropic_7 = Palette('Tropic_7', color_store['cartoon']['diverging']['Tropic_7'], 'diverging')
    # cmocean
    Balance_5 = Palette('Balance_5', color_store['cmocean']['diverging']['Balance_5'], 'diverging')
    Balance_7 = Palette('Balance_7', color_store['cmocean']['diverging']['Balance_7'], 'diverging')
    Curl_5 = Palette('Curl_5', color_store['cmocean']['diverging']['Curl_5'], 'diverging')
    Curl_7 = Palette('Curl_7', color_store['cmocean']['diverging']['Curl_7'], 'diverging')
    Delta_5 = Palette('Delta_5', color_store['cmocean']['diverging']['Delta_5'], 'diverging')
    Delta_7 = Palette('Delta_7', color_store['cmocean']['diverging']['Delta_7'], 'diverging')
    # colorbrew
    BrBG_5 = Palette('BrBG_5', color_store['colorbrewer']['diverging']['BrBG_5'], 'diverging')
    BrBG_7 = Palette('BrBG_7', color_store['colorbrewer']['diverging']['BrBG_7'], 'diverging')
    PRGn_5 = Palette('PRGn_5', color_store['colorbrewer']['diverging']['PRGn_5'], 'diverging')
    PRGn_7 = Palette('PRGn_7', color_store['colorbrewer']['diverging']['PRGn_7'], 'diverging')
    PiYG_5 = Palette('PiYG_5', color_store['colorbrewer']['diverging']['PiYG_5'], 'diverging')
    PiYG_7 = Palette('PiYG_7', color_store['colorbrewer']['diverging']['PiYG_7'], 'diverging')
    PuOr_5 = Palette('PuOr_5', color_store['colorbrewer']['diverging']['PuOr_5'], 'diverging')
    PuOr_7 = Palette('PuOr_7', color_store['colorbrewer']['diverging']['PuOr_7'], 'diverging')
    RdBu_5 = Palette('RdBu_5', color_store['colorbrewer']['diverging']['RdBu_5'], 'diverging')
    RdBu_7 = Palette('RdBu_7', color_store['colorbrewer']['diverging']['RdBu_7'], 'diverging')
    RdGy_5 = Palette('RdGy_5', color_store['colorbrewer']['diverging']['RdGy_5'], 'diverging')
    RdGy_7 = Palette('RdGy_7', color_store['colorbrewer']['diverging']['RdGy_7'], 'diverging')
    # matplolib
    seismic = Palette('seismic', seismic_colors, 'diverging')
    RdYlBu = 'RdYlBu'
    RdYlGn = 'RdYlGn'
    Spectral = 'Spectral'
    coolwarm = 'coolwarm'
    # -- END -- Diverging palettes

    # -- BEGIN -- Qualitative colormaps
    # seaborn
    deep = 'deep'
    muted = 'muted'
    bright = 'bright'
    pastel = 'pastel'
    dark = 'dark'
    colorblind = 'colorblind'
    # matplotlib
    Pastel1 = 'Pastel1'
    Pastel2 = 'Pastel2'
    Paired = 'Paired'
    Accent = 'Accent'
    Dark2 = 'Dark2'
    Set1 = 'Set1'
    Set2 = 'Set2'
    Set3 = 'Set3'
    tab10 = 'tab10'
    tab20 = 'tab20'
    tab20b = 'tab20b'
    tab20c = 'tab20c'
    husl = 'husl'
    hls = 'hls'
    # -- END -- Qualitative colormaps

    @classmethod
    def get_palette(self, name):
        palette = getattr(self, name)
        if isinstance(palette, Palette):
            return palette.colormap
        else:
            return palette
"""
 This is a module that contains the class of the main gmx_MMPBSA
 Application.
"""

# Import system modules

# ##############################################################################
#                           GPLv3 LICENSE INFO                                 #
#                                                                              #
#  Copyright (C) 2020  Mario S. Valdes-Tresanco and Mario E. Valdes-Tresanco   #
#  Copyright (C) 2014  Jason Swails, Bill Miller III, and Dwight McGee         #
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

import os
import signal
import sys
import logging
# Import gmx_MMPBSA modules
from GMXMMPBSA import utils
from GMXMMPBSA.amber_outputs import (QHout, NMODEout, QMMMout, GBout, PBout, PolarRISM_std_Out, RISM_std_Out,
                                     PolarRISM_gf_Out, RISM_gf_Out, SingleTrajBinding, MultiTrajBinding, IEout, C2out)
from GMXMMPBSA.calculation import (CalculationList, EnergyCalculation, PBEnergyCalculation, RISMCalculation,
                                   NmodeCalc, QuasiHarmCalc, CopyCalc, PrintCalc, LcpoCalc, MolsurfCalc,
                                   InteractionEntropyCalc, C2EntropyCalc)
from GMXMMPBSA.commandlineparser import parser
from GMXMMPBSA.createinput import create_inputs
from GMXMMPBSA.exceptions import (MMPBSA_Error, InternalError, InputError, GMXMMPBSA_ERROR, GMXMMPBSA_WARNING)
from GMXMMPBSA.findprogs import find_progs
from GMXMMPBSA.infofile import InfoFile
from GMXMMPBSA.fake_mpi import MPI as FakeMPI
from GMXMMPBSA.input_parser import input_file as _input_file
from GMXMMPBSA.make_trajs import make_trajectories, make_mutant_trajectories
from GMXMMPBSA.output_file import (write_stability_output, write_binding_output, write_decomp_stability_output,
                                   write_decomp_binding_output, Data2h5)
from GMXMMPBSA.parm_setup import MMPBSA_System
from GMXMMPBSA.make_top import CheckMakeTop
from GMXMMPBSA.timer import Timer


# Global variables for the excepthook replacement at the bottom. Override these
# in the MMPBSA_App constructor and input file reading
_unbuf_stdout = utils.Unbuffered(sys.stdout)  # unbuffered stdout
_unbuf_stderr = utils.Unbuffered(sys.stderr)  # unbuffered stderr
_stdout = sys.stdout
_stderr = sys.stderr
_debug_printlevel = 2
_mpi_size = 1
_rank = 0
_MPI = FakeMPI()


# Main class

class MMPBSA_App(object):
    """ Main MM/PBSA application for driving the entire calculation """
    # The command line parser and input file objects are class attributes here
    clparser = parser
    input_file = _input_file
    debug_printlevel = 2

    def __init__(self, MPI, stdout=None, stderr=None, size=None):
        """
        Sets up the main gmx_MMPBSA driver class. All we set up here is the output
        and error streams (unbuffered by default) and the prefix for the
        intermediate files. Also set up empty INPUT dict
        """
        global _rank, _stdout, _stderr, _mpi_size, _MPI
        _MPI = self.MPI = MPI
        self.pre = '_GMXMMPBSA_'
        self.INPUT = {}
        if stdout is None:
            _stdout = self.stdout = _unbuf_stdout
        else:
            _stdout = self.stdout = stdout

        if stderr is None:
            _stderr = self.stderr = _unbuf_stderr
        else:
            _stderr = self.stderr = stderr

        # MPI-related variables. Squash output for non-master threads
        _rank = self.mpi_rank = self.MPI.COMM_WORLD.Get_rank()
        self.master = self.mpi_rank == 0
        _mpi_size = self.mpi_size = self.MPI.COMM_WORLD.Get_size()
        if not self.master:
            self.stdout = open(os.devnull, 'w')
        if self.master:
            logging.info('Starting')

        # Set up timers
        timers = [Timer() for i in range(self.mpi_size)]
        self.timer = timers[self.mpi_rank]

        # Support possible threading for those that don't use MPI. However, if
        # mpi_size is > 1, just use the MPI mechanism instead
        if size is not None and self.mpi_size == 1:
            self.mpi_size = size

    def file_setup(self):
        """ Sets up the trajectories and input files """
        # If we are rewriting the output file only, bail out here
        if self.FILES.rewrite_output:
            return
        # This work belongs to the 'setup' timer
        self.timer.start_timer('setup')
        if not hasattr(self, 'normal_system'):
            GMXMMPBSA_ERROR('MMPBSA_App not set up and parms not checked!', InternalError)
        # Set up some local refs for convenience
        FILES, INPUT, master = self.FILES, self.INPUT, self.master

        # # Now we're getting ready, remove existing intermediate files
        # if master and FILES.use_mdins:
        #     self.remove(-1)
        # elif master and not FILES.rewrite_output:
        #     self.remove(0)

        # Create input files based on INPUT dict
        if master and not FILES.use_mdins:
            create_inputs(INPUT, self.normal_system, self.pre)
        self.timer.stop_timer('setup')
        # Bail out if we only wanted to generate mdin files
        if FILES.make_mdins:
            self.stdout.write('Created mdin files. Quitting.\n')
            sys.exit(0)

        # Now create our trajectory files

        self.timer.add_timer('cpptraj', 'Creating trajectories with cpptraj:')
        self.timer.start_timer('cpptraj')

        if master:
            self.stdout.write('Preparing trajectories for simulation...\n')
            self.numframes, rec_frames, lig_frames, self.numframes_nmode = make_trajectories(INPUT, FILES,
                                                                                             self.mpi_size,
                                                                     self.external_progs['cpptraj'], self.pre)
            if self.traj_protocol == 'MTP' and not self.numframes == rec_frames == lig_frames:
                GMXMMPBSA_ERROR('The complex, receptor, and ligand trajectories must be the same length. Since v1.5.0 '
                                'we have simplified a few things to make the code easier to maintain. Please check the '
                                'documentation')

        self.MPI.COMM_WORLD.Barrier()

        self.timer.stop_timer('cpptraj')

        self.timer.add_timer('muttraj', 'Mutating trajectories:')
        self.timer.start_timer('muttraj')

        if INPUT['alarun']:
            self.stdout.write('Mutating trajectories...\n')
        _, mutant_residue = make_mutant_trajectories(INPUT, FILES, self.mpi_rank, self.external_progs['cpptraj'],
                                                     self.normal_system, self.mutant_system, self.pre)

        self.MPI.COMM_WORLD.Barrier()

        if master:
            self.stdout.write(('%d frames were processed by cpptraj for use in '
                               'calculation.\n') % self.numframes)
            if INPUT['nmoderun']:
                self.stdout.write(('%d frames were processed by cpptraj for '
                                   'nmode calculations.\n') % self.numframes_nmode)

        self.timer.stop_timer('muttraj')

        # Add all of the calculation timers
        self.timer.add_timer('calc', 'Total calculation time:')
        if INPUT['gbrun']:
            self.timer.add_timer('gb', 'Total GB calculation time:')
        if INPUT['pbrun']:
            self.timer.add_timer('pb', 'Total PB calculation time:')
        if INPUT['rismrun']:
            self.timer.add_timer('rism', 'Total 3D-RISM calculation time:')
        if INPUT['nmoderun']:
            self.timer.add_timer('nmode', 'Total normal mode calculation time:')
        if INPUT['qh_entropy']:
            self.timer.add_timer('qh', 'Total quasi-harmonic calculation time:')

        self.sync_mpi()

    def run_mmpbsa(self, rank=None):
        """
        Runs the MM/PBSA analysis. This assumes FILES and INPUT are already set.
        """

        if not hasattr(self, 'external_progs'):
            GMXMMPBSA_ERROR('external_progs not declared in run_mmpbsa!', InternalError)

        FILES, INPUT = self.FILES, self.INPUT
        if rank is None:
            rank = self.mpi_rank
        master = rank == 0

        # Load the list of calculations we need to do, then run them.

        if master:
            self.timer.start_timer('calc')

        self.load_calc_list()

        self.stdout.write('\n')

        self.calc_list.run(rank, self.stdout)

        self.sync_mpi()

        if master:
            self.timer.stop_timer('calc')
            # Write out the info file now
            info = InfoFile(self)
            info.write_info(self.pre + 'info')

    def load_calc_list(self):
        """
        Sets up all of the calculations to be run. When adding a new
        calculation type, add a class to calculation.py, import it at the top of
        the file here, then append it to the calc list appropriately
        """
        self.calc_list = CalculationList(self.timer)

        if not self.INPUT['mutant_only']:
            self.calc_list.append(
                PrintCalc('Running calculations on normal system...'),
                timer_key=None)
            self._load_calc_list(self.pre, False, self.normal_system)
        if self.INPUT['alarun']:
            self.calc_list.append(
                PrintCalc('\nRunning calculations on mutant system...'), timer_key=None)
            self._load_calc_list(self.pre + 'mutant_', True, self.mutant_system)

    def _load_calc_list(self, prefix, mutant, parm_system):
        """
        Internal routine to handle building calculation list. Called separately
        for mutant and normal systems
        """
        # Set up a dictionary of external programs to use based one external progs
        progs = {'gb': self.external_progs['mmpbsa_py_energy'],
                 'sa': self.external_progs['cpptraj'],
                 'pb': self.external_progs['mmpbsa_py_energy'],
                 'rism': self.external_progs['rism3d.snglpnt'],
                 'qh': self.external_progs['cpptraj'],
                 'nmode': self.external_progs['mmpbsa_py_nabnmode']
                 }
        if self.INPUT['use_sander'] or self.INPUT['decomprun']:
            progs['gb'] = progs['pb'] = self.external_progs['sander']
        if self.INPUT['sander_apbs']:
            progs['pb'] = self.external_progs['sander.APBS']
        if self.INPUT['ifqnt']:
            progs['gb'] = self.external_progs['sander']

        # NetCDF or ASCII intermediate trajectories?
        trj_sfx = 'nc' if self.INPUT['netcdf'] else 'mdcrd'

        # Determine if we just copy the receptor files. This only happens if we
        # are doing mutant calculations, we're not only doing the mutant, and the
        # receptor/mutant receptor topologies are equal. Same for the ligand
        copy_receptor = (mutant and not self.INPUT['mutant_only'] and
                         self.FILES.receptor_prmtop == self.FILES.mutant_receptor_prmtop)
        copy_ligand = (mutant and not self.INPUT['mutant_only'] and
                       self.FILES.ligand_prmtop == self.FILES.mutant_ligand_prmtop)

        # First load the GB calculations
        if self.INPUT['gbrun']:
            # See if we need a PDB or restart file for the inpcrd
            if 'mmpbsa_py_energy' in progs['gb']:
                incrd = '%s%%s.pdb' % prefix
            else:
                incrd = '%sdummy%%s.inpcrd' % prefix

            # See whether we are doing molsurf or LCPO. Reduce # of arguments
            # needed to 3, filling in the others here
            if self.INPUT['molsurf']:
                SAClass = lambda a1, a2, a3: MolsurfCalc(progs['sa'], a1, a2, a3,
                                                         self.INPUT['probe'], self.INPUT['msoffset'])
            else:
                SAClass = lambda a1, a2, a3: LcpoCalc(progs['sa'], a1, a2, a3,
                                                      self.INPUT['probe'], self.INPUT['msoffset'])

            # Mdin depends on decomp or not
            if self.INPUT['decomprun']:
                mdin_template = self.pre + 'gb_decomp_%s.mdin'
            elif self.INPUT['ifqnt']:
                mdin_template = self.pre + 'gb_qmmm_%s.mdin'
            else:
                mdin_template = self.pre + 'gb.mdin'

            # Now do complex-specific stuff
            try:
                mdin = mdin_template % 'com'
            except TypeError:
                mdin = mdin_template

            self.calc_list.append(PrintCalc(f"\nBeginning GB calculations with {progs['gb']}"), timer_key='gb')

            c = EnergyCalculation(progs['gb'], parm_system.complex_prmtop,
                                  incrd % 'complex',
                                  '%scomplex.%s.%%d' % (prefix, trj_sfx),
                                  mdin, '%scomplex_gb.mdout.%%d' % (prefix),
                                  self.pre + 'restrt.%d')
            self.calc_list.append(c, '  calculating complex contribution...',
                                  timer_key='gb')
            c = SAClass(parm_system.complex_prmtop,
                        '%scomplex.%s.%%d' % (prefix, trj_sfx),
                        '%scomplex_gb_surf.dat.%%d' % prefix)
            self.calc_list.append(c, '', timer_key='gb')

            if not self.stability:
                try:
                    mdin = mdin_template % 'rec'
                except TypeError:
                    mdin = mdin_template

                # Either copy the existing receptor if the mutation is in the ligand
                # or perform a receptor calculation
                if copy_receptor:
                    c = CopyCalc('%sreceptor_gb.mdout.%%d' % self.pre,
                                 '%sreceptor_gb.mdout.%%d' % prefix)
                    self.calc_list.append(c, '  no mutation found in receptor; '
                                             'using unmutated files', timer_key='gb')
                    c = CopyCalc('%sreceptor_gb_surf.dat.%%d' % self.pre,
                                 '%sreceptor_gb_surf.dat.%%d' % prefix)
                    self.calc_list.append(c, '', timer_key='gb')
                else:
                    c = EnergyCalculation(progs['gb'], parm_system.receptor_prmtop,
                                          incrd % 'receptor',
                                          '%sreceptor.%s.%%d' % (prefix, trj_sfx),
                                          mdin, '%sreceptor_gb.mdout.%%d' % (prefix),
                                          self.pre + 'restrt.%d')
                    self.calc_list.append(c, '  calculating receptor contribution...',
                                          timer_key='gb')
                c = SAClass(parm_system.receptor_prmtop,
                            '%sreceptor.%s.%%d' % (prefix, trj_sfx),
                            '%sreceptor_gb_surf.dat.%%d' % prefix)
                self.calc_list.append(c, '', timer_key='gb')

                try:
                    mdin = mdin_template % 'lig'
                except TypeError:
                    mdin = mdin_template

                # Either copy the existing ligand if the mutation is in the receptor
                # or perform a ligand calculation
                if copy_ligand:
                    c = CopyCalc('%sligand_gb.mdout.%%d' % self.pre,
                                 '%sligand_gb.mdout.%%d' % prefix)
                    self.calc_list.append(c, '  no mutation found in ligand; '
                                             'using unmutated files', timer_key='gb')
                    c = CopyCalc('%sligand_gb_surf.dat.%%d' % self.pre,
                                 '%sligand_gb_surf.dat.%%d' % prefix)
                    self.calc_list.append(c, '', timer_key='gb')
                else:
                    c = EnergyCalculation(progs['gb'], parm_system.ligand_prmtop,
                                          incrd % 'ligand',
                                          '%sligand.%s.%%d' % (prefix, trj_sfx),
                                          mdin, '%sligand_gb.mdout.%%d' % (prefix),
                                          self.pre + 'restrt.%d')
                    self.calc_list.append(c, '  calculating ligand contribution...',
                                          timer_key='gb')
                c = SAClass(parm_system.ligand_prmtop,
                            '%sligand.%s.%%d' % (prefix, trj_sfx),
                            '%sligand_gb_surf.dat.%%d' % prefix)
                self.calc_list.append(c, '', timer_key='gb')

        # end if self.INPUT['gbrun']

        # Next load the PB calculations
        if self.INPUT['pbrun']:
            # See if we need a PDB or restart file for the inpcrd
            if 'mmpbsa_py_energy' in progs['pb']:
                incrd = '%s%%s.pdb' % prefix
            else:
                incrd = '%sdummy%%s.inpcrd' % prefix

            # Mdin depends on decomp or not
            if self.INPUT['decomprun']:
                mdin_template = self.pre + 'pb_decomp_%s.mdin'
                mdin_template2 = mdin_template
            else:
                mdin_template = self.pre + 'pb.mdin'
                mdin_template2 = self.pre + 'pb.mdin2'

            # Now do complex-specific stuff
            try:
                mdin = mdin_template % 'com'
            except TypeError:
                mdin = mdin_template

            self.calc_list.append(PrintCalc(f"\nBeginning PB calculations with {progs['pb']}"),
                                  timer_key='pb')

            c = PBEnergyCalculation(progs['pb'], parm_system.complex_prmtop,
                                    incrd % 'complex',
                                    '%scomplex.%s.%%d' % (prefix, trj_sfx),
                                    mdin, '%scomplex_pb.mdout.%%d' % (prefix),
                                    self.pre + 'restrt.%d')
            self.calc_list.append(c, '  calculating complex contribution...',
                                  timer_key='pb')
            if not self.stability:
                try:
                    mdin = mdin_template % 'rec'
                except TypeError:
                    mdin = mdin_template

                # Either copy the existing receptor if the mutation is in the ligand
                # or perform a receptor calculation
                if copy_receptor:
                    c = CopyCalc('%sreceptor_pb.mdout.%%d' % self.pre,
                                 '%sreceptor_pb.mdout.%%d' % prefix)
                    self.calc_list.append(c, '  no mutation found in receptor; '
                                             'using unmutated files', timer_key='pb')
                else:
                    c = PBEnergyCalculation(progs['pb'], parm_system.receptor_prmtop,
                                            incrd % 'receptor',
                                            '%sreceptor.%s.%%d' % (prefix, trj_sfx),
                                            mdin, '%sreceptor_pb.mdout.%%d' % (prefix),
                                            self.pre + 'restrt.%d')
                    self.calc_list.append(c, '  calculating receptor contribution...',
                                          timer_key='pb')

                try:
                    mdin2 = mdin_template2 % 'lig'
                except TypeError:
                    mdin2 = mdin_template2

                # Either copy the existing ligand if the mutation is in the receptor
                # or perform a ligand calculation
                if copy_ligand:
                    c = CopyCalc('%sligand_pb.mdout.%%d' % self.pre,
                                 '%sligand_pb.mdout.%%d' % prefix)
                    self.calc_list.append(c, '  no mutation found in ligand; '
                                             'using unmutated files', timer_key='pb')
                else:
                    c = PBEnergyCalculation(progs['pb'], parm_system.ligand_prmtop,
                                            incrd % 'ligand',
                                            '%sligand.%s.%%d' % (prefix, trj_sfx),
                                            mdin2, '%sligand_pb.mdout.%%d' % (prefix),
                                            self.pre + 'restrt.%d')
                    self.calc_list.append(c, '  calculating ligand contribution...',
                                          timer_key='pb')
        # end if self.INPUT['pbrun']

        if self.INPUT['rismrun']:
            self.calc_list.append(
                PrintCalc('\nBeginning 3D-RISM calculations with %s' %
                          progs['rism']), timer_key='rism')

            c = RISMCalculation(progs['rism'], parm_system.complex_prmtop,
                                '%scomplex.pdb' % prefix, '%scomplex.%s.%%d' %
                                (prefix, trj_sfx), self.FILES.xvvfile,
                                '%scomplex_rism.mdout.%%d' % prefix, self.INPUT)
            self.calc_list.append(c, '  calculating complex contribution...',
                                  timer_key='rism')

            if not self.stability:
                if copy_receptor:
                    c = CopyCalc('%sreceptor_rism.mdout.%%d' % self.pre,
                                 '%sreceptor_rism.mdout.%%d' % prefix)
                    self.calc_list.append(c, '  no mutation found in receptor; '
                                             'using unmutated files', timer_key='pb')
                else:
                    c = RISMCalculation(progs['rism'], parm_system.receptor_prmtop,
                                        '%sreceptor.pdb' % prefix,
                                        '%sreceptor.%s.%%d' % (prefix, trj_sfx),
                                        self.FILES.xvvfile,
                                        '%sreceptor_rism.mdout.%%d' % prefix, self.INPUT)
                    self.calc_list.append(c, '  calculating receptor contribution...',
                                          timer_key='rism')

                if copy_ligand:
                    c = CopyCalc('%sligand_rism.mdout.%%d' % self.pre,
                                 '%sligand_rism.mdout.%%d' % prefix)
                    self.calc_list.append(c, '  no mutation found in ligand; '
                                             'using unmutated files', timer_key='pb')
                else:
                    c = RISMCalculation(progs['rism'], parm_system.ligand_prmtop,
                                        '%sligand.pdb' % prefix,
                                        '%sligand.%s.%%d' % (prefix, trj_sfx),
                                        self.FILES.xvvfile,
                                        '%sligand_rism.mdout.%%d' % prefix, self.INPUT)
                    self.calc_list.append(c, '  calculating ligand contribution...',
                                          timer_key='rism')

        # end if self.INPUT['rismrun']

        if self.INPUT['nmoderun']:
            self.calc_list.append(
                PrintCalc('\nBeginning nmode calculations with %s' %
                          progs['nmode']), timer_key='nmode')

            c = NmodeCalc(progs['nmode'], parm_system.complex_prmtop,
                          '%scomplex.pdb' % prefix,
                          '%scomplex_nm.%s.%%d' % (prefix, trj_sfx),
                          '%scomplex_nm.out.%%d' % prefix, self.INPUT)
            self.calc_list.append(c, '  calculating complex contribution...',
                                  timer_key='nmode')

            if not self.stability:
                if copy_receptor:
                    c = CopyCalc('%sreceptor_nm.out.%%d' % self.pre,
                                 '%sreceptor_nm.out.%%d' % prefix)
                    self.calc_list.append(c, '  no mutation found in receptor; '
                                             'using unmutated files', timer_key='pb')
                else:
                    c = NmodeCalc(progs['nmode'], parm_system.receptor_prmtop,
                                  '%sreceptor.pdb' % prefix,
                                  '%sreceptor_nm.%s.%%d' % (prefix, trj_sfx),
                                  '%sreceptor_nm.out.%%d' % prefix, self.INPUT)
                    self.calc_list.append(c, '  calculating receptor contribution...',
                                          timer_key='rism')

                if copy_ligand:
                    c = CopyCalc('%sligand_nm.out.%%d' % self.pre,
                                 '%sligand_nm.out.%%d' % prefix)
                    self.calc_list.append(c, '  no mutation found in ligand; '
                                             'using unmutated files', timer_key='pb')
                else:
                    c = NmodeCalc(progs['nmode'], parm_system.ligand_prmtop,
                                  '%sligand.pdb' % prefix,
                                  '%sligand_nm.%s.%%d' % (prefix, trj_sfx),
                                  '%sligand_nm.out.%%d' % prefix, self.INPUT)
                    self.calc_list.append(c, '  calculating ligand contribution...',
                                          timer_key='rism')

        # end if self.INPUT['nmoderun']

        # Only master does entropy calculations
        if self.INPUT['qh_entropy']:
            self.calc_list.append(
                PrintCalc('\nBeginning quasi-harmonic calculations with %s' %
                          progs['qh']), timer_key='qh')

            c = QuasiHarmCalc(progs['qh'], parm_system.complex_prmtop,
                              '%scomplex.%s' % (prefix, trj_sfx),
                              '%scpptrajentropy.in' % prefix,
                              '%scpptraj_entropy.out' % prefix,
                              self.INPUT['receptor_mask'],
                              self.INPUT['ligand_mask'], self.pre)
            self.calc_list.append(c, '', timer_key='qh')


    def make_prmtops(self):
        self.timer.add_timer('setup_gmx', 'Total GROMACS setup time:')
        self.timer.start_timer('setup_gmx')
        # Now we're getting ready, remove existing intermediate files
        if self.master and self.FILES.use_mdins:
            self.remove(-1)
        elif self.master and not self.FILES.rewrite_output:
            self.remove(0)

        # Find external programs IFF we are doing a calc
        if not self.FILES.make_mdins:
            external_progs = {}
            if self.master:
                external_progs = find_progs(self.INPUT, self.mpi_size)
            external_progs = self.MPI.COMM_WORLD.bcast(external_progs, root=0)
            # Make external_progs an instance attribute
            self.external_progs = external_progs
        if self.master:
            # Make amber topologies
            logging.info('Building AMBER Topologies from GROMACS files...')
            maketop = CheckMakeTop(self.FILES, self.INPUT, self.external_progs)
            (self.FILES.complex_prmtop, self.FILES.receptor_prmtop, self.FILES.ligand_prmtop,
             self.FILES.mutant_complex_prmtop,
             self.FILES.mutant_receptor_prmtop, self.FILES.mutant_ligand_prmtop) = maketop.buildTopology()
            logging.info('Building AMBER Topologies from GROMACS files...Done.\n')
            self.INPUT['receptor_mask'], self.INPUT['ligand_mask'], self.resl = maketop.get_masks()
            self.mut_str = maketop.mut_label
            self.FILES.complex_fixed = self.FILES.prefix + 'COM_FIXED.pdb'
        self.FILES = self.MPI.COMM_WORLD.bcast(self.FILES, root=0)
        self.INPUT = self.MPI.COMM_WORLD.bcast(self.INPUT, root=0)
        self.sync_mpi()
        self.timer.stop_timer('setup_gmx')

    def loadcheck_prmtops(self):
        """ Loads the topology files and checks their consistency """
        # Start setup timer and make sure we've already set up our input
        self.timer.add_timer('setup', 'Total AMBER setup time:')
        self.timer.start_timer('setup')
        if not hasattr(self, 'FILES') or not hasattr(self, 'INPUT'):
            GMXMMPBSA_ERROR('MMPBSA_App not set up! Cannot check parms yet!', InternalError)
        # create local aliases to avoid abundant selfs
        FILES, INPUT = self.FILES, self.INPUT
        if self.master:
            # Now load the parms and check them
            logging.info('Loading and checking parameter files for compatibility...\n')
        self.normal_system = MMPBSA_System(FILES.complex_prmtop, FILES.receptor_prmtop, FILES.ligand_prmtop)
        self.using_chamber = self.normal_system.complex_prmtop.chamber
        self.mutant_system = None
        if INPUT['alarun']:
            if (FILES.mutant_receptor_prmtop is None and FILES.mutant_ligand_prmtop is None and not self.stability):
                GMXMMPBSA_ERROR('Alanine scanning requires either a mutated receptor or mutated ligand topology '
                                   'file!')
            if FILES.mutant_receptor_prmtop is None:
                FILES.mutant_receptor_prmtop = FILES.receptor_prmtop
            elif FILES.mutant_ligand_prmtop is None:
                FILES.mutant_ligand_prmtop = FILES.ligand_prmtop
            self.mutant_system = MMPBSA_System(FILES.mutant_complex_prmtop, FILES.mutant_receptor_prmtop,
                                               FILES.mutant_ligand_prmtop)
        # If we have a chamber prmtop, force using sander
        if self.using_chamber:
            INPUT['use_sander'] = True
            if INPUT['rismrun']:
                GMXMMPBSA_ERROR('CHAMBER prmtops cannot be used with 3D-RISM')
            if INPUT['nmoderun']:
                GMXMMPBSA_ERROR('CHAMBER prmtops cannot be used with NMODE')
            self.stdout.write('CHAMBER prmtops found. Forcing use of sander\n')

        self.normal_system.Map(INPUT['receptor_mask'], INPUT['ligand_mask'])
        self.normal_system.CheckConsistency()
        if INPUT['alarun']:
            self.mutant_system.Map(INPUT['receptor_mask'], INPUT['ligand_mask'])
            self.mutant_system.CheckConsistency()
        if (INPUT['ligand_mask'] is None or INPUT['receptor_mask'] is None):
            com_mask, INPUT['receptor_mask'], INPUT['ligand_mask'] = \
                self.normal_system.Mask('all', in_complex=True)
        self.sync_mpi()
        self.timer.stop_timer('setup')

    def write_final_outputs(self):
        """ Writes the final output files for gmx_MMPBSA """
        self.timer.add_timer('output', 'Statistics calculation & output writing:')
        self.timer.start_timer('output')
        if (not hasattr(self, 'input_file_text') or not hasattr(self, 'FILES') or
                not hasattr(self, 'INPUT') or not hasattr(self, 'normal_system')):
            GMXMMPBSA_ERROR('I am not prepared to write the final output file!', InternalError)
        # Only the master does this, so bail out if we are not master
        if not self.master:
            return
        # If we haven't already parsed our output files, do that now
        if not hasattr(self, 'calc_types'):
            self.parse_output_files()
        # Do the output files now
        if self.stability:
            write_stability_output(self)
        else:
            write_binding_output(self)
        if self.INPUT['decomprun']:
            if self.stability:
                write_decomp_stability_output(self.FILES, self.INPUT, self.mpi_size,
                                              self.normal_system, self.mutant_system, self.mut_str, self.pre)
            else:
                write_decomp_binding_output(self.FILES, self.INPUT, self.mpi_size,
                                            self.normal_system, self.mutant_system, self.mut_str, self.pre)
        if self.INPUT['save_mode']:
            # Store the calc_types data in a h5 file
            Data2h5(self)
        self.timer.stop_timer('output')

    def finalize(self):
        """ We are done. Finish up timers and print out timing info """
        self.timer.done()
        if not self.master:
            self.MPI.Finalize()
            sys.exit(0)
        self.stdout.write('\nTiming:\n')
        self.timer.print_('setup_gmx', self.stdout)
        self.timer.print_('setup', self.stdout)

        if not self.FILES.rewrite_output:
            self._finalize_timers()
        self.timer.print_('output', self.stdout)
        self.timer.print_('global', self.stdout)

        self.remove(self.INPUT['keep_files'])

        logging.info('\n\nThank you for using gmx_MMPBSA. Please cite us if you publish this work with this '
                     'reference:\n    Mario S. Valdés Tresanco, Mario E. Valdes-Tresanco, Pedro A. Valiente, & '
                     'Ernesto Moreno Frías \n    gmx_MMPBSA (Version v1.4.3). '
                     'Zenodo. http://doi.org/10.5281/zenodo.4569307'
                     '\n\nAlso consider citing MMPBSA.py\n    Miller III, B. R., McGee Jr., '
                     'T. D., Swails, J. M. Homeyer, N. Gohlke, H. and Roitberg, A. E.\n    J. Chem. Theory Comput., '
                     '2012, 8 (9) pp 3314-3321\n')
        self.MPI.Finalize()

        end = 0
        if self.FILES.gui:
            import subprocess
            logging.info('Opening gmx_MMPBSA_ana to analyze results...\n')
            g = subprocess.Popen(['gmx_MMPBSA_ana', '-f', self.FILES.prefix + 'info'])
            if g.wait():
                end = 1
        if end:
            logging.error('Unable to start gmx_MMPBSA_ana...')
        logging.info('Finalized...')
        sys.exit(end)

    def _finalize_timers(self):
        self.timer.print_('cpptraj', self.stdout)

        if self.INPUT['alarun']:
            self.timer.print_('muttraj', self.stdout)

        self.timer.print_('calc', self.stdout)
        self.stdout.write('\n')

        if self.INPUT['gbrun']:
            self.timer.print_('gb', self.stdout)

        if self.INPUT['pbrun']:
            self.timer.print_('pb', self.stdout)

        if self.INPUT['nmoderun']:
            self.timer.print_('nmode', self.stdout)

        if self.INPUT['qh_entropy']:
            self.timer.print_('qh', self.stdout)

        self.stdout.write('\n')

    def get_cl_args(self, args=None):
        """
        Gets the command-line arguments to load the INPUT array. Also determines
        if we are doing a stability calculation or not
        """
        if args is None:
            args = sys.argv
        if self.master:
            self.FILES = self.clparser.parse_args(args)
            # save args in gmx_MMPBSA.log
            logging.info('Command-line\n'
                         '  gmx_MMPBSA ' + ' '.join(args) + '\n')
        else:
            self.FILES = object()
        # Broadcast the FILES
        self.FILES = self.MPI.COMM_WORLD.bcast(self.FILES)
        # Hand over the file prefix to the App instance
        self.pre = self.FILES.prefix
        if self.FILES.receptor_trajs or self.FILES.ligand_trajs:
            self.traj_protocol = 'MTP'  # multiple traj protocol
        else:
            self.traj_protocol = 'STP'  # single traj protocol
        # change by explicit argument
        self.stability = self.FILES.stability

    def read_input_file(self, infile=None):
        """ Reads the input file, pull it from FILES if not provided here """
        global _debug_printlevel
        if infile is None:
            if not hasattr(self, 'FILES'):
                GMXMMPBSA_ERROR('FILES not present and no input file given!', InternalError)
            infile = self.FILES.input_file
        self.INPUT = self.input_file.Parse(infile)
        _debug_printlevel = self.INPUT['debug_printlevel']
        self.input_file_text = str(self.input_file)
        if self.master:
            with open('gmx_MMPBSA.log', 'a') as log:
                log.write('[INFO   ] Input file\n')
                log.write(self.input_file_text)

    def process_input(self):
        """
        This handles processing of the INPUT dict if necessary if this is a 'new'
        calculation (i.e., not re-writing output). This does the following prep:
           - invert scale
           - determine trajectory file suffix
           - set decomp-dependent GBSA default
           - adjust verbose for stability calcs
           - 3D-RISM setup
           - Set temperature. Don't put it in namelist, because temp change
             for entropy requires changes to nmode and cpptraj calcs, meaning it
             is not as easily changed here.
        """
        # Invert scale
        self.INPUT['scale'] = 1 / self.INPUT['scale']

        # Set up netcdf variables and decide trajectory suffix
        if self.INPUT['netcdf'] == 0:
            self.INPUT['netcdf'] = ''
            self.trjsuffix = 'mdcrd'
        else:
            self.INPUT['netcdf'] = 'netcdf'
            self.trjsuffix = 'nc'

        # Set default GBSA for Decomp
        if self.INPUT['decomprun']:
            self.INPUT['gbsa'] = 2

        # Force to use Sander when intdiel is defined
        if self.INPUT['intdiel'] > 1.0:
            self.INPUT['use_sander'] = 1

        # Stability: no terms cancel, so print them all
        if self.stability:
            self.INPUT['verbose'] = 2

        # 3D-RISM stuff (keywords are case-insensitive)
        self.INPUT['thermo'] = self.INPUT['thermo'].lower()
        if self.INPUT['solvcut'] is None:
            self.INPUT['solvcut'] = self.INPUT['buffer']
        self.INPUT['rismrun_std'] = (self.INPUT['rismrun'] and
                                     self.INPUT['thermo'] in ['std', 'both'])
        self.INPUT['rismrun_gf'] = (self.INPUT['rismrun'] and
                                    self.INPUT['thermo'] in ['gf', 'both'])

        # Default temperature
        self.INPUT['temp'] = 298.15

    def check_for_bad_input(self, INPUT=None):
        """ Checks for bad user input """
        if INPUT is None:
            INPUT = self.INPUT
        if not self.master:
            return
        # Check deprecated variables
        # check force fields
        if not INPUT['igb'] in [1, 2, 5, 7, 8]:
            GMXMMPBSA_ERROR('Invalid value for IGB (%s)! ' % INPUT['igb'] + 'It must be 1, 2, 5, 7, or 8.', InputError)
        if INPUT['saltcon'] < 0:
            GMXMMPBSA_ERROR('SALTCON must be non-negative!', InputError)
        if INPUT['surften'] < 0:
            GMXMMPBSA_ERROR('SURFTEN must be non-negative!', InputError)
        if INPUT['indi'] < 0:
            GMXMMPBSA_ERROR('INDI must be non-negative!', InputError)
        if INPUT['exdi'] < 0:
            GMXMMPBSA_ERROR('EXDI must be non-negative!', InputError)
        if INPUT['scale'] < 0:
            GMXMMPBSA_ERROR('SCALE must be non-negative!', InputError)
        if INPUT['linit'] < 0:
            GMXMMPBSA_ERROR('LINIT must be a positive integer!', InputError)
        if not INPUT['prbrad'] in [1.4, 1.6]:
            GMXMMPBSA_ERROR('PRBRAD (%s) must be 1.4 and 1.6!' % INPUT['prbrad'], InputError)
        if INPUT['istrng'] < 0:
            GMXMMPBSA_ERROR('ISTRNG must be non-negative!', InputError)
        if not INPUT['inp'] in [0, 1, 2]:
            GMXMMPBSA_ERROR('INP/NPOPT (%s) must be 0, 1, or 2!' % INPUT['inp'], InputError)
        if INPUT['cavity_surften'] < 0:
            GMXMMPBSA_ERROR('CAVITY_SURFTEN must be non-negative!', InputError)
        if INPUT['fillratio'] <= 0:
            GMXMMPBSA_ERROR('FILL_RATIO must be positive!', InputError)
        if not INPUT['radiopt'] in [0, 1]:
            GMXMMPBSA_ERROR('RADIOPT (%s) must be 0 or 1!' % INPUT['radiopt'], InputError)
        if INPUT['dielc'] <= 0:
            GMXMMPBSA_ERROR('DIELC must be positive!', InputError)
        if INPUT['maxcyc'] < 1:
            GMXMMPBSA_ERROR('MAXCYC must be a positive integer!', InputError)
        if not INPUT['idecomp'] in [0, 1, 2, 3, 4]:
            GMXMMPBSA_ERROR('IDECOMP (%s) must be 1, 2, 3, or 4!' %
                             INPUT['idecomp'], InputError)
        if INPUT['idecomp'] != 0 and INPUT['sander_apbs'] == 1:
            GMXMMPBSA_ERROR('IDECOMP cannot be used with sander.APBS!', InputError)
        if not INPUT['sander_apbs'] in [0, 1]:
            GMXMMPBSA_ERROR('SANDER_APBS must be 0 or 1!', InputError)
        if INPUT['alarun'] and INPUT['netcdf'] != '':
            GMXMMPBSA_ERROR('Alanine scanning is incompatible with NETCDF != 0!', InputError)
        if INPUT['decomprun'] and INPUT['idecomp'] == 0:
            GMXMMPBSA_ERROR('IDECOMP cannot be 0 for Decomposition analysis!', InputError)
        if INPUT['ions_parameters'] not in range(1,13):
            GMXMMPBSA_ERROR('Ions parameters file name must be in %s!' % range(1,13), InputError)
        if INPUT['PBRadii'] not in [1, 2, 3, 4]:
            GMXMMPBSA_ERROR('PBRadii must be 1, 2, 3 or 4!', InputError)
        if INPUT['solvated_trajectory'] not in [0, 1]:
            GMXMMPBSA_ERROR('SOLVATED_TRAJECTORY must be 0 or 1!', InputError)
        if not INPUT['use_sander'] in [0, 1]:
            GMXMMPBSA_ERROR('USE_SANDER must be set to 0 or 1!', InputError)
        if not INPUT['ifqnt'] in [0, 1]:
            GMXMMPBSA_ERROR('QMMM must be 0 or 1!', InputError)
        if INPUT['ifqnt'] == 1:
            if not INPUT['qm_theory'] in ['PM3', 'AM1', 'MNDO', 'PDDG-PM3', 'PM3PDDG',
                                          'PDDG-MNDO', 'PDDGMNDO', 'PM3-CARB1',
                                          'PM3CARB1', 'DFTB', 'SCC-DFTB', 'RM1', 'PM6',
                                          'PM3-ZnB', 'PM3-MAIS', 'PM6-D', 'PM6-DH+',
                                          'AM1-DH+', 'AM1-D*', 'PM3ZNB', 'MNDO/D',
                                          'MNDOD']:
                GMXMMPBSA_ERROR('Invalid QM_THEORY (%s)! ' % INPUT['qm_theory'] +
                                'This variable must be set to allowable options.\n' +
                                '       See the Amber manual for allowable options.', InputError)
            if INPUT['qm_residues'] == '':
                GMXMMPBSA_ERROR('QM_RESIDUES must be specified for IFQNT = 1!', InputError)
            if INPUT['decomprun']:
                GMXMMPBSA_ERROR('QM/MM and decomposition are incompatible!', InputError)
            if (INPUT['qmcharge_lig'] + INPUT['qmcharge_rec'] !=
                    INPUT['qmcharge_com'] and not self.stability):
                GMXMMPBSA_ERROR('The total charge of the ligand and receptor ' +
                                 'does not equal the charge of the complex!', InputError)
        if INPUT['rismrun']:
            if INPUT['rism_verbose'] > 2 or INPUT['rism_verbose'] < 0:
                GMXMMPBSA_ERROR('RISM_VERBOSE must be 0, 1, or 2!', InputError)
            if INPUT['buffer'] < 0 and INPUT['solvcut'] < 0:
                GMXMMPBSA_ERROR('If BUFFER < 0, SOLVCUT must be > 0!', InputError)
            if INPUT['tolerance'] < 0:
                GMXMMPBSA_ERROR('TOLERANCE must be positive!', InputError)
            if INPUT['buffer'] < 0 and INPUT['ng'] == '':
                GMXMMPBSA_ERROR('You must specify NG if BUFFER < 0!', InputError)
            if INPUT['closure'] == 'pse' and INPUT['closureorder'] < 1:
                GMXMMPBSA_ERROR('You must specify CLOSUREORDER if CLOSURE=pse!', InputError)
            if not INPUT['polardecomp'] in [0, 1]:
                GMXMMPBSA_ERROR('POLARDECOMP must be either 0 or 1!', InputError)
            if not INPUT['thermo'] in ['std', 'gf', 'both']:
                GMXMMPBSA_ERROR('THERMO must be "std", "gf", or "both"!', InputError)
        if not (INPUT['gbrun'] or INPUT['pbrun'] or INPUT['rismrun'] or
                INPUT['nmoderun'] or INPUT['qh_entropy']):
            GMXMMPBSA_ERROR('You did not specify any type of calculation!', InputError)

        if INPUT['decomprun'] and not (INPUT['gbrun'] or INPUT['pbrun']):
            GMXMMPBSA_ERROR('DECOMP must be run with either GB or PB!', InputError)

        if not INPUT['molsurf'] and (INPUT['msoffset'] != 0 or INPUT['probe'] != 1.4):
            if self.master:
                logging.warning('offset and probe are molsurf-only options')
        if not INPUT['cas_intdiel'] in [0, 1]:
            GMXMMPBSA_ERROR('cas_intdiel must be set to 0 or 1!', InputError)

        # User warning when intdiel > 10
        if self.INPUT['intdiel'] > 10:
            GMXMMPBSA_WARNING(f"Intdiel is great than 10...")
        # check mutant definition
        if not self.INPUT['mutant'].upper() in ['ALA', 'A', 'GLY', 'G']:
            GMXMMPBSA_ERROR('The mutant most be ALA (or A) or GLY (or G)', InputError)

        # fixed the error when try to open gmx_MMPBSA_ana in the issue
        # https://github.com/Valdes-Tresanco-MS/gmx_MMPBSA/issues/33
        if self.INPUT['startframe'] < 1:
            # GMXMMPBSA_ERROR('The startframe variable must be >= 1')
            GMXMMPBSA_WARNING(f"The startframe variable must be >= 1. Changing startframe from"
                              f" {self.INPUT['startframe']} to 1")
            self.INPUT['startframe'] = 1
        if self.INPUT['nmstartframe'] < 1:
            GMXMMPBSA_WARNING(f"The nmstartframe variable must be >= 1. Changing nmstartframe from"
                              f" {self.INPUT['nmstartframe']} to 1")
            self.INPUT['nmstartframe'] = 1

        # check files
        if self.FILES.complex_top or self.INPUT['cas_intdiel']:
            self.INPUT['use_sander'] = 1

    def remove(self, flag):
        """ Removes temporary files """
        if not self.master:
            return
        utils.remove(flag, mpi_size=self.mpi_size, fnpre=self.pre)

    def sync_mpi(self):
        """ Throws up a barrier """
        self.MPI.COMM_WORLD.Barrier()

    def parse_output_files(self):
        """
        This parses the output files and loads them into dicts for easy access
        """
        # Only the master does this
        if not self.master:
            return
        self.calc_types = type('calc_types', (dict,), {'mutant': {}})()
        INPUT, FILES = self.INPUT, self.FILES
        # Quasi-harmonic analysis is a special-case, so handle that separately
        if INPUT['qh_entropy']:
            if not INPUT['mutant_only']:
                self.calc_types['qh'] = QHout(self.pre + 'cpptraj_entropy.out', INPUT['temp'])
            if INPUT['alarun']:
                self.calc_types.mutant['qh'] = QHout(self.pre + 'mutant_cpptraj_entropy.out', INPUT['temp'])
        # Set BindingClass based on whether it's a single or multiple trajectory
        # analysis
        if self.traj_protocol == 'STP':
            BindClass = SingleTrajBinding
        else:
            BindClass = MultiTrajBinding
        # Determine if our GB is QM/MM or not
        GBClass = QMMMout if INPUT['ifqnt'] else GBout
        # Determine which kind of RISM output class we are based on std/gf and
        # polardecomp
        if INPUT['polardecomp']:
            RISM_GF = PolarRISM_gf_Out
            RISM_Std = PolarRISM_std_Out
        else:
            RISM_GF = RISM_gf_Out
            RISM_Std = RISM_std_Out
        # Now we make a list of the other calculation types, their INPUT triggers,
        # their key in the calc_types dict, the base name of their output files
        # without the prefix (with %s-substitution for complex, receptor, or
        # ligand), and the class for their output
        triggers = ('nmoderun', 'gbrun', 'pbrun', 'rismrun_std', 'rismrun_gf')
        outclass = (NMODEout, GBClass, PBout, RISM_Std, RISM_GF)
        outkey = ('nmode', 'gb', 'pb', 'rism std', 'rism gf')
        basename = ('%s_nm.out', '%s_gb.mdout', '%s_pb.mdout', '%s_rism.mdout', '%s_rism.mdout')

        if self.INPUT['interaction_entropy']:
            if not INPUT['mutant_only']:
                self.calc_types['ie'] = IEout()
            if INPUT['alarun']:
                self.calc_types.mutant['ie'] = IEout()
        if self.INPUT['c2_entropy']:
            if not INPUT['mutant_only']:
                self.calc_types['c2'] = C2out()
            if INPUT['alarun']:
                self.calc_types.mutant['c2'] = C2out()

        for i, key in enumerate(outkey):
            if not INPUT[triggers[i]]:
                continue
            # Non-mutant
            if not INPUT['mutant_only']:
                self.calc_types[key] = {'complex': outclass[i](self.pre + basename[i] % 'complex', self.INPUT,
                                                               self.mpi_size, self.using_chamber)}
                if not self.stability:
                    self.calc_types[key]['receptor'] = outclass[i](self.pre +
                                                                   basename[i] % 'receptor', self.INPUT, self.mpi_size,
                                                                   self.using_chamber)
                    self.calc_types[key]['ligand'] = outclass[i](self.pre +
                                                                 basename[i] % 'ligand', self.INPUT, self.mpi_size,
                                                                 self.using_chamber)
                    self.calc_types[key]['delta'] = BindClass(
                        self.calc_types[key]['complex'],
                        self.calc_types[key]['receptor'],
                        self.calc_types[key]['ligand'],
                        self.INPUT['verbose'], self.using_chamber)

                    if key in ['gb', 'pb', 'rism std', 'rism gf']:
                        if 'ie' in self.calc_types:
                            edata = self.calc_types[key]['delta'].data['DELTA G gas']
                            ie = InteractionEntropyCalc(edata, self,
                                                        self.pre + f"{key.replace(' ', '_')}_iteraction_entropy.dat")
                            self.calc_types['ie'].data[key] = {'data': ie.data, 'iedata': ie.iedata,
                                                               'ieframes': ie.ieframes, 'sigma': ie.ie_std}
                        if 'c2' in self.calc_types:
                            edata = self.calc_types[key]['delta'].data['DELTA G gas']
                            c2 = C2EntropyCalc(edata, self, self.pre + f"{key.replace(' ', '_')}_c2_entropy.dat")
                            self.calc_types['c2'].data[key] = {'c2data': c2.c2data, 'sigma': c2.ie_std,
                                                               'c2_std': c2.c2_std, 'c2_ci': c2.c2_ci}
                            # self.calc_types[self.key]['delta'].data['DELTA G gas']
                else:
                    self.calc_types[key]['complex'].fill_composite_terms()
            # Time for mutant
            if INPUT['alarun']:
                self.calc_types.mutant[key] = {'complex':
                                                      outclass[i](self.pre + 'mutant_' + basename[i] % 'complex',
                                                                  self.INPUT, self.mpi_size, self.using_chamber)}
                if not self.stability:
                    self.calc_types.mutant[key]['receptor'] = outclass[i](
                        self.pre + 'mutant_' + basename[i] % 'receptor',
                        self.INPUT, self.mpi_size, self.using_chamber)
                    self.calc_types.mutant[key]['ligand'] = outclass[i](
                        self.pre + 'mutant_' + basename[i] % 'ligand',
                        self.INPUT, self.mpi_size, self.using_chamber)
                    self.calc_types.mutant[key]['delta'] = BindClass(
                        self.calc_types.mutant[key]['complex'],
                        self.calc_types.mutant[key]['receptor'],
                        self.calc_types.mutant[key]['ligand'],
                        self.INPUT['verbose'], self.using_chamber)
                    if key in ['gb', 'pb', 'rism std', 'rism gf']:
                        if 'ie' in self.calc_types.mutant:
                            edata = self.calc_types.mutant[key]['delta'].data['DELTA G gas']
                            mie = InteractionEntropyCalc(edata, self, self.pre + 'mutant_' +
                                                         f"{key.replace(' ', '_')}_iteraction_entropy.dat")
                            self.calc_types.mutant['ie'].data[key] = {'data': mie.data, 'iedata': mie.iedata,
                                                                      'ieframes': mie.ieframes, 'sigma': mie.ie_std}
                        if 'c2' in self.calc_types.mutant:
                            edata = self.calc_types.mutant[key]['delta'].data['DELTA G gas']
                            c2 = C2EntropyCalc(edata, self, self.pre + 'mutant_' +
                                               f"{key.replace(' ', '_')}_c2_entropy.dat")
                            self.calc_types.mutant['c2'].data[key] = {'c2data': c2.c2data, 'sigma': c2.ie_std,
                                                                      'c2_std': c2.c2_std, 'c2_ci': c2.c2_ci}
                else:
                    self.calc_types.mutant[key]['complex'].fill_composite_terms()

        if INPUT['decomprun']:
            self.calc_types.decomp = self._get_decomp()

    def _get_decomp(self):
        from GMXMMPBSA.amber_outputs import (DecompOut, PairDecompOut, DecompBinding,
                                             PairDecompBinding, MultiTrajDecompBinding,
                                             MultiTrajPairDecompBinding)
        outkey = ('gb', 'pb')
        triggers = ('gbrun', 'pbrun')
        basename = ('%s_gb.mdout', '%s_pb.mdout')
        INPUT, FILES = self.INPUT, self.FILES
        multitraj = bool(self.FILES.receptor_trajs or self.FILES.ligand_trajs)
        # Single trajectory
        if not multitraj:
            # Per-residue
            if self.INPUT['idecomp'] in [1, 2]:
                BindingClass = DecompBinding
                SingleClass = DecompOut
            # Pairwise
            else:
                BindingClass = PairDecompBinding
                SingleClass = PairDecompOut
        else:  # Multiple trajectories
            # Per-residue
            if self.INPUT['idecomp'] in [1, 2]:
                BindingClass = MultiTrajDecompBinding
                SingleClass = DecompOut
            # Pairwise
            else:
                BindingClass = MultiTrajPairDecompBinding
                SingleClass = PairDecompOut

        if not hasattr(self, 'resl'):
            from GMXMMPBSA.utils import res2map
            from copy import deepcopy
            import re
            masks, res_list, order_list, _ = res2map(FILES.complex_index, FILES.complex_fixed)
            self.resl = res_list

            if INPUT['alarun']:
                # to change the self.resl to get the mutant label in decomp analysis
                mut = re.split(r":\s*|/\s*", INPUT['mutant_res'])

                self.resl['MUT_COM'] = deepcopy(self.resl['COM'])
                for r in self.resl['MUT_COM']:
                    if r.string.split(':')[0::2] == mut:
                        r.name = INPUT['mutant']
                        break
                self.resl['MUT_REC'] = deepcopy(self.resl['REC'])
                self.resl['MUT_LIG'] = deepcopy(self.resl['LIG'])
                for r in self.resl['MUT_REC']:
                    if r.string.split(':')[0::2] == mut:
                        r.name = INPUT['mutant']
                        break
                for r in self.resl['MUT_LIG']:
                    if r.string.split(':')[0::2] == mut:
                        r.name = INPUT['mutant']
                        break

        return_data = type('calc_types', (dict,), {'mutant': {}})()
        for i, key in enumerate(outkey):
            if not INPUT[triggers[i]]:
                continue
            if not self.INPUT['mutant_only']:
                return_data[key] = {'complex': SingleClass(self.pre + basename[i] % 'complex',
                                 self.FILES.complex_prmtop, INPUT['surften'],
                                 False, self.mpi_size, INPUT['dec_verbose']).get_data(self.numframes, self.resl['COM'])}
                if not self.stability:
                    return_data[key]['receptor'] = SingleClass(self.pre + basename[i] % 'receptor',
                                                               self.FILES.receptor_prmtop, INPUT['surften'],
                                                               False, self.mpi_size, INPUT['dec_verbose']).get_data(
                        self.numframes, self.resl['REC'])
                    return_data[key]['ligand'] = SingleClass(self.pre + basename[i] % 'ligand',
                                                               self.FILES.ligand_prmtop, INPUT['surften'],
                                                               False, self.mpi_size, INPUT['dec_verbose']).get_data(
                        self.numframes, self.resl['LIG'])

            if INPUT['alarun']:
                # Do mutant
                return_data.mutant[key] = {'complex': SingleClass(self.pre + 'mutant_' + basename[i] % 'complex',
                                                           self.FILES.complex_prmtop, INPUT['surften'],
                                                           False, self.mpi_size, INPUT['dec_verbose']).get_data(
                    self.numframes, self.resl['MUT_COM'])}
                if not self.stability:
                    return_data.mutant[key]['receptor'] = SingleClass(self.pre + 'mutant_' + basename[i] % 'receptor',
                                                               self.FILES.receptor_prmtop, INPUT['surften'],
                                                               False, self.mpi_size, INPUT['dec_verbose']).get_data(
                        self.numframes, self.resl['MUT_REC'])
                    return_data.mutant[key]['ligand'] = SingleClass(self.pre + 'mutant_' + basename[i] % 'ligand',
                                                             self.FILES.ligand_prmtop, INPUT['surften'],
                                                             False, self.mpi_size, INPUT['dec_verbose']).get_data(
                        self.numframes, self.resl['MUT_LIG'])
        return return_data
# Local methods

def excepthook(exception_type, exception_value, tb):
    """
    Replaces sys.excepthook so fatal exceptions kill all MPI threads and we can
    control the printing of tracebacks. Those are helpful for debugging purposes,
    but may be unsightly to users. debug_printlevel set above controls this
    behavior
    """
    import traceback
    global _debug_printlevel, _stderr, _mpi_size, _rank
    if _debug_printlevel > 1 or not isinstance(exception_type, MMPBSA_Error):
        traceback.print_tb(tb)
    _stderr.write('%s: %s\n' % (exception_type.__name__, exception_value))
    if _mpi_size > 1:
        _stderr.write('Error occured on rank %d.' % _rank + os.linesep)
    _stderr.write('Exiting. All files have been retained.' + os.linesep)
    _MPI.COMM_WORLD.Abort(1)


def interrupt_handler(signal, frame):
    """ Handles interrupt signals for a clean exit """
    global _MPI, _stderr
    _stderr.write('\n%s interrupted! Program terminated. All files are kept.\n' %
                  os.path.split(sys.argv[0])[1])
    _MPI.COMM_WORLD.Abort(1)


def setup_run():
    """
    Replace the uncaught exception handler to control traceback printing. Also
    add a signal handler for a SIGINT (Ctrl-C). However, we only want to do this
    if we're running gmx_MMPBSA -- for the API, we don't want to clobber the
    users' python environments like this.
    """
    sys.excepthook = excepthook
    signal.signal(signal.SIGINT, interrupt_handler)

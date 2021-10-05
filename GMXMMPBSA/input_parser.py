"""
This is a module that contains functions responsible for parsing the
input file for gmx_MMPBSA. It must be included with gmx_MMPBSA to
ensure proper functioning.
"""

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

from GMXMMPBSA.exceptions import InputError, InternalError
import re

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

class Variable(object):
    """ Base variable class. It has a name and a single value """

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def __init__(self, varname, dat_type=int, default=None, chars_to_match=4,
                 case_sensitive=False, description=''):
        """ Initializes the variable type. Sets the default value as well as
          specifying how many characters are required by the parser to trigger
          recognition
        """
        # Catch illegalities
        if not dat_type in (int, str, float, list):
            raise InputError('Variable has unknown data type %s' % dat_type.__name__)

        # You can't match more characters than you have characters!
        chars_to_match = min(chars_to_match, len(varname))

        self.name = varname
        self.datatype = dat_type
        if default is not None:
            if self.datatype is str:
                self.value = default.replace("'", '').replace('"', '')
            elif self.datatype is list:
                self.value = [x.strip() for x in re.split("(?<!\d)[,;](?!\d)", default.replace('"', '').replace("'", ''))]
            else:
                self.value = self.datatype(default)
        else:
            self.value = None
        self.tomatch = chars_to_match
        self.case_sensitive = case_sensitive
        self.description = description

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def __str__(self):
        """ Prints statistics for the variable """
        string = 'Variable name:  %s\n' % self.name
        string += 'Variable type:  %s\n' % self.datatype
        string += 'Variable value: %s\n' % self.value
        string += 'Matching chars: %s\n' % self.tomatch
        string += 'Description:    %s\n' % self.description
        return string

    def help_str(self, length):
        """ returns the string [<name> = <value>.... # description] """
        if self.datatype is str:
            valstring = '%s = "%s"' % (self.name, self.value)
        else:
            valstring = '%s = %s' % (self.name, self.value)
        valstring += ' ' + '.' * (length - len(valstring) - 2) + ' '
        return valstring + '# %s' % self.description

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def __eq__(self, teststring):
        """ Determines if a variable string matches this variable """

        if len(teststring) > len(self.name):
            return False

        if len(teststring) < self.tomatch:
            return False

        myvar = self.name
        if not self.case_sensitive:
            myvar = self.name.lower()
            teststring = teststring.lower()

        return myvar[:len(teststring)] == teststring

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def __ne__(self, teststring):
        """ Not equal """
        return not self.__eq__(teststring)

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def SetValue(self, value):
        """ Sets the value of the variable """
        if self.datatype is str:
            self.value = value.replace('"', '').replace("'", '')
        elif self.datatype is list:
            self.value = [x.strip() for x in re.split("(?<!\d)[,;](?!\d)", value.replace('"', '').replace("'", ''))]
        else:
            self.value = self.datatype(value)


# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

class Namelist(object):
    """ Sets up a namelist. This holds many different Variables, and these
       variables will only be recognized when parsing this particular namelist.
       Set up to mimic the behavior of a Fortran namelist (so that the input is
       similar to the rest of Amber). Some of the known deficiencies:

         o the body of the namelist cannot start on the same line as the start
           or end of the namelist

         o the end of the namelist must be &end or / and must be on its own line

         o It will not (yet) recognize array lengths -- those are simply parsed
           as strings
   """

    MIN_CHARS_TO_MATCH = 4

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def __init__(self, trigger, full_name, to_match=3):
        """ Sets up the list of variables, which is just the trigger for now. The
          trigger is a logical variable that gets set to true if this namelist
          is parsed. Open() trips the trigger if it exists. It can be passed in
          as anything that evaluates to False if it doesn't exist.
      """
        self.trigger = trigger
        self.variables = {}
        if self.trigger is not None:
            self.variables = {self.trigger: False}
        self.open = False
        self.full_name = full_name
        self.to_match = to_match

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def __eq__(self, nml):
        """ A namelist is equal if the name matches properly """
        return nml == self.full_name[:len(nml)] and len(nml) >= \
               min(self.to_match, len(self.full_name))

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def __ne__(self, nml):
        """ Not equal """
        return not self.__eq__(nml)

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def addVariable(self, varname, datatype, default=None, description=None):
        """ Adds a variable to this namelist. It checks to make sure that it's
          going to create a conflict with an existing variable.
        """

        if varname in list(self.variables.keys()):
            raise InternalError('Duplicated variable %s in Namelist' % varname)

        # See if we need to update the minimum number of characters that any
        # variables need based on similarities with this variable
        tomatch = self.MIN_CHARS_TO_MATCH
        for var in list(self.variables.keys()):
            # Trigger never appears, so ignore it
            if var == self.trigger: continue
            hit_difference = False
            for i in range(min(len(var), len(varname))):
                if var[i] == varname[i]: continue
                # At this point, they differ. Update the existing variable if
                # necessary here
                hit_difference = True
                if i + 1 > self.variables[var].tomatch:
                    self.variables[var].tomatch = i + 1
                tomatch = max(tomatch, i + 1)
                break
            # Now handle the case where one variable is a substring of the other
            if not hit_difference:
                if len(varname) > len(var):
                    self.variables[var].tomatch = len(var)
                    tomatch = max(len(var), tomatch)
                else:
                    self.variables[var].tomatch = max(self.variables[var].tomatch,
                                                      len(varname))
                    tomatch = len(varname)
                    break
        self.variables[varname] = Variable(varname, datatype, default, tomatch,
                                           description=description)

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def Open(self):
        """ Signifies that the namelist is open """
        if self.open:
            raise InputError('Namelist already open. Cannot open before closing')

        if self.trigger: self.variables[self.trigger] = True
        self.open = True

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def __str__(self):
        """
        Prints out the full contents of this namelist in the Fortran namelist
        format
        """
        maxlen = max([len(v) + len(str(self.variables[v].value))
                      for v in self.variables if v is not self.trigger]) + 7
        maxlen = max(maxlen, 25)
        retstr = '&%s\n' % self.full_name
        for variable in self.variables:
            if variable is self.trigger: continue
            retstr += '  %s\n' % self.variables[variable].help_str(maxlen)
        return retstr + '/'


# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

class InputFile(object):
    """ Defines the Input File and parses it. You have to add stuff to the parser
       via addNamelist. Use it as follows:

       input = InputFile()

       input.addNamelist('gb', 'gb', [['saltcon', float, 0], ...],
                         trigger='gbrun')
       input.addNamelist('ala', 'alanine_scanning', [['mutant', int, 0]],
                         trigger='alarun')

       INPUT = input.Parse('mmpbsa.in')
   """

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def __init__(self):
        """ Initializes the input file, sets up empty arrays/dictionaries """
        self.ordered_namelist_keys = []
        self.namelists = {}
        self.text = ''  # text of the given input file

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def __str__(self):
        """ Prints out the input file """
        if not self.text:
            return

        ret_text = self.text.replace('\n', '\n|')  # Add | to start of each line

        return ('|Input file:\n|---------------------------------------' +
                '-----------------------\n|' + ret_text +
                '-----------------------------------------------------' +
                '---------\n')

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def print_contents(self, destination):
        """ Prints the contents of the input file """
        # Open a file to write to if need be
        if hasattr(destination, 'write'):
            dest = destination
        else:
            dest = open(destination, 'w')
        for namelist in self.ordered_namelist_keys:
            destination.write('%s\n' % self.namelists[namelist])
        # Close the file if we opened it.
        if dest is not destination:
            dest.close()

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def addNamelist(self, name, full_name, variable_list, trigger=None):
        """ Adds a namelist to the input file that will be parsed. Variable list
          must be an array of arrays. Each array element must be an array that
          has the information [varname, datatype, default, chars to match]. The
          'trigger' is the logical variable that gets set to true if this
          namelist is specified in the input file.
        """

        if name in self.ordered_namelist_keys:
            raise InputError('Namelist %s defined multiple times' % name)

        self.ordered_namelist_keys.append(name)
        self.namelists[name] = Namelist(trigger, full_name)

        for var in variable_list:

            if not isinstance(var, (list, tuple)) or len(var) != 4:
                raise InputError('variables in variable_list must be lists of ' +
                                 'length 4. [varname, datatype, default, description]')

            self.namelists[name].addVariable(var[0], var[1], var[2], var[3])

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def _full_namelist_name(self, nml):
        """ Determines what the full namelist name is. We try to make as many
          allowances as possible. We will match the first 3 characters and
          replace all _'s with
      """
        nml = nml.replace(' ', '_')  # replaces spaces with _'s
        for key in self.ordered_namelist_keys:
            if self.namelists[key] == nml: return key

        raise InputError('Unrecognized namelist %s' % nml)

    # -#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#-#

    def Parse(self, filename):
        """
        This subroutine parses the input file. Only data in namelists are
          parsed, and all namelists must be set prior to calling this routine.

          It will create a dictionary of Input variables for all variables in
          all namelists. They all flood the same namespace. If there are any
          conflicts between variables in namelists, an error will be raised.
          Make sure all input variables are unique!
        """
        from os.path import exists

        # Make sure our file exists

        if filename is None:
            raise InputError("No input file was provided!")
        if not exists(filename):
            raise InputError("Can't find input file (%s)" % filename)

        # Load the whole thing into memory. This should be plenty short enough.
        lines = open(filename, 'r').readlines()

        # Save the text of the input file so we can echo it back later
        self.text = ''.join(lines)

        # We will loop through the input file three times:
        #
        # 1st: Load all of the data into an array (namelist_fields)
        # 2nd: Combine multi-element values (to allow commas in input variables)
        # 3rd: Loop through the fields to change the values of the variables.

        declared_namelists = []  # keep track of the namelists we've found so far
        namelist_fields = []  # entries in a given namelist
        innml = False  # are we in a namelist now? Don't enter multiple

        # split up the input file into separate fields by comma

        for line in lines:
            # Skip title lines (we are flexible here) and comments
            if not innml and not line.strip().startswith('&'):
                continue
            if line.strip().startswith('#') or line.strip().startswith('!'):
                continue

            # Catch some errors
            if innml and line.strip().startswith('&'):
                raise InputError('Invalid input. Terminate each namelist prior ' +
                                 'to starting another one.')

            # End of a namelist
            elif innml and line.strip() in ['/', '&end']:
                innml = False

            # Now if we finally find a namelist
            elif not innml and line.strip().startswith('&'):
                innml = True
                namelist = line.strip()[1:].lower()
                namelist = self._full_namelist_name(namelist)

                if namelist in declared_namelists:
                    raise InputError('Namelist %s specified multiple times' %
                                     namelist)

                self.namelists[namelist].Open()
                declared_namelists.append(namelist)
                namelist_fields.append([])

            # We are in a namelist here, now fill in the fields
            elif innml:
                items = line.strip().split(',')

                # Screen any blank fields
                j = 0
                while j < len(items):
                    items[j] = items[j].strip()
                    if len(items[j]) == 0:
                        items.pop(j)
                    else:
                        j += 1

                namelist_fields[len(namelist_fields) - 1].extend(items)

            # end if [elif innml]

        # end for line in lines

        # Combine any multi-element fields into the last field that has a = in it

        begin_field = -1
        for i in range(len(namelist_fields)):
            for j in range(len(namelist_fields[i])):
                if not '=' in namelist_fields[i][j]:
                    if begin_field == -1:
                        raise InputError('Invalid input file! Error reading ' +
                                         'namelist %s' % declared_namelists[i])
                    else:
                        namelist_fields[i][begin_field] += \
                            ',%s' % namelist_fields[i][j]
                else:
                    begin_field = j

        # Now parse through the items to add them to the master dictionary. Note
        # that thanks to the last step, all data in namelist_fields will be
        # contained within fields that have a '='. All others can be ignored

        for i in range(len(namelist_fields)):
            for j in range(len(namelist_fields[i])):

                if not '=' in namelist_fields[i][j]:
                    continue
                else:
                    var = namelist_fields[i][j].split('=')
                    var[0] = var[0].strip()
                    var[1] = var[1].strip()

                    # Now we have to loop through all variables in that namelist to
                    # see if this is the variable we want.

                    found = False
                    for key in list(self.namelists[declared_namelists[i]].variables.keys()):
                        if self.namelists[declared_namelists[i]].variables[key] == \
                                var[0]:
                            self.namelists[declared_namelists[i]].variables[key]. \
                                SetValue(var[1])
                            found = True
                            break

                    if not found:
                        raise InputError('Unknown variable %s in &%s' % (var[0], declared_namelists[i]))

        # Now it's time to fill the INPUT dictionary

        INPUT = {}

        for nml in self.ordered_namelist_keys:
            for var in list(self.namelists[nml].variables.keys()):

                # Here, the triggers are just bool types, so protect from accessing
                # an attribute that doesn't exist! We only allow Variable types and
                # bool types

                var_object = self.namelists[nml].variables[var]
                try:
                    INPUT[var] = self.namelists[nml].variables[var].value
                except AttributeError:
                    if isinstance(var_object, bool):
                        INPUT[var] = var_object
                    else:
                        raise InputError('Disallowed namelist variable type')

        return INPUT


# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

# Define the MM/PBSA input file here
input_file = InputFile()

strip_mask = ':WAT,Cl*,CIO,Cs+,IB,K*,Li+,MG*,Na+,Rb+,CS,RB,NA,F,CL'

# Add namelists with a list of variables. The variables are added to the
# namelists in lists. The entries are:
# [<variable name> <variable type> <default value> <# of characters to match>]

input_file.addNamelist('general', 'general',
                       [
                           ['assign_chainID', int, 0, 'Assign chains ID'],
                           ['debug_printlevel', int, 0, 'Increase debugging info printed'],
                           ['endframe', int, 9999999, 'Last frame to analyze'],
                           ['qh_entropy', int, 0, 'Do quasi-harmonic calculation'],
                           ['interaction_entropy', int, 0, 'Do Interaction Entropy calculation'],
                           ['ie_segment', int, 25, 'Trajectory segment to calculate interaction entropy'],
                           ['c2_entropy', int, 0, 'Do C2 Entropy calculation'],
                           ['c2_segment', int, 25, 'Trajectory segment to calculate c2 entropy'],
                           ['exp_ki', float, 0, 'Experimental Ki in nM'],
                           ['full_traj', int, 0, 'Print a full traj. AND the thread trajectories'],
                           ['gmx_path', str, '', 'Force to use this path to get GROMACS executable'],
                           ['interval', int, 1, 'Number of frames between adjacent frames analyzed'],
                           ['ions_parameters', int, 1, 'Define ions parameters to build the Amber topology'],
                           ['keep_files', int, 2, 'How many files to keep after successful completion'],
                           ['forcefields', list, 'oldff/leaprc.ff99SB, leaprc.gaff', 'Define the force field to build '
                                                                                   'the Amber topology'],
                           ['netcdf', int, 0, 'Use NetCDF intermediate trajectories'],
                           ['overwrite_data', int, 0, 'Defines whether the gmxMMPBSA data will be overwritten'],
                           ['PBRadii', int, 3, 'Define PBRadii to build amber topology from GROMACS files'],
                           # ['receptor_mask', str, None, 'Amber mask of receptor atoms in complex prmtop'],
                           # ['search_path', str, '', 'Look for intermediate programs in all of PATH'],
                           ['save_mode', int, 1, 'Save mode'],
                           ['solvated_trajectory', int, 1, 'Define if it is necessary to cleanup the trajectories'],
                           ['startframe', int, 1, 'First frame to analyze'],
                           ['strip_mask', str, strip_mask, 'Amber mask to strip from solvated prmtop'],
                           ['sys_name', str, '', 'System name'],
                           ['temperature', float, 298.15, 'Temperature to calculate Binding Free Energy '
                                                          'from Ki and interaction entropy'],
                           ['use_sander', int, 0, 'Use sander to compute energies'],
                           ['verbose', int, 1, 'How many energy terms to print in the final output']
                       ], trigger=None)

input_file.addNamelist('gb', 'gb',
                       [
                           ['igb', int, 5, 'GB model to use'],
                           ['extdiel', float, 78.3, 'External dielectric constant for sander'],
                           ['saltcon', float, 0, 'Salt concentration (M)'],
                           ['surften', float, 0.0072, 'Surface tension'],
                           ['rgbmax', float, 999.0, 'Distance cutoff in Angstroms to use when computing effective '
                                                    'GB radii'],
                           ['intdiel', float, 1.0, 'Internal dielectric constant for sander'],
                           ['ifqnt', int, 0, 'Use QM on part of the system'],
                           ['qm_theory', str, '', 'Semi-empirical QM theory to use'],
                           ['qm_residues', str, '', 'Residues to treat with QM'],
                           ['qmcharge_com', int, 0, 'Charge of QM region in complex'],
                           ['qmcharge_lig', int, 0, 'Charge of QM region in ligand'],
                           ['qmcharge_rec', int, 0, 'Charge of QM region in receptor'],
                           ['qmcut', float, 9999, 'Cutoff in the QM region'],
                           ['surfoff', float, 0.0, 'Surface tension offset'],
                           ['molsurf', int, 0, 'Use Connelly surface (\'molsurf\' program)'],
                           ['msoffset', float, 0.0, 'Offset for molsurf calculation'],
                           ['probe', float, 1.4, 'Solvent probe radius for surface area calc']
                       ], trigger='gbrun')

input_file.addNamelist('pb', 'pb',
                       [
                           ['ntb', int, 0, 'Apply PBC conditions?'],
                           ['cut', float, 999.0, 'Nonbonded cutoff in Angstroms'],
                           ['nsnb', int, 99999, 'Determines the frequency of nonbonded list updates when igb=0 and '
                                                'nbflag=0'],
                           ['imin', int, 5, 'Decide whether to perform MD, Minimization, or Trajectory '
                                            'Post-Processing'],
                           ['maxcyc', int, 1, 'The maximum number of cycles of minimization'],
                           ['ioutfm', int, 0, 'The format of coordinate and velocity trajectory files (mdcrd, mdvel '
                                              'and inptraj).'],
                           ['ntx', int, 1, 'Option to read the initial coordinates, velocities and box size from the '
                                           'inpcrd file'],
                           ['inp', int, 2, 'Nonpolar solvation method'],
                           ['smoothopt', int, 1, 'Instructs PB how to set up dielectric values for finite-difference '
                                                 'grid edges that are located across the solute/solvent dielectric '
                                                 'boundary'],
                           ['radiopt', int, 1, 'Use optimized radii?'],
                           ['npbopt', int, 0, 'Use NonLinear PB solver?'],
                           ['solvopt', int, 1, 'Select iterative solver'],
                           ['linit', int, 1000, 'Number of SCF iterations'],
                           ['nfocus', int, 2, 'Electrostatic focusing calculation'],
                           ['fscale', int, 8, 'Set the ratio between the coarse and fine grid spacings in an '
                                              'electrostatic focussing calculation'],
                           ['indi', float, 1, 'Internal dielectric constant'],
                           ['exdi', float, 80, 'External dielectric constant'],
                           ['istrng', float, 0.0, 'Ionic strength (M)'],
                           ['prbrad', float, 1.4, 'Probe radius'],
                           ['iprob', float, 2.0, 'Mobile ion probe radius (Angstroms) for ion accessible surface used '
                                                 'to define the Stern layer'],
                           ['accept', float, 0.001, 'Sets the iteration convergence criterion (relative to the initial '
                                                    'residue)'],
                           ['fillratio', float, 4, 'See "fillratio" in AmberTools/PBSA manual'],
                           ['scale', float, 2.0, '1/scale = grid spacing for the finite difference solver '
                                                 '(default = 1/2 Å)'],
                           ['bcopt', int, 5, 'Boundary condition option'],
                           ['eneopt', int, 2, 'Compute electrostatic energy and forces'],
                           ['cutnb', float, 0.0, 'Cutoff for nonbonded interations'],
                           ['sprob', float, 0.557, 'Solvent probe radius for solvent accessible surface area (SASA) '
                                                   'used to compute the dispersion term'],
                           ['cavity_surften', float, 0.0378, 'Surface tension'],
                           ['cavity_offset', float, -0.5692, 'Offset for nonpolar solvation calc'],
                           ['emem', float, 1.0, 'Membrane dielectric constant'],
                           ['memopt', int, 0, 'Use PB optimization for membrane'],
                           # ['memoptzero', int, 0, 'Used in PB optimization for ligand'],
                           ['sasopt', int, 0, 'Molecular surface in PB implict model'],
                           ['mthick', float, 40.0, 'Membrane thickness'],
                           ['mctrdz', float, 0.0, 'Distance to offset membrane in Z direction'],
                           ['maxarcdot', int, 1500, 'Number of dots used to store arc dots per atom '],
                           ['poretype', int, 1, 'Use exclusion region for channel proteins'],
                           ['npbverb', int, 0, 'Option to turn on verbose mode'],
                           ['frcopt', int, 0, 'Output for computing electrostatic forces'],
                           ['cutfd', float, 5.0, 'Cutoff for finite-difference interactions'],
                           ['ipb', int, 2, 'Dielectric model for PB'],
                           ['sander_apbs', int, 0, 'Use sander.APBS?'],
                           ['pbtemp', float, 300, 'Temperature (in K) used for the PB equation'],
                           ['arcres', float, 0.25, 'The resolution (Å) to compute solvent accessible arcs'],
                           ['mprob', float, 2.70, 'Membrane probe radius in Å'],
                           ['nbuffer', float, 0, 'Sets how far away (in grid units) the boundary of the finite '
                                                 'difference grid is away from the solute surface'],
                           ['npbgrid', int, 1, 'Sets how often the finite-difference grid is regenerated'],
                           ['scalec', int, 0, 'Option to compute reaction field energy and forces'],
                           ['nsnba', int, 1, 'Sets how often atom-based pairlist is generated'],
                           ['phiout', int, 0, 'output spatial distribution of electrostatic potential '
                                              'for visualization?'],
                           ['phiform', int, 0, 'Controls the format of the electrostatic potential file'],
                           ['decompopt', int, 2, 'Option to select different decomposition schemes when INP = 2'],
                           ['use_rmin', int, 1, 'The option to set up van der Waals radii'],
                           ['vprob', float, 1.300, 'Solvent probe radius for molecular volume (the volume enclosed by '
                                                   'SASA) used to compute nonpolar cavity solvation free energy'],
                           ['rhow_effect', float, 1.129, 'Effective water density used in the non-polar dispersion '
                                                         'term calculation'],
                           ['use_sav', int, 1, 'The option to use molecular volume (the volume enclosed by SASA) or '
                                               'to use molecular surface (SASA) for cavity term calculation'],
                           ['maxsph', int, 400, 'Approximate number of dots to represent the maximum atomic solvent '
                                                'accessible surface']
                       ], trigger='pbrun')

input_file.addNamelist('ala', 'alanine_scanning',
                       [
                           ['mutant_only', int, 0, 'Only compute mutant energies'],
                           ['mutant', str, 'ALA', 'Defines if Alanine or Glycine scanning will be performed'],
                           ['mutant_res', str, '', 'Which residue will be mutated'],
                           ['cas_intdiel', int, 0, 'Change the intdiel value based on which aa is mutated'],
                           ['intdiel_nonpolar', int, 1, 'intdiel for nonpolar residues'],
                           ['intdiel_polar', int, 3, 'intdiel for polar residues'],
                           ['intdiel_positive', int, 5, 'intdiel for positive charged residues'],
                           ['intdiel_negative', int, 5, 'intdiel for negative charged residues']
                       ], trigger='alarun')

input_file.addNamelist('nmode', 'nmode',
                       [
                           ['dielc', float, 1, 'Dielectric constant'],
                           ['drms', float, 0.001, 'Minimization gradient cutoff'],
                           ['maxcyc', int, 10000, 'Maximum number of minimization cycles'],
                           ['nminterval', int, 1, 'Interval to take snapshots for normal mode analysis'],
                           ['nmendframe', int, 1000000, 'Last frame to analyze for normal modes'],
                           ['nmode_igb', int, 1, 'GB model to use for normal mode calculation'],
                           ['nmode_istrng', float, 0, 'Ionic strength for GB model (M)'],
                           ['nmstartframe', int, 1, 'First frame to analyze for normal modes']
                       ], trigger='nmoderun')

input_file.addNamelist('decomp', 'decomposition',
                       [
                           ['csv_format', int, 1, 'Write decomposition data in CSV format'],
                           ['dec_verbose', int, 0, 'Control energy terms are printed to the output'],
                           ['idecomp', int, 0, 'Which type of decomposition analysis to do'],
                           ['print_res', str, 'within 6', 'Which residues to print decomposition data for']
                       ], trigger='decomprun')

input_file.addNamelist('rism', 'rism',
                       [
                           ['closure', str, 'kh', 'Closure equation to use'],
                           ['buffer', float, 14, 'Distance between solute and edge of grid'],
                           ['grdspc', float, 0.5, 'Grid spacing'],
                           ['solvcut', float, None, 'Cutoff of the box'],
                           ['tolerance', float, 1.0e-5, 'Convergence tolerance'],
                           ['closureorder', int, 1, 'Order of closure if PSE'],
                           ['ng', str, '-1,-1,-1', 'Number of grid points'],
                           ['solvbox', str, '-1,-1,-1', 'Box limits'],
                           ['polardecomp', int, 0, 'Break solv. energy into polar and nonpolar terms'],
                           ['rism_verbose', int, 0, 'Control how much 3D-RISM info to print'],
                           ['thermo', str, 'std', 'Type of thermodynamic analysis to do'],

                           ['asympCorr', int, 1, 'Turn off long range asymptotic corrections for thermodynamic '
                                                 'output only'],
                           ['mdiis_del', float, 0.7, 'MDIIS step size'],
                           ['mdiis_restart', float, 10.0, 'If the current residual is mdiis_restart times larger than '
                                                          'the smallest residual in memory, then the MDIIS procedure '
                                                          'is restarted using the lowest residual solution stored in '
                                                          'memory'],
                           ['mdiis_nvec', int, 5, 'Number of previous iterations MDIIS uses to predict a new solution'],
                           ['maxstep', int, 10000, 'Maximum number of iterative steps per solution'],
                           ['npropagate', int, 5, 'Number of previous solutions to use in predicting a new solution'],
                           ['centering', int, 1, 'Select how solute is centered in the solvent box'],
                           ['entropicDecomp', int, 0, 'Decomposes solvation free energy into energy and entropy '
                                                      'components'],
                           ['pc+', int, 0, 'Compute the PC+/3D-RISM excess chemical potential functional'],
                           ['uccoeff', str, '0.0,0.0,0.0,0.0', 'Compute the UC excess chemical potential functional '
                                                               'with the provided coefficients'],
                           ['treeDCF', int, 1, 'Use direct sum or the treecode approximation to calculate the direct '
                                               'correlation function long-range asymptotic correction'],
                           ['treeTCF', int, 1, 'Use direct sum or the treecode approximation to calculate the total '
                                               'correlation function long-range asymptotic correction'],
                           ['treeCoulomb', int, 0, 'Use direct sum or the treecode approximation to calculate the '
                                                   'Coulomb potential energy'],
                           ['treeDCFOrder', int, 2, 'Treecode Taylor series order for the direct correlation function '
                                                    'long-range asymptotic correction'],
                           ['treeTCFOrder', int, 2, 'Treecode Taylor series order for the total correlation function '
                                                    'long-range asymptotic correction'],
                           ['treeCoulombOrder', int, 2, 'Treecode Taylor series order for the Coulomb potential energy'],
                           ['treeDCFN0', int, 500, 'Maximum number of grid points contained within the treecode leaf '
                                                   'clusters for the direct correlation function long-range asymptotic '
                                                   'correction'],
                           ['treeTCFN0', int, 500, 'Maximum number of grid points contained within the treecode leaf '
                                                   'clusters for the total correlation function long-range asymptotic '
                                                   'correction'],
                           ['treeCoulombN0', int, 500, 'Maximum number of grid points contained within the treecode '
                                                       'leaf clusters for the Coulomb potential energy'],
                           ['treeDCFMAC', float, 0.1, 'Treecode multipole acceptance criterion for the direct '
                                                      'correlation function long-range asymptotic correction'],
                           ['treeTCFMAC', float, 0.1, 'Treecode multipole acceptance criterion for the total '
                                                      'correlation function long-range asymptotic correction'],
                           ['treeCoulombMAC', float, 0.1, 'Treecode multipole acceptance criterion for the Coulomb '
                                                          'potential energy'],
                           ['asympKSpaceTolerance', float, -1.0, 'Determines the reciprocal space long range '
                                                                 'asymptotics cutoff distance based on the desired '
                                                                 'accuracy of the calculation'],
                           ['ljTolerance', float, -1.0, 'Determines the Lennard-Jones cutoff distance based on the '
                                                        'desired accuracy of the calculation']

                       ], trigger='rismrun')

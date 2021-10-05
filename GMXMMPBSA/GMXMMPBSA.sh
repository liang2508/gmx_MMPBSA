#!/usr/bin/env bash
#
#                          GPLv3 LICENSE INFO
#
# Copyright (C) 2020  Mario S. Valdes-Tresanco and Mario E. Valdes-Tresanco
# Copyright (C) 2014  Jason Swails, Bill Miller III, and Dwight McGee
#
#  Project: https://github.com/Valdes-Tresanco-MS/gmx_MMPBSA
#
#  This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.


# Since gmx_MMPBSA has many flags, we believe that this autocompletion can significantly improve productivity, be
# more user-friendly and reduce the number of unforced errors. That is why we created this script, which manages the
# autocompletion of the gmx_MMPBSA and gmx_MMPBSA_ana.
#
# Installation:
# Make sure the file has executed permissions.
# On Ubuntu, Debian, Linux Mint or related:
#   GUI:
#     Right-click on the file > Properties> Permissions> mark the checkbox "Allow to execute the file as a program"
#   or
#   Terminal:
#     chmod 755 /path_to_installed_gmx_MMPBSA/GMXMMPBSA.sh
#
# Once the file has execution permissions, enter the following command in the terminal:
#
#   source /path_to_installed_gmx_MMPBSA/GMXMMPBSA.sh
#
#  If you followed the gmx_MMPBSA installation instructions, this path should be as follows:
#  /path/to/ambertools/lib/python3.8/site-packages/GMXMMPBSA/GMXMMPBSA.sh
#
# If you want it to be activated automatically, add that command to your .bashrc
#
# NOTE: this script requires that gmx_MMPBSA and gmx_MMPBSA_ana be accessible in PATH
#
# Functioning:
# All you have to do is enter the name of the program in the terminal and press the tab key twice:
# gmx_MMPBSA <tab> <tab>


shopt -s extglob
_gmxmmpbsa_compl() {
local p c
COMPREPLY=() c=${COMP_WORDS[COMP_CWORD]} p=${COMP_WORDS[COMP_CWORD-1]}
if (( $COMP_CWORD <= 1 )) || [[ $c == -* ]];
 then
   COMPREPLY=( $(compgen  -W ' -h -v --input-file-help -O --overwrite -prefix -i -xvvfile -o -do -eo -deo -nogui -s
    --stability -cs -ci -cg -ct -cp -cr -rs -ri -rg -rt -rp -lm -ls -li -lg -lt -lp  -n -q -h -make-mdins -use-mdins
    -rewrite-output --clean --version --help' -- $c)); return 0; fi
case "$p" in

-xvvfile)          COMPREPLY=( $(compgen -S ' ' -X '!*@(.xvv|)' -f -- $c ; compgen -S '/' -d $c));;
-o)                COMPREPLY=( $(compgen -S ' ' -X '!*@(.dat|.txt|)' -f -- $c ; compgen -S '/' -d $c));;
-do)               COMPREPLY=( $(compgen -S ' ' -X '!*@(.dat|.txt|)' -f -- $c ; compgen -S '/' -d $c));;
-eo)               COMPREPLY=( $(compgen -S ' ' -X '!*@(.csv||)' -f -- $c ; compgen -S '/' -d $c));;
-deo)              COMPREPLY=( $(compgen -S ' ' -X '!*@(.csv|)' -f -- $c ; compgen -S '/' -d $c));;
-cs)               COMPREPLY=( $(compgen -S ' ' -X '!*@(.tpr|.pdb|.gro|)' -f -- $c ; compgen -S '/' -d $c));;
-ci)               COMPREPLY=( $(compgen -S ' ' -X '!*@(.ndx|)' -f -- $c ; compgen -S '/' -d $c));;
-ct)               COMPREPLY=( $(compgen -S ' ' -X '!*@(.xtc|.trr|.pdb|)' -f -- $c ; compgen -S '/' -d $c));;
-cp)               COMPREPLY=( $(compgen -S ' ' -X '!*@(.top|)' -f -- $c ; compgen -S '/' -d $c));;
-cr )              COMPREPLY=( $(compgen -S ' ' -X '!*@(.pdb|)' -f -- $c ; compgen -S '/' -d $c));;
-rs )              COMPREPLY=( $(compgen -S ' ' -X '!*@(.tpr|.pdb|.gro|)' -f -- $c ; compgen -S '/' -d $c));;
-ri )              COMPREPLY=( $(compgen -S ' ' -X '!*@(.ndx|)' -f -- $c ; compgen -S '/' -d $c));;
-rt )              COMPREPLY=( $(compgen -S ' ' -X '!*@(.xtc|.trr|.pdb|)' -f -- $c ; compgen -S '/' -d $c));;
-rp )              COMPREPLY=( $(compgen -S ' ' -X '!*@(.top|)' -f -- $c ; compgen -S '/' -d $c));;
-lm )              COMPREPLY=( $(compgen -S ' ' -X '!*@(.mol2|)' -f -- $c ; compgen -S '/' -d $c));;
-ls )              COMPREPLY=( $(compgen -S ' ' -X '!*@(.tpr|.pdb|.gro|)' -f -- $c ; compgen -S '/' -d $c));;
-li )              COMPREPLY=( $(compgen -S ' ' -X '!*@(.ndx|)' -f -- $c ; compgen -S '/' -d $c));;
-lt )              COMPREPLY=( $(compgen -S ' ' -X '!*@(.xtc|.trr|.pdb|)' -f -- $c ; compgen -S '/' -d $c));;
-lp )              COMPREPLY=( $(compgen -S ' ' -X '!*@(.top|)' -f -- $c ; compgen -S '/' -d $c));;
esac }
complete -F _gmxmmpbsa_compl gmx_MMPBSA

shopt -s extglob
_gmxmmpbsa_ana_compl() {
local p c
COMPREPLY=() c=${COMP_WORDS[COMP_CWORD]} p=${COMP_WORDS[COMP_CWORD-1]}
if (( $COMP_CWORD <= 1 )) || [[ $c == -* ]];
  then
    COMPREPLY=( $(compgen  -W ' -h -v --version --help -f --file -r --recursive' -- $c));
    return 0;
fi
case "$p" in
-f)       COMPREPLY=( $(compgen -S ' ' -X '!*@(_info|)' -f -- $c ; compgen -S '/' -d $c));;
--files)   COMPREPLY=( $(compgen -S ' ' -X '!*@(_info|)' -f -- $c ; compgen -S '/' -d $c));;
esac }
complete -F _gmxmmpbsa_ana_compl gmx_MMPBSA_ana

shopt -s extglob
_gmxmmpbsa_test_compl() {
local p c
COMPREPLY=() c=${COMP_WORDS[COMP_CWORD]} p=${COMP_WORDS[COMP_CWORD-1]}
if (( $COMP_CWORD <= 1 )) || [[ $c == -* ]];
  then
    COMPREPLY=( $(compgen  -W ' -h -v --version --help -f --folder -t --test -n --num_processors' -- $c));
    return 0;
fi
case "$p" in
-t)       COMPREPLY=( $(compgen -S ' ' -W $'all\nminimal\nprot_lig_st\nprot_prot\nprot_dna\nmemb_prot\nprot_glycan
            \nmetalloprot_pep\nprot_dna_rna_ions_lig\nprot_lig_charmm\nala_scan\nstability\ndecomp\nprot_lig_mt\nie
            \nnmode\n3drism' --  $c));;
esac }
complete -F _gmxmmpbsa_test_compl gmx_MMPBSA_test

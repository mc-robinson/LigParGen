from BOSSReader import BOSSReader, CheckForHs
from BOSS2OPENMM import mainBOSS2OPM
from BOSS2CHARMM import mainBOSS2CHARMM
from BOSS2GMX import mainBOSS2GMX
from BOSS2XPLOR import mainBOSS2XPLOR
from BOSS2Q import mainBOSS2Q
from CreatZmat import GenMolRep
import argparse
import pickle
import os
from shutil import which


def main(**kwargs):
    optim = args.opt
    clu = False
    charge = args.charge
    lbcc = False
    assert (which('obabel')
            is not None), "OpenBabel is Not installed or \n the executable location is not accessable"
    if os.path.exists('/tmp/' + args.resname + '.xml'):
        os.system('/bin/rm /tmp/' + args.resname + '.*')
    if args.lbcc:
        if args.charge == 0:
            lbcc = True
        else:
            lbcc = False
            print(
                '1.14*CM1A-LBCC is only available for neutral molecules\n Assigning unscaled CM1A charges')

    if args.smiles:
        os.chdir('/tmp/')
        smifile = open('%s.smi' % args.resname, 'w+')
        smifile.write('%s' % args.smiles)
        smifile.close()
        GenMolRep('%s.smi' % args.resname, optim, args.resname, charge)
        mol = BOSSReader('%s.z' % args.resname, optim, charge, lbcc)
    if args.mol:
        os.system('cp %s /tmp/' % args.mol)
        os.chdir('/tmp/')
        GenMolRep(args.mol, optim, args.resname, charge)
        mol = BOSSReader('%s.z' % args.resname, optim, charge, lbcc)
    if args.pdb:
        os.system('cp %s /tmp/' % args.pdb)
        os.chdir('/tmp/')
        GenMolRep(args.pdb, optim, args.resname, charge)
        mol = BOSSReader('%s.z' % args.resname, optim, charge, lbcc)
        clu = True
    assert (mol.MolData['TotalQ']['Reference-Solute'] ==
            charge), "PROPOSED CHARGE IS NOT POSSIBLE: SOLUTE MAY BE AN OPEN SHELL"
    assert(CheckForHs(mol.MolData['ATOMS'])
           ), "Hydrogens are not added. Please add Hydrogens"

    pickle.dump(mol, open(args.resname + ".p", "wb"))
    mainBOSS2OPM(args.resname, clu)
    print('DONE WITH OPENMM')
    mainBOSS2Q(args.resname, clu)
    print('DONE WITH Q')
    mainBOSS2XPLOR(args.resname, clu)
    print('DONE WITH XPLOR')
    mainBOSS2CHARMM(args.resname, clu)
    print('DONE WITH CHARMM/NAMD')
    mainBOSS2GMX(args.resname, clu)
    print('DONE WITH GROMACS')
    os.remove(args.resname + ".p")
    mol.cleanup()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='Converter.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
	SCRIPT TO CONVERT WRITE OPENMM PDB AND XML FILES 
	FROM BOSS ZMATRIX
	Created on Mon Feb 15 15:40:05 2016
	@author: Leela S. Dodda leela.dodda@yale.edu
	@author: William L. Jorgensen Lab 
	
	if using BOSS Zmat
	Usage: python Converter.py -z phenol.z -r PHN -c 0 

	if using MOL file 
	Usage: python Converter.py -m phenol.mol -r PHN -c 0

	if using PDB file 
	Usage: python Converter.py -p phenol.pdb -r PHN -c 0
	
	if using BOSS SMILES CODE 
	Usage: python Converter.py -s 'c1ccc(cc1)O' -r PHN -c 0 
	
	REQUIREMENTS:
	BOSS (need to set BOSSdir in bashrc and cshrc)
	Preferably Anaconda python with following modules
	pandas 
	argparse
	numpy
	RDKit for using with SMILES code
	"""
    )
    parser.add_argument(
        "-r", "--resname", help="Residue name from PDB FILE", type=str)
    parser.add_argument(
        "-s", "--smiles", help="Paste SMILES code from CHEMSPIDER or PubChem", type=str)
    parser.add_argument(
        "-m", "--mol", help="Submit MOL file from CHEMSPIDER or PubChem", type=str)
    parser.add_argument(
        "-p", "--pdb", help="Submit PDB file from CHEMSPIDER or PubChem", type=str)
    parser.add_argument(
        "-o", "--opt", help="Optimization or Single Point Calculation", type=int, choices=[0, 1, 2, 3])
    parser.add_argument("-c", "--charge", type=int,
                        choices=[0, -1, 1, -2, 2], help="0: Neutral <0: Anion >0: Cation ")
    parser.add_argument(
        "-l", "--lbcc", help="Use 1.14*CM1A-LBCC charges instead of 1.14*CM1A", action="store_true")
    args = parser.parse_args()
    main(**vars(args))

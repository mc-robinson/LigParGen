from LigParGen.BOSSReader import BOSSReader, CheckForHs
from LigParGen.BOSS2OPENMM import mainBOSS2OPM
from LigParGen.BOSS2CHARMM import mainBOSS2CHARMM
from LigParGen.BOSS2GMX import mainBOSS2GMX
from LigParGen.BOSS2XPLOR import mainBOSS2XPLOR
from LigParGen.BOSS2Q import mainBOSS2Q
from LigParGen.CreatZmat import GenMolRep
import argparse
import pickle
import os
# from shutil import which

def main():

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

    convert(**vars(args))

def convert(**kwargs):

    # set the default values
    options = {
            'opt' : 0,
            'smiles' : None,
            'zmat' : None, 
            'charge' : 0,
            'lbcc' : False,
            'mol' : None,
            'resname' : 'UNK',
            'pdb' : None }

    # update the default values based on the arguments
    options.update(kwargs)

    # set the arguments that you would used to get from argparse
    opt = options['opt']
    smiles = options['smiles']
    zmat = options['zmat']
    charge = options['charge']
    lbcc = options['lbcc']
    resname = options['resname']
    mol = options['mol']
    pdb = options['pdb']

    if opt != None:
        optim = opt
    else:
        optim = 0

    clu = False
    #charge = charge
    lbcc = False

    # assert (which('obabel')
            # is not None), "OpenBabel is Not installed or \n the executable location is not accessable"
    if os.path.exists('/tmp/' + resname + '.xml'):
        os.system('/bin/rm /tmp/' + resname + '.*')
    if lbcc:
        if charge == 0:
            lbcc = True
        else:
            lbcc = False
            print(
                '1.14*CM1A-LBCC is only available for neutral molecules\n Assigning unscaled CM1A charges')

    if smiles != None:
        os.chdir('/tmp/')
        smifile = open('%s.smi' % resname, 'w+')
        smifile.write('%s' % smiles)
        smifile.close()
        GenMolRep('%s.smi' % resname, optim, resname, charge)
        mol = BOSSReader('%s.z' % resname, optim, charge, lbcc)
    elif mol != None:
        os.system('cp %s /tmp/' % mol)
        os.chdir('/tmp/')
        GenMolRep(mol, optim, resname, charge)
        mol = BOSSReader('%s.z' % resname, optim, charge, lbcc)
    elif pdb != None:
        os.system('cp %s /tmp/' % pdb)
        os.chdir('/tmp/')
        GenMolRep(pdb, optim, resname, charge)
        mol = BOSSReader('%s.z' % resname, optim, charge, lbcc)
        clu = True
    assert (mol.MolData['TotalQ']['Reference-Solute'] ==
            charge), "PROPOSED CHARGE IS NOT POSSIBLE: SOLUTE MAY BE AN OPEN SHELL"
    assert(CheckForHs(mol.MolData['ATOMS'])
           ), "Hydrogens are not added. Please add Hydrogens"

    pickle.dump(mol, open(resname + ".p", "wb"))
    mainBOSS2OPM(resname, clu)
    print('DONE WITH OPENMM')
    mainBOSS2Q(resname, clu)
    print('DONE WITH Q')
    mainBOSS2XPLOR(resname, clu)
    print('DONE WITH XPLOR')
    mainBOSS2CHARMM(resname, clu)
    print('DONE WITH CHARMM/NAMD')
    mainBOSS2GMX(resname, clu)
    print('DONE WITH GROMACS')
    os.remove(resname + ".p")
    mol.cleanup()

if __name__ == "__main__":
  
    main()

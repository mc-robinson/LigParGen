# !/usr/bin/env python
# File name: run_ligpargen_regression_tests.py
# Author: Matt Robinson, Jorgensen Lab @ Yale
# Email: matthew.robinson@yale.edu
# Date created: 07/18/2017
# Python Version: 3.6

# to get the module imports to work, need to add .. to python path
import sys, os
testdir = os.path.dirname(__file__)
srcdir = '../LigParGen'
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

# import the package
#import LigParGen
# import the make_single_topology module
#from LigParGen import Converter
# now import all functions
#from LigParGen.Conve import *
import Converter

molecules_list = [['N#Cc1ccccc1', 'BCN', 0],
                    ['COc1ccccc1OC(=O)c1ccccc1', 'ZINC00000349', 0],
                    ['O=C([O-])CCCNC(=O)NC1CCCCC1', 'ZINC08754389', -1],
                    ['CCC(CO)[NH2+]CC[NH2+]C(CC)CO', 'ZINC19364219', 2],
                    ['O=C([O-])c1cc(Br)ccc1[N-]S(=O)(=O)c1ccc(Cl)cc1', 'ZINC35930493', -2]]
                    #['CC(C)CC[NH2+]CC1COc2ccccc2O1', 'ZINC04214115', 1],

def run_tests():


    FILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))

    # bool that will go to false if one of the tests failed
    passed_all_tests = True

    for mol in molecules_list:

        smiles_code = mol[0]
        ZINC_id = mol[1]
        charge = mol[2]

        zmat_path = os.path.join(FILE_DIR, 'data', ZINC_id + '.z')
        mol_path = os.path.join(FILE_DIR, 'data', ZINC_id + '.mol')
        pdb_path = os.path.join(FILE_DIR, 'data', ZINC_id + '.pdb')

        try:
            Converter.convert(smiles=smiles_code, charge=charge, resname='UNK')
        except:
            print("SMILES CODE FAILED ON " + ZINC_id)
            passed_all_tests = False

        try: 
            Converter.convert(pdb=pdb_path, charge=charge, resname='BCN')
        except:
            print("PDB CODE FAILED ON " + ZINC_id)
            passed_all_tests = False

        try: 
            Converter.convert(mol=mol_path, charge=charge, resname='UNK')
        except:
            print("MOL CODE FAILED ON " + ZINC_id)
            passed_all_tests = False

    if passed_all_tests:
        print('PASSED ALL TESTS')

if __name__ == '__main__':
    run_tests()






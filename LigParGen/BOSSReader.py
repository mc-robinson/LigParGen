from __future__ import print_function
import os
import numpy as np
import mol_boss
import pandas as pd
from collections import OrderedDict
from fepzmat import BCC_file2zmat
from CreatZmat import GenMolRep 

def VerifyMolandSave(mol,charge,resname):
    if mol is not None: 
        import pickle
        assert (mol.MolData['TotalQ']['Reference-Solute'] ==
                charge), "PROPOSED CHARGE IS NOT POSSIBLE: SOLUTE MAY BE AN OPEN SHELL"
        pickle.dump(mol, open(resname + ".p", "wb"))
    else: 
        print('Problem Detected Molecule Object Not created')
    return None

def LinCheck(fname):
    imp_dat = 0
    zlines  = open(fname,'r').readlines()
    for l in range(len(zlines)):
        if 'Geometry Variations follow ' in zlines[l]: imp_dat = l
    Atypes = []
    for l in zlines[1:imp_dat]:Atypes.append(l.split()[2])
    Atypes = np.array(Atypes,dtype=np.int)
    Atypes = Atypes[Atypes<0]
    Check =False
    if len(Atypes)>2: Check = True
    return Check

def mod_add_diheds(line):
    adihed = [int(l) for l in line.split()[0:4]]+[-1,-1]
    return(adihed)

def fix_add_dihed(zmat_name):
    flines = open('%s.z'%zmat_name,'r').readlines()
    imp_lines=[]
    for l in range(len(flines)):
        if 'Additional Dihedrals follow' in flines[l]:
            imp_lines.append(l+1)
        elif 'Domain Definitions follow' in flines[l]:
            imp_lines.append(l)
    ofile = open('%s_fixed.z'%zmat_name,'w+')
    for line in flines[0:imp_lines[0]]: ofile.write('%s\n'%(line.rstrip()))
    for line in flines[imp_lines[0]:imp_lines[1]]:
        m_ad = mod_add_diheds(line)
        ofile.write('%4d%4d%4d%4d%4d%4d\n'%(m_ad[0],m_ad[1],m_ad[2],m_ad[3],m_ad[4],m_ad[5]))
    for line in flines[imp_lines[1]:]: ofile.write('%s\n'%line.rstrip())
    ofile.close()
    return(None)

def CheckForHs(atoms):
    atype = [line.split()[1][0] for line in atoms]
    ans = False
    if ('H' in atype): ans = True 
    return ans 

def bcc_db(file):
    df = pd.read_csv(file)
    db = OrderedDict()
    for name, value in zip(df.BTYPE, df.BCC):
        db[name] = value
    return db


def Refine_PDB_file(fname):
    flines = open(fname, 'r+').readlines()
    pdb_lines = []
    for line in flines:
        if ('ATOM' in line) or ('HETATM' in line):
            line = line.rstrip()
            line = line.lstrip()
            if not 'DUM' in line:
                pdb_lines.append(line)
    return pdb_lines


def get_coos_from_pdb(pdb_dat):
    atoms = []
    coos = []
    for line in pdb_dat:
        atom = line.split()[2]
        x, y, z = line[28:56].split()
        atoms.append(atom)
        coos.append([float(x), float(y), float(z)])
    return (atoms, coos)

def pairing_func(a, b):
    ans = (a + b) * (a + b + 1) * 0.5
    if a > b:
        ans = ans + a
        pans = '%6d%6d' % (b, a)
    else:
        ans = ans + b
        pans = '%6d%6d' % (a, b)
    return (int(ans), pans)


def ucomb(vec, blist):
    res = 0
    for a in vec:
        vec.remove(a)
        for b in vec:
            ans = (a + b) * (a + b + 1) * 0.5
            if (ans + a in blist) or (ans + b in blist):
                res = res + 1
    return res


def tor_cent(vec, blist):
    db = {}
    for a in vec:
        na = 0
        for b in vec:
            ans = (a + b) * (a + b + 1) * 0.5
            if (ans + a in blist) or (ans + b in blist):
                na += 1
        db[a] = na
#    print(db)
    new_vec = list(sorted(db, key=db.__getitem__, reverse=True))
    return (new_vec)


def bossPdbAtom2Element(attype):
    elem = ''.join([i for i in attype[:-1] if not i.isdigit()])
    return elem


def bossElement2Mass(elem):
    symb2mass = {
        'H': 1.008,
        'F': 18.998403163,
        'Cl': 35.45,
        'Br': 79.904,
        'I': 126.90447,
        'O': 15.999,
        'S': 32.06,
        'N': 14.007,
        'P': 30.973761998,
        'C': 12.011,
        'Si': 28.085,
        'Na': 22.98976928,
        'SOD': 22.98976928,
        'K': 39.0983,
        'Mg': 24.305,
        'Ca': 40.078,
        'Mn': 54.938044,
        'Fe': 55.845,
        'Co': 58.933194,
        'Ni': 58.6934,
        'Cu': 63.546,
        'Zn': 65.38, }
    try:
        res = symb2mass[elem]
    except NameError:
        print("Mass for atom %s is not available \n add it to symb2mass dictionary")
    return res


def Refine_file(fname):
    flines = open(fname, 'r+')
    lines = []
    for line in flines:
        if line.rstrip():
            line = line.rstrip()
            line = line.lstrip()
            lines.append(line)
    flines.close()
    return lines


class BOSSReader(object):

    def __init__(self, zmatrix, optim, charge=0, lbcc=False):
        self.zmat = zmatrix
        self.impDat = {}
        self.MolData = {}
        self.refine_data(optim, charge, lbcc)

    def Get_OPT(self, optim, charge):
        assert os.path.isfile(
            self.zmat), 'File named %10s does not exist' % self.zmat
        assert ('BOSSdir' in os.environ) and os.path.isfile((os.environ[
            'BOSSdir'] + '/scripts/xZCM1A')), 'Please Make sure $BOSSdir is defined \n xZCM1A and related files are in scripts directory of BOSS'
        execs = {
             2: os.environ['BOSSdir'] + '/scripts/xZCM1A+2 > /tmp/olog',
             1: os.environ['BOSSdir'] + '/scripts/xZCM1A+  > /tmp/olog',
             0: os.environ['BOSSdir'] + '/scripts/xZCM1A > /tmp/olog',
            -1: os.environ['BOSSdir'] + '/scripts/xZCM1A-  > /tmp/olog',
            -2: os.environ['BOSSdir'] + '/scripts/xZCM1A-2 > /tmp/olog',
        }
        #print('MOLECULE HAS A CHARGE of %d' % charge)
        if optim > 0:
            print('Optimization level requested %d' % optim)
            for opt_lev in range(optim):
                print('Performing Stage %d of Charge Generation'%(opt_lev+1)) 
                execfile = execs[charge]
                coma = execfile + ' ' + self.zmat[:-2]
                os.system(coma)
                os.system('cp sum %s' % (self.zmat))
                execfile = os.environ['BOSSdir'] + '/scripts/xOPT > /tmp/olog'
                coma = execfile + ' ' + self.zmat[:-2]
                os.system(coma)
                os.system('cd /tmp;/bin/cp sum %s' % (self.zmat))
        execfile = os.environ['BOSSdir'] + '/scripts/xSPM > /tmp/olog'
        coma = execfile + ' ' + self.zmat[:-2]
        os.system(coma)
        os.system('cd /tmp;/bin/cp sum %s' % (self.zmat))
        return (None)

    def get_addihed(self, data):
        add = []
        nadd = 0
        for line in data:
            if line[0].isdigit():
                add.append(line.split()[0:4])
                nadd = nadd + 1
        return (add)

    def get_atinfo(self, data):
        ats = []
        nat = 0
        for line in data:
            if line[0].isdigit() and float(line.split()[2]) > 1:
                ats.append(line)
                nat += 1
        return (ats)

    def get_charge(self, data):
        TotQ = {}
        for line in data[1:]:
            words = line.split()
            TotQ['-'.join(words[:-1])] = round(float(words[-1]), 3)
#        print(TotQ)
        return TotQ

    def get_tors(self, data):
        tors = []
        ntor = 0
        for line in data:
            if 'All Solutes' in line:
                tors.append(line.split()[4:8])
                for tor in line.split()[4:8]:
                    if abs(float(tor)) > 0.0:
                        ntor = ntor + 1
        return (tors)

    def get_QLJ(self, data):
        qlj = []
        nqlj = 0
        for line in data:
            if 'All Solutes' in line and line[0].isalpha():
                qlj.append([line.split()[0], line.split()[2],
                            line.split()[3], line.split()[4]])
                nqlj += 1
        return (qlj)

    def get_angs(self, data):
        angs = {'cl1': [], 'cl2': [], 'cl3': [], 'R': [], 'K': []}
        nang = 0
        for line in data:
            if line[0].isdigit() and float(line.split()[4]) > 0:
                word = line.split()
                angs['cl1'].append(int(word[0]))
                angs['cl2'].append(int(word[1]))
                angs['cl3'].append(int(word[2]))
                angs['R'].append(float(word[3]))
                angs['K'].append(float(word[4]))
                nang = nang + 1
            #        print 'Total No of Non-zero Angles in BOSS is %d' % (nang)
        return (angs)

    def get_XYZ(self, data):
        XYZ = {'at_num': [], 'X': [], 'Y': [], 'Z': [], 'at_symb': []}
        for line in data:
            if line[0].isdigit() and len(line.split()) == 5:
                word = line.split()
                XYZ['at_num'].append(int(word[0]))
                XYZ['X'].append(float(word[1]))
                XYZ['Y'].append(float(word[2]))
                XYZ['Z'].append(float(word[3]))
                XYZ['at_symb'].append(float(word[4]))
        return XYZ

    def get_pairs(self, data):
        data = data[1:]
        plnos = []
        for i in range(0, len(data)):
            if 'Atom' in data[i]:
                plnos.append(i)
        plnos.append(len(data))
        pair_dat = {i: ' '.join(data[plnos[i]:plnos[i + 1]])
                    for i in range(len(plnos) - 1)}
        for nu in range(len(plnos) - 1):
            pair_dat[nu] = list(pair_dat[nu][10:].split())
            pair_dat[nu] = np.array([int(a) - 2 for a in pair_dat[nu]])
        pairs = []
        for k in pair_dat.keys():
            for j in pair_dat[k]:
                pairs.append('%6d%6d%6d\n' % (k - 1, j, 1))
        return pairs

    def get_bonds(self, data):
        bnds = {'cl1': [], 'cl2': [], 'RIJ': [], 'KIJ': [], 'TIJ': []}
        nbnd = 0
        for line in data:
            if line[0].isdigit() and float(line.split()[3]) > 0:
                word = line.split()
                bnds['cl1'].append(int(word[0]))
                bnds['cl2'].append(int(word[1]))
                bnds['RIJ'].append(float(word[2]))
                bnds['KIJ'].append(float(word[3]))
                bnds['TIJ'].append(line[-5:])
                nbnd += 1
            #        print 'Total No of Non-zero Bonds in BOSS is %d' % (nbnd)
        return (bnds)

    def prep_lbcc(self, bond_data, qdata):
        db = bcc_db('/Users/Sriram/Dropbox/Paprica/NAR/Code/Debug/bonds.csv')
        bnd_df = pd.DataFrame(bond_data)
        bnd_df = bnd_df[['cl1', 'cl2']]
        bnd_df.columns = ['I', 'J']
        q_df = pd.DataFrame(columns=['TY', 'Q'])
        q_df.loc[0] = ['1', 0.000]
        q_df.loc[1] = ['2', 0.000]
        for i in range(len(qdata)):
            q_df.loc[i + 2] = [qdata[i][0], float(qdata[i][1])]
        bond, cha, QBC1 = mol_boss.new_mol_info(db, q_df, bnd_df)
        lbcc_qdat = []
        for i in range(len(qdata)):
            lbcc_qdat.append(
                [qdata[i][0], str(cha.QBCC.values[i]), qdata[i][2], qdata[i][3]])
        bond.to_csv('LBCC_BONDS.csv', index=False)
        cha.to_csv('LBCC_CHARGES.csv', index=False)
        print(bond)
        print(cha)
        return np.array(cha.QBCC), lbcc_qdat

    def cleanup(self):
        os.system('cd /tmp;/bin/rm sum log olog out plt.pdb')

    def get_ImpDat(self, optim, charge):
        self.Get_OPT(optim, charge)
        odat = Refine_file('/tmp/out')
        sdat = Refine_file('/tmp/sum')
        MolData = {}
        impDat = {}
        MolData['PDB'] = Refine_file('/tmp/plt.pdb')
        for nl in range(len(odat)):
            if 'Z-Matrix for Reference Solutes' in odat[nl]:
                impDat['ATMinit'] = nl
            elif 'Net Charge' in odat[nl]:
                impDat['TotalQ'] = nl
            elif 'OPLS Force Field Parameters' in odat[nl]:
                impDat['ATMfinal'] = nl
                impDat['NBDinit'] = nl
            elif 'Fourier Coefficients' in odat[nl]:
                impDat['TORinit'] = nl
                impDat['NBDfinal'] = nl
            elif 'Bond Stretching Parameters' in odat[nl]:
                impDat['TORfinal'] = nl
                impDat['BNDinit'] = nl
            elif 'Angle Bending Parameters' in odat[nl]:
                impDat['BNDfinal'] = nl
                impDat['ANGinit'] = nl
            elif 'Non-bonded Pairs List' in odat[nl]:
                impDat['ANGfinal'] = nl
                impDat['PAIRinit'] = nl
            elif 'Solute 0:   X          Y          Z' in odat[nl]:
                impDat['XYZinit'] = nl
            elif 'Atom I      Atom J      RIJ' in odat[nl]:
                impDat['XYZfinal'] = nl
            elif 'Checking' in odat[nl]:
                impDat['PAIRfinal'] = nl
#### THIS PART IS READ FROM SUM FILE ###
        for ml in range(len(sdat)):
            if 'Additional Dihedrals follow' in sdat[ml]:
                impDat['ADDinit'] = ml
            elif 'Domain Definitions follow' in sdat[ml]:
                impDat['ADDfinal'] = ml
#### THIS PART IS READ FROM SUM FILE ###
        MolData['ATOMS'] = self.get_atinfo(
            odat[impDat['ATMinit']:impDat['ATMfinal']])
        MolData['Q_LJ'] = self.get_QLJ(
            odat[impDat['NBDinit']:impDat['NBDfinal']])
        MolData['BONDS'] = self.get_bonds(
            odat[impDat['BNDinit']:impDat['BNDfinal']])
        MolData['ANGLES'] = self.get_angs(
            odat[impDat['ANGinit']:impDat['ANGfinal']])
        MolData['TORSIONS'] = self.get_tors(
            odat[impDat['TORinit']:impDat['TORfinal']])
        MolData['ADD_DIHED'] = self.get_addihed(
            sdat[impDat['ADDinit']:impDat['ADDfinal']])
        MolData['XYZ'] = self.get_XYZ(
            sdat[impDat['XYZinit']:impDat['XYZfinal']])
        MolData['PAIRS'] = self.get_pairs(
            odat[impDat['PAIRinit']:impDat['PAIRfinal']])
        MolData['TotalQ'] = self.get_charge(
            odat[impDat['TotalQ']:impDat['TotalQ'] + 4])
        return MolData

    def refine_data(self, optim, charge, lbcc):
        if lbcc and (charge == 0):
            lbcc_MD = self.get_ImpDat(optim, charge)
            QLBCC, DATA_Q_LJ = self.prep_lbcc(
                lbcc_MD['BONDS'], lbcc_MD['Q_LJ'])
            lbcc_MD['Q_LJ'] = DATA_Q_LJ
            BCC_file2zmat(self.zmat, QLBCC,
                          oname='/tmp/%s_BCC.z' % self.zmat[:-2])
            os.system('mv %s.z %s_NO_LBCC.z' %
                      (self.zmat[:-2], self.zmat[:-2]))
            os.system('mv %s_BCC.z %s.z' % (self.zmat[:-2], self.zmat[:-2]))
            self.MolData = lbcc_MD
        elif lbcc and (charge != 0):
            print('LBCC IS SUPPORTED ONLY FOR NEUTRAL MOLECULES')
        else:
            self.MolData = self.get_ImpDat(optim, charge)
        return None

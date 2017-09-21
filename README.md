# LigParGen server 2.0 #

Python script to convert BOSS generated OPLS-AA/CM1A(-LBCC) parameters to:

- OPENMM PDB AND XML FILES,
- CHARMM RTF AND PRM FILES,
- GROMACS ITP AND GRO FILES,
- PDB2PQR PQR FILES,  
- MCPRO & BOSS ZMATRIX

### authors: ###

* [Leela S. Dodda](https://github.com/leelasd) - `<leela.dodda@yale.edu>`
* [Matt Robinson](https://github.com/mc-robinson) - `<matthew.robinson@yale.edu>`

### Usage ###

if using BOSS Zmat:
`python Converter.py -z phenol.z -r PHN -c 0` 

if using MOL file:
`python Converter.py -m phenol.mol -r PHN -c 0`

if using PDB file:
`python Converter.py -p phenol.pdb -r PHN -c 0`

if using BOSS SMILES CODE: 
`python Converter.py -s 'c1ccc(cc1)O' -r PHN -c 0` 

To ensure your version is working, `cd` into the `tests/` folder and run the following:
`python run_ligpargen_regression_tests.py`

### REQUIREMENTS: ###
- BOSS (need to set BOSSdir in bashrc and cshrc)
- Preferably Anaconda python with following modules
- pandas 
- argparse
- numpy
- RDKit for using with SMILES code

Additionally you must make changes to the following BOSS scripts

* xZCM1A
	* comment out everything after first single point calculation
* xMOLZ
	* change `default` to `varadd` in the line, `$BOSSdir/autozmat -i mdl -z default <${argv[1]}.mol >${argv[1]}.z`
* xPDBZ
	* same as for xMOLZ

### What more to do ? ###

-  **Fix issues with Linear Molecules (Fixed)**
-  Create BOSS2LAMMPS (IC)
-  Create BOSS2Q      (LSD??)
-  Create BOSS2AMBER  (JTR)
-  Create Halogen bond extra site feature
-  ** Create RelFEP setup for BOSS, MCPro, Gromacs and NAMD (Code is done by LSD & MR)**
-  Include RelFEP in server as **Alchemist** ?? (IC)

### Who do I talk to? ###

* Leela S. Dodda leela.dodda@yale.edu 
* Israel Cabeza de Vaca 
* Matthew Robinson 


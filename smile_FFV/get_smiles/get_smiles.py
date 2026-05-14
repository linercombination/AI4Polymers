import os
from rdkit import Chem
import openbabel


def pdb_to_smiles(pdb_file):
    """
    Converts a PDB file to SMILES notation using Open Babel.
    """
    # Open Babel转换PDB到SMILES
    ob_conversion = openbabel.OBConversion()
    ob_conversion.SetInFormat("pdb")
    ob_conversion.SetOutFormat("smiles")

    mol = openbabel.OBMol()
    ob_conversion.ReadFile(mol, pdb_file)
    smiles = ob_conversion.WriteString(mol)

    return smiles.strip()  # 去除尾部多余的空格或换行符


def replace_f_with_star(smiles):
    """
    Replaces 'F' in the SMILES with '*' to mark the connection points.
    """
    return smiles.replace('F', '*')


def process_pdb_files_in_folder(folder_path, output_file):
    """
    Processes all PDB files in a folder, converts them to SMILES,
    replaces 'F' with '*' and saves them to an output file.
    """
    smiles_dict = {}

    for filename in os.listdir(folder_path):
        if filename.endswith(".pdb"):
            pdb_path = os.path.join(folder_path, filename)
            smiles = pdb_to_smiles(pdb_path)
            modified_smiles = replace_f_with_star(smiles)
            smiles_dict[filename] = modified_smiles

    # Save the modified SMILES to the output file
    with open(output_file, 'w') as f:
        for pdb_file, smiles in smiles_dict.items():
            f.write(f"{pdb_file}: {smiles}\n")

    print(f"SMILES conversion completed and saved to {output_file}")


# Example usage:
folder_path = "PIM-PIs/mol_pdb"  # Replace with your folder path
output_file = "converted_smiles_PIM-PIs.txt"  # Output file for the SMILES strings

process_pdb_files_in_folder(folder_path, output_file)

import os
import openbabel


def pdb_to_smiles(pdb_file):
    """
    Convert a PDB file to SMILES notation using Open Babel.
    """
    ob_conversion = openbabel.OBConversion()
    ob_conversion.SetInFormat("pdb")
    ob_conversion.SetOutFormat("smiles")

    mol = openbabel.OBMol()
    ob_conversion.ReadFile(mol, pdb_file)
    smiles = ob_conversion.WriteString(mol)
    return smiles.strip()


def normalize_smiles(smiles):
    """
    Keep the converted SMILES as-is.

    Blindly replacing 'F' with '*' is unsafe for this project because many
    polymers here are genuinely fluorinated. If connection-point annotation is
    needed later, it should be done with a curated, polymer-specific rule rather
    than a character-level replacement.
    """
    return smiles


def process_pdb_files_in_folder(folder_path, output_file):
    """
    Process all PDB files in a folder, convert them to SMILES,
    and save them to an output file.
    """
    smiles_dict = {}

    for filename in os.listdir(folder_path):
        if filename.endswith(".pdb"):
            pdb_path = os.path.join(folder_path, filename)
            smiles = pdb_to_smiles(pdb_path)
            smiles_dict[filename] = normalize_smiles(smiles)

    with open(output_file, "w", encoding="utf-8") as f:
        for pdb_file, smiles in smiles_dict.items():
            f.write(f"{pdb_file}: {smiles}\n")

    print(f"SMILES conversion completed and saved to {output_file}")


# Example usage:
folder_path = "PIM-PIs/mol_pdb"  # Replace with your folder path
output_file = "converted_smiles_PIM-PIs.txt"  # Output file for the SMILES strings

process_pdb_files_in_folder(folder_path, output_file)

from rdkit import Chem
from rdkit.Chem import Draw


def smiles_to_image(smiles, output_image="molecule.png", size=(500, 500), kekule=True):
    """
    Converts a SMILES string to a 2D image, removes hydrogens and saves the image to a file.

    Args:
    smiles (str): The SMILES string.
    output_image (str): The output image file name.
    size (tuple): Image size (width, height).
    kekule (bool): If True, generates Kekule-style (single/double bonds) SMILES, else aromatic bonds.

    Returns:
    bool: True if the image was successfully generated, False otherwise.
    """
    # Parse SMILES string to molecule
    mol = Chem.MolFromSmiles(smiles, sanitize=True)
    if mol is None:
        print("Error: Cannot parse SMILES string.")
        return False

    # Remove hydrogen atoms to prevent them from being displayed
    mol = Chem.RemoveHs(mol)

    # Try to generate a nice 2D image
    try:
        # Optionally generate Kekule-style SMILES for better bond display
        if kekule:
            Chem.Kekulize(mol)

        # Generate and save the 2D image
        Draw.MolToFile(mol, output_image, size=size)
        print(f"Molecule image saved as: {output_image}")
        return True
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        return False


if __name__ == "__main__":
    # SMILES strings with complex structures
    smiles_1 = "c1(c(cc(cc1C)c1cc(c(n2c(=O)c3c(cc4c(oc5c(cc6c([C@@]7(c8c(cc9c(oc%10c(cc%11c(c(=O)n(c%11=O)*)c%10)o9)c8)[C@]6(c6c7cccc6)C(C)C)C(C)C)c5)o4)c3)c2=O)c(c1)C)C)C)*"
    #           C12C(=SC3=Nc4c(NC3[SH+]1)cc(c(c4)*)*)[C@]1(c3c([C@]2(CCC)c2c1cccc2)cc(c(c3)O*)O*)CCCC12C(=CC3=Nc4c(N=C3C1)cc(c(c4)*)*)[C@]1(c3c([C@]2(C(C)C)c2c1cccc2)cc(c(c3)O*)O*)C(C)C           C12=C([SH+]C3=[N]=c4c(=[N]=C3[SH+]1)cc(c(c4)*)*)[C@]1(c3c([C@]2(CCC)c2c1cccc2)cc(c(c3)O*)O*)CCC
    output_image = "molecule_1.png"

    # Generate 2D image
    success = smiles_to_image(smiles_1, output_image, size=(600, 600), kekule=True)
    if success:
        print("Molecule image generated successfully!")

import ast

def extract_animations(file_name, scene_name):
    """
    Mengekstrak pemanggilan self.play dan self.wait dari Scene yang ditentukan.
    Mengembalikan daftar tuple (line_number, animation_type, args).
    """

    with open(file_name, "r", encoding="utf-8") as f:
        source_code = f.read()

    tree = ast.parse(source_code)
    animations = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == scene_name:
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Attribute):
                    if subnode.func.attr in ["play", "wait"]:
                        line_number = subnode.lineno
                        animation_type = subnode.func.attr
                        args = [ast.unparse(arg) for arg in subnode.args] if hasattr(ast, 'unparse') else []
                        animations.append((line_number, animation_type, args))

    return animations

def count_animations(file_name, scene_name):
    """
    Menghitung jumlah self.play dan self.wait dalam Scene yang ditentukan.
    Langsung mencetak hasilnya.
    """
    animations = extract_animations(file_name, scene_name)
    play_count = sum(1 for _, anim, _ in animations if anim == "play")
    wait_count = sum(1 for _, anim, _ in animations if anim == "wait")

    print(f"Total animations: {play_count + wait_count}; self.play: {play_count}, self.wait: {wait_count}")

def list_animations(file_name, scene_name):
    """
    Menampilkan daftar self.play dan self.wait dalam Scene yang ditentukan,
    termasuk urutan eksekusi dan nomor baris. Hasilnya langsung dicetak.
    """
    animations = extract_animations(file_name, scene_name)

    if animations:
        print(f"Animations in {scene_name} (in order):")
        for idx, (line, anim_type, args) in enumerate(sorted(animations, key=lambda x: x[0]), start=0):
            print(f"{idx}. Line {line}: {anim_type}({', '.join(args)})")
    else:
        print("No animation is found.")

def extract_classes(file_name):
    """
    Mengekstrak semua nama kelas dalam file Python.
    Mengembalikan daftar nama kelas yang ditemukan.
    """
    with open(file_name, "r", encoding="utf-8") as f:
        source_code = f.read()

    tree = ast.parse(source_code)
    return [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
    
def extract_anim(file_name=None, scene_name=None):
    """
    Menganalisis animasi dalam Scene tertentu.
    Jika scene_name diberikan, mencetak jumlah self.play dan self.wait beserta daftar animasi.
    Jika tidak, mencetak daftar kelas yang tersedia dalam file.
    """
    if not file_name:
        print("Please provide the file name to use '--extract_anim' flag.")
        return
    
    if not file_name.lower().endswith(".py"):
        print("Error: The file must have a .py extension.")
        return
    
    if not scene_name:
        classes = extract_classes(file_name)
        if classes:
            n = len(classes)
            if n == 1:
                scene_name = classes[0]
                print(f"One scene is found: {scene_name}")
                count_animations(file_name, scene_name)
                list_animations(file_name, scene_name)
            else:
                print("Cannot extract animations. Please input a scene name!")
                print(f"Available classes in {file_name}:", ", ".join(classes))
                print(f"Example: manimgl {file_name} {classes[-1]} --extract_anim")
        else:
            print("No classes found in the file.")

        return
    
    scene_name = scene_name[0]
    count_animations(file_name, scene_name)
    list_animations(file_name, scene_name)

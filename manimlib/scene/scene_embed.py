from __future__ import annotations

import inspect
import pyperclip
import traceback
import ast
import textwrap

from IPython.terminal import pt_inputhooks
from IPython.terminal.embed import InteractiveShellEmbed

from manimlib.animation.fading import VFadeInThenOut
from manimlib.config import manim_config
from manimlib.constants import RED, DEG, T, F, TT
from manimlib.logger import log
from manimlib.mobject.mobject import Mobject
from manimlib.mobject.frame import FullScreenRectangle
from manimlib.module_loader import ModuleLoader

# play sound when error ocurred
import winsound

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from manimlib.scene.scene import Scene
    from manimlib.typing import ManimColor


class InteractiveSceneEmbed:
    def __init__(self, scene: Scene):
        self.scene = scene
        self.checkpoint_manager = CheckpointManager()

        self.shell = self.get_ipython_shell_for_embedded_scene()
        self.enable_gui()
        self.ensure_frame_update_post_cell()
        self.ensure_flash_on_error()
        if manim_config.embed.autoreload:
            self.auto_reload()
        self.last_executed_line = None

    def launch(self):
        self.shell()

    def get_ipython_shell_for_embedded_scene(self) -> InteractiveShellEmbed:
        """
        Create embedded IPython terminal configured to have access to
        the local namespace of the caller
        """
        # Triple back should take us to the context in a user's scene definition
        # which is calling "self.embed"
        caller_frame = inspect.currentframe().f_back.f_back.f_back

        # Update the module's namespace to include local variables
        module = ModuleLoader.get_module(caller_frame.f_globals["__file__"])
        module.__dict__.update(caller_frame.f_locals)
        module.__dict__.update(self.get_shortcuts())
        exception_mode = manim_config.embed.exception_mode

        return InteractiveShellEmbed(
            user_module=module,
            display_banner=False,
            xmode=exception_mode
        )

    def get_shortcuts(self):
        """
        A few custom shortcuts useful to have in the interactive shell namespace
        """
        scene = self.scene
        return dict(
            play=scene.play,
            wait=scene.wait,
            add=scene.add,
            remove=scene.remove,
            remove_all_except=scene.remove_all_except,
            clear=scene.clear,
            focus=scene.focus,
            save_state=scene.save_state,
            undo=scene.undo,
            redo=scene.redo,
            i2g=scene.i2g,
            i2m=scene.i2m,
            checkpoint_paste=self.checkpoint_paste,
            clear_checkpoints=self.checkpoint_manager.clear_checkpoints,
            reload=self.reload_scene,  # Defined below
            remove_last=scene.remove_last,
            mobject_names = scene.mobject_names,
            count_animations = self.count_animations,
            list_animations = self.list_animations,
            reload_background = self.reload_background,
            reload_skip = self.reload_skip,
            reload_script = self.reload_script,
            run_animation_number = self.run_animation_number,
            activate_autoreload = self.activate_autoreload,
        )

    def enable_gui(self):
        """Enables gui interactions during the embed"""
        def inputhook(context):
            while not context.input_is_ready():
                if not self.scene.is_window_closing():
                    self.scene.update_frame(dt=0)
            if self.scene.is_window_closing():
                self.shell.ask_exit()

        pt_inputhooks.register("manim", inputhook)
        self.shell.enable_gui("manim")

    def ensure_frame_update_post_cell(self):
        """Ensure the scene updates its frame after each ipython cell"""
        def post_cell_func(*args, **kwargs):
            if not self.scene.is_window_closing():
                self.scene.update_frame(dt=0, force_draw=True)

        self.shell.events.register("post_run_cell", post_cell_func)

    def ensure_flash_on_error(self):
        """Flash border, and potentially play sound, on exceptions"""
        def custom_exc(shell, etype, evalue, tb, tb_offset=None):
            # Show the error don't just swallow it
            shell.showtraceback((etype, evalue, tb), tb_offset=tb_offset)
            rect = FullScreenRectangle().set_stroke(RED, 30).set_fill(opacity=0)
            rect.fix_in_frame()
            winsound.MessageBeep()  # play sound when error ocurred
            self.scene.play(VFadeInThenOut(rect, run_time=0.5))

        self.shell.set_custom_exc((Exception,), custom_exc)

    def validate_syntax(self, file_path: str) -> bool:
        """
        Validates the syntax of a Python file without executing it.
        Returns True if syntax is valid, False otherwise.
        Prints syntax errors to the console if found.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()

            # Use compile() to check for syntax errors without executing
            compile(source_code, file_path, 'exec')
            return True

        except SyntaxError as e:
            print(f"\nSyntax Error in {file_path}:")
            print(f"  Line {e.lineno}: {e.text.strip() if e.text else ''}")
            print(f"  {' ' * (e.offset - 1 if e.offset else 0)}^")
            print(f"  {e.msg}")
            return False

        except Exception as e:
            print(f"\nError reading {file_path}: {e}")
            return False

    def reload_scene(self, embed_line: int | None = None, skip: bool = False) -> None:
        """
        Reloads the scene just like the `manimgl` command would do with the
        same arguments that were provided for the initial startup. This allows
        for quick iteration during scene development since we don't have to exit
        the IPython kernel and re-run the `manimgl` command again. The GUI stays
        open during the reload.

        If `embed_line` is provided, the scene will be reloaded at that line
        number. This corresponds to the `linemarker` param of the
        `extract_scene.insert_embed_line_to_module()` method.

        Before reload, the scene is cleared and the entire state is reset, such
        that we can start from a clean slate. This is taken care of by the
        run_scenes function in __main__.py, which will catch the error raised by the
        `exit_raise` magic command that we invoke here.

        Note that we cannot define a custom exception class for this error,
        since the IPython kernel will swallow any exception. While we can catch
        such an exception in our custom exception handler registered with the
        `set_custom_exc` method, we cannot break out of the IPython shell by
        this means.
        """
        # Get the current file path for syntax validation
        current_file = self.shell.user_module.__file__

        # Validate syntax before attempting reload
        if not self.validate_syntax(current_file):
            print("[ERROR] Reload cancelled due to syntax errors. Fix the errors and try again.")
            return

        # Update the global run configuration.
        run_config = manim_config.run
        run_config.is_reload = True
        if embed_line:
            run_config.embed_line = embed_line

        # skipping
        manim_config.scene.skip_animations = bool(skip)
        manim_config.scene.preview_while_skipping = True
        if skip == TT:
            manim_config.scene.preview_while_skipping = False

        print("Reloading...")
        self.shell.run_line_magic("exit_raise", "")

    def reload_skip(self, embed_line: int | None = None, preview: bool = False) -> None:
        # Update the global run configuration.
        manim_config.scene.skip_animations = True
        manim_config.scene.preview_while_skipping = preview
        manim_config.run.is_reload = True
        if embed_line:
            manim_config.run.embed_line = embed_line
        print("Reloading...")
        if preview:
            print("Skipping with preview")
        else:
            print("Skipping without preview")
        self.shell.run_line_magic("exit_raise", "")

    def reload_background(self, color: ManimColor, opacity: float = 1.0) -> None:
        manim_config.camera.background_color = color
        manim_config.camera.background_opacity = opacity
        manim_config.scene.skip_animations = True
        manim_config.scene.preview_while_skipping = False
        log.warning("This will NOT change background_color for rendering video.")
        log.warning("Use flag: -c [color] or custom_config.yml instead!")
        self.shell.run_line_magic("exit_raise", "")

    def reload_script(self, this_scene: bool=False) -> None:
        if this_scene:
            scene = [self.scene.__class__.__name__]
            manim_config.run.scene_names = scene
        else:
            manim_config.run.embed_line = None
            manim_config.run.scene_names = []

        self.shell.run_line_magic("exit_raise", "")

    def run_animation_number(
        self,
        start_index: int | None = None, 
        end_index: int | None = None,
        preview: bool = False
    ):
        """
        Menjalankan ulang animasi mulai dari ke-`start_index` hingga ke-`end_index`
        """
        if start_index is not None and end_index is None:
            end_index = start_index + 1  # Menangani input satu angka

        if start_index is None or end_index is None:
            print("You must provide at least one parameter!")
            return

        if start_index >= end_index or start_index < 0:
            print("Wrong input. 'start_index' must be non-negative and smaller than 'end_index'!")
            return
        
        start = start_index + 1
        end = end_index
        
        file_name = manim_config.run.file_name
        scene_name = manim_config.run.scene_names[0]
        
        construct_line = self.get_construct_line(file_name, scene_name)
        start_line = construct_line  # lines = f.readlines() starts from index 0
        
        animations = self.list_animations(return_list=True)
        for i, anim_data in enumerate(animations[start_index:end_index]):
            print(start_index + i, anim_data)
        print("\n")
        first_animation_line = animations[start - 1][0]
        lines = self.get_codes(file_name)
        code_to_run = "".join(lines[start_line:first_animation_line-1])
        dedented_code = textwrap.dedent(code_to_run) # Remove unnecessary indentation
        
        # this will handle all animations before the chosen animations
        manim_config.scene.preview_while_skipping = preview
        manim_config.run.is_reload = True
        # the code below is important for a reset because after the frame manipulation, 
        # especially after using 3D scene, the settings will remain.
        self.scene.clear()
        fovy: float = 45 * DEG # see: CameraFrame __init__
        self.scene.frame.to_default_state()
        self.scene.frame.set_field_of_view(fovy)
        self.scene.always_depth_test = True
        with self.scene.temp_config_change(skip=True, record=False, progress_bar=True):
            self.shell.run_cell(dedented_code)

        # Now, it will handle the chosen animations
        last_animation_line = animations[end - 1][0]
        last_animation_start = last_animation_line
        last_animation_end = self.get_end_line_of_play(file_name, last_animation_start)
        code_to_run_ = "".join(lines[first_animation_line-1:last_animation_end])
        dedented_code_ = textwrap.dedent(code_to_run_) # Remove unnecessary indentation
        
        with self.scene.temp_config_change(skip=False, record=False, progress_bar=True):
            self.shell.run_cell(dedented_code_)
            
        self.last_executed_line = last_animation_end - 1

    def auto_reload(self):
        """Enables reload the shell's module before all calls"""
        def pre_cell_func(*args, **kwargs):
            new_mod = ModuleLoader.get_module(self.shell.user_module.__file__, is_during_reload=True)
            self.shell.user_ns.update(vars(new_mod))

        self.shell.events.register("pre_run_cell", pre_cell_func)

    def checkpoint_paste(
        self,
        skip: bool = False,
        record: bool = False,
        progress_bar: bool = True
    ):
        with self.scene.temp_config_change(skip, record, progress_bar):
            self.checkpoint_manager.checkpoint_paste(self.shell, self.scene)

    def activate_autoreload(self, autoreload: bool = True) -> None:
        manim_config.embed.autoreload = autoreload
        manim_config.scene.skip_animations = True
        manim_config.scene.preview_while_skipping = False
        self.shell.run_line_magic("exit_raise", "")

    def list_animations(self, return_list=False):
        """
        Mengembalikan atau menampilkan daftar self.play dan self.wait dalam Scene yang ditentukan 
        di manim_config.run.scene_names, termasuk urutan eksekusi dan nomor baris.
        
        Jika return_list=True, maka fungsi mengembalikan daftar animasi dalam bentuk list.
        Jika return_list=False, maka daftar animasi hanya dicetak di layar.
        """
        file_name = manim_config.run.file_name
        scene_names = manim_config.run.scene_names
        
        if not scene_names:
            print("Tidak ada scene yang ditemukan dalam manim_config.run.scene_names.")
            return [] if return_list else None

        target_scene = scene_names[0]

        with open(file_name, "r", encoding="utf-8") as f:
            source_code = f.read()

        tree = ast.parse(source_code)
        animations = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == target_scene:
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Attribute):
                        if subnode.func.attr in ["play", "wait"]:
                            line_number = subnode.lineno
                            animation_type = subnode.func.attr
                            args = [ast.unparse(arg) for arg in subnode.args] if hasattr(ast, 'unparse') else []
                            animations.append((line_number, animation_type, args))

        animations.sort(key=lambda x: x[0])

        if return_list:
            return animations  # 🔹 Kembalikan daftar animasi sebagai list
        else:
            if animations:
                print(f"Animations in {target_scene} (in order):")
                for idx, (line, anim_type, args) in enumerate(animations, start=0):
                    print(f"{idx}. Line {line}: {anim_type}({', '.join(args)})")
            else:
                print("No animation is found.")
                
    def count_animations(self):
        """
        Menghitung jumlah pemanggilan play dan wait dalam scene yang dipilih,
        lalu mencetak hasilnya dalam format tertentu.
        
        Returns:
            dict: Dictionary dengan jumlah 'play' dan 'wait'.
        """
        animations = self.list_animations(return_list=True)
        
        count = {"play": 0, "wait": 0}
        for _, anim_type, _ in animations:
            if anim_type in count:
                count[anim_type] += 1
        
        total = sum(count.values())
        print(f"Total animations: {total}; self.play: {count['play']}, self.wait: {count['wait']}")
        
        return count

    def get_codes(self, file_name):
        """
        Membaca isi file dan mengembalikan daftar baris.
        """
        with open(file_name, "r", encoding="utf-8") as f:
            return f.readlines()

    def get_construct_line(self, file_name, scene_name):
        """
        Mengembalikan nomor baris di mana metode construct dideklarasikan dalam scene tertentu.
        """
        
        lines = self.get_codes(file_name)
        source_code = "".join(lines)  # Gabungkan kembali menjadi string
        tree = ast.parse(source_code)

        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == scene_name:
                for subnode in node.body:
                    if isinstance(subnode, ast.FunctionDef) and subnode.name == "construct":
                        return subnode.lineno  # Nomor baris `construct`
        
        return None  # Jika tidak 

    def get_end_line_of_play(self, file_name, start_line: int):
        """Menentukan baris akhir dari self.play() yang dimulai pada start_line menggunakan AST."""
        
        lines = self.get_codes(file_name)
        source_code = "".join(lines)  # Gabungkan kembali menjadi string
        tree = ast.parse(source_code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr):  # Mencari ekspresi seperti self.play(...)
                if hasattr(node, "lineno") and node.lineno == start_line:
                    if hasattr(node, "end_lineno"):  # Python 3.8+
                        return node.end_lineno  # Baris akhir yang akurat
        return start_line  # Jika tidak ditemukan, anggap hanya 1 baris

class CheckpointManager:
    def __init__(self):
        self.checkpoint_states: dict[str, list[tuple[Mobject, Mobject]]] = dict()

    def checkpoint_paste(self, shell, scene):
        """
        Used during interactive development to run (or re-run)
        a block of scene code.

        If the copied selection starts with a comment, this will
        revert to the state of the scene the first time this function
        was called on a block of code starting with that comment.
        """
        code_string = pyperclip.paste()
        checkpoint_key = self.get_leading_comment(code_string)
        self.handle_checkpoint_key(scene, checkpoint_key)
        shell.run_cell(code_string)

    @staticmethod
    def get_leading_comment(code_string: str) -> str:
        leading_line = code_string.partition("\n")[0].lstrip()
        if leading_line.startswith("#"):
            return leading_line
        return ""

    def handle_checkpoint_key(self, scene, key: str):
        if not key:
            return
        elif key in self.checkpoint_states:
            # Revert to checkpoint
            scene.restore_state(self.checkpoint_states[key])

            # Clear out any saved states that show up later
            all_keys = list(self.checkpoint_states.keys())
            index = all_keys.index(key)
            for later_key in all_keys[index + 1:]:
                self.checkpoint_states.pop(later_key)
        else:
            self.checkpoint_states[key] = scene.get_state()

    def clear_checkpoints(self):
        self.checkpoint_states = dict()

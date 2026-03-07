#!/usr/bin/env python
from addict import Dict

from manimlib import __version__
from manimlib.config import manim_config
from manimlib.config import parse_cli
import manimlib.extract_scene
from manimlib.extract_animation import extract_anim
from manimlib.utils.cache import clear_cache
from manimlib.window import Window


from IPython.terminal.embed import KillEmbedded


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from argparse import Namespace


def run_scenes():
    """
    Runs the scenes in a loop and detects when a scene reload is requested.
    """
    # Create a new dict to be able to upate without
    # altering global configuration
    scene_config = Dict(manim_config.scene)
    run_config = manim_config.run
    print("config.py: args.write_file = any([args.write_file, args.open, args.finder]) [see: parse_cli()]")
    print("config.py: show_in_window = not args.write_file [see: update_run_config()]")
    print("\033[33mshow_in_window\033[0m:",run_config.show_in_window)
    print("window_config:",manim_config.window)
    instance = """\033[91mNOTE\033[0m:
    1. An instance of a Scene is created in exctract_scene.py by function scene_from_class(), 
       by passing argument: **scene_config.
    2. An instance of Window is created in __main__.py if show_in_window = True, 
       by passing argument: **window_config, then it is included in scene_config."""
    print(instance)

    if run_config.show_in_window:
        # Create a reusable window
        window = Window(**manim_config.window)
        scene_config.update(window=window)

    while True:
        try:
            # Blocking call since a scene may init an IPython shell()
            scenes = manimlib.extract_scene.main(scene_config, run_config)
            # nama_scenes = [obj.__class__.__name__ for obj in scenes]
            # print(nama_scenes)
            print(f"\033[33mscene_config:\033[0m\n{scene_config}")
            print(f"\033[33mrun_config:\033[0m\n{run_config}\n")

            for scene in scenes:
                scene.run()
            return
        except KillEmbedded:
            # Requested via the `exit_raise` IPython runline magic
            # by means of the reload_scene() command
            scene_config.skip_animations = manim_config.scene.skip_animations
            scene_config.preview_while_skipping = manim_config.scene.preview_while_skipping
            # skip_animations and preview_while_skipping can be changed during reload_scene() or others
            scene_config.start_at_animation_number = manim_config.scene.start_at_animation_number
            # pass
        except KeyboardInterrupt:
            break


def main():
    """
    Main entry point for ManimGL.
    """
    print(f"ManimGL \033[32mv{__version__}\033[0m")

    args = parse_cli()
    if args.version and args.file is None:
        return
    if args.clear_cache:
        clear_cache()

    if args.extract_anim:
        extract_anim(args.file, args.scene_names)
        return

    run_scenes()


if __name__ == "__main__":
    main()

## Project Description
 - AI image generator using v1-5-pruned.safetensors
 - PyQt6 Desktop Application(currently launches from the terminal).
 - This project is in the very early stages of development and is not ready to be taken seriously.
 - Live preview, steps, cfg, seed, positive/negative prompts, resolution, token counter(SD1.5 only supports 77 token prompts), status on the left, progress on the right, sampler selection(not working yet). Empty tabs for Talk-2-It, Structure-It, and Train-It.

## Prerequisites
 - python >=3.12
 - pip for installing dependencies/requirements.
 - A GPU with enough VRAM to load the full-merged-checkpoint(UNet, VAE, Clip), 8GB Suggested-Minimum.

## Installation (Ubuntu 26.04)

 - Step (1): clone the repository.
```bash
git clone https://github.com/RobertSullender/Artificial-It.git
```

 - Step (2): change directory.
```bash
cd Artificial-It
```

 - Step (3): create a python virtual environment.
```bash
python3 -m venv .venv
```

 - Step (4): activate your virtual environment.
```bash
source .venv/bin/activate
```

 - Step (5): install requirements.
```bash
pip install -r requirements.txt
```

 - Step (6): start the program.
```bash
python src/main.py
```

 - Step (7): Download the model.
    - https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5/blob/main/v1-5-pruned.safetensors
    - Place the v1-5-pruned.safetensors file in the auto-generated models folder.

## Notes
 - Closing the terminal used to start the application will kill the application.
 - Use deactivate to kill the python virtual environment.
```bash
deactivate
```
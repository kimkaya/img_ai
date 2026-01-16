#!/usr/bin/env python3
"""
IMG AI Studio - Real AI Art Generation
Transforms photos into actual anime/cartoon artwork using Stable Diffusion
"""

import argparse
import sys
import os
from pathlib import Path

def print_progress(percent, message=""):
    print(f"PROGRESS:{percent}", flush=True)
    if message:
        print(f"STATUS:{message}", flush=True)

def main():
    parser = argparse.ArgumentParser(description='IMG AI - Art Generation')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--style', default='anime', choices=['anime', 'cartoon', 'ghibli', 'comic'])
    parser.add_argument('--strength', type=float, default=0.55)
    parser.add_argument('--prompt', default='')
    parser.add_argument('--steps', type=int, default=30)
    parser.add_argument('--guidance', type=float, default=7.0)

    args = parser.parse_args()

    print_progress(5, "Initializing...")

    if not os.path.exists(args.input):
        print(f"ERROR: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print_progress(10, "Loading AI libraries...")

    try:
        import torch
        import torch_directml
        from PIL import Image
        from diffusers import StableDiffusionImg2ImgPipeline

    except ImportError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print_progress(15, "Setting up GPU...")

    dml = torch_directml.device()
    print(f"GPU: {dml}", flush=True)

    print_progress(20, "Loading AI model...")

    # Style configurations - 자연스러운 스타일 변환
    # strength 낮게, guidance 낮게 = 원본 유지하면서 부드러운 스타일
    style_configs = {
        'anime': {
            'model': 'Ojimi/anime-kawai-diffusion',
            'prompt': 'anime style',
            'negative': 'deformed, distorted, disfigured, bad anatomy, wrong anatomy, ugly, disgusting, blurry, noisy',
            'guidance': 5.0,
            'strength': 0.35
        },
        'cartoon': {
            'model': 'nitrosocke/mo-di-diffusion',
            'prompt': 'mo-di style',
            'negative': 'deformed, distorted, disfigured, bad anatomy, ugly, blurry, noisy',
            'guidance': 5.0,
            'strength': 0.35
        },
        'ghibli': {
            'model': 'nitrosocke/Ghibli-Diffusion',
            'prompt': 'ghibli style',
            'negative': 'deformed, distorted, disfigured, bad anatomy, ugly, blurry, noisy',
            'guidance': 5.0,
            'strength': 0.35
        },
        'comic': {
            'model': 'ogkalu/Comic-Diffusion',
            'prompt': 'comic style',
            'negative': 'deformed, distorted, disfigured, bad anatomy, ugly, blurry, noisy',
            'guidance': 5.0,
            'strength': 0.35
        }
    }

    config = style_configs.get(args.style, style_configs['anime'])

    try:
        print_progress(25, f"Loading: {config['model']}")

        pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
            config['model'],
            torch_dtype=torch.float32,
            safety_checker=None,
            requires_safety_checker=False
        )

        # Use default scheduler (compatible with all models)
        pipe = pipe.to(dml)

        print_progress(50, "Model ready")

    except Exception as e:
        print(f"ERROR: Model loading failed: {e}", file=sys.stderr)
        sys.exit(1)

    print_progress(55, "Processing image...")

    try:
        init_image = Image.open(args.input).convert("RGB")
        w, h = init_image.size

        # Optimal size for SD 1.5 (512x512)
        max_size = 512
        if w > h:
            new_w = max_size
            new_h = int(h * (max_size / w))
        else:
            new_h = max_size
            new_w = int(w * (max_size / h))

        new_w = (new_w // 8) * 8
        new_h = (new_h // 8) * 8
        new_w = max(new_w, 384)
        new_h = max(new_h, 384)

        init_image = init_image.resize((new_w, new_h), Image.LANCZOS)
        print(f"Image: {new_w}x{new_h}", flush=True)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print_progress(60, "Generating artwork...")

    # Build prompt (간단하게 - 원본 이미지 구조 유지)
    full_prompt = config['prompt']
    if args.prompt:
        full_prompt += args.prompt

    # 사용자가 설정한 strength 사용, 기본값이면 config 사용
    strength = args.strength
    guidance = config['guidance']

    print(f"Style: {args.style}", flush=True)
    print(f"Strength: {strength}", flush=True)

    try:
        with torch.no_grad():
            result = pipe(
                prompt=full_prompt,
                negative_prompt=config['negative'],
                image=init_image,
                strength=strength,
                guidance_scale=guidance,
                num_inference_steps=args.steps
            )

        output_image = result.images[0]

    except Exception as e:
        print(f"ERROR: Generation failed: {e}", file=sys.stderr)
        sys.exit(1)

    print_progress(90, "Saving...")

    try:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_image.save(str(output_path), "PNG")
        print(f"Saved: {output_path}", flush=True)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print_progress(100, "Done!")
    print("SUCCESS", flush=True)

    del pipe

if __name__ == "__main__":
    main()

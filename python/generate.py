#!/usr/bin/env python3
"""
IMG AI Studio - 이미지 스타일 변환
RTX 5060 Ti 16GB 최적화
"""

import argparse
import sys
import os
from pathlib import Path

# 진행률 출력 함수
def print_progress(percent, message=""):
    print(f"PROGRESS:{percent}", flush=True)
    if message:
        print(f"STATUS:{message}", flush=True)

def main():
    parser = argparse.ArgumentParser(description='IMG AI - 이미지 스타일 변환')
    parser.add_argument('--input', required=True, help='입력 이미지 경로')
    parser.add_argument('--output', required=True, help='출력 이미지 경로')
    parser.add_argument('--style', default='anime', choices=['anime', 'cartoon', 'ghibli', 'comic'])
    parser.add_argument('--strength', type=float, default=0.75, help='변환 강도 (0.0-1.0)')
    parser.add_argument('--prompt', default='', help='추가 프롬프트')
    parser.add_argument('--steps', type=int, default=30, help='생성 스텝 수')
    parser.add_argument('--guidance', type=float, default=7.5, help='가이던스 스케일')

    args = parser.parse_args()

    print_progress(5, "초기화 중...")

    # 입력 파일 확인
    if not os.path.exists(args.input):
        print(f"ERROR: 입력 파일을 찾을 수 없습니다: {args.input}", file=sys.stderr)
        sys.exit(1)

    print_progress(10, "라이브러리 로딩...")

    try:
        import torch
        from PIL import Image
        from diffusers import (
            StableDiffusionImg2ImgPipeline,
            StableDiffusionXLImg2ImgPipeline,
            DPMSolverMultistepScheduler,
            AutoencoderKL
        )
        from diffusers.utils import load_image
        import numpy as np

    except ImportError as e:
        print(f"ERROR: 필요한 라이브러리가 설치되지 않았습니다: {e}", file=sys.stderr)
        print("setup.bat을 실행하여 설치해주세요.", file=sys.stderr)
        sys.exit(1)

    print_progress(15, "GPU 확인...")

    # GPU 설정
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    if device == "cpu":
        print("WARNING: GPU를 사용할 수 없습니다. CPU로 실행합니다 (느림).", file=sys.stderr)

    print(f"Device: {device}", flush=True)
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB", flush=True)

    print_progress(20, "모델 로딩...")

    # 스타일별 모델 및 프롬프트 설정
    style_configs = {
        'anime': {
            'model': 'cagliostrolab/animagine-xl-3.1',  # 애니메이션 특화 SDXL
            'prompt_prefix': 'anime artwork, anime style, vibrant colors, detailed, masterpiece, best quality, ',
            'negative': 'photo, realistic, 3d, deformed, ugly, blurry, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, low quality, worst quality',
            'guidance': 7.0,
            'strength': 0.7
        },
        'cartoon': {
            'model': 'stabilityai/stable-diffusion-xl-base-1.0',
            'prompt_prefix': 'cartoon style, pixar disney style, 3d cartoon, colorful, smooth shading, cute character, high quality, ',
            'negative': 'anime, realistic photo, dark, scary, violent, deformed, ugly, bad anatomy, blurry',
            'guidance': 8.0,
            'strength': 0.75
        },
        'ghibli': {
            'model': 'cagliostrolab/animagine-xl-3.1',
            'prompt_prefix': 'studio ghibli style, ghibli anime, hayao miyazaki style, soft watercolor, pastoral scene, whimsical, detailed background, masterpiece, ',
            'negative': 'photo, realistic, 3d, dark, modern, urban, deformed, ugly, blurry, low quality',
            'guidance': 7.5,
            'strength': 0.7
        },
        'comic': {
            'model': 'stabilityai/stable-diffusion-xl-base-1.0',
            'prompt_prefix': 'comic book style, american comic art, bold ink lines, halftone dots, dynamic pose, superhero comic, vibrant colors, high contrast, ',
            'negative': 'anime, photo, realistic, soft shading, pastel colors, deformed, ugly, blurry',
            'guidance': 8.5,
            'strength': 0.8
        }
    }

    config = style_configs.get(args.style, style_configs['anime'])

    # 모델 로드
    try:
        print_progress(25, f"모델 다운로드/로딩: {config['model']}")

        # SDXL 모델 사용
        pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
            config['model'],
            torch_dtype=dtype,
            use_safetensors=True,
            variant="fp16" if dtype == torch.float16 else None
        )

        # 스케줄러 설정 (빠른 샘플링)
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            pipe.scheduler.config,
            use_karras_sigmas=True,
            algorithm_type="sde-dpmsolver++"
        )

        pipe = pipe.to(device)

        # 메모리 최적화
        if device == "cuda":
            pipe.enable_model_cpu_offload()
            try:
                pipe.enable_xformers_memory_efficient_attention()
                print("xformers 활성화됨", flush=True)
            except:
                print("xformers 미사용", flush=True)

    except Exception as e:
        print(f"ERROR: 모델 로딩 실패: {e}", file=sys.stderr)
        sys.exit(1)

    print_progress(50, "이미지 처리 중...")

    # 이미지 로드 및 전처리
    try:
        init_image = load_image(args.input)

        # 이미지 리사이즈 (SDXL 최적 크기)
        max_size = 1024
        width, height = init_image.size

        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))

        # 8의 배수로 맞추기
        new_width = (new_width // 8) * 8
        new_height = (new_height // 8) * 8

        init_image = init_image.resize((new_width, new_height), Image.LANCZOS)
        init_image = init_image.convert("RGB")

        print(f"Image size: {new_width}x{new_height}", flush=True)

    except Exception as e:
        print(f"ERROR: 이미지 로딩 실패: {e}", file=sys.stderr)
        sys.exit(1)

    print_progress(60, "AI 이미지 생성 중...")

    # 프롬프트 구성
    full_prompt = config['prompt_prefix']
    if args.prompt:
        full_prompt += args.prompt + ", "
    full_prompt += "high quality, detailed"

    # 강도 조정 (사용자 설정 또는 스타일 기본값)
    strength = args.strength if args.strength != 0.75 else config['strength']
    guidance = args.guidance if args.guidance != 7.5 else config['guidance']

    print(f"Prompt: {full_prompt[:100]}...", flush=True)
    print(f"Strength: {strength}, Guidance: {guidance}", flush=True)

    # 이미지 생성
    try:
        with torch.inference_mode():
            result = pipe(
                prompt=full_prompt,
                negative_prompt=config['negative'],
                image=init_image,
                strength=strength,
                guidance_scale=guidance,
                num_inference_steps=args.steps,
                generator=torch.Generator(device=device).manual_seed(42)
            )

        output_image = result.images[0]

    except Exception as e:
        print(f"ERROR: 이미지 생성 실패: {e}", file=sys.stderr)
        sys.exit(1)

    print_progress(90, "이미지 저장 중...")

    # 출력 저장
    try:
        # 출력 디렉토리 생성
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # PNG로 저장 (고품질)
        output_image.save(str(output_path), "PNG", optimize=True)

        print(f"Saved: {output_path}", flush=True)

    except Exception as e:
        print(f"ERROR: 저장 실패: {e}", file=sys.stderr)
        sys.exit(1)

    print_progress(100, "완료!")
    print("SUCCESS", flush=True)

    # 메모리 정리
    if device == "cuda":
        del pipe
        torch.cuda.empty_cache()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
IMG AI Studio - 설치 스크립트
RTX 5060 Ti 16GB 최적화
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description=""):
    """명령어 실행"""
    print(f"\n{'='*50}")
    print(f"[*] {description}")
    print(f"[>] {cmd}")
    print('='*50)

    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"[!] 경고: 명령어가 실패했습니다 (코드: {result.returncode})")
        return False
    return True

def check_python():
    """Python 버전 확인"""
    version = sys.version_info
    print(f"[*] Python 버전: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("[!] Python 3.10 이상이 필요합니다!")
        return False
    return True

def check_gpu():
    """GPU 확인"""
    try:
        result = subprocess.run(
            'nvidia-smi --query-gpu=name,memory.total --format=csv,noheader',
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            gpu_info = result.stdout.strip()
            print(f"[*] GPU 감지됨: {gpu_info}")
            return True
    except:
        pass

    print("[!] NVIDIA GPU를 찾을 수 없습니다.")
    print("    - NVIDIA 드라이버가 설치되어 있는지 확인하세요.")
    print("    - RTX 5060 Ti를 사용하려면 최신 드라이버가 필요합니다.")
    return False

def install_pytorch():
    """PyTorch 설치 (CUDA 12.4)"""
    # RTX 50시리즈는 CUDA 12.4 이상 필요
    cmd = (
        "pip install torch torchvision torchaudio "
        "--index-url https://download.pytorch.org/whl/cu124"
    )
    return run_command(cmd, "PyTorch + CUDA 12.4 설치")

def verify_pytorch():
    """PyTorch CUDA 확인"""
    try:
        import torch
        print(f"\n[*] PyTorch 버전: {torch.__version__}")
        print(f"[*] CUDA 사용 가능: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            print(f"[*] CUDA 버전: {torch.version.cuda}")
            print(f"[*] GPU 이름: {torch.cuda.get_device_name(0)}")
            print(f"[*] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            return True
        else:
            print("[!] CUDA를 사용할 수 없습니다.")
            return False
    except ImportError:
        print("[!] PyTorch가 설치되지 않았습니다.")
        return False

def install_dependencies():
    """의존성 패키지 설치"""
    packages = [
        ("diffusers>=0.30.0", "Diffusers (Stable Diffusion)"),
        ("transformers>=4.40.0", "Transformers"),
        ("accelerate>=0.30.0", "Accelerate"),
        ("safetensors>=0.4.0", "Safetensors"),
        ("Pillow>=10.0.0", "Pillow (이미지 처리)"),
        ("opencv-python>=4.8.0", "OpenCV"),
        ("controlnet-aux>=0.0.7", "ControlNet Auxiliary"),
        ("xformers>=0.0.27", "xFormers (메모리 최적화)"),
        ("huggingface-hub>=0.23.0", "HuggingFace Hub"),
        ("tqdm>=4.66.0", "tqdm (진행률 표시)"),
        ("omegaconf>=2.3.0", "OmegaConf"),
        ("einops>=0.7.0", "einops"),
    ]

    for package, description in packages:
        run_command(f"pip install {package}", f"{description} 설치")

def download_models():
    """AI 모델 사전 다운로드"""
    print("\n[*] AI 모델 다운로드 (첫 실행 시 자동 다운로드)")
    print("    - animagine-xl-3.1 (애니메이션 특화)")
    print("    - stable-diffusion-xl-base-1.0")
    print("\n    모델은 첫 이미지 생성 시 자동으로 다운로드됩니다.")
    print("    (총 약 10-15GB 필요)")

    # 선택적 사전 다운로드
    response = input("\n    지금 모델을 미리 다운로드하시겠습니까? (y/n): ").strip().lower()

    if response == 'y':
        try:
            from diffusers import StableDiffusionXLImg2ImgPipeline
            import torch

            print("\n[*] 애니메이션 모델 다운로드 중...")
            pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
                "cagliostrolab/animagine-xl-3.1",
                torch_dtype=torch.float16,
                use_safetensors=True,
                variant="fp16"
            )
            del pipe

            print("\n[*] SDXL 기본 모델 다운로드 중...")
            pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                torch_dtype=torch.float16,
                use_safetensors=True,
                variant="fp16"
            )
            del pipe

            print("\n[+] 모델 다운로드 완료!")

        except Exception as e:
            print(f"\n[!] 모델 다운로드 중 오류: {e}")
            print("    나중에 첫 이미지 생성 시 자동으로 다운로드됩니다.")

def create_test_script():
    """테스트 스크립트 생성"""
    test_code = '''
import torch
print("=" * 50)
print("IMG AI Studio - 시스템 테스트")
print("=" * 50)

print(f"\\nPyTorch: {torch.__version__}")
print(f"CUDA 사용 가능: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA 버전: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # 간단한 GPU 테스트
    x = torch.randn(1000, 1000, device='cuda')
    y = torch.randn(1000, 1000, device='cuda')
    z = torch.matmul(x, y)
    print(f"\\nGPU 연산 테스트: 성공!")

try:
    from diffusers import StableDiffusionXLImg2ImgPipeline
    print("\\nDiffusers: 설치됨")
except ImportError:
    print("\\nDiffusers: 설치 필요")

print("\\n" + "=" * 50)
print("테스트 완료!")
print("=" * 50)
'''

    script_path = Path(__file__).parent / "test_system.py"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(test_code)

    print(f"\n[*] 테스트 스크립트 생성됨: {script_path}")

def main():
    print("=" * 60)
    print("  IMG AI Studio 설치 프로그램")
    print("  RTX 5060 Ti 16GB 최적화")
    print("=" * 60)

    # 1. Python 확인
    print("\n[Step 1/6] Python 확인...")
    if not check_python():
        print("\n[!] Python 3.10 이상을 설치하고 다시 실행하세요.")
        sys.exit(1)

    # 2. GPU 확인
    print("\n[Step 2/6] GPU 확인...")
    gpu_available = check_gpu()

    if not gpu_available:
        response = input("\nGPU 없이 계속하시겠습니까? (CPU만 사용, 매우 느림) (y/n): ")
        if response.lower() != 'y':
            print("\n[!] GPU 드라이버를 설치한 후 다시 실행하세요.")
            sys.exit(1)

    # 3. pip 업그레이드
    print("\n[Step 3/6] pip 업그레이드...")
    run_command("python -m pip install --upgrade pip", "pip 업그레이드")

    # 4. PyTorch 설치
    print("\n[Step 4/6] PyTorch 설치...")
    install_pytorch()

    # PyTorch 확인
    if not verify_pytorch():
        print("\n[!] PyTorch 설치에 실패했습니다.")
        print("    수동으로 설치하세요: https://pytorch.org/get-started/locally/")

    # 5. 의존성 설치
    print("\n[Step 5/6] 의존성 패키지 설치...")
    install_dependencies()

    # 6. 모델 다운로드 (선택)
    print("\n[Step 6/6] AI 모델 설정...")
    download_models()

    # 테스트 스크립트 생성
    create_test_script()

    # 완료
    print("\n" + "=" * 60)
    print("  설치 완료!")
    print("=" * 60)
    print("""
다음 단계:
1. 테스트 실행: python python/test_system.py
2. XAMPP Apache 시작
3. 브라우저에서 http://localhost/img_ai 접속
4. 이미지 촬영/업로드 후 AI 변환 시작!

문제 발생 시:
- GPU 드라이버 최신 버전으로 업데이트
- CUDA Toolkit 12.4 설치 확인
- 가상 메모리 32GB 이상 설정 확인
""")

if __name__ == "__main__":
    main()

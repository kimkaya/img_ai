<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$response = [
    'ready' => false,
    'gpu' => '확인 중...',
    'model' => '확인 필요',
    'python' => false,
    'cuda' => false
];

try {
    // Python 확인
    exec('python --version 2>&1', $pythonOutput, $pythonReturn);
    $response['python'] = $pythonReturn === 0;
    $response['python_version'] = $pythonOutput[0] ?? 'N/A';

    // CUDA/GPU 확인 (nvidia-smi)
    exec('nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits 2>&1', $gpuOutput, $gpuReturn);

    if ($gpuReturn === 0 && !empty($gpuOutput[0])) {
        $gpuInfo = explode(', ', $gpuOutput[0]);
        $response['gpu'] = trim($gpuInfo[0] ?? 'Unknown');
        $response['vram_total'] = isset($gpuInfo[1]) ? intval($gpuInfo[1]) . ' MB' : 'N/A';
        $response['vram_free'] = isset($gpuInfo[2]) ? intval($gpuInfo[2]) . ' MB' : 'N/A';
        $response['cuda'] = true;
    } else {
        $response['gpu'] = 'GPU 미감지 (드라이버 설치 필요)';
    }

    // 모델 확인
    $modelDir = __DIR__ . '/../models/';
    $modelFiles = glob($modelDir . '*.{safetensors,ckpt,bin}', GLOB_BRACE);

    if (!empty($modelFiles)) {
        $response['model'] = basename($modelFiles[0]);
        $response['model_ready'] = true;
    } else {
        // 기본 모델 확인 (diffusers 캐시)
        $homeDir = getenv('USERPROFILE') ?: getenv('HOME');
        $cacheDir = $homeDir . '/.cache/huggingface/';

        if (is_dir($cacheDir)) {
            $response['model'] = '캐시된 모델 사용 가능';
            $response['model_ready'] = true;
        } else {
            $response['model'] = '설치 필요';
            $response['model_ready'] = false;
        }
    }

    // PyTorch CUDA 확인
    $checkScript = 'import torch; print("CUDA:" + str(torch.cuda.is_available()) + ",Device:" + (torch.cuda.get_device_name(0) if torch.cuda.is_available() else "None"))';
    exec("python -c \"$checkScript\" 2>&1", $torchOutput, $torchReturn);

    if ($torchReturn === 0 && !empty($torchOutput[0])) {
        if (strpos($torchOutput[0], 'CUDA:True') !== false) {
            $response['pytorch_cuda'] = true;
            preg_match('/Device:(.+)/', $torchOutput[0], $matches);
            if (!empty($matches[1]) && $matches[1] !== 'None') {
                $response['gpu'] = trim($matches[1]);
            }
        }
    }

    // 전체 준비 상태
    $response['ready'] = $response['python'] &&
                         ($response['cuda'] || ($response['pytorch_cuda'] ?? false)) &&
                         ($response['model_ready'] ?? false);

    // 디스크 공간 확인
    $freeSpace = disk_free_space(__DIR__ . '/../');
    $response['disk_free'] = round($freeSpace / (1024 * 1024 * 1024), 2) . ' GB';

} catch (Exception $e) {
    $response['error'] = $e->getMessage();
}

echo json_encode($response, JSON_UNESCAPED_UNICODE);

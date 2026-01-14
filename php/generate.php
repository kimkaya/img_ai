<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$response = ['success' => false];

try {
    // JSON 입력 받기
    $input = json_decode(file_get_contents('php://input'), true);

    if (!$input || !isset($input['filename'])) {
        throw new Exception('잘못된 요청입니다.');
    }

    $filename = basename($input['filename']); // 보안: path traversal 방지
    $style = $input['style'] ?? 'anime';
    $strength = floatval($input['strength'] ?? 0.75);
    $prompt = $input['prompt'] ?? '';

    // 파일 존재 확인
    $uploadDir = __DIR__ . '/../uploads/';
    $outputDir = __DIR__ . '/../outputs/';
    $pythonDir = __DIR__ . '/../python/';

    $inputPath = $uploadDir . $filename;

    if (!file_exists($inputPath)) {
        throw new Exception('입력 이미지를 찾을 수 없습니다.');
    }

    // 출력 디렉토리 확인
    if (!is_dir($outputDir)) {
        mkdir($outputDir, 0777, true);
    }

    // 출력 파일명 생성
    $outputFilename = 'gen_' . pathinfo($filename, PATHINFO_FILENAME) . '_' . $style . '.png';
    $outputPath = $outputDir . $outputFilename;

    // 진행 상태 파일
    $progressFile = $uploadDir . pathinfo($filename, PATHINFO_FILENAME) . '_progress.json';
    file_put_contents($progressFile, json_encode([
        'status' => 'processing',
        'progress' => 10,
        'message' => 'AI 처리 시작'
    ]));

    // 스타일별 프롬프트 설정
    $stylePrompts = [
        'anime' => 'anime style, anime artwork, vibrant colors, detailed anime illustration, high quality anime art',
        'cartoon' => 'cartoon style, disney pixar style, 3d rendered, colorful, smooth shading, cartoon character',
        'ghibli' => 'studio ghibli style, ghibli anime, hayao miyazaki style, soft colors, detailed background, whimsical',
        'comic' => 'comic book style, marvel dc comics, bold lines, halftone dots, dynamic, superhero comic art'
    ];

    $basePrompt = $stylePrompts[$style] ?? $stylePrompts['anime'];
    $fullPrompt = $prompt ? "$basePrompt, $prompt" : $basePrompt;

    // Python 스크립트 실행
    $pythonScript = $pythonDir . 'generate.py';

    // Windows에서 Python 경로
    $pythonPath = 'python'; // 또는 전체 경로

    $command = sprintf(
        '%s "%s" --input "%s" --output "%s" --style "%s" --strength %f --prompt "%s" 2>&1',
        $pythonPath,
        $pythonScript,
        $inputPath,
        $outputPath,
        $style,
        $strength,
        addslashes($fullPrompt)
    );

    // 비동기 실행 (Windows)
    $descriptorSpec = [
        0 => ['pipe', 'r'],
        1 => ['pipe', 'w'],
        2 => ['pipe', 'w']
    ];

    $process = proc_open($command, $descriptorSpec, $pipes);

    if (is_resource($process)) {
        // 출력 읽기 (타임아웃 설정)
        stream_set_blocking($pipes[1], false);
        stream_set_blocking($pipes[2], false);

        $output = '';
        $error = '';
        $startTime = time();
        $timeout = 300; // 5분 타임아웃

        while (true) {
            $status = proc_get_status($process);

            if (!$status['running']) {
                break;
            }

            if (time() - $startTime > $timeout) {
                proc_terminate($process);
                throw new Exception('처리 시간이 초과되었습니다.');
            }

            $output .= stream_get_contents($pipes[1]);
            $error .= stream_get_contents($pipes[2]);

            // 진행률 업데이트 파싱
            if (preg_match('/PROGRESS:(\d+)/', $output, $matches)) {
                file_put_contents($progressFile, json_encode([
                    'status' => 'processing',
                    'progress' => intval($matches[1]),
                    'message' => 'AI 처리 중...'
                ]));
            }

            usleep(500000); // 0.5초 대기
        }

        fclose($pipes[0]);
        fclose($pipes[1]);
        fclose($pipes[2]);

        $returnCode = proc_close($process);

        if ($returnCode !== 0 && !file_exists($outputPath)) {
            // 오류 로그 저장
            file_put_contents(__DIR__ . '/../logs/error_' . date('Ymd_His') . '.log',
                "Command: $command\nOutput: $output\nError: $error\nReturn: $returnCode");

            throw new Exception('AI 처리 중 오류가 발생했습니다: ' . $error);
        }
    } else {
        throw new Exception('Python 프로세스를 시작할 수 없습니다.');
    }

    // 결과 확인
    if (!file_exists($outputPath)) {
        throw new Exception('이미지 생성에 실패했습니다.');
    }

    // 진행 완료
    file_put_contents($progressFile, json_encode([
        'status' => 'complete',
        'progress' => 100,
        'message' => '완료'
    ]));

    // 결과 메타데이터 저장
    $resultMeta = [
        'input' => $filename,
        'output' => $outputFilename,
        'style' => $style,
        'strength' => $strength,
        'prompt' => $fullPrompt,
        'created_at' => date('Y-m-d H:i:s')
    ];

    file_put_contents(
        $outputDir . pathinfo($outputFilename, PATHINFO_FILENAME) . '.json',
        json_encode($resultMeta, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)
    );

    $response = [
        'success' => true,
        'output' => $outputFilename,
        'message' => '이미지 생성 완료'
    ];

} catch (Exception $e) {
    $response = [
        'success' => false,
        'error' => $e->getMessage()
    ];

    // 진행 실패 기록
    if (isset($progressFile)) {
        file_put_contents($progressFile, json_encode([
            'status' => 'failed',
            'progress' => 0,
            'message' => $e->getMessage()
        ]));
    }
}

echo json_encode($response, JSON_UNESCAPED_UNICODE);

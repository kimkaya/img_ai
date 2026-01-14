<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$response = ['success' => false];

try {
    // 업로드 디렉토리 확인
    $uploadDir = __DIR__ . '/../uploads/';
    if (!is_dir($uploadDir)) {
        mkdir($uploadDir, 0777, true);
    }

    // 파일 확인
    if (!isset($_FILES['image']) || $_FILES['image']['error'] !== UPLOAD_ERR_OK) {
        throw new Exception('이미지 업로드에 실패했습니다.');
    }

    $file = $_FILES['image'];

    // 파일 타입 검증
    $allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    $mimeType = finfo_file($finfo, $file['tmp_name']);
    finfo_close($finfo);

    if (!in_array($mimeType, $allowedTypes)) {
        throw new Exception('지원하지 않는 이미지 형식입니다.');
    }

    // 파일 크기 제한 (20MB)
    if ($file['size'] > 20 * 1024 * 1024) {
        throw new Exception('파일 크기가 너무 큽니다. (최대 20MB)');
    }

    // 고유 파일명 생성
    $extension = pathinfo($file['name'], PATHINFO_EXTENSION);
    if (!$extension) {
        $extension = 'jpg';
    }
    $filename = 'img_' . date('Ymd_His') . '_' . uniqid() . '.' . $extension;
    $filepath = $uploadDir . $filename;

    // 파일 이동
    if (!move_uploaded_file($file['tmp_name'], $filepath)) {
        throw new Exception('파일 저장에 실패했습니다.');
    }

    // 메타데이터 저장
    $style = $_POST['style'] ?? 'anime';
    $strength = $_POST['strength'] ?? 0.75;
    $prompt = $_POST['prompt'] ?? '';

    $metadata = [
        'filename' => $filename,
        'original_name' => $file['name'],
        'style' => $style,
        'strength' => $strength,
        'prompt' => $prompt,
        'uploaded_at' => date('Y-m-d H:i:s'),
        'status' => 'uploaded'
    ];

    $metaFile = $uploadDir . pathinfo($filename, PATHINFO_FILENAME) . '.json';
    file_put_contents($metaFile, json_encode($metadata, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

    $response = [
        'success' => true,
        'filename' => $filename,
        'message' => '업로드 완료'
    ];

} catch (Exception $e) {
    $response = [
        'success' => false,
        'error' => $e->getMessage()
    ];
}

echo json_encode($response, JSON_UNESCAPED_UNICODE);

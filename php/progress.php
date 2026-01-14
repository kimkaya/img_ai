<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$response = ['status' => 'unknown', 'progress' => 0];

try {
    $filename = $_GET['filename'] ?? '';

    if (empty($filename)) {
        throw new Exception('파일명이 필요합니다.');
    }

    $filename = basename($filename); // 보안
    $uploadDir = __DIR__ . '/../uploads/';
    $progressFile = $uploadDir . pathinfo($filename, PATHINFO_FILENAME) . '_progress.json';

    if (file_exists($progressFile)) {
        $data = json_decode(file_get_contents($progressFile), true);
        $response = $data ?: $response;
    }

} catch (Exception $e) {
    $response['error'] = $e->getMessage();
}

echo json_encode($response, JSON_UNESCAPED_UNICODE);

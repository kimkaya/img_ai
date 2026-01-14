<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$response = ['success' => false, 'images' => []];

try {
    $outputDir = __DIR__ . '/../outputs/';

    if (!is_dir($outputDir)) {
        mkdir($outputDir, 0777, true);
        echo json_encode($response, JSON_UNESCAPED_UNICODE);
        exit;
    }

    $images = [];
    $files = glob($outputDir . '*.{png,jpg,jpeg,webp}', GLOB_BRACE);

    // 최신순 정렬
    usort($files, function($a, $b) {
        return filemtime($b) - filemtime($a);
    });

    // 최대 50개
    $files = array_slice($files, 0, 50);

    foreach ($files as $file) {
        $filename = basename($file);
        $metaFile = $outputDir . pathinfo($filename, PATHINFO_FILENAME) . '.json';

        $meta = [];
        if (file_exists($metaFile)) {
            $meta = json_decode(file_get_contents($metaFile), true) ?: [];
        }

        $images[] = [
            'output' => $filename,
            'input' => $meta['input'] ?? '',
            'style' => $meta['style'] ?? 'unknown',
            'date' => date('Y-m-d H:i', filemtime($file)),
            'size' => filesize($file)
        ];
    }

    $response = [
        'success' => true,
        'images' => $images,
        'total' => count($images)
    ];

} catch (Exception $e) {
    $response['error'] = $e->getMessage();
}

echo json_encode($response, JSON_UNESCAPED_UNICODE);

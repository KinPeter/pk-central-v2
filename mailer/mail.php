<?php

// https://github.com/PHPMailer/PHPMailer
use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

require './phpmailer/src/Exception.php';
require './phpmailer/src/PHPMailer.php';
require './phpmailer/src/SMTP.php';

header('Content-Type: application/json');

$apiKey = 'api-key-1234567890'; // Replace with your actual API key

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $data = json_decode(file_get_contents('php://input'), true);

    // Check if the API key is present and valid
    if (!isset($data['apiKey']) || $data['apiKey'] !== $apiKey) {
        http_response_code(401);
        echo json_encode(['message' => 'Unauthorized. Invalid API key.']);
        exit;
    }

    if (!isset($data['to'], $data['subject'], $data['html'])) {
        http_response_code(400);
        echo json_encode(['message' => 'Invalid request. Missing required fields.']);
        exit;
    }

    $mail = new PHPMailer(true);

    try {
        // SMTP configuration
        $mail->isSMTP();
        $mail->Host = 'mail.domain.com';
        $mail->SMTPAuth = true;
        $mail->Username = 'name@domain.com';
        $mail->Password = 'password';
        $mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
        $mail->Port = 587;

        // Email settings
        $mail->setFrom('name@domain.com', 'domain.com');
        $mail->addAddress($data['to']);
        $mail->Subject = $data['subject'];
        $mail->isHTML(true);
        $mail->Body = $data['html'];

        // Handle multiple attachments if present
        if (isset($data['attachments']) && is_array($data['attachments'])) {
            foreach ($data['attachments'] as $attachment) {
                if (isset($attachment['content'], $attachment['filename'])) {
                    $mail->addStringAttachment($attachment['content'], $attachment['filename']);
                }
            }
        }

        // Backward compatibility: handle single attachment fields if present
        if (isset($data['attachmentContent'], $data['attachmentFilename'])) {
            $mail->addStringAttachment($data['attachmentContent'], $data['attachmentFilename']);
        }

        $mail->send();
        http_response_code(200);
        echo json_encode(['message' => 'Email sent successfully.']);
    } catch (Exception $e) {
        http_response_code(500);
        echo json_encode(['message' => 'Email could not be sent. Mailer Error: ' . $mail->ErrorInfo]);
    }
} else {
    http_response_code(405);
    echo json_encode(['message' => 'Method not allowed.']);
}
?>
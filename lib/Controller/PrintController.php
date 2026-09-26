<?php

declare(strict_types=1);

namespace OCA\CupsPrint\Controller;

use OCP\AppFramework\Controller;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\Attribute\FrontpageRoute;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\DataResponse;
use OCP\Files\File;
use OCP\Files\IRootFolder;
use OCP\Http\Client\IClientService;
use OCP\IConfig;
use OCP\IL10N;
use OCP\IRequest;
use Psr\Log\LoggerInterface;

class PrintController extends Controller {
	/** Only formats CUPS can handle directly are accepted. */
	private const ALLOWED_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg', 'txt', 'md'];
	/** "1-3,5" only; the relay turns this into the CUPS page-ranges option. */
	private const PAGE_RANGES_PATTERN = '/^[0-9,\-\s]{1,64}$/';

	public function __construct(
		string $appName,
		IRequest $request,
		private IRootFolder $rootFolder,
		private IClientService $clientService,
		private IConfig $config,
		private IL10N $l,
		private LoggerInterface $logger,
		private ?string $userId,
	) {
		parent::__construct($appName, $request);
	}

	#[NoAdminRequired]
	#[FrontpageRoute(verb: 'POST', url: '/print')]
	public function print(int $fileId, int $copies = 1, string $color = 'color', string $pageRanges = ''): DataResponse {
		if ($this->userId === null) {
			return new DataResponse(['error' => $this->l->t('Authentication required')], Http::STATUS_UNAUTHORIZED);
		}

		$node = $this->findFile($fileId);
		if ($node === null) {
			return new DataResponse(['error' => $this->l->t('File not found')], Http::STATUS_NOT_FOUND);
		}
		if (!$node->isReadable()) {
			return new DataResponse(['error' => $this->l->t('You are not allowed to read this file')], Http::STATUS_FORBIDDEN);
		}

		$extension = strtolower($node->getExtension());
		if (!in_array($extension, self::ALLOWED_EXTENSIONS, true)) {
			return new DataResponse(
				['error' => $this->l->t('Only PDF, PNG, JPEG, text and Markdown files can be printed')],
				Http::STATUS_UNSUPPORTED_MEDIA_TYPE
			);
		}

		$ranges = trim($pageRanges);
		if ($ranges !== '' && !preg_match(self::PAGE_RANGES_PATTERN, $ranges)) {
			return new DataResponse(
				['error' => $this->l->t('The page range is not valid')],
				Http::STATUS_BAD_REQUEST
			);
		}

		$url = rtrim($this->config->getAppValue('cups_print', 'relay_url', ''), '/');
		$token = $this->config->getAppValue('cups_print', 'relay_token', '');
		if ($url === '' || $token === '') {
			return new DataResponse(
				['error' => $this->l->t('The print relay is not configured yet')],
				Http::STATUS_SERVICE_UNAVAILABLE
			);
		}

		$handle = $node->fopen('r');
		if ($handle === false) {
			return new DataResponse(['error' => $this->l->t('Could not open the file')], Http::STATUS_INTERNAL_SERVER_ERROR);
		}

		try {
			$headers = [
				'Authorization' => 'Bearer ' . $token,
				'Content-Type' => 'application/octet-stream',
				'X-Print-Filename' => rawurlencode($node->getName()),
				'X-Print-Copies' => (string) max(1, min(99, $copies)),
				'X-Print-Color' => $color === 'monochrome' ? 'monochrome' : 'color',
			];
			if ($ranges !== '') {
				$headers['X-Print-Ranges'] = $ranges;
			}
			$response = $this->clientService->newClient()->post($url . '/print', [
				'headers' => $headers,
				'body' => $handle,
				'timeout' => 60,
				'nextcloud' => ['allow_local_address' => true],
			]);
		} catch (\Throwable $error) {
			$this->logger->error('cups_print: relay request failed', ['exception' => $error]);
			return new DataResponse(['error' => $this->l->t('Could not reach the print relay')], Http::STATUS_BAD_GATEWAY);
		} finally {
			if (is_resource($handle)) {
				fclose($handle);
			}
		}

		$result = json_decode((string)$response->getBody(), true);
		if (!is_array($result) || !isset($result['job'])) {
			return new DataResponse(['error' => $this->l->t('Could not confirm the print job')], Http::STATUS_BAD_GATEWAY);
		}

		return new DataResponse(['job' => (string)$result['job']]);
	}

	private function findFile(int $fileId): ?File {
		$folder = $this->rootFolder->getUserFolder($this->userId);
		foreach ($folder->getById($fileId) as $node) {
			if ($node instanceof File) {
				return $node;
			}
		}
		return null;
	}
}

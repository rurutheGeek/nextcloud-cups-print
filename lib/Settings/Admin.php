<?php

declare(strict_types=1);

namespace OCA\CupsPrint\Settings;

use OCP\AppFramework\Http\TemplateResponse;
use OCP\IConfig;
use OCP\IL10N;
use OCP\IRequest;
use OCP\IURLGenerator;
use OCP\Settings\IDelegatedSettings;

class Admin implements IDelegatedSettings {
	public function __construct(
		private IConfig $config,
		private IRequest $request,
		private IURLGenerator $url,
		private IL10N $l,
	) {
	}

	public function getForm(): TemplateResponse {
		return new TemplateResponse('cups_print', 'admin', [
			'relay_url' => $this->config->getAppValue('cups_print', 'relay_url', ''),
			'token_set' => $this->config->getAppValue('cups_print', 'relay_token', '') !== '',
			'status' => (string)$this->request->getParam('cups_print', ''),
			'save_url' => $this->url->linkToRoute('cups_print.settings.save'),
		]);
	}

	public function getSection(): string {
		return 'cups_print';
	}

	public function getPriority(): int {
		return 50;
	}

	public function getName(): ?string {
		return $this->l->t('CUPS Print');
	}

	public function getAuthorizedAppConfig(): array {
		return ['cups_print' => ['/relay_url/', '/relay_token/']];
	}
}

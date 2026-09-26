<?php

declare(strict_types=1);

namespace OCA\CupsPrint\Settings;

use OCP\IL10N;
use OCP\IURLGenerator;
use OCP\Settings\IIconSection;

class AdminSection implements IIconSection {
	public function __construct(
		private IL10N $l,
		private IURLGenerator $url,
	) {
	}

	public function getID(): string {
		return 'cups_print';
	}

	public function getName(): string {
		return $this->l->t('CUPS Print');
	}

	public function getPriority(): int {
		return 50;
	}

	public function getIcon(): string {
		return $this->url->imagePath('cups_print', 'app.svg');
	}
}

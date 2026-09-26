<?php
/**
 * @var \OCP\IL10N $l
 * @var array $_ the template parameters from Settings\Admin
 */
?>
<div id="cups_print" class="section">
	<h2><?php p($l->t('CUPS Print')); ?></h2>
	<p class="settings-hint">
		<?php p($l->t('URL of the print relay reachable from this Nextcloud server, e.g. http://192.168.1.10:6320. The relay and its setup are documented in the server/ directory of the app repository.')); ?>
	</p>

	<?php if ($_['status'] === 'ok'): ?>
		<p class="success"><?php p($l->t('Saved. The relay answered the health check.')); ?></p>
	<?php elseif ($_['status'] === 'unreachable'): ?>
		<p class="warning"><?php p($l->t('Saved, but the relay did not answer the health check. Check the URL, the token and the network.')); ?></p>
	<?php elseif ($_['status'] === 'incomplete'): ?>
		<p class="warning"><?php p($l->t('Saved. Set both the relay URL and the token to enable printing.')); ?></p>
	<?php endif; ?>

	<form method="post" action="<?php p($_['save_url']); ?>">
		<input type="hidden" name="requesttoken" value="<?php p($_['requesttoken']); ?>">
		<p>
			<label for="cups_print_relay_url"><?php p($l->t('Relay URL')); ?></label><br>
			<input type="url" id="cups_print_relay_url" name="relayUrl" class="text"
				style="width: 24em" value="<?php p($_['relay_url']); ?>"
				placeholder="http://192.168.1.10:6320">
		</p>
		<p>
			<label for="cups_print_relay_token"><?php p($l->t('Relay token')); ?></label><br>
			<input type="password" id="cups_print_relay_token" name="relayToken" class="text"
				style="width: 24em" value="" autocomplete="new-password"
				placeholder="<?php p($_['token_set'] ? $l->t('stored — leave empty to keep') : $l->t('shared secret')); ?>">
		</p>
		<?php if ($_['token_set']): ?>
			<p>
				<label>
					<input type="checkbox" name="clearToken" value="1">
					<?php p($l->t('Remove the stored token')); ?>
				</label>
			</p>
		<?php endif; ?>
		<button type="submit" class="button primary"><?php p($l->t('Save')); ?></button>
	</form>
</div>

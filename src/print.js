import { registerFileAction } from '@nextcloud/files'
import { translate as t } from '@nextcloud/l10n'
import { generateUrl } from '@nextcloud/router'
import axios from '@nextcloud/axios'

const PRINTABLE = ['pdf', 'png', 'jpg', 'jpeg', 'txt', 'md']
const toast = (method, message) => {
	if (window.OCP?.Toast?.[method]) {
		window.OCP.Toast[method](message)
	}
}

function element(tag, text, style) {
	const node = document.createElement(tag)
	if (text) {
		node.textContent = text
	}
	if (style) {
		node.style.cssText = style
	}
	return node
}

function showPrintDialog(filename) {
	return new Promise((resolve) => {
		const overlay = element('div', '', 'position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:10000;display:flex;align-items:center;justify-content:center')
		const box = element('div', '', 'background:var(--color-main-background,#fff);color:var(--color-main-text,#222);padding:20px;border-radius:8px;width:min(360px,92vw)')
		const close = (value) => {
			overlay.remove()
			resolve(value)
		}

		box.appendChild(element('h3', t('cups_print', 'Print'), 'margin-top:0'))
		box.appendChild(element('p', filename, 'font-size:13px;opacity:.8;margin-top:0;word-break:break-all'))

		const row = (label, input) => {
			const wrapper = element('label', '', 'display:block;margin:10px 0')
			wrapper.appendChild(element('span', label, 'display:block;font-size:12px;opacity:.8'))
			wrapper.appendChild(input)
			box.appendChild(wrapper)
		}

		const copies = document.createElement('input')
		copies.type = 'number'
		copies.className = 'input'
		copies.min = '1'
		copies.max = '99'
		copies.value = '1'
		copies.style.cssText = 'width:6em'
		row(t('cups_print', 'Copies'), copies)

		const color = document.createElement('select')
		color.className = 'input'
		for (const [value, label] of [
			['color', t('cups_print', 'Color')],
			['monochrome', t('cups_print', 'Monochrome')],
		]) {
			const option = document.createElement('option')
			option.value = value
			option.textContent = label
			color.appendChild(option)
		}
		row(t('cups_print', 'Color mode'), color)

		const ranges = document.createElement('input')
		ranges.type = 'text'
		ranges.className = 'input'
		ranges.placeholder = t('cups_print', 'e.g. 1-3,5 (empty = all pages)')
		ranges.style.cssText = 'width:100%'
		row(t('cups_print', 'Page range'), ranges)

		const actions = element('div', '', 'display:flex;gap:8px;margin-top:12px;flex-wrap:wrap')
		const submit = element('button', t('cups_print', 'Print'), '')
		submit.className = 'button primary'
		submit.addEventListener('click', () => close({
			copies: Math.max(1, Math.min(99, parseInt(copies.value, 10) || 1)),
			color: color.value,
			pageRanges: ranges.value.trim(),
		}))
		actions.appendChild(submit)
		const cancel = element('button', t('cups_print', 'Cancel'), '')
		cancel.className = 'button'
		cancel.addEventListener('click', () => close(null))
		actions.appendChild(cancel)
		box.appendChild(actions)

		overlay.addEventListener('click', (event) => {
			if (event.target === overlay) {
				close(null)
			}
		})
		overlay.appendChild(box)
		document.body.appendChild(overlay)
	})
}

registerFileAction({
	id: 'cups-print',
	displayName: () => t('cups_print', 'Print'),
	iconSvgInline: () => '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M6 3h12v4H6V3zm-4 6h20v8h-4v4H6v-4H2V9zm4 6v4h12v-4H6zm12-4a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/></svg>',
	enabled: ({ nodes }) => nodes.length === 1
		&& PRINTABLE.includes((nodes[0].extension || '').toLowerCase().replace(/^\./, '')),
	exec: async ({ nodes }) => {
		const [node] = nodes
		const options = await showPrintDialog(node.basename || '')
		if (!options) {
			return false
		}
		try {
			const { data } = await axios.post(generateUrl('/apps/cups_print/print'), {
				fileId: node.fileid,
				copies: options.copies,
				color: options.color,
				pageRanges: options.pageRanges,
			})
			toast('success', t('cups_print', 'Printed (job {job})', { job: data.job }))
			return true
		} catch (error) {
			toast('error', error?.response?.data?.error
				|| t('cups_print', 'Printing failed'))
			return false
		}
	},
	order: 25,
})

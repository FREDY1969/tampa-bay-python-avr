
(function ($, ucc) {
	ucc.menu = {};
	ucc.menu.handlers = {
		'open-package': function () {
			$.getJSON('/ajax/fs/examples', function(data) {
				var markup = $('<div class="center">\
									<p>Please choose a Package:</p>\
									<div class="margin"><select></select></div>\
									<div class="margin"><input type="button" value="Ok" class="modal-ok-button" />\
										<input type="button" value="Cancel" class="modal-cancel-button simplemodal-close" /></div>\
								</div>');
				$(data).each(function () {
					$('select', markup).append('<option value="' + this + '">' + this + '</option>');
				});
				$('.modal-ok-button', markup).click(function () {
					console.log($('select', markup).val());
					$.modal.close();
				});
				$(markup).modal();
			});
		},
		'save-current-word': function () {
			
		},
		'compile-program': function () {
			
		},
		'load-program': function () {
			
		}
	};
	
	$(function () {
		$('#menu a').click(function (e) {
			var href = $(this).attr('href');
			var hash_index = href.indexOf('#');
			if (hash_index >= 0) {
				var hash = href.slice(hash_index+1);
				ucc.menu.handlers[hash]();
			}
		});
	});
})(jQuery, ucc);

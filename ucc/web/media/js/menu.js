
(function ($, ucc) {
	ucc.menu = {};
	ucc.menu.handlers = {
		'open-package': function () {
			
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
